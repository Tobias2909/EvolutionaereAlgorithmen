"""
    Parameterstudie zu Hypothese H4.

    Variiert jeweils einen NEAT-Parameter, waehrend alle anderen auf ihrem
    Ausgangswert bleiben, und rechnet dafuer dieselben Wiederholungen wie die
    Hauptmessung: Wiederholung i benutzt Labyrinth i und Lauf-Seed i.

    Gerechnet wird nur auf einer Variante. Der besten aus der Hauptmessung.
    Eine vollstaendige Kombination aller Varianten mit allen Parameterwerten
    waere zeitlich nicht sinnvoll durchfuehrbar.

    Der jeweils mittlere Parameterwert entspricht der Hauptmessung und wird
    nicht erneut gerechnet. Die Auswertung holt ihn aus runs.csv.

    Ergebnisse landen in ergebnisse/sweep_runs.csv und
    ergebnisse/sweep_generations.csv.
"""

import csv
import os
import statistics
import time

import experiment


# ---------------------------------------------------------------------------
# Einstellungen
# ---------------------------------------------------------------------------

# Auf welcher Variante wird gerechnet? None = automatisch die beste aus
# runs.csv, sonst z.B. "V3".
#
# Fest auf V1 gesetzt: V1 und V3 sind in der Hauptmessung nicht unterscheidbar
# (beide 8 von 10 geloest), die automatische Wahl wuerde bei diesem Gleichstand
# aber V3 nehmen - und V3 rechnet mit Radius 2 rund 40 % laenger pro Lauf,
# ohne einen messbaren Vorteil zu bieten.
SWEEP_VARIANTE = "V1"

# Wiederholungen je Parameterwert.
#
# MUSS zur Kartenzahl der Hauptmessung in runs.csv passen. Der Vergleichspunkt
# jedes Parameters wird nicht neu gerechnet, sondern von der Auswertung aus
# runs.csv geholt; bei abweichender Zahl verglichen man verschiedene
# Kartenmengen und die Paarung waere hinfaellig.
REPETITIONS = 10

GENERATIONEN = 100

# Die untersuchten Parameter. Der mittlere Wert ist jeweils der Ausgangswert
# aus neat-config und wird uebersprungen.
# compatibility_threshold: der wirksame Bereich ist eng. Gemessen an der
# Zahl der Spezies in der Startpopulation (pop_size 1000): 2.0 ergibt 997
# Spezies und sprengt die Konfiguration (neat verlangt
# pop_size >= num_species * 2), 2.4 ergibt 268, 2.8 ergibt 14, 3.0 ergibt 3,
# und ab 3.2 bleibt genau eine Spezies uebrig dort ist die Speziesbildung
# faktisch abgeschaltet und hoehere Werte aendern nichts mehr. Gewaehlt sind
# deshalb 2.6 und 3.2, also einmal deutlich mehr Spezies als im Ausgangs-
# zustand und einmal keine.
PARAMETER = {
    "pop_size": [250, 500, 1000],
    "compatibility_threshold": [2.6, 2.8, 3.2],
    "conn_add_prob": [0.3, 0.5, 0.7],
    "node_add_prob": [0.1, 0.3, 0.5],
}

SWEEP_RUNS_SPALTEN = (["sweep_parameter", "sweep_wert"]
                      + experiment.RUNS_SPALTEN)
SWEEP_GEN_SPALTEN = (["sweep_parameter", "sweep_wert"]
                     + experiment.GENERATIONS_SPALTEN)


# ---------------------------------------------------------------------------

def ausgangswerte():
    """Liest die Ausgangswerte der untersuchten Parameter aus neat-config."""
    import agent_neat
    config = agent_neat.load_config()
    return {
        "pop_size": config.pop_size,
        "compatibility_threshold":
            config.species_set_config.compatibility_threshold,
        "conn_add_prob": config.genome_config.conn_add_prob,
        "node_add_prob": config.genome_config.node_add_prob,
    }


