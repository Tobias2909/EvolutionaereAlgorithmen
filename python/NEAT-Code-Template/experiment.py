"""
    Fuehrt die Messreihe der Hausarbeit aus.

    Jede Variante wird mit REPETITIONS Wiederholungen gerechnet. Wiederholung i
    benutzt Labyrinth i und Lauf-Seed i, sodass alle Varianten auf denselben
    Karten mit denselben Startpopulationen antreten.

    Ergebnisse landen in ergebnisse/runs.csv (eine Zeile pro Lauf) und
    ergebnisse/generations.csv (eine Zeile pro Generation).
"""

import csv
import os
import statistics
import time
from collections import deque

import neat

import agent_neat


# ---------------------------------------------------------------------------
# Einstellungen
# ---------------------------------------------------------------------------

# Welche Varianten sollen laufen? "all" oder eine Liste, z.B. ["V1", "V3"].
RUN_VARIANTS = "all"

# Wiederholungen pro Variante. Jede benutzt ihre eigene Karte und ihren
# eigenen Lauf-Seed, alle Varianten benutzen dieselben.
REPETITIONS = 10

# Obergrenze fuer die Evolution. Ein Lauf bricht frueher ab, wenn die in
# neat-config hinterlegte fitness_threshold ueberschritten wird.
GENERATIONEN = 100

# Die untersuchten Wahrnehmungsvarianten aus Kapitel 3 der Ausarbeitung.
VARIANTEN = {
    "V0": {"radius": 1, "zielrichtung": False},
    "V1": {"radius": 1, "zielrichtung": True},
    "V2": {"radius": 2, "zielrichtung": False},
    "V3": {"radius": 2, "zielrichtung": True},
    "V4": {"radius": 3, "zielrichtung": True},
}

# Abweichende NEAT-Parameter fuer einen einzelnen Durchgang. Leer lassen fuer
# die Hauptmessung.
NEAT_PARAMETER = {}


_HIER = os.path.dirname(os.path.abspath(__file__))
ERGEBNIS_DIR = os.path.join(os.path.dirname(os.path.dirname(_HIER)),
                            "ergebnisse")

RUNS_SPALTEN = [
    "variante", "radius", "zielrichtung", "wiederholung",
    "maze_seed", "run_seed", "wanddichte", "kuerzester_weg",
    "geloest", "ziel_generation", "schwelle_generation", "generationen",
    "beste_fitness", "schritte_bester", "netz_knoten", "netz_verbindungen",
    "pop_size", "compatibility_threshold", "conn_add_prob", "node_add_prob",
    "laufzeit_s",
]

GENERATIONS_SPALTEN = [
    "variante", "wiederholung", "generation",
    "beste_fitness", "mittlere_fitness", "stdabw_fitness",
    "anzahl_spezies", "ziel_erreicht",
]


# ---------------------------------------------------------------------------
# Kennzahlen der Karten
# ---------------------------------------------------------------------------

def wanddichte(karte):
    """Anteil der Felder, die eine Wand sind."""
    felder = [f for zeile in karte for f in zeile]
    return sum(1 for f in felder if f == 1) / len(felder)


def kuerzester_weg(karte):
    """
        Laenge des kuerzesten Weges vom Start zum Ziel (Breitensuche).

        Dient als Schwierigkeitsmass der Karte. Die Begehbarkeit wird ueber
        Agent._is_free() geprueft, damit hier keine zweite Auslegung davon
        entsteht, was ein begehbares Feld ist.
    """
    groesse = agent_neat.MAP_SIZE
    sonde = agent_neat.Agent(net=None)
    sonde.set_map(karte)

    start = (groesse - 1, groesse - 1)
    warteschlange = deque([(start, 0)])
    gesehen = {start}
    while warteschlange:
        (x, y), abstand = warteschlange.popleft()
        if (x, y) == (0, 0):
            return abstand
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (nx, ny) not in gesehen and sonde._is_free(nx, ny):
                gesehen.add((nx, ny))
                warteschlange.append(((nx, ny), abstand + 1))
    return None


