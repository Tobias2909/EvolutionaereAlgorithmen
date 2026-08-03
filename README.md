# Evolutionäre Algorithmen — Praktikum und Hausarbeit

Repository zum Wahlpflichtkurs *Evolutionäre Algorithmen* (HAW Hamburg,
Sommersemester 2026, Prof. Dr.-Ing. Christian Lins). Es enthält die Lösungen der
Praktikumsaufgaben und die Hausarbeit, die auf Aufgabenblatt 3 aufbaut.

## Die Hausarbeit

**Fragestellung:** Wie viel Wahrnehmung — Zielrichtung und Sichtradius — braucht
ein NEAT-Agent, um ein Labyrinth zuverlässig zu lösen, und ab wann schadet mehr
Eingabe mehr, als sie nützt?

Untersucht werden fünf Wahrnehmungsvarianten und vier NEAT-Parameter. Die
Ausarbeitung liegt in `report-latex/` (ACM `acmart`, Format `sigconf`).

| Variante | Sichtradius | Zielrichtung | Eingänge |
|---|---|---|---|
| V0 | 1 | nein | 8 |
| V1 | 1 | ja | 10 |
| V2 | 2 | nein | 24 |
| V3 | 2 | ja | 26 |
| V4 | 3 | ja | 50 |

## Einrichtung

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Getestet mit Python 3.14. Für `visualize.draw_net()` wird zusätzlich das
systemweite Graphviz gebraucht ohne das Programm `dot`
laufen alle Messungen trotzdem, nur die Netz-Abbildung fehlt.

## Aufbau

```
python/NEAT-Code-Template/
    agent_neat.py     Agent, Labyrinth-Generator, Fitness, NEAT-Anbindung
    neat-config       NEAT-Parameter
    experiment.py     Messreihe über alle Varianten
    sweep.py          Parameterstudie zu Hypothese H4
    auswertung.py     Abbildungen und LaTeX-Tabelle aus den Messdaten
    visualize.py      Zeichenhilfen aus der Aufgabenvorlage
ergebnisse/           Messdaten als CSV
report-latex/         Ausarbeitung (main.tex) und erzeugte Abbildungen
java/, notebook.ipynb Lösungen der übrigen Aufgabenblätter
```

## Ausführen

Alle Skripte werden direkt gestartet und über Konstanten am Dateikopf gesteuert.
Das Arbeitsverzeichnis ist beliebig.

**Ein einzelner Lauf mit Anzeige** (rund drei Minuten):

```bash
.venv/bin/python python/NEAT-Code-Template/agent_neat.py
```

Zeigt am Ende den Pfad des besten Netzes in einem Fenster. Die Stellschrauben
stehen oben in `agent_neat.py`: `RADIUS`, `USE_GOAL_DIR`, `ALLOW_BACKTRACK`,
`MAZE_SEED`, `RUN_SEED`.

**Die Messreihe** (fünf Varianten × zehn Wiederholungen, rund 2,5 Stunden):

```bash
.venv/bin/python python/NEAT-Code-Template/experiment.py
```

Einstellungen: `RUN_VARIANTS` (`"all"` oder z. B. `["V1", "V3"]`),
`REPETITIONS`, `GENERATIONEN`. Ergebnisse landen in `ergebnisse/runs.csv`
(eine Zeile pro Lauf) und `ergebnisse/generations.csv` (eine Zeile pro
Generation). Jede Zeile wird sofort geschrieben, ein Abbruch kostet also nur
den laufenden Lauf.

**Die Parameterstudie** (rund 2,5 Stunden):

```bash
.venv/bin/python python/NEAT-Code-Template/sweep.py
```

Braucht eine **vollständige** `runs.csv`, weil sie daraus die beste Variante
wählt, mit `SWEEP_VARIANTE` lässt sich das überschreiben. Die Ausgangswerte der
Parameter werden nicht erneut gerechnet, sondern bei der Auswertung aus
`runs.csv` geholt. Schreibt `ergebnisse/sweep_runs.csv` und
`ergebnisse/sweep_generations.csv`.

**Auswertung** (Sekunden):

```bash
.venv/bin/python python/NEAT-Code-Template/auswertung.py
```

Erzeugt die Abbildungen in `report-latex/abbildungen/` und die Tabelle
`report-latex/ergebnistabelle.tex`, die `main.tex` per `\input` einbindet.
Kommt mit unvollständigen Messreihen zurecht.

Reihenfolge also: `experiment.py` → `sweep.py` → `auswertung.py`.

## Reproduzierbarkeit

Wiederholung *i* benutzt Labyrinth *i* und Lauf-Seed *i*, und alle Varianten
bekommen dieselben zehn Paare. Dadurch treten sie gegen dieselben Labyrinthe
mit denselben Startpopulationen an. Die Karten entstehen aus einem eigenen
Zufallsgenerator und beeinflussen den Zufallsstrom der Evolution nicht.

Gleiche Seeds, gleiche Paketversionen und gleicher Code ergeben dieselben
Zahlen. Deshalb sind die Versionen in `requirements.txt` festgenagelt.

## Die Ausarbeitung bauen

```bash
cd report-latex
pdflatex main && pdflatex main
```

`report-latex/main.pdf` ist mit eingecheckt und lässt sich also auch ohne
TeX-Installation lesen.
