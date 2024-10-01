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
import pygame
from PIL import Image, ImageTk, ImageSequence

# Version des Tools
VERSION = "v0.5"

# Filterkriterien für Option 60
option_60_patterns = ["6000", "6100", "6200", "6300", "6400"]

# CSV-Datei Pfad
csv_file = "dhcp_devices.csv"
session_logs_folder = "Session-Logs"

# Gesehene Geräte speichern (um doppelte Einträge zu vermeiden)
seen_devices = set()

# Flag, um den Discovery-Prozess zu stoppen
stop_discovery = False

# Batch-Größe festlegen
BATCH_SIZE = 5  # Wie viele Switches pro Batch provisioniert werden

# Pfad zum Ordner "data"
data_folder = "data"

# Initialisiere pygame für die Musik
pygame.mixer.init()
pygame.mixer.music.load(os.path.join(data_folder, "bgm.mp3"))  # Hintergrundmusik laden
pygame.mixer.music.play(-1)  # Musik in Endlosschleife abspielen

# Sicherstellen, dass der Ordner für Session-Logs existiert
if not os.path.exists(session_logs_folder):
    os.makedirs(session_logs_folder)

# GUI erstellen
class DHCPGui:
    def __init__(self, root):
        self.root = root
        # Fensterhöhe um 25% erhöhen
        self.root.title(f"Aruba AOS CX Discovery & Provisioning Tool {VERSION} (GUI Mode)")
        self.root.geometry("800x750")  # Erhöhte Fenstergröße (25% mehr Höhe)

        # Setze ein modernes Theme
        style = ttk.Style(self.root)
        style.theme_use('clam')

        # Definiere Farben für den Hintergrund
        self.bg_color = "#F5F5F5"  # Helles Grau
        self.button_color = "#FFA500"  # Orange für Buttons
        self.text_color = "#FFFFFF"  # Weiß für Schrift auf Buttons

        self.root.configure(bg=self.bg_color)

        self.interface_var = StringVar()
        self.log_text = StringVar()

        # Queue für parallele Provisionierung
        self.switch_queue = queue.Queue()

        # Variable für die Lautstärke
        self.volume_var = DoubleVar(value=0.5)  # Anfangslautstärke auf 50%
        pygame.mixer.music.set_volume(self.volume_var.get())  # Setze anfängliche Lautstärke

        # GUI Layout
        self.create_widgets()

    def create_widgets(self):
        # Konfiguration des Grid-Layouts für die GUI
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)

        # Bild anzeigen in der oberen linken Ecke
        image = Image.open(os.path.join(data_folder, "h.webp"))  # Bild laden
        image = image.resize((100, 100))  # Bild verkleinern
        self.img = ImageTk.PhotoImage(image)
        self.img_label = Label(self.root, image=self.img, bg=self.bg_color)
        self.img_label.grid(row=0, column=0, sticky='nw', padx=0, pady=10)  # Entferne das Padding nach rechts (padx=0)

        # Animiertes GIF zentriert über "Netzwerk-Interface auswählen"
        self.gif_label = Label(self.root, bg=self.bg_color)
        self.gif_label.grid(row=0, column=0, columnspan=3, pady=5, sticky='n')  # Verwende columnspan=3 um es mittig zu machen

        # Funktion, um das animierte GIF anzuzeigen
        self.load_gif(os.path.join(data_folder, "title.gif"), scale=1.5)  # 1,5-fache Vergrößerung des GIFs

        # Lautstärkeregler und Stummschaltknopf in die obere rechte Ecke
        self.volume_slider = Scale(self.root, from_=0, to=1, orient=HORIZONTAL, resolution=0.1, variable=self.volume_var, command=self.set_volume, bg=self.bg_color)
        self.volume_slider.grid(row=0, column=2, sticky='ne', padx=10, pady=10)

        self.mute_button = Button(self.root, text="Stumm schalten", command=self.toggle_mute, bg=self.button_color, fg=self.text_color)
        self.mute_button.grid(row=0, column=2, sticky='ne', padx=150, pady=10)

        # Interface Auswahl
        Label(self.root, text="Netzwerk-Interface auswählen:", bg=self.bg_color).grid(row=2, column=0, columnspan=3, pady=10)
        self.interface_combo = ttk.Combobox(self.root, textvariable=self.interface_var, width=90)  # Breite um ein halbes Mal vergrößert
        self.interface_combo.grid(row=3, column=0, columnspan=3)

        # Log Fenster ohne Scrollbar
        Label(self.root, text="Log:", bg=self.bg_color).grid(row=4, column=0, columnspan=3, pady=10)
        self.log_area = scrolledtext.ScrolledText(self.root, width=80, height=20, wrap=WORD, bg="#E8EAF6", fg="#000000", font=("Segoe UI", 10))
        self.log_area.grid(row=5, column=0, columnspan=3, padx=10, pady=10)

        # Buttons untereinander platzieren
        self.start_button = Button(self.root, text="Discovery Starten", command=self.start_discovery, bg=self.button_color, fg=self.text_color, font=("Segoe UI", 10, "bold"))
        self.start_button.grid(row=6, column=0, columnspan=3, pady=5)

        self.stop_button = Button(self.root, text="Discovery Stoppen", command=self.stop_discovery_process, state=DISABLED, bg=self.button_color, fg=self.text_color, font=("Segoe UI", 10, "bold"))
        self.stop_button.grid(row=7, column=0, columnspan=3, pady=5)

        self.provision_button = Button(self.root, text="Provisionierung Starten", command=self.open_provision_window, state=DISABLED, bg=self.button_color, fg=self.text_color, font=("Segoe UI", 10, "bold"))
        self.provision_button.grid(row=8, column=0, columnspan=3, pady=5)

        # Button zum Beenden des Programms
        self.exit_button = Button(self.root, text="Beenden", command=self.exit_program, bg=self.button_color, fg=self.text_color, font=("Segoe UI", 10, "bold"))
        self.exit_button.grid(row=9, column=0, columnspan=3, pady=5)

        # Interfaces laden
        self.load_interfaces()

    def load_gif(self, gif_path, scale=1.5):
        """Lädt und animiert das GIF."""
        self.gif = Image.open(gif_path)
        self.gif_frames = [ImageTk.PhotoImage(img.resize((int(img.width * scale), int(img.height * scale)))) for img in ImageSequence.Iterator(self.gif)]
        self.gif_frame_count = len(self.gif_frames)
        self.current_frame = 0
        self.update_gif_frame()

    def update_gif_frame(self):
        """Aktualisiert den Frame des GIFs."""
        frame = self.gif_frames[self.current_frame]
        self.gif_label.config(image=frame)
        self.current_frame = (self.current_frame + 1) % self.gif_frame_count
        self.root.after(100, self.update_gif_frame)  # Wechselt alle 100ms das Bild

    def set_volume(self, volume):
        """Setzt die Lautstärke der Musik."""
        pygame.mixer.music.set_volume(float(volume))

    def toggle_mute(self):
        """Schaltet die Musik stumm oder hebt die Stummschaltung auf."""
        if pygame.mixer.music.get_volume() > 0:
            self.previous_volume = pygame.mixer.music.get_volume()
            pygame.mixer.music.set_volume(0)
            self.mute_button.config(text="Stummschaltung aufheben")
        else:
            pygame.mixer.music.set_volume(self.previous_volume)
            self.mute_button.config(text="Stumm schalten")

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
        global stop_discovery
        stop_discovery = False
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
        """Provisionierungsfenster mit demselben Stil und Farben öffnen."""
        provision_window = Toplevel(self.root)
        provision_window.title("Switch Provisionierung")
        provision_window.geometry("600x500")
        provision_window.configure(bg=self.bg_color)

        # Hostname-Präfix-Eingabefeld
        Label(provision_window, text="Hostnamen-Präfix eingeben:", bg=self.bg_color, fg="#000000").pack(pady=5)
        self.hostname_prefix_var = StringVar(value="myswitch")
        hostname_entry = Entry(provision_window, textvariable=self.hostname_prefix_var)
        hostname_entry.pack(pady=5)

        # Admin Passwort-Eingabefeld
        Label(provision_window, text="Admin Passwort eingeben:", bg=self.bg_color, fg="#000000").pack(pady=5)
        self.password_var = StringVar()
        password_entry = Entry(provision_window, textvariable=self.password_var, show="*")
        password_entry.pack(pady=5)

        # IP-Adresse-Eingabefeld
        Label(provision_window, text="Start-IP-Adresse (optional):", bg=self.bg_color, fg="#000000").pack(pady=5)
        self.ip_address_var = StringVar()
        ip_address_entry = Entry(provision_window, textvariable=self.ip_address_var)
        ip_address_entry.pack(pady=5)

        # SNMP Community-Eingabefeld
        Label(provision_window, text="SNMP Community (optional):", bg=self.bg_color, fg="#000000").pack(pady=5)
        self.snmp_community_var = StringVar()
        snmp_entry = Entry(provision_window, textvariable=self.snmp_community_var)
        snmp_entry.pack(pady=5)

        # Gefundene Hosts laden
        hosts_with_option60 = self.get_hosts_with_option60_from_csv(csv_file)
        self.selected_switches = []

        for host, option_60 in hosts_with_option60:
            var = BooleanVar()
            cb = Checkbutton(provision_window, text=f"{host} - {option_60}", variable=var, bg=self.bg_color, fg="#000000")
            cb.pack(anchor=W)
            self.selected_switches.append((host, var))

        Button(provision_window, text="Provisionierung Starten", command=self.start_provision_batch, bg=self.button_color, fg=self.text_color, font=("Segoe UI", 10, "bold")).pack(pady=20)
        Button(provision_window, text="Abbrechen", command=provision_window.destroy, bg=self.button_color, fg=self.text_color, font=("Segoe UI", 10, "bold")).pack(pady=10)

    def get_hosts_with_option60_from_csv(self, csv_file):
        """Liest IP-Adressen und Option 60 aus der CSV-Datei."""
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
        selected_hosts = [host for host, var in self.selected_switches if var.get()]
        hostname_prefix = self.hostname_prefix_var.get()
        admin_password = self.password_var.get()  # Admin Passwort
        ip_address = self.ip_address_var.get()
        snmp_community = self.snmp_community_var.get()

        ip_base = None
        if ip_address:
            try:
                ip_base = ipaddress.IPv4Address(ip_address)
            except ipaddress.AddressValueError:
                messagebox.showerror("Fehler", "Ungültige IP-Adresse")
                return

        for index, host_ip in enumerate(selected_hosts, start=1):
            hostname = f"{hostname_prefix}{index:02d}"

            # IP-Adresse für jeden Switch inkrementieren
            if ip_base:
                new_ip = str(ip_base + index)
            else:
                new_ip = host_ip

            self.configure_switch(host_ip, hostname, admin_password, new_ip, snmp_community)

    def configure_switch(self, switch_ip, hostname, admin_password, new_ip, snmp_community):
        session_log = os.path.join(session_logs_folder, f'session_log_{switch_ip}.txt')
        switch = {
            'device_type': 'aruba_os',
            'host': switch_ip,
            'username': 'admin',
            'password': '',
            'secret': 'secret',
            'global_delay_factor': 4,
            'session_log': session_log
        }

        try:
            self.log(f"Verbinde zu {switch_ip} für die Provisionierung...")

            connection = ConnectHandler(**switch)
            connection.enable()

            # Konfigurationsbefehle
            commands = [
                f"conf t",
                f"hostname {hostname}",
                f"user admin password plaintext {admin_password}",
                "vlan 105",
                "name TEST_105",
                "vlan 106",
                "name TEST_106",
                "vlan 107",
                "name TEST_107",
            ]

            if new_ip:
                commands.extend([
                    "interface vlan 1",
                    f"ip address {new_ip} 255.255.255.0",
                ])

            if snmp_community:
                commands.append(f"snmp-server community {snmp_community}")

            for command in commands:
                output = connection.send_command(command)
                self.log(output)

            connection.send_command("write memory")
            connection.disconnect()

            self.log(f"Provisionierung von {hostname} ({switch_ip}) erfolgreich abgeschlossen.")

        except Exception as e:
            self.log(f"Fehler bei der Provisionierung von {switch_ip}: {e}")

    def exit_program(self):
        """Programm beenden."""
        self.root.destroy()

# Start der GUI
if __name__ == "__main__":
    root = Tk()
    app = DHCPGui(root)
    root.mainloop()

