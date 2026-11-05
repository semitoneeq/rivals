# Arena Duel – 1v1 Bot (Windows)

Eigenständiges, originales, kleines Ego-Shooter-Arenaspiel im Stil eines schnellen 1v1-Duells. **Kein Roblox-Spiel und keine Kopie von Roblox Rivals.** Alle Grafiken sind programmatisch erzeugt; keine Fremd-Assets.

## Das Spiel

- Ego-Perspektive und Maus-Zielen, linke Maustaste schießt
- Ein Bot-Gegner mit drei Schwierigkeitsstufen
- WASD Bewegung, Shift sprinten, R nachladen, Esc Pause, Tab Minimap
- Lebenspunkte, Munition, Kills, Respawn, Zeitlimit von 2 Minuten
- Gewinner: zuerst 5 Punkte oder Führung nach Ablauf der Zeit

## Ohne Installation von Python (empfohlen)

Das gesamte Projekt in ein **neues** GitHub Repository hochladen, inklusive des versteckten Ordners `.github` mit dem Workflow darin. Unter GitHub **Actions** startet der Workflow `Arena Duel - Windows EXE` automatisch bei Push auf `main`. Wenn der Lauf grün ist, im Abschnitt **Artifacts** `ArenaDuel-Windows` herunterladen. ZIP entpacken, darin `ArenaDuel.exe` per Doppelklick starten.

Falls in GitHub Actions nur `Get started with GitHub Actions` steht, wurde `.github/workflows/build-windows.yml` nicht hochgeladen (GitHub-Weboberfläche überspringt gelegentlich versteckte Ordner). Erstelle dann manuell unter **Actions > set up a workflow yourself** die Datei `.github/workflows/build-windows.yml` und kopiere ihren Inhalt hinein. 

Windows SmartScreen kann eine Warnung für selbst erstellte, nicht signierte EXEs anzeigen. Der Quellcode ist einsehbar; installiere nur aus einem vertrauenswürdigen eigenen Build.

## Für Entwickler

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python arena_duel.py
```

## Grenzen

Version 1.0 ist ein bewusst kleines, eigenständiges Offline-Spiel mit Raycasting-Pseudo-3D, **nicht** das originale Roblox Rivals und kein vollwertiger 3D-Multiplayer-Shooter. Kein Online-Modus, keine Roblox-Anbindung. Die Grafik benötigt Pygame. Hier wurde die Spiellogik per Python-Tests geprüft, aber eine Windows EXE kann nur auf Windows/GitHub Actions verifiziert werden.
