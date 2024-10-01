import scapy.all as scapy
from scapy.layers.dhcp import DHCP
from scapy.layers.inet import IP
from scapy.layers.l2 import Ether
import csv
import os
import threading
from tkinter import *
from tkinter import ttk, scrolledtext, messagebox
from netmiko import ConnectHandler

# Filterkriterien für Option 60
option_60_patterns = ["6000", "6100", "6200", "6300", "6400"]

# CSV-Datei Pfad
csv_file = "dhcp_devices.csv"

# Gesehene Geräte speichern (um doppelte Einträge zu vermeiden)
seen_devices = set()

# Flag, um den Discovery-Prozess zu stoppen
stop_discovery = False

# GUI erstellen
class DHCPGui:
    def __init__(self, root):
        self.root = root
        self.root.title("DHCP Discovery und Provisionierung")
        self.root.geometry("800x600")  # Breite für langen Text

        self.interface_var = StringVar()
        self.log_text = StringVar()

        # GUI Layout
        self.create_widgets()

    def create_widgets(self):
        # Interface Auswahl
        Label(self.root, text="Netzwerk-Interface auswählen:").pack(pady=10)
        self.interface_combo = ttk.Combobox(self.root, textvariable=self.interface_var, width=90)  # Breite um ein halbes Mal vergrößert
        self.interface_combo.pack()

        # Log Fenster
        Label(self.root, text="Log:").pack(pady=10)
        self.log_area = scrolledtext.ScrolledText(self.root, width=80, height=20)
        self.log_area.pack(padx=10, pady=10)

        # Buttons
        self.start_button = Button(self.root, text="Discovery Starten", command=self.start_discovery)
        self.start_button.pack(pady=5)

        self.stop_button = Button(self.root, text="Discovery Stoppen", command=self.stop_discovery_process, state=DISABLED)
        self.stop_button.pack(pady=5)

        self.provision_button = Button(self.root, text="Provisionierung Starten", command=self.open_provision_window, state=DISABLED)
        self.provision_button.pack(pady=5)

        # Button zum Beenden des Programms
        self.exit_button = Button(self.root, text="Beenden", command=self.exit_program)
        self.exit_button.pack(pady=10)

        # Interfaces laden
        self.load_interfaces()

    def log(self, message):
        self.log_area.insert(END, message + "\n")
        self.log_area.see(END)

    def load_interfaces(self):
        # Alle verfügbaren Interfaces abrufen
        interfaces = scapy.get_if_list()
        interface_list = []

        # Loopback-Interface ausschließen und Namen mit IP-Adressen kombinieren
        for interface in interfaces:
            if interface != "lo":
                try:
                    ip_addr = scapy.get_if_addr(interface)
                    interface_list.append(f"{interface} - {ip_addr}")  # Name + IP-Adresse
                except Exception as e:
                    # Wenn keine IP-Adresse zugeordnet ist, wird es übersprungen
                    interface_list.append(f"{interface} - Keine IP-Adresse")

        self.interface_combo['values'] = interface_list

        if interface_list:
            self.interface_combo.current(0)

    def start_discovery(self):
        self.start_button.config(state=DISABLED)
        self.stop_button.config(state=NORMAL)

        # Discovery-Thread starten
        thread = threading.Thread(target=self.discovery_thread)
        thread.start()

    def stop_discovery_process(self):
        global stop_discovery
        stop_discovery = True
        self.log("Discovery-Prozess wird gestoppt...")
        self.stop_button.config(state=DISABLED)

    def discovery_thread(self):
        global stop_discovery
        stop_discovery = False

        selected_interface = self.interface_var.get()

        if not selected_interface:
            messagebox.showerror("Fehler", "Bitte ein Interface auswählen")
            self.start_button.config(state=NORMAL)
            return

        # Extrahieren des Interface-Namens (vor dem Bindestrich)
        interface = selected_interface.split(" - ")[0]

        self.log(f"Überwache DHCP-Requests auf Interface: {interface}")

        # CSV-Datei vorbereiten
        if not os.path.exists(csv_file):
            with open(csv_file, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["MAC-Adresse", "IP-Adresse", "Option 60"])

        while not stop_discovery:
            scapy.sniff(iface=interface, filter="udp and (port 67 or port 68)", prn=self.dhcp_packet_callback, store=0, timeout=1)

        self.log("Discovery-Prozess beendet.")
        self.stop_button.config(state=DISABLED)
        self.provision_button.config(state=NORMAL)

    def dhcp_packet_callback(self, packet):
        if packet.haslayer(DHCP):
            mac_addr = packet[Ether].src
            ip_addr = packet[IP].src if IP in packet else "0.0.0.0"

            if ip_addr == "0.0.0.0":
                ip_addr = self.get_requested_ip(packet[DHCP].options)
                if ip_addr is None:
                    return

            for option in packet[DHCP].options:
                if option[0] == 'vendor_class_id':
                    option_60 = option[1].decode('utf-8')
                    if any(pattern in option_60 for pattern in option_60_patterns):
                        self.write_to_csv(mac_addr, ip_addr, option_60)
                        self.log(f"Erkanntes Gerät: {mac_addr}, {ip_addr}, {option_60}")
                    break

    def write_to_csv(self, mac, ip, option_60):
        global seen_devices
        if (mac, ip, option_60) not in seen_devices:
            seen_devices.add((mac, ip, option_60))
            with open(csv_file, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([mac, ip, option_60])

    def get_requested_ip(self, dhcp_options):
        for option in dhcp_options:
            if option[0] == 'requested_addr':
                return option[1]
        return None

    def open_provision_window(self):
        # Fenster öffnen, um Switches für die Provisionierung auszuwählen
        provision_window = Toplevel(self.root)
        provision_window.title("Switch Provisionierung")
        provision_window.geometry("400x500")

        Label(provision_window, text="Wählen Sie die zu provisionierenden Switches:").pack(pady=10)

        # Hostname-Eingabefeld
        Label(provision_window, text="Hostnamen-Präfix eingeben:").pack(pady=5)
        self.hostname_prefix_var = StringVar(value="pyswitch")
        self.hostname_entry = Entry(provision_window, textvariable=self.hostname_prefix_var)
        self.hostname_entry.pack(pady=5)

        # Gefundene Hosts laden
        hosts = self.get_hosts_from_csv(csv_file)

        # Checkbuttons für jeden gefundenen Switch
        self.selected_switches = []
        for host in hosts:
            var = BooleanVar()
            cb = Checkbutton(provision_window, text=host, variable=var)
            cb.pack(anchor=W)
            self.selected_switches.append((host, var))

        Button(provision_window, text="Provisionierung Starten", command=self.start_provision).pack(pady=20)

        # Button zum Beenden des Programms im Provisionierungsfenster
        Button(provision_window, text="Abbrechen", command=self.exit_program).pack(pady=10)

    def get_hosts_from_csv(self, csv_file):
        hosts = []
        try:
            with open(csv_file, mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    hosts.append(row['IP-Adresse'])  # Hier wird die IP-Adresse jeder Zeile hinzugefügt
        except Exception as e:
            self.log(f"Fehler beim Lesen der CSV-Datei: {e}")
        return hosts

    def start_provision(self):
        # Nur ausgewählte Switches provisionieren
        selected_hosts = [host for host, var in self.selected_switches if var.get()]

        # Hostnamen-Präfix aus der Eingabe lesen
        hostname_prefix = self.hostname_prefix_var.get()

        provisioned_switches = []

        if selected_hosts:
            for index, host_ip in enumerate(selected_hosts, start=1):
                self.log(f"Verbinde zu Host: {host_ip}")
                hostname = self.configure_switch(host_ip, index, hostname_prefix)
                if hostname:
                    provisioned_switches.append((hostname, host_ip))

            # Nach der Provisionierung eine Erfolgsnachricht anzeigen
            self.show_provision_success(provisioned_switches)
        else:
            self.log("Keine Switches ausgewählt. Provisionierung abgebrochen.")

    def configure_switch(self, host_ip, switch_number, hostname_prefix):
        aruba_cx_switch = {
            'device_type': 'aruba_os',
            'host': host_ip,
            'username': 'admin',
            'password': '',
            'secret': 'secret',
            'global_delay_factor': 4,
            'session_log': f'session_log_{host_ip}.txt'
        }

        try:
            connection = ConnectHandler(**aruba_cx_switch)
            connection.enable()

            # Benutzerspezifizierter Hostname mit aufsteigenden Ziffern
            hostname = f"{hostname_prefix}{switch_number:02d}"

            command_list = [
                f'conf t',
                f'hostname {hostname}',  # Benutzerdefinierter Hostname wird gesetzt
                'user admin password plaintext admin',
                'vlan 105',
                'name  TEST_105',
                'vlan 106',
                'name  TEST_106',
                'vlan 107',
                'name  TEST_107',
            ]

            for command in command_list:
                output = connection.send_command(command, expect_string=r'#')
                self.log(output)

            connection.send_command('write memory', expect_string=r'')

            connection.disconnect()

            return hostname  # Hostname zurückgeben
        except Exception as e:
            self.log(f"Fehler beim Verbinden oder Ausführen von Befehlen auf {host_ip}: {e}")
            return None

    def show_provision_success(self, provisioned_switches):
        # Erfolgsfenster anzeigen
        success_window = Toplevel(self.root)
        success_window.title("Provisionierung erfolgreich")

        Label(success_window, text="Provisionierung erfolgreich beendet!").pack(pady=10)

        # Liste der provisionierten Switches anzeigen
        for hostname, ip in provisioned_switches:
            Label(success_window, text=f"{hostname} - {ip}").pack(anchor=W)

        Button(success_window, text="Okay", command=success_window.destroy).pack(pady=10)

    def exit_program(self):
        # Programm komplett beenden
        self.root.destroy()

# Start der GUI
if __name__ == "__main__":
    root = Tk()
    app = DHCPGui(root)
    root.mainloop()
