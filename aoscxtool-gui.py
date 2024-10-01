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
import queue
import ipaddress

# Version des Tools
VERSION = "v0.4"

# Filterkriterien für Option 60
option_60_patterns = ["6000", "6100", "6200", "6300", "6400"]

# CSV-Datei Pfad
csv_file = "dhcp_devices.csv"

# Gesehene Geräte speichern (um doppelte Einträge zu vermeiden)
seen_devices = set()

# Flag, um den Discovery-Prozess zu stoppen
stop_discovery = False

# Batch-Größe festlegen
BATCH_SIZE = 5  # Wie viele Switches pro Batch provisioniert werden

# GUI erstellen
class DHCPGui:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Aruba AOS CX Discovery Provisioning Tool {VERSION} (GUI Mode)")
        self.root.geometry("800x600")  # Breite für langen Text

        self.interface_var = StringVar()
        self.log_text = StringVar()

        # Queue für parallele Provisionierung
        self.switch_queue = queue.Queue()

        # GUI Layout
        self.create_widgets()

    def create_widgets(self):
        # Interface Auswahl
        Label(self.root, text=f"Netzwerk-Interface auswählen:").pack(pady=10)
        self.interface_combo = ttk.Combobox(self.root, textvariable=self.interface_var, width=90)  # Breite um ein halbes Mal vergrößert
        self.interface_combo.pack()

        # Log Fenster
        Label(self.root, text=f"Log:").pack(pady=10)
        self.log_area = scrolledtext.ScrolledText(self.root, width=80, height=20)
        self.log_area.pack(padx=10, pady=10)

        # Buttons
        self.start_button = Button(self.root, text=f"Discovery Starten", command=self.start_discovery)
        self.start_button.pack(pady=5)

        self.stop_button = Button(self.root, text=f"Discovery Stoppen", command=self.stop_discovery_process, state=DISABLED)
        self.stop_button.pack(pady=5)

        self.provision_button = Button(self.root, text=f"Provisionierung Starten", command=self.open_provision_window, state=DISABLED)
        self.provision_button.pack(pady=5)

        # Button zum Beenden des Programms
        self.exit_button = Button(self.root, text=f"Beenden", command=self.exit_program)
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
        self.log(f"Discovery-Prozess wird gestoppt...")
        self.stop_button.config(state=DISABLED)

    def discovery_thread(self):
        global stop_discovery
        stop_discovery = False

        selected_interface = self.interface_var.get()

        if not selected_interface:
            messagebox.showerror(f"Fehler", "Bitte ein Interface auswählen")
            self.start_button.config(state=NORMAL)
            return

        # Extrahieren des Interface-Namens (vor dem Bindestrich)
        interface = selected_interface.split(" - ")[0]

        self.log(f"Überwache DHCP-Requests auf Interface: {interface}

        # CSV-Datei vorbereiten
        if not os.path.exists(csv_file):
            with open(csv_file, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["MAC-Adresse", "IP-Adresse", "Option 60"])

        while not stop_discovery:
            scapy.sniff(iface=interface, filter="udp and (port 67 or port 68)", prn=self.dhcp_packet_callback, store=0, timeout=1)

        self.log(f"Discovery-Prozess beendet.")
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
        provision_window.title(f"Switch Provisionierung")
        provision_window.geometry("600x500")

        Label(provision_window, text=f"Wählen Sie die zu provisionierenden Switches:").pack(pady=10)

        # Hostname-Eingabefeld
        Label(provision_window, text="Hostnamen-Präfix eingeben:").pack(pady=5)
        self.hostname_prefix_var = StringVar(value="pyswitch")
        self.hostname_entry = Entry(provision_window, textvariable=self.hostname_prefix_var)
        self.hostname_entry.pack(pady=5)

        # Passwort-Eingabefeld
        Label(provision_window, text="Admin Passwort setzen:").pack(pady=5)
        self.password_var = StringVar()
        self.password_entry = Entry(provision_window, textvariable=self.password_var, show="*")
        self.password_entry.pack(pady=5)

        # IP-Adresse Eingabefeld
        Label(provision_window, text="Start-IP-Adresse eingeben (optional):").pack(pady=5)
        self.ip_address_var = StringVar(value="")
        self.ip_address_entry = Entry(provision_window, textvariable=self.ip_address_var)
        self.ip_address_entry.pack(pady=5)

        # SNMP Community Eingabefeld
        Label(provision_window, text="SNMP Community (optional):").pack(pady=5)
        self.snmp_community_var = StringVar(value="")
        self.snmp_entry = Entry(provision_window, textvariable=self.snmp_community_var)
        self.snmp_entry.pack(pady=5)

        # Gefundene Hosts laden
        hosts_with_option60 = self.get_hosts_with_option60_from_csv(csv_file)
        self.selected_switches = []

        for host, option_60 in hosts_with_option60:
            var = BooleanVar()
            cb = Checkbutton(provision_window, text=f"{host} - {option_60}", variable=var)
            cb.pack(anchor=W)
            self.selected_switches.append((host, var))

        Button(provision_window, text=f"Provisionierung Starten", command=self.start_provision_batch).pack(pady=20)

        # Button zum Beenden des Programms im Provisionierungsfenster
        Button(provision_window, text=f"Beenden", command=self.exit_program).pack(pady=10)

    def get_hosts_with_option60_from_csv(self, csv_file):
        # Diese Funktion liest die IP-Adressen und Option 60 aus der CSV-Datei und gibt sie als Liste zurück
        hosts_with_option60 = []
        try:
            with open(csv_file, mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    hosts_with_option60.append((row['IP-Adresse'], row['Option 60']))
        except Exception as e:
            self.log(f"Fehler beim Lesen der CSV-Datei: {e}")
        return hosts_with_option60

    def start_provision_batch(self):
        # Provisionierung wird in Batches aufgeteilt
        selected_hosts = [host for host, var in self.selected_switches if var.get()]

        # Hostnamen-Präfix und andere Eingaben lesen
        hostname_prefix = self.hostname_prefix_var.get()
        admin_password = self.password_var.get()  # Admin Passwort
        ip_address = self.ip_address_var.get()
        snmp_community = self.snmp_community_var.get()

        # Validierung der IP-Adresse (optional)
        if ip_address:
            try:
                ip_base = ipaddress.IPv4Address(ip_address)
            except ipaddress.AddressValueError:
                messagebox.showerror(f"Fehler", "Ungültige IP-Adresse")
                return
        else:
            ip_base = None

        if selected_hosts:
            # Hosts in Batches aufteilen
            for i in range(0, len(selected_hosts), BATCH_SIZE):
                batch = selected_hosts[i:i + BATCH_SIZE]
                self.log(f"Provisioniere Batch: {batch}")
                # Parallele Threads für die Provisionierung der Batches
                thread = threading.Thread(target=self.provision_batch, args=(batch, hostname_prefix, admin_password, ip_base, snmp_community, i))
                thread.start()
        else:
            self.log(f"Keine Switches ausgewählt. Provisionierung abgebrochen.")

    def provision_batch(self, batch, hostname_prefix, admin_password, ip_base, snmp_community, batch_index):
        provisioned_switches = []
        for index, host_ip in enumerate(batch, start=1):
            # IP-Adresse für jeden Switch inkrementieren
            if ip_base:
                ip_address = str(ip_base + index + batch_index * BATCH_SIZE)
            else:
                ip_address = None

            hostname = self.configure_switch(host_ip, index, hostname_prefix, admin_password, ip_address, snmp_community)
            if hostname:
                provisioned_switches.append((hostname, host_ip))

        # Erfolgreich provisionierte Switches anzeigen
        if provisioned_switches:
            self.show_provision_success(provisioned_switches)

    def configure_switch(self, host_ip, switch_number, hostname_prefix, admin_password, ip_address, snmp_community):
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
                f'user admin password plaintext {admin_password}',  # Admin Passwort setzen
                'vlan 105',
                'name  TEST_105',
                'vlan 106',
                'name  TEST_106',
                'vlan 107',
                'name  TEST_107',
            ]

            # Optional: IP-Adresse konfigurieren, falls eingegeben
            if ip_address:
                command_list.append(f"interface vlan 1")
                command_list.append(f"ip address {ip_address} 255.255.255.0")

            # Optional: SNMP konfigurieren, falls eingegeben
            if snmp_community:
                command_list.append(f"snmp-server community {snmp_community}")

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
        success_window.title(f"Provisionierung erfolgreich! Tool by h0nigd4chs & fre4ki")

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