def schritte_bis_ziel(net, karte):
    """
        Spielt das Siegernetz auf der Karte nach und zaehlt die Schritte bis
        zum Ziel. Gibt None zurueck, wenn das Ziel nicht erreicht wird.

        Ungueltige Schritte zaehlen mit, genau wie in Agent.run().
    """
    agent = agent_neat.Agent(net)
    agent.set_map(karte)
    agent.set_goal(0, 0)
    agent.set_start(agent_neat.MAP_SIZE - 1, agent_neat.MAP_SIZE - 1)

    for schritt in range(1, agent_neat.MAX_STEPS + 1):
        agent.move(agent.activate_net(agent._get_map_env()))
        if (agent.pos_x, agent.pos_y) == (0, 0):
            return schritt
    return None


# ---------------------------------------------------------------------------
# Datensammler
# ---------------------------------------------------------------------------

class Sammler(neat.reporting.BaseReporter):
    """
        Schreibt pro Generation eine Zeile mit und merkt sich, wann zum ersten
        Mal ein Agent das Ziel erreicht hat.
    """

    def __init__(self, variante, wiederholung):
        self.variante = variante
        self.wiederholung = wiederholung
        self.zeilen = []
        self.generation = 0
        self.ziel_generation = None
        self.schwelle_generation = None
        self.beste_fitness = None

    def start_generation(self, generation):
        self.generation = generation

    def post_evaluate(self, config, population, species, best_genome):
        werte = [g.fitness for g in population.values() if g.fitness is not None]
        erreicht = any(getattr(g, "ziel_erreicht", False)
                       for g in population.values())

        if erreicht and self.ziel_generation is None:
            self.ziel_generation = self.generation

        bestwert = max(werte)
        if self.beste_fitness is None or bestwert > self.beste_fitness:
            self.beste_fitness = bestwert

        self.zeilen.append({
            "variante": self.variante,
            "wiederholung": self.wiederholung,
            "generation": self.generation,
            "beste_fitness": round(bestwert, 5),
            "mittlere_fitness": round(statistics.mean(werte), 5),
            "stdabw_fitness": round(statistics.pstdev(werte), 5),
            "anzahl_spezies": len(species.species),
            "ziel_erreicht": int(erreicht),
        })

    def found_solution(self, config, generation, best):
        # Wird aufgerufen, wenn fitness_threshold ueberschritten wurde.
        self.schwelle_generation = generation


# ---------------------------------------------------------------------------
# Ein einzelner Lauf
# ---------------------------------------------------------------------------

def einzellauf(variante, wiederholung, parameter=None):
    """
        Rechnet eine Wiederholung einer Variante und gibt ihre Kennzahlen
        zurueck.

        `parameter` ueberschreibt einzelne NEAT-Parameter; ohne Angabe gilt
        NEAT_PARAMETER. Der Sweep zu H4 reicht hier seine Werte herein.
    """
    einstellung = VARIANTEN[variante]

    # Stellschrauben der Wahrnehmung setzen. agent_neat liest die Globals bei
    # jedem Aufruf, die Aenderung wirkt also sofort.
    agent_neat.RADIUS = einstellung["radius"]
    agent_neat.USE_GOAL_DIR = einstellung["zielrichtung"]

    karte = agent_neat.make_maze(wiederholung).map
    agent_neat.seed_run(wiederholung)

    config = agent_neat.load_config()
    for name, wert in (NEAT_PARAMETER if parameter is None
                       else parameter).items():
        if name == "pop_size":
            config.pop_size = wert
        elif name == "compatibility_threshold":
            config.species_set_config.compatibility_threshold = wert
        else:
            setattr(config.genome_config, name, wert)
    config.map = karte

    sammler = Sammler(variante, wiederholung)
    p = neat.Population(config)
    p.add_reporter(sammler)

    beginn = time.perf_counter()
    winner = p.run(agent_neat.eval_genomes, GENERATIONEN)
    dauer = time.perf_counter() - beginn

    netz = neat.nn.FeedForwardNetwork.create(winner, config)
    aktive = sum(1 for c in winner.connections.values() if c.enabled)

    zeile = {
        "variante": variante,
        "radius": einstellung["radius"],
        "zielrichtung": int(einstellung["zielrichtung"]),
        "wiederholung": wiederholung,
        "maze_seed": wiederholung,
        "run_seed": wiederholung,
        "wanddichte": round(wanddichte(karte), 4),
        "kuerzester_weg": kuerzester_weg(karte),
        "geloest": int(sammler.ziel_generation is not None),
        "ziel_generation": sammler.ziel_generation,
        "schwelle_generation": sammler.schwelle_generation,
        "generationen": len(sammler.zeilen),
        "beste_fitness": round(sammler.beste_fitness, 5),
        "schritte_bester": schritte_bis_ziel(netz, karte),
        "netz_knoten": len(winner.nodes),
        "netz_verbindungen": aktive,
        "pop_size": config.pop_size,
        "compatibility_threshold": config.species_set_config.compatibility_threshold,
        "conn_add_prob": config.genome_config.conn_add_prob,
        "node_add_prob": config.genome_config.node_add_prob,
        "laufzeit_s": round(dauer, 1),
    }
    return zeile, sammler.zeilen