def beste_variante():
    """
        Waehlt die Variante mit der hoechsten Erfolgsquote aus runs.csv.

        Bei Gleichstand entscheidet die kleinere mittlere Generationenzahl bis
        zur Zielerreichung, danach die Reihenfolge aus experiment.VARIANTEN.
    """
    pfad = os.path.join(experiment.ERGEBNIS_DIR, "runs.csv")
    if not os.path.exists(pfad):
        raise SystemExit(f"{pfad} fehlt. Zuerst experiment.py laufen lassen "
                         f"oder SWEEP_VARIANTE von Hand setzen.")

    with open(pfad, encoding="utf-8") as datei:
        zeilen = list(csv.DictReader(datei))
    if not zeilen:
        raise SystemExit("runs.csv enthaelt keine Zeilen.")

    bewertung = {}
    for variante in experiment.VARIANTEN:
        eigene = [z for z in zeilen if z["variante"] == variante]
        if not eigene:
            continue
        geloest = [z for z in eigene if z["geloest"] == "1"]
        quote = len(geloest) / len(eigene)
        schnitt = (statistics.mean(int(z["ziel_generation"])
                                   for z in geloest)
                   if geloest else float("inf"))
        bewertung[variante] = (quote, schnitt, len(eigene))

    if not bewertung:
        raise SystemExit("runs.csv enthaelt keine bekannten Varianten.")

    unvollstaendig = [v for v, (_, _, n) in bewertung.items()
                      if n < REPETITIONS]
    if unvollstaendig or len(bewertung) < len(experiment.VARIANTEN):
        print("Achtung: die Hauptmessung ist unvollstaendig. Die Auswahl der "
              "besten Variante kann sich noch aendern.")

    return max(bewertung, key=lambda v: (bewertung[v][0], -bewertung[v][1]))


def laeufe_planen(basis):
    """Liste der zu rechnenden (Parameter, Wert)-Paare ohne die Ausgangswerte."""
    plan = []
    for name, werte in PARAMETER.items():
        for wert in werte:
            if wert == basis[name]:
                continue          # entspricht der Hauptmessung
            plan.append((name, wert))
    return plan


def zusammenfassung(zeilen, basis):
    print("\n" + "=" * 78)
    print("Zusammenfassung des Parameter-Sweeps")
    print("=" * 78)
    for name in PARAMETER:
        print(f"\n{name} (Ausgangswert {basis[name]}):")
        for wert in PARAMETER[name]:
            eigene = [z for z in zeilen
                      if z["sweep_parameter"] == name and z["sweep_wert"] == wert]
            if not eigene:
                hinweis = ("  -> aus der Hauptmessung, siehe runs.csv"
                           if wert == basis[name] else "  -> nicht gerechnet")
                print(f"  {wert:>8}{hinweis}")
                continue
            geloest = sum(z["geloest"] for z in eigene)
            fitness = statistics.mean(z["beste_fitness"] for z in eigene)
            print(f"  {wert:>8}  geloest {geloest}/{len(eigene)}, "
                  f"beste Fitness im Mittel {fitness:.2f}")


def _bereits_gerechnet(pfad):
    """Liest, welche (Parameter, Wert, Wiederholung) schon in der CSV stehen."""
    if not os.path.exists(pfad):
        return set(), []
    with open(pfad, encoding="utf-8") as datei:
        zeilen = list(csv.DictReader(datei))
    fertig = {(z["sweep_parameter"], float(z["sweep_wert"]),
               int(z["wiederholung"])) for z in zeilen}
    return fertig, zeilen


def _anhaengen(pfad, spalten):
    """Oeffnet eine CSV zum Anhaengen, schreibt den Kopf nur bei neuer Datei."""
    neu = not os.path.exists(pfad)
    datei = open(pfad, "a", newline="", encoding="utf-8")
    schreiber = csv.DictWriter(datei, fieldnames=spalten)
    if neu:
        schreiber.writeheader()
    return datei, schreiber


