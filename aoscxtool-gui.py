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
import pygame  # Bibliothek für die Musiksteuerung
from PIL import Image, ImageTk, ImageSequence  # Bibliothek für die Bildanzeige und GIF-Animation

# Version des Tools
VERSION = "v0.5"

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

# Pfad zum Ordner "data"
data_folder = "data"

# Initialisiere pygame für die Musik
pygame.mixer.init()
pygame.mixer.music.load(os.path.join(data_folder, "bgm.mp3"))  # Hintergrundmusik laden
pygame.mixer.music.play(-1)  # Musik in Endlosschleife abspielen

# GUI erstellen
class DHCPGui:
    def __init__(self, root):
        self.root = root
        # Fensterhöhe um 25% erhöhen
        self.root.title(f"Aruba AOS CX Discovery Provisioning Tool {VERSION} (GUI Mode)")
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

    def open_provision_window(self):
        # Dummy-Methode als Platzhalter, um den Fehler zu beheben
        pass

    def exit_program(self):
        # Programm komplett beenden
        self.root.destroy()

# Start der GUI
if __name__ == "__main__":
    root = Tk()
    app = DHCPGui(root)
    root.mainloop()
