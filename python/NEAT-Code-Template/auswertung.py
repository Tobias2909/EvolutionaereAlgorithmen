"""
    Erzeugt aus den Messdaten die Abbildungen und die Ergebnistabelle fuer die
    Ausarbeitung.

    Liest ergebnisse/runs.csv und ergebnisse/generations.csv, schreibt nach
    report-latex/abbildungen/ sowie report-latex/ergebnistabelle.tex.

    Sie kommt mit unvollstaendigen Messreihen zurecht und ueberspringt Varianten,
    zu denen noch keine Daten vorliegen.
"""

import csv
import os
import statistics

import matplotlib
matplotlib.use("Agg")          # keine Fenster, nur Dateien
import matplotlib.pyplot as plt

import experiment


# ---------------------------------------------------------------------------
# Farben und Stil
# ---------------------------------------------------------------------------
# Kategoriale Palette in fester Reihenfolge eine Farbe gehoert dauerhaft zu
# einer Variante und wird nicht nach Rang vergeben. Die Reihenfolge ist auf
# Farbfehlsichtigkeit geprueft (schlechtestes benachbartes Paar dE 9.1).
FARBEN = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]

# Zweite Unterscheidung neben der Farbe, damit die Abbildungen auch
# schwarzweiss gedruckt lesbar bleiben.
LINIEN = ["-", "--", "-.", ":", (0, (3, 1, 1, 1))]
MARKER = ["o", "s", "^", "D", "v"]

INK = "#0b0b0b"          # Primaertext
MUTED = "#898781"        # Achsenbeschriftung
GRID = "#e1e0d9"         # Gitterlinien
BASELINE = "#c3c2b7"     # Achsenlinie

_HIER = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(_HIER))
BERICHT_DIR = os.path.join(REPO, "report-latex")
BILD_DIR = os.path.join(BERICHT_DIR, "abbildungen")

# Spaltenbreite des zweispaltigen ACM-Layouts in Zoll.
BREITE = 3.3


def stil(ax):
    """Achsen zurueckhaltend gestalten: Daten vor Dekoration."""
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    for rand in ("top", "right"):
        ax.spines[rand].set_visible(False)
    for rand in ("left", "bottom"):
        ax.spines[rand].set_color(BASELINE)
        ax.spines[rand].set_linewidth(0.8)
    ax.tick_params(colors=MUTED, labelsize=7, length=0)
    ax.xaxis.label.set_color(MUTED)
    ax.yaxis.label.set_color(MUTED)
    ax.xaxis.label.set_fontsize(8)
    ax.yaxis.label.set_fontsize(8)