def main():
    basis = ausgangswerte()
    variante = SWEEP_VARIANTE or beste_variante()
    plan = laeufe_planen(basis)
    gesamt = len(plan) * REPETITIONS

    print(f"Parameter-Sweep auf Variante {variante}")
    print(f"{len(plan)} Konfigurationen x {REPETITIONS} Wiederholungen "
          f"= {gesamt} Laeufe")
    print(f"Ausgangswerte (nicht erneut gerechnet): {basis}\n")

    os.makedirs(experiment.ERGEBNIS_DIR, exist_ok=True)
    runs_pfad = os.path.join(experiment.ERGEBNIS_DIR, "sweep_runs.csv")
    fertig, alte_zeilen = _bereits_gerechnet(runs_pfad)
    if fertig:
        print(f"{len(fertig)} Laeufe stehen schon in sweep_runs.csv und "
              f"werden uebersprungen.\n")

    runs_datei, runs_csv = _anhaengen(runs_pfad, SWEEP_RUNS_SPALTEN)
    gen_datei, gen_csv = _anhaengen(
        os.path.join(experiment.ERGEBNIS_DIR, "sweep_generations.csv"),
        SWEEP_GEN_SPALTEN)

    # GENERATIONEN wirkt ueber das Modul, in dem einzellauf() lebt.
    vorher = experiment.GENERATIONEN
    experiment.GENERATIONEN = GENERATIONEN

    # Bereits gerechnete Zeilen fuer die Zusammenfassung wiederverwenden
    alle = [{**z, "sweep_wert": float(z["sweep_wert"]),
             "geloest": int(z["geloest"]),
             "beste_fitness": float(z["beste_fitness"])}
            for z in alte_zeilen]
    gescheitert = []
    beginn = time.perf_counter()
    try:
        nummer = 0
        for name, wert in plan:
            for wiederholung in range(REPETITIONS):
                # Zaehler laeuft ueber den Plan, nicht ueber die Ergebnisliste:
                # bei einer Wiederaufnahme stehen dort schon Zeilen aus einem
                # frueheren Durchgang.
                nummer += 1
                if (name, float(wert), wiederholung) in fertig:
                    continue
                print(f"[{nummer}/{gesamt}] {name} = {wert}, "
                      f"Wiederholung {wiederholung} ...", flush=True)

                try:
                    zeile, generationen = experiment.einzellauf(
                        variante, wiederholung, parameter={name: wert})
                except Exception as fehler:
                    # Manche Parameterwerte sind fuer neat-python nicht
                    # durchfuehrbar (etwa eine zu kleine
                    # compatibility_threshold, die fast jedes Genom zur
                    # eigenen Spezies macht). Das darf die restliche Reihe
                    # nicht kosten.
                    gescheitert.append((name, wert, wiederholung, fehler))
                    print(f"    FEHLER, uebersprungen: "
                          f"{type(fehler).__name__}: {fehler}", flush=True)
                    continue

                kopf = {"sweep_parameter": name, "sweep_wert": wert}
                zeile = {**kopf, **zeile}
                alle.append(zeile)

                runs_csv.writerow(zeile)
                runs_datei.flush()
                gen_csv.writerows({**kopf, **g} for g in generationen)
                gen_datei.flush()

                status = (f"Ziel in Generation {zeile['ziel_generation']}"
                          if zeile["geloest"] else "nicht geloest")
                print(f"    {status}, beste Fitness "
                      f"{zeile['beste_fitness']:.2f}, "
                      f"{zeile['laufzeit_s']:.0f} s", flush=True)
    finally:
        experiment.GENERATIONEN = vorher
        runs_datei.close()
        gen_datei.close()

    print(f"\nGesamtlaufzeit: {(time.perf_counter() - beginn) / 60:.1f} min")
    if gescheitert:
        print(f"\n{len(gescheitert)} Laeufe sind gescheitert:")
        for name, wert, w, fehler in gescheitert:
            print(f"  {name} = {wert}, Wiederholung {w}: {fehler}")
    zusammenfassung(alle, basis)


if __name__ == "__main__":
    main()