# ---------------------------------------------------------------------------
# Messreihe
# ---------------------------------------------------------------------------

def _schreiber(pfad, spalten):
    """Oeffnet eine CSV-Datei und schreibt die Kopfzeile."""
    datei = open(pfad, "w", newline="", encoding="utf-8")
    schreiber = csv.DictWriter(datei, fieldnames=spalten)
    schreiber.writeheader()
    return datei, schreiber


def zusammenfassung(zeilen):
    """Druckt die Kennzahlen je Variante als Tabelle."""
    print("\n" + "=" * 78)
    print("Zusammenfassung")
    print("=" * 78)
    print(f"{'Variante':9}{'geloest':>10}{'Gen. bis Ziel':>16}"
          f"{'beste Fitness':>16}{'Schritte':>12}")

    for variante in VARIANTEN:
        eigene = [z for z in zeilen if z["variante"] == variante]
        if not eigene:
            continue

        geloest = [z for z in eigene if z["geloest"]]
        quote = f"{len(geloest)}/{len(eigene)}"

        if geloest:
            gen = [z["ziel_generation"] for z in geloest]
            schritte = [z["schritte_bester"] for z in geloest
                        if z["schritte_bester"] is not None]
            gen_text = f"{statistics.mean(gen):.1f}"
            if len(gen) > 1:
                gen_text += f" +- {statistics.stdev(gen):.1f}"
            schritt_text = (f"{statistics.mean(schritte):.1f}"
                            if schritte else "-")
        else:
            gen_text = schritt_text = "-"

        fitness = [z["beste_fitness"] for z in eigene]
        fit_text = f"{statistics.mean(fitness):.2f}"
        if len(fitness) > 1:
            fit_text += f" +- {statistics.stdev(fitness):.2f}"

        print(f"{variante:9}{quote:>10}{gen_text:>16}{fit_text:>16}"
              f"{schritt_text:>12}")


def main():
    varianten = list(VARIANTEN) if RUN_VARIANTS == "all" else list(RUN_VARIANTS)
    unbekannt = [v for v in varianten if v not in VARIANTEN]
    if unbekannt:
        raise SystemExit(f"Unbekannte Varianten in RUN_VARIANTS: {unbekannt}")

    os.makedirs(ERGEBNIS_DIR, exist_ok=True)
    runs_datei, runs_csv = _schreiber(os.path.join(ERGEBNIS_DIR, "runs.csv"),
                                      RUNS_SPALTEN)
    gen_datei, gen_csv = _schreiber(
        os.path.join(ERGEBNIS_DIR, "generations.csv"), GENERATIONS_SPALTEN)

    gesamt = len(varianten) * REPETITIONS
    alle = []
    beginn = time.perf_counter()

    try:
        for variante in varianten:
            for wiederholung in range(REPETITIONS):
                nummer = len(alle) + 1
                print(f"[{nummer}/{gesamt}] {variante}, "
                      f"Wiederholung {wiederholung} ...", flush=True)

                zeile, generationen = einzellauf(variante, wiederholung)
                alle.append(zeile)

                # Sofort schreiben, damit ein Abbruch nicht alles kostet.
                runs_csv.writerow(zeile)
                runs_datei.flush()
                gen_csv.writerows(generationen)
                gen_datei.flush()

                status = (f"Ziel in Generation {zeile['ziel_generation']}"
                          if zeile["geloest"] else "nicht geloest")
                print(f"    {status}, beste Fitness "
                      f"{zeile['beste_fitness']:.2f}, "
                      f"{zeile['laufzeit_s']:.0f} s", flush=True)
    finally:
        runs_datei.close()
        gen_datei.close()

    print(f"\nGesamtlaufzeit: {(time.perf_counter() - beginn) / 60:.1f} min")
    print(f"Ergebnisse in {ERGEBNIS_DIR}")
    zusammenfassung(alle)


if __name__ == "__main__":
    main()
