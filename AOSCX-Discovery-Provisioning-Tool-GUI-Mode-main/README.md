# Aruba AOS CX Discovery Provisioning Tool (GUI Mode)

Willkommen zum **Aruba AOS CX Discovery Provisioning Tool (GUI Mode)**! Dieses Tool bietet eine benutzerfreundliche grafische Oberfläche (GUI), um Aruba AOS CX-Switches in deinem Netzwerk über DHCP-Anfragen automatisch zu erkennen, sie zu provisionieren und verwalten.

## Version

**Aktuelle Version**: v0.4

## Funktionen

- **Netzwerkerkennung**: Automatisches Erkennen von Aruba AOS CX-Switches im Netzwerk durch das Abhören von DHCP-Anfragen.
- **Provisionierung**: Konfiguration der Switches, einschließlich Setzen von Hostnamen, IP-Adressen, VLANs, SNMP-Communitys und Admin-Passwörtern.
- **GUI-Oberfläche**: Eine einfache, intuitive grafische Benutzeroberfläche für die Bedienung.
- **Vendor Class ID (Option 60)**: Erkennung des Vendor Class Identifier (Switch-Typ) durch die Analyse der DHCP-Anfragen.
- **Batch-Provisionierung**: Die Provisionierung kann in Batches durchgeführt werden, sodass mehrere Switches gleichzeitig konfiguriert werden können.
- **Logausgabe**: Protokolle aller Vorgänge zur Fehlerbehebung und Überwachung.

## Change-Log

Details zu den Änderungen in jeder Version findest du in der Datei [CHANGELOG.md](CHANGELOG.md).

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

2. **Netzwerkschnittstelle auswählen**: Wähle die Netzwerkschnittstelle aus, über die die DHCP-Anfragen überwacht werden sollen. Das Tool erkennt automatisch die verfügbaren Netzwerkschnittstellen deines Systems und listet sie zur Auswahl auf.

3. **Erkennung starten**: Klicke auf den Button "Discovery Starten", um den Erkennungsprozess zu starten. Das Tool überwacht die DHCP-Anfragen und zeigt die erkannten Aruba AOS CX-Switches sowie ihre **IP-Adressen** und **Vendor Class Identifier (Option 60)** in der GUI an.

4. **Erkennung stoppen**: Wenn genügend Geräte erkannt wurden, kannst du den Erkennungsprozess über den Button "Discovery Stoppen" beenden.

5. **Switches provisionieren**:
   - Klicke auf "Provisionierung Starten", um ein neues Fenster zu öffnen, in dem du die zu provisionierenden Switches auswählen kannst.
   - Gib ein **Hostname-Präfix** (z. B. `myswitch`) ein, und das Tool fügt automatisch eine fortlaufende Nummer hinzu (z. B. `myswitch01`, `myswitch02`).
   - Du kannst optional ein **Admin-Passwort**, eine **Start-IP-Adresse** und eine **SNMP-Community** festlegen.
   - Die Liste zeigt die **IP-Adressen** und die **Vendor Class Identifier (Option 60)** der erkannten Switches an, sodass du gezielt Geräte provisionieren kannst.
   - Wähle die Switches aus, die du provisionieren möchtest, und klicke auf "Provisionierung Starten".

6. **Logs anzeigen**: Im Log-Bereich der GUI werden detaillierte Logs des Erkennungs- und Provisionierungsprozesses angezeigt. Hier kannst du den Status und etwaige Fehlermeldungen nachvollziehen.

7. **Beenden**: Du kannst das Tool jederzeit über den Button "Beenden" schließen.

## Beispielkonfigurationen

### Discovery
Nach dem Start des Tools kannst du die Netzwerkschnittstelle auswählen und auf "Discovery Starten" klicken. Im Log-Bereich erscheinen dann Einträge, sobald DHCP-Anfragen erkannt werden, die Informationen wie MAC-Adresse, IP-Adresse und Vendor Class Identifier enthalten.

### Provisionierung
Angenommen, du möchtest die Switches mit folgenden Einstellungen konfigurieren:

- Hostname-Präfix: `myswitch`
- Admin-Passwort: `admin123`
- Start-IP-Adresse: `10.10.10.2`
- SNMP-Community: `public`

Nach dem Auswählen der Switches und dem Festlegen der oben genannten Optionen werden die Switches entsprechend provisioniert:

- Switch 1: `myswitch01`, IP-Adresse: `10.10.10.2`
- Switch 2: `myswitch02`, IP-Adresse: `10.10.10.3`, usw.

Die Logs zeigen den Fortschritt der Provisionierung an.

## Fehlerbehebung

Hier sind einige gängige Probleme und Lösungen:

### 1. **Keine Switches erkannt**
- Stelle sicher, dass du die richtige Netzwerkschnittstelle ausgewählt hast.
- Überprüfe, ob die Switches DHCP-Anfragen senden und sich im selben Netzwerksegment wie dein System befinden.

### 2. **SSH-Fehler bei der Provisionierung**
- Überprüfe, ob du die richtigen Zugangsdaten für die SSH-Verbindung angegeben hast.
- Vergewissere dich, dass die SSH-Dienste auf den Switches aktiv sind und du über Netzwerkzugriff verfügst.

### 3. **Ungültige IP-Adresse bei der Provisionierung**
- Achte darauf, dass du eine gültige IPv4-Adresse eingibst (z. B. `192.168.1.10`).
- Das Tool inkrementiert die letzte Ziffer der IP-Adresse automatisch für jeden weiteren Switch im Batch.

## Anwendungsfälle

### 1. **Automatische Massenkonfiguration von Switches**
Dieses Tool ist besonders nützlich, wenn du eine große Anzahl von Aruba AOS CX-Switches im Netzwerk konfigurieren möchtest. Du kannst die Switches in Batches konfigurieren, um den Prozess zu beschleunigen, und dabei wichtige Parameter wie Hostnamen, IP-Adressen und VLANs automatisch zuweisen.

### 2. **Erkennung und Provisionierung neuer Geräte**
Wenn neue Switches in ein Netzwerk integriert werden, kannst du mithilfe des Tools deren DHCP-Anfragen überwachen, um sie sofort zu erkennen und zu provisionieren.

### 3. **Netzwerkanalyse**
Durch das Abhören von DHCP-Anfragen kannst du auch andere Geräte im Netzwerk erkennen und analysieren, die Vendor Class Identifier verwenden. Dies kann hilfreich sein, um Geräte unterschiedlicher Hersteller zu identifizieren.

## Screenshots

*Füge hier Screenshots der GUI und der wichtigsten Schritte hinzu, z. B. Discovery-Prozess, Auswahl der Switches zur Provisionierung, Log-Ausgaben etc.*

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe die Datei [LICENSE](LICENSE) für Details.

## Beiträge

Beiträge sind willkommen! Wenn du etwas beitragen möchtest, kannst du gerne einen Pull Request einreichen oder ein Issue öffnen.

## Kontakt

Bei Fragen oder Anmerkungen, bitte kontaktieren:

- **h0nigd4chs** - honigdachsbau.de
