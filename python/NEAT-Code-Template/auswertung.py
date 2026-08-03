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

# Strichmuster als zweite Unterscheidung neben der Farbe. Nicht wegen
# Schwarzweissdruck - die Ausarbeitung wird farbig gelesen -, sondern weil sich
# die Kurven ueber weite Strecken ueberdecken und die obenliegende sonst die
# darunter komplett verbirgt. Punktmarker gab es zusaetzlich, sie sind
# entfernt: bei fuenf farbigen Kurven trennt die Farbe bereits eindeutig.
LINIEN = ["-", "--", "-.", ":", (0, (3, 1, 1, 1))]

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

    def optional(name):
        pfad = os.path.join(experiment.ERGEBNIS_DIR, name)
        return lesen(pfad) if os.path.exists(pfad) else []

    return (lesen(pfad_runs), gen, optional("sweep_runs.csv"),
            optional("ablation_runs.csv"),
            optional("replikation_karten10-19.csv"))


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
                linestyle=LINIEN[nummer % len(LINIEN)], label=variante)

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
# Loesungsmatrizen
# ---------------------------------------------------------------------------
# Die Matrizen zeigen dieselben Daten wie die Balken- und Punktdiagramme, aber
# ohne zu mitteln: eine Zelle je Lauf. Erst dadurch wird sichtbar, dass die
# Zeilen (Konfigurationen) sich kaum unterscheiden, waehrend die Spalten
# (Karten) fast alles erklaeren - das Mitteln verschenkt genau diese Information.

LUECKE = 0.16          # Anteil der Zelle, der als Abstand frei bleibt
ZELLE = 0.155          # Kantenlaenge einer Zelle in Zoll

# Die Matrizen zeigen einen Ja-Nein-Zustand, keine Zugehoerigkeit. Deshalb
# tragen alle Zellen dieselbe neutrale Farbe und das Ergebnis steckt allein in
# gefuellt gegen leer.
ZELLFARBE = "#3d3b36"

LEGENDE = "gefüllt = Ziel erreicht, leer = nicht erreicht"


