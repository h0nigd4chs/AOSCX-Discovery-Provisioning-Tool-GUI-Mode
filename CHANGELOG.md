# Change-Log

## [v0.5] - 2023-10-02

### Hinzugefügt
- Hintergrundmusik (bgm.mp3) wird nun abgespielt, sobald das Tool gestartet wird. Diese kann über einen Lautstärkeregler angepasst oder stummgeschaltet werden.
- Ein animiertes GIF (`title.gif`) wurde mittig im oberen Bereich der Benutzeroberfläche platziert.
- Die Benutzeroberfläche wurde um 25% in der Höhe vergrößert.
- Farben und Styles der GUI wurden überarbeitet, um eine modernere und ansprechendere Benutzeroberfläche zu bieten.
- Ein Lautstärkeregler und eine Stummschaltfunktion wurden oben rechts hinzugefügt.
- Alle verwendeten Mediendateien befinden sich jetzt im Unterordner `data`.

### Änderungen
- Die Datei `h.webp` wurde in die obere linke Ecke verschoben, um mehr Platz für andere GUI-Elemente zu schaffen.
- Entfernung der Scrollbar aus der Benutzeroberfläche, um die Navigation zu vereinfachen.
- Anpassung der Größe und Ausrichtung des GIFs und der Bilddateien, um eine bessere visuelle Konsistenz zu gewährleisten.

## [v0.4] - 2023-10-01

### Hinzugefügt
- Ein neues Feld für das Admin-Passwort wurde im Provisionierungsfenster hinzugefügt, um das Passwort auf den Switches festzulegen.
- Anzeige des Vendor Class Identifier (Option 60) neben der IP-Adresse der Switches im Provisionierungsfenster.
- Der "Beenden"-Button dient nun auch zum Abbrechen des Programms in beiden Fenstern.
- Erfolgsfenster nach erfolgreicher Provisionierung, welches alle provisionierten Switches mit Hostnamen und IP-Adressen auflistet.

## [v0.3] - 2023-09-29

### Hinzugefügt
- Grundlegende DHCP-Discovery-Funktionalität mit GUI.
- Auswahl von Netzwerkinterfaces zur DHCP-Überwachung.
- Log-Fenster, um den Erkennungsprozess zu überwachen.
- Provisionierungsfunktion, um ausgewählte Switches über eine SSH-Verbindung zu konfigurieren.
- Möglichkeit, den Hostnamen der Switches zu setzen und Batches von Switches gleichzeitig zu konfigurieren.
