# Aruba AOS CX Discovery Provisioning Tool (GUI Mode)

Willkommen zum **Aruba AOS CX Discovery Provisioning Tool (GUI Mode)**! Dieses Tool ermöglicht das automatische Erkennen von Aruba AOS CX-Switches in deinem Netzwerk über DHCP-Anfragen, die Bereitstellung von Konfigurationen und die Verwaltung des Prozesses über eine benutzerfreundliche grafische Oberfläche (GUI).

## Funktionen

- **Netzwerkerkennung**: Automatisches Erkennen von Aruba AOS CX-Switches im Netzwerk über DHCP-Anfragen.
- **Provisionierung**: Konfiguration der Switches mit benutzerdefinierten Hostnamen und VLAN-Einstellungen.
- **GUI-Oberfläche**: Intuitive grafische Benutzeroberfläche für eine einfache Bedienung.
- **Benutzerdefinierte Hostnamen**: Definiere ein Hostnamen-Präfix, und das Tool fügt automatisch eine fortlaufende Nummer für jeden bereitgestellten Switch hinzu.
- **Selektive Provisionierung**: Wähle aus, welche entdeckten Switches provisioniert werden sollen.
- **Logausgabe**: Detaillierte Protokolle des Erkennungs- und Provisionierungsprozesses.

## Voraussetzungen

Um dieses Tool auszuführen, benötigst du folgende Abhängigkeiten:

- **Python 3.x**
- **Scapy** zur Erkennung von Netzwerkpaketen.
- **Netmiko** für die SSH-basierte Konfiguration der Switches.
- **Tkinter** für die grafische Benutzeroberfläche (normalerweise in Python enthalten).

Um die benötigten Python-Bibliotheken zu installieren, führe folgenden Befehl aus:

```bash
python -m pip install scapy netmiko
```

## Installation

1. Klone das Repository:

    ```bash
    git clone https://github.com/deinbenutzername/aruba-aos-cx-discovery-provisioning-tool.git
    cd aruba-aos-cx-discovery-provisioning-tool
    ```


2. Starte das Tool:

    ```bash
    python discovery_provisioning_gui.py
    ```

## Verwendung

1. **Tool starten**: Führe das `discovery_provisioning_gui.py`-Skript aus, um die GUI zu öffnen.
   
2. **Netzwerkschnittstelle auswählen**: Wähle die Netzwerkschnittstelle, auf der DHCP-Anfragen überwacht werden sollen.
   
3. **Erkennung starten**: Klicke auf den Button "Discovery Starten", um den Erkennungsprozess zu starten. Das Tool lauscht auf DHCP-Anfragen von Aruba-Switches.
   
4. **Erkennung stoppen**: Sobald du zufrieden bist, klicke auf "Discovery Stoppen", um den Erkennungsprozess zu beenden.

5. **Switches provisionieren**:
   - Klicke auf "Provisionierung Starten", um ein neues Fenster zu öffnen.
   - Gib ein **Hostname-Präfix** ein (z. B. `myswitch`), und das Tool fügt eine fortlaufende Nummer zu jedem Hostnamen hinzu (z. B. `myswitch01`, `myswitch02`).
   - Wähle die Switches aus, die provisioniert werden sollen.
   - Klicke auf "Provisionierung Starten", um die Konfiguration auf die ausgewählten Switches zu übertragen.

6. **Logs anzeigen**: Das Protokollfenster zeigt detaillierte Logs des Erkennungs- und Provisionierungsprozesses an.

7. **Beenden**: Du kannst das Tool jederzeit über den Button "Beenden" schließen.

## Screenshots

![image](https://github.com/user-attachments/assets/c2e35b93-a9d7-4164-a2b4-ddfd8805c53b)


## Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe die Datei [LICENSE](LICENSE) für Details.

## Beiträge

Beiträge sind willkommen! Wenn du etwas beitragen möchtest, kannst du gerne einen Pull Request einreichen oder ein Issue öffnen.

## Kontakt

Bei Fragen oder Anmerkungen, bitte kontaktieren:

- **h0nigd4chs** - honigdachsbau.de