def _matrix(bloecke, karten, legende=LEGENDE, fussnote=None, zusatzzeilen=0):
    """
        Zeichnet alle Bloecke in EINE Achse, damit die Zellen ueberall gleich
        gross und quadratisch sind.

        `bloecke` ist eine Liste aus (Gruppentitel oder None, zeilen), wobei
        eine Zeile (Beschriftung, Farbe, {Karte: geloest}) ist. Fehlt eine
        Karte im Woerterbuch, wurde sie nicht gemessen und bleibt leer.
    """
    from matplotlib.patches import Rectangle

    # Zeilenraster aufbauen: Gruppentitel belegen eine eigene Zeile.
    raster = []
    for titel, zeilen in bloecke:
        if titel:
            raster.append(("titel", titel, None, None))
        for name, farb, werte in zeilen:
            raster.append(("daten", name, farb, werte))

    hoehe = len(raster) + (1 if fussnote else 0) + zusatzzeilen
    # Die Breite muss die Zeilenbeschriftungen mittragen, die Hoehe folgt aus
    # der Zellengroesse. Der Anker oben verhindert, dass die durch
    # aspect="equal" gestauchte Achse in der Figur zentriert wird und darunter
    # eine grosse Luecke stehen bleibt.
    fig, ax = plt.subplots(figsize=(len(karten) * ZELLE + 1.6,
                                    hoehe * ZELLE + 0.55))
    ax.set_anchor("N")

    beschriftungen = []
    for y, (art, name, farb, werte) in enumerate(raster):
        if art == "titel":
            # Linksbuendig am Rasterrand, damit lange Gruppentitel die Spalte
            # der Zeilenbeschriftungen nicht aufblaehen.
            ax.text(0.0, y + 0.55, name, ha="left", va="center",
                    fontsize=7.5, color=INK, fontweight="bold")
            beschriftungen.append("")
            continue
        beschriftungen.append(name)
        for x, karte in enumerate(karten):
            if karte not in werte:
                continue
            ax.add_patch(Rectangle(
                (x + LUECKE / 2, y + LUECKE / 2), 1 - LUECKE, 1 - LUECKE,
                facecolor=farb if werte[karte] else "white",
                edgecolor=farb, linewidth=0.9))

    if fussnote:
        y = len(raster)
        ax.text(-0.4, y + 0.55, fussnote, ha="right", va="center",
                fontsize=7, color=MUTED)
        for x, karte in enumerate(karten):
            gemessen = [w for a, _, _, w in raster if a == "daten"
                        and karte in w]
            ax.text(x + 0.5, y + 0.55, str(sum(w[karte] for w in gemessen)),
                    ha="center", va="center", fontsize=7, color=INK)
        beschriftungen.append("")

    ax.set_aspect("equal")
    ax.set_xlim(0, len(karten))
    ax.set_ylim(hoehe, 0)
    ax.set_xticks([x + 0.5 for x in range(len(karten))])
    ax.set_xticklabels([str(k) for k in karten], fontsize=7)
    ax.set_yticks([y + 0.5 for y in range(len(beschriftungen))])
    ax.set_yticklabels(beschriftungen, fontsize=7)
    ax.xaxis.set_ticks_position("top")
    ax.xaxis.set_label_position("top")
    ax.set_xlabel("Karte", fontsize=8, color=MUTED, labelpad=4)
    ax.tick_params(colors=MUTED, length=0)
    for rand in ax.spines.values():
        rand.set_visible(False)
    for text in ax.get_yticklabels():
        text.set_color(INK)

    if legende:
        ax.annotate(legende, xy=(0, 0), xytext=(0, -10),
                    xycoords="axes fraction", textcoords="offset points",
                    fontsize=6.8, color=MUTED, va="top")

    return fig, ax


def _geloest_je_karte(zeilen, variante):
    """{Kartennummer: 0/1} fuer eine Variante aus einer Liste von CSV-Zeilen."""
    return {z["maze_seed"]: z["geloest"] for z in zeilen
            if z["variante"] == variante}


def abbildung_loesungsmatrix(runs, sweep, ablation):
    """Alle Konfigurationen gegen die zehn Karten der Hauptmessung."""
    karten = sorted({z["maze_seed"] for z in runs})
    if not karten:
        return

    bloecke = []
    for titel, namen in (("ohne Zielrichtung", ("V0", "V2", "V1K")),
                         ("mit Zielrichtung", ("V1", "V3", "V4"))):
        zeilen = []
        for name in namen:
            quelle = ablation if name == "V1K" else runs
            werte = {k: v for k, v in _geloest_je_karte(quelle, name).items()
                     if k in karten}
            if werte:
                zeilen.append((name, ZELLFARBE, werte))
        if zeilen:
            bloecke.append((titel, zeilen))

    if sweep:
        kurz = {"pop_size": "pop_size", "compatibility_threshold": "compat_thr",
                "conn_add_prob": "conn_add", "node_add_prob": "node_add"}
        gesehen, zeilen = [], []
        for z in sweep:
            schluessel = (z["sweep_parameter"], z["sweep_wert"])
            if schluessel in gesehen:
                continue
            gesehen.append(schluessel)
            name, wert = schluessel
            werte = {z2["maze_seed"]: z2["geloest"] for z2 in sweep
                     if (z2["sweep_parameter"], z2["sweep_wert"]) == schluessel}
            zeilen.append((f"{kurz.get(name, name)} = {wert:g}", ZELLFARBE,
                           werte))
        if zeilen:
            bloecke.append(("NEAT-Parameter, sonst wie V1", zeilen))

    anzahl = sum(len(z) for _, z in bloecke)
    fig, _ = _matrix(bloecke, karten, legende=LEGENDE,
                     fussnote=f"von {anzahl} gelöst:")
    speichern(fig, "loesungsmatrix.png")