def speichern(fig, name):
    os.makedirs(BILD_DIR, exist_ok=True)
    pfad = os.path.join(BILD_DIR, name)
    fig.savefig(pfad, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  {os.path.relpath(pfad, REPO)}")


# ---------------------------------------------------------------------------
# Daten laden
# ---------------------------------------------------------------------------

def zahl(text):
    """CSV-Feld in Zahl wandeln, leere Felder werden zu None."""
    if text is None or text == "":
        return None
    return float(text) if "." in text else int(text)


def lade():
    pfad_runs = os.path.join(experiment.ERGEBNIS_DIR, "runs.csv")
    pfad_gen = os.path.join(experiment.ERGEBNIS_DIR, "generations.csv")
    if not os.path.exists(pfad_runs):
        raise SystemExit(f"Keine Messdaten gefunden: {pfad_runs}\n"
                         f"Zuerst experiment.py laufen lassen.")

    zahlenspalten = {"radius", "zielrichtung", "wiederholung", "maze_seed",
                     "run_seed", "wanddichte", "kuerzester_weg", "geloest",
                     "ziel_generation", "schwelle_generation", "generationen",
                     "beste_fitness", "schritte_bester", "netz_knoten",
                     "netz_verbindungen", "pop_size", "generation",
                     "mittlere_fitness", "stdabw_fitness", "anzahl_spezies",
                     "ziel_erreicht", "laufzeit_s", "sweep_wert",
                     "compatibility_threshold", "conn_add_prob",
                     "node_add_prob"}

    def lesen(pfad):
        with open(pfad, encoding="utf-8") as datei:
            zeilen = []
            for roh in csv.DictReader(datei):
                zeilen.append({k: (zahl(v) if k in zahlenspalten else v)
                               for k, v in roh.items()})
            return zeilen

    gen = lesen(pfad_gen) if os.path.exists(pfad_gen) else []

    pfad_sweep = os.path.join(experiment.ERGEBNIS_DIR, "sweep_runs.csv")
    sweep = lesen(pfad_sweep) if os.path.exists(pfad_sweep) else []

    return lesen(pfad_runs), gen, sweep


def vorhandene_varianten(runs):
    """Varianten in der Reihenfolge aus experiment.VARIANTEN, nur mit Daten."""
    da = {z["variante"] for z in runs}
    return [v for v in experiment.VARIANTEN if v in da]


def farbe(variante):
    """Farbe haengt an der Variante, nicht an ihrer Position im Diagramm."""
    return FARBEN[list(experiment.VARIANTEN).index(variante) % len(FARBEN)]


def stilnummer(variante):
    return list(experiment.VARIANTEN).index(variante)


# ---------------------------------------------------------------------------
# Abbildungen
# ---------------------------------------------------------------------------

def abbildung_erfolgsquote(runs, varianten):
    """Balkendiagramm: Anteil geloester Laeufe je Variante."""
    fig, ax = plt.subplots(figsize=(BREITE, 2.1))

    for i, variante in enumerate(varianten):
        eigene = [z for z in runs if z["variante"] == variante]
        geloest = sum(z["geloest"] for z in eigene)
        anteil = geloest / len(eigene)
        # 2px Abstand zwischen benachbarten Balken ueber die Balkenbreite.
        ax.bar(i, anteil, width=0.68, color=farbe(variante))
        ax.text(i, anteil + 0.03, f"{geloest}/{len(eigene)}",
                ha="center", va="bottom", fontsize=7.5, color=INK)

    ax.set_xticks(range(len(varianten)))
    ax.set_xticklabels(varianten)
    ax.set_xlim(-0.6, len(varianten) - 0.4)
    ax.set_ylim(0, 1.15)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0 %", "25 %", "50 %", "75 %", "100 %"])
    ax.set_ylabel("gelöste Läufe")
    stil(ax)
    speichern(fig, "erfolgsquote.png")


def abbildung_fitnessverlauf(gen, varianten):
    """Linien: mittlere beste Fitness je Generation, gemittelt über die Läufe."""
    if not gen:
        return
    fig, ax = plt.subplots(figsize=(BREITE, 2.3))

    # Laenge der Achse: die laengste Wiederholung ueberhaupt.
    letzte = max(z["generation"] for z in gen)

    for variante in varianten:
        eigene = [z for z in gen if z["variante"] == variante]
        if not eigene:
            continue

        # Je Wiederholung das kumulative Maximum bilden und bis zum Ende der
        # Achse fortschreiben. Ein geloester Lauf bricht vorzeitig ab. Wuerde
        # man nur ueber die noch laufenden Wiederholungen mitteln, saehe die
        # Kurve genau dort einen Sprung, wo in Wirklichkeit nur die Zahl der
        # gemittelten Laeufe wechselt.
        proLauf = {}
        for z in eigene:
            proLauf.setdefault(z["wiederholung"], {})[z["generation"]] = \
                z["beste_fitness"]

        kurven = []
        for werte in proLauf.values():
            kurve, bisher = [], None
            for g in range(letzte + 1):
                if g in werte:
                    bisher = werte[g] if bisher is None else max(bisher,
                                                                 werte[g])
                kurve.append(bisher)
            kurven.append(kurve)

        x = list(range(letzte + 1))
        y = [statistics.mean(k[g] for k in kurven) for g in x]

        nummer = stilnummer(variante)
        ax.plot(x, y, color=farbe(variante), linewidth=1.6,
                linestyle=LINIEN[nummer % len(LINIEN)],
                marker=MARKER[nummer % len(MARKER)], markersize=3.5,
                markevery=max(1, len(x) // 8), label=variante)

    ax.set_xlabel("Generation")
    ax.set_ylabel("beste Fitness bisher")
    stil(ax)
    legende = ax.legend(frameon=False, fontsize=7, ncol=3,
                        loc="lower right", handlelength=2.6)
    for text in legende.get_texts():
        text.set_color(INK)
    speichern(fig, "fitness_verlauf.png")


def abbildung_generationen(runs, varianten):
    """Punktdiagramm: Generation der ersten Zielerreichung, ein Punkt je Lauf."""
    fig, ax = plt.subplots(figsize=(BREITE, 2.1))
    etwas = False

    for i, variante in enumerate(varianten):
        werte = [z["ziel_generation"] for z in runs
                 if z["variante"] == variante and z["geloest"]]
        if not werte:
            continue
        etwas = True
        # Punkte leicht versetzen, damit gleiche Werte sichtbar bleiben.
        versatz = [i + (k - (len(werte) - 1) / 2) * 0.06
                   for k in range(len(werte))]
        ax.plot(versatz, werte, linestyle="none", marker="o", markersize=4.5,
                color=farbe(variante), markeredgecolor="white",
                markeredgewidth=0.6)
        mittel = statistics.mean(werte)
        ax.plot([i - 0.25, i + 0.25], [mittel, mittel], color=INK,
                linewidth=1.4, solid_capstyle="butt")

    if not etwas:
        plt.close(fig)
        print("  (kein Lauf hat das Ziel erreicht, "
              "generationen_bis_ziel.png übersprungen)")
        return

    ax.set_xticks(range(len(varianten)))
    ax.set_xticklabels(varianten)
    ax.set_xlim(-0.6, len(varianten) - 0.4)
    ax.set_ylabel("Generation der Zielerreichung")
    stil(ax)
    speichern(fig, "generationen_bis_ziel.png")


def abbildung_sweep(runs, sweep):
    """
        Vier kleine Diagramme, eines je NEAT-Parameter: Erfolgsquote ueber den
        Parameterwert.

        Der Ausgangswert wurde nicht erneut gerechnet, sondern stammt aus der
        Hauptmessung, er ist hohl gezeichnet, damit die Herkunft sichtbar
        bleibt. Getrennte Diagramme statt eines gemeinsamen, weil die vier
        Parameter voellig verschiedene Wertebereiche haben und in ein Bild
        gezwungen nur ueber eine zweite Achse passen wuerden.
    """
    if not sweep:
        return

    variante = sweep[0]["variante"]
    basis = [z for z in runs if z["variante"] == variante]
    namen = []
    for z in sweep:
        if z["sweep_parameter"] not in namen:
            namen.append(z["sweep_parameter"])

    fig, achsen = plt.subplots(2, 2, figsize=(BREITE, 2.9), sharey=True)
    grundfarbe = farbe(variante)

    for ax, name in zip(achsen.flat, namen):
        eigene = [z for z in sweep if z["sweep_parameter"] == name]
        werte = sorted({z["sweep_wert"] for z in eigene})

        basiswert = basis[0][name] if basis and name in basis[0] else None
        if basiswert is not None and basiswert not in werte:
            werte = sorted(werte + [basiswert])

        x, y, ist_basis = [], [], []
        for i, wert in enumerate(werte):
            if wert == basiswert:
                quelle = basis
            else:
                quelle = [z for z in eigene if z["sweep_wert"] == wert]
            if not quelle:
                continue
            x.append(i)
            y.append(sum(z["geloest"] for z in quelle) / len(quelle))
            ist_basis.append(wert == basiswert)

        ax.plot(x, y, color=grundfarbe, linewidth=1.4, zorder=1)
        for xi, yi, b in zip(x, y, ist_basis):
            ax.plot([xi], [yi], marker="o", markersize=5, zorder=2,
                    color="white" if b else grundfarbe,
                    markeredgecolor=grundfarbe, markeredgewidth=1.4)

        ax.set_xticks(range(len(werte)))
        ax.set_xticklabels([f"{w:g}" for w in werte], fontsize=6.5)
        ax.set_xlim(-0.4, len(werte) - 0.6)
        ax.set_ylim(-0.05, 1.1)
        ax.set_yticks([0, 0.5, 1.0])
        ax.set_yticklabels(["0 %", "50 %", "100 %"])
        ax.set_title(name.replace("_", " "), fontsize=7, color=INK, pad=3)
        stil(ax)

    for ax in achsen.flat[len(namen):]:
        ax.set_visible(False)

    fig.supylabel("gelöste Läufe", fontsize=8, color=MUTED)
    fig.tight_layout(pad=0.3)
    speichern(fig, "parameter_sweep.png")


# ---------------------------------------------------------------------------
# Tabelle fuer die Ausarbeitung
# ---------------------------------------------------------------------------

def tabelle(runs, varianten):
    """Schreibt eine mit \\input einbindbare LaTeX-Tabelle."""
    zeilen = [
        r"% Automatisch erzeugt von python/NEAT-Code-Template/auswertung.py.",
        r"% Nicht von Hand aendern - beim naechsten Lauf wird die Datei ersetzt.",
        r"\begin{tabular}{@{}lrrrrr@{}}",
        r"  \toprule",
        r"  Variante & Eingaben & gelöst & Generationen & Fitness & Schritte \\",
        r"  \midrule",
    ]

    for variante in varianten:
        eigene = [z for z in runs if z["variante"] == variante]
        geloest = [z for z in eigene if z["geloest"]]
        radius = eigene[0]["radius"]
        eingaben = (2 * radius + 1) ** 2 - 1 + 2 * eigene[0]["zielrichtung"]

        def mittel(werte, stellen=1):
            werte = [w for w in werte if w is not None]
            if not werte:
                return "--"
            text = f"{statistics.mean(werte):.{stellen}f}"
            if len(werte) > 1:
                text += f" $\\pm$ {statistics.stdev(werte):.{stellen}f}"
            return text

        zeilen.append(
            f"  {variante} & {eingaben} & "
            f"{len(geloest)}/{len(eigene)} & "
            f"{mittel([z['ziel_generation'] for z in geloest])} & "
            f"{mittel([z['beste_fitness'] for z in eigene], 2)} & "
            f"{mittel([z['schritte_bester'] for z in geloest])} \\\\")

    zeilen += [r"  \bottomrule", r"\end{tabular}"]

    pfad = os.path.join(BERICHT_DIR, "ergebnistabelle.tex")
    with open(pfad, "w", encoding="utf-8") as datei:
        datei.write("\n".join(zeilen) + "\n")
    print(f"  {os.path.relpath(pfad, REPO)}")


# ---------------------------------------------------------------------------

def main():
    runs, gen, sweep = lade()
    varianten = vorhandene_varianten(runs)
    if not varianten:
        raise SystemExit("runs.csv enthält keine auswertbaren Zeilen.")

    unvollstaendig = [v for v in experiment.VARIANTEN if v not in varianten]
    print(f"{len(runs)} Läufe, Varianten: {', '.join(varianten)}")
    if unvollstaendig:
        print(f"Noch ohne Daten: {', '.join(unvollstaendig)}")
    print("\nErzeugt:")

    abbildung_erfolgsquote(runs, varianten)
    abbildung_fitnessverlauf(gen, varianten)
    abbildung_generationen(runs, varianten)
    abbildung_sweep(runs, sweep)
    tabelle(runs, varianten)


if __name__ == "__main__":
    main()
