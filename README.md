# GerRepair SPD RAW Dumper


## Status

- Alpha-Version
- DDR4-SPD-Daten lesen/dumpen
- Experimentelle Schreibfunktion für 512-Byte-DDR4-SPD-BIN-Dateien
- Vor jedem Schreibvorgang wird zwingend ein Backup-Dump erstellt
- Nutzung auf eigene Verantwortung

## Funktionen

- DDR4-SPD als rohe `.bin`-Datei dumpen
- Eine ausgewählte 512-Byte-`.bin` auf ein einzelnes SPD-EEPROM schreiben
- Pflicht-Backup vor dem Schreiben
- Doppelread des Backups vor dem Schreiben
- CRC-/Plausibilitätsprüfung der zu schreibenden BIN
- Verify-Dump nach dem Schreiben
- GUI mit Log-Ausgabe
- Intel-/AMD-Auswahl
- Dekodierung wichtiger SPD-Informationen
- XMP-Erkennung
- Hersteller-, Seriennummer- und Part-Number-Anzeige, soweit im SPD vorhanden

## Sehr wichtige Warnung zur Schreibfunktion

Das Schreiben auf den SPD-EEPROM kann den RAM unbrauchbar machen. Wenn ein falscher Dump geschrieben wird, der Schreibvorgang abbricht oder der EEPROM teilweise beschrieben wird, startet das System eventuell nicht mehr mit diesem RAM-Modul.

Im Ernstfall muss der EEPROM auf dem RAM-Modul mit einem externen Hardware-Flasher neu beschrieben werden.

**Nutzung auf eigene Gefahr.**

Die Schreibfunktion verlangt deshalb:

1. eine einzelne Zieladresse, z. B. `0x50` oder `0x51`,
2. eine exakt 512 Byte große DDR4-SPD-BIN,
3. gültige DDR4-CRC-Blöcke,
4. eine Bestätigung der Warnung per Button,
5. einen Backup-Dump vor dem Schreibvorgang,
6. einen Verify-Dump nach dem Schreibvorgang.

## Voraussetzungen

- Windows 10/11, 64-bit empfohlen
- Administratorrechte
- Python 3 zum Start aus dem Quellcode
- Für Low-Level-Portzugriff eine passende Treiber-DLL im Programmordner, z. B. `inpoutx64.dll`

Vor dem Lesen oder Schreiben bitte Sensor-, RGB- und Monitoring-Tools schließen, z. B. HWiNFO, CPU-Z Sensor Tab, Ryzen Master, ZenTimings, OpenRGB oder Mainboard-Tools.

## Start aus dem Quellcode

```bat
py -3 SPD_Read_GerRepair_Alpha.py
```

## EXE bauen

```bat
build_exe_GerRepair.bat
```

Die fertige EXE liegt danach unter `dist\GerRepair_SPD_RAW_Dumper_Alpha.exe`.

## Treiberdateien

Dieses Repository enthält den Quellcode. Drittanbieter-Treiberdateien wie `inpoutx64.dll` sollten vorzugsweise im Release-ZIP mitgeliefert werden. Beachte den Lizenzhinweis unter:

```text
licenses/LICENSE-InpOutx64.txt
```

## Lizenz

Der eigene Quellcode steht unter der MIT-Lizenz. Drittanbieter-Komponenten behalten ihre jeweilige Lizenz.