def abbildung_replikation(runs, ablation, replikation):
    """Die vier auf allen zwanzig Karten gemessenen Konfigurationen."""
    if not replikation or not ablation:
        return

    zusammen = runs + ablation + replikation
    karten = sorted({z["maze_seed"] for z in zusammen})

    bloecke = []
    anzahl = 0
    for titel, eintraege in (
            ("ohne Zielrichtung", (("V0", "V0"),
                                   ("V1K", "V1K  (konstant)"))),
            ("mit Zielrichtung", (("V1", "V1"), ("V3", "V3  ($r=2$)")))):
        zeilen = []
        for name, text in eintraege:
            werte = _geloest_je_karte(zusammen, name)
            # Nur Konfigurationen zeigen, die auf allen Karten liefen.
            if len(werte) == len(karten):
                zeilen.append((f"{text}   {sum(werte.values())}/{len(karten)}",
                               ZELLFARBE, werte))
        anzahl += len(zeilen)
        if zeilen:
            bloecke.append((titel, zeilen))

    if anzahl < 2:
        return

    fig, ax = _matrix(bloecke, karten, legende=LEGENDE, zusatzzeilen=1)
    zeilen = [z for _, b in bloecke for z in b]

    # Trennlinie zwischen Hauptmessung und den frischen Karten.
    grenze = sum(1 for k in karten if k < 10)
    if 0 < grenze < len(karten):
        ax.axvline(grenze, color=INK, linewidth=0.9, zorder=3)
        # Unter der letzten Zeile: Datenzeilen plus die Zeilen der Gruppentitel.
        unten = len(zeilen) + len(bloecke) + 0.6
        for mitte, text in ((grenze / 2, "Hauptmessung"),
                            ((grenze + len(karten)) / 2, "frische Karten")):
            ax.text(mitte, unten, text, ha="center", va="center",
                    fontsize=7.5, color=MUTED)
    speichern(fig, "replikation.png")


# ---------------------------------------------------------------------------
# Tabelle fuer die Ausarbeitung
# ---------------------------------------------------------------------------

KOPF = [
    r"% Automatisch erzeugt von python/NEAT-Code-Template/auswertung.py.",
    r"% Nicht von Hand aendern - beim naechsten Lauf wird die Datei ersetzt.",
]


def _mittel(werte, stellen=1, streuung=True):
    werte = [w for w in werte if w is not None]
    if not werte:
        return "--"
    text = f"{statistics.mean(werte):.{stellen}f}"
    if streuung and len(werte) > 1:
        text += f" $\\pm$ {statistics.stdev(werte):.{stellen}f}"
    return text


def _schreiben(name, zeilen):
    pfad = os.path.join(BERICHT_DIR, name)
    with open(pfad, "w", encoding="utf-8") as datei:
        datei.write("\n".join(KOPF + zeilen) + "\n")
    print(f"  {os.path.relpath(pfad, REPO)}")


def tabelle(runs, varianten, ablation):
    """Kennzahlen je Wahrnehmungsvariante, mit \\input einbindbar."""
    zeilen = [
        r"\begin{tabular}{@{}lrrrrr@{}}",
        r"  \toprule",
        r"  Variante & Eing. & gelöst & Gen. bis Ziel & beste Fitness "
        r"& s/Lauf \\",
        r"  \midrule",
    ]

    quellen = [(v, runs) for v in varianten]
    if ablation:
        quellen.append(("V1K", ablation))

    for variante, daten in quellen:
        eigene = [z for z in daten if z["variante"] == variante
                  and z["maze_seed"] < 10]
        if not eigene:
            continue
        geloest = [z for z in eigene if z["geloest"]]
        radius = eigene[0]["radius"]
        eingaben = (2 * radius + 1) ** 2 - 1 + 2 * eigene[0]["zielrichtung"]

        zeilen.append(
            f"  {variante} & {eingaben} & "
            f"{len(geloest)}/{len(eigene)} & "
            f"{_mittel([z['ziel_generation'] for z in geloest])} & "
            f"{_mittel([z['beste_fitness'] for z in eigene], 2)} & "
            f"{_mittel([z['laufzeit_s'] for z in eigene], 0, False)} \\\\")

    zeilen += [r"  \bottomrule", r"\end{tabular}"]
    _schreiben("ergebnistabelle.tex", zeilen)


