"""
    Ablationstest zu H1: liefert die Zielrichtung Information, oder haengt der
    Unterschied zwischen V0 und V1 nur an den zwei zusaetzlichen Eingaengen?

    Der Vergleich V0 gegen V1 aendert zwei Dinge gleichzeitig. V1 bekommt die
    Zielrichtung, hat dadurch aber auch zwei Eingaenge mehr, also ein groesseres
    Netz und einen groesseren Suchraum fuer NEAT. Bleibt ein Effekt aus, sind
    zwei Erklaerungen moeglich: die Information nuetzt nichts, oder sie nuetzt
    etwas und der groessere Suchraum frisst den Gewinn genau auf.

    V1K trennt das. Es ist V1 mit einer Konstante an den beiden
    Zielrichtungs-Eingaengen: gleiche Eingabelaenge, gleiche Netzgroesse,
    gleiche Startpopulation, gleiche Groessenordnung der Werte nur ohne
    Information. Ein konstanter Eingang ist funktional ein zweiter Bias-Pfad.

    Ergebnis landet in ergebnisse/ablation_runs.csv und
    ergebnisse/ablation_generations.csv.
"""

import csv
import os
import time

import experiment


# Die Hauptmessung benutzt die Karten 0-9, die Replikation 10-19.
# range(0, 20) rechnet beides, damit der Vergleich auf derselben Datenmenge
# steht wie V0 und V1.
KARTEN = range(0, 20)

# Zu vergleichende Ablationsvariante aus experiment.ABLATION.
VARIANTE = "V1K"


def main():
    os.makedirs(experiment.ERGEBNIS_DIR, exist_ok=True)
    runs_pfad = os.path.join(experiment.ERGEBNIS_DIR, "ablation_runs.csv")
    gen_pfad = os.path.join(experiment.ERGEBNIS_DIR,
                            "ablation_generations.csv")

    runs_datei, runs_csv = experiment._schreiber(runs_pfad,
                                                 experiment.RUNS_SPALTEN)
    gen_datei, gen_csv = experiment._schreiber(gen_pfad,
                                               experiment.GENERATIONS_SPALTEN)

    beginn = time.perf_counter()
    zeilen = []
    try:
        for nummer, karte in enumerate(KARTEN, start=1):
            print(f"[{nummer}/{len(KARTEN)}] {VARIANTE}, Karte {karte} ...",
                  flush=True)

            zeile, generationen = experiment.einzellauf(VARIANTE, karte)
            zeilen.append(zeile)

            # Sofort schreiben, damit ein Abbruch nicht alles kostet.
            runs_csv.writerow(zeile)
            runs_datei.flush()
            gen_csv.writerows(generationen)
            gen_datei.flush()

            status = (f"Ziel in Generation {zeile['ziel_generation']}"
                      if zeile["geloest"] else "nicht geloest")
            print(f"    {status}, beste Fitness {zeile['beste_fitness']:.2f}, "
                  f"{zeile['laufzeit_s']:.0f} s", flush=True)
    finally:
        runs_datei.close()
        gen_datei.close()

    geloest = [z for z in zeilen if z["geloest"]]
    print(f"\nGesamtlaufzeit: {(time.perf_counter() - beginn) / 60:.1f} min")
    print(f"{VARIANTE}: {len(geloest)}/{len(zeilen)} geloest, Karten "
          f"{sorted(z['maze_seed'] for z in geloest)}")
    print("Zum Vergleich aus runs.csv und replikation_karten10-19.csv:")
    print("  V0  (8 Eingaenge, keine Zielrichtung)  14/20")
    print("  V1  (10 Eingaenge, Zielrichtung)       14/20")


if __name__ == "__main__":
    main()