def tabelle_sweep(runs, sweep):
    """
        Kennzahlen je Sweep-Konfiguration.

        Die Spalte Evaluationen ist noetig, weil Generationen ueber
        verschiedene pop_size hinweg nicht vergleichbar sind: eine Generation
        mit 250 Individuen kostet ein Viertel einer Generation mit 1000.
    """
    if not sweep:
        return

    variante = sweep[0]["variante"]
    basis = [z for z in runs if z["variante"] == variante]

    zeilen = [
        r"\begin{tabular}{@{}llrrrr@{}}",
        r"  \toprule",
        r"  Parameter & Wert & gelöst & Gen. & Eval. & s/Lauf \\",
        r"  \midrule",
    ]

    def block(name, wert, daten, hinweis=""):
        geloest = [z for z in daten if z["geloest"]]
        pop = daten[0]["pop_size"]
        evals = [pop * (z["ziel_generation"] + 1) for z in geloest]
        return (f"  {name} & {wert}{hinweis} & "
                f"{len(geloest)}/{len(daten)} & "
                f"{_mittel([z['ziel_generation'] for z in geloest], 1, False)} & "
                f"{_mittel(evals, 0, False)} & "
                f"{_mittel([z['laufzeit_s'] for z in daten], 0, False)} \\\\")

    if basis:
        zeilen.append(block(r"\emph{Referenz}", variante, basis))
        zeilen.append(r"  \midrule")

    gesehen = []
    for z in sweep:
        if z["sweep_parameter"] not in gesehen:
            gesehen.append(z["sweep_parameter"])

    for name in gesehen:
        eigene = [z for z in sweep if z["sweep_parameter"] == name]
        for wert in sorted({z["sweep_wert"] for z in eigene}):
            daten = [z for z in eigene if z["sweep_wert"] == wert]
            zeilen.append(block(name.replace("_", r"\_"), f"{wert:g}", daten))

    zeilen += [r"  \bottomrule", r"\end{tabular}"]
    _schreiben("sweeptabelle.tex", zeilen)


# ---------------------------------------------------------------------------

def main():
    runs, gen, sweep, ablation, replikation = lade()
    varianten = vorhandene_varianten(runs)
    if not varianten:
        raise SystemExit("runs.csv enthält keine auswertbaren Zeilen.")

    unvollstaendig = [v for v in experiment.VARIANTEN if v not in varianten]
    print(f"{len(runs)} Läufe, Varianten: {', '.join(varianten)}")
    if unvollstaendig:
        print(f"Noch ohne Daten: {', '.join(unvollstaendig)}")
    for name, daten in (("Sweep", sweep), ("Ablation", ablation),
                        ("Replikation", replikation)):
        print(f"{name}: {len(daten)} Läufe" if daten
              else f"{name}: keine Daten")
    print("\nErzeugt:")

    abbildung_erfolgsquote(runs, varianten)
    abbildung_fitnessverlauf(gen, varianten)
    abbildung_generationen(runs, varianten)
    abbildung_sweep(runs, sweep)
    abbildung_loesungsmatrix(runs, sweep, ablation)
    abbildung_replikation(runs, ablation, replikation)
    tabelle(runs, varianten, ablation)
    tabelle_sweep(runs, sweep)


if __name__ == "__main__":
    main()
