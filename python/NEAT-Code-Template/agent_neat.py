import random
from tkinter import Tk, Canvas
import neat
import math
import visualize

# Kantenlänge des Labyrinths
MAP_SIZE = 25

# Maximale Schrittzahl pro Agent (Training und Visualisierung nutzen denselben Wert)
MAX_STEPS = MAP_SIZE * MAP_SIZE//4

# Duerfen bereits besuchte Felder erneut betreten werden?
#   False: Der Agent faehrt sich in einer Sackgasse endgueltig fest.
#   True:  Der Agent kann aus Sackgassen zurueck, kann seine Schritte aber auch mit Hin- und herlaufen verschwenden.
ALLOW_BACKTRACK = False

# Sichtradius des Agenten: wie viele Felder er in jede Richtung wahrnimmt.
# Der Eingabevektor enthaelt dadurch (2*RADIUS+1)^2 - 1 Felder, also 8 bei
# Radius 1, 24 bei Radius 2 und 48 bei Radius 3.
# num_inputs in neat-config wird beim Start automatisch angepasst.
RADIUS = 1

# Bekommt das Netz zusaetzlich die Richtung zum Ziel als zwei Eingaben?
# Ohne sie sind zwei Stellen im Labyrinth, deren Umgebung gleich aussieht,
# fuer ein vorwaertsgerichtetes Netz ununterscheidbar - es waehlt dort
# zwangslaeufig dieselbe Richtung, egal wo das Ziel liegt.
USE_GOAL_DIR = False

# Seeds fuer die beiden Zufallsquellen des Versuchs. Wiederholung i der Studie
# benutzt spaeter MAZE_SEED = i und RUN_SEED = i, sodass jede Variante auf
# denselben zehn Labyrinthen mit denselben Startpopulationen geprueft wird.
MAZE_SEED = 0   # bestimmt das Labyrinth
RUN_SEED = 0    # bestimmt Startpopulation, Mutationen und Elternauswahl

class MapGenerator:
    """
        MapGenerator kümmert sich um die Erzeugung und die Anzeige der
        Labyrinth-Karten.
    """

    def __init__(self, size, start, end):
        self.size = size
        self.start = start
        self.end = end
        self.map = [[0 for _ in range(size)] for _ in range(size)]
        self.tilesize = 20
    
    def generate(self, seed=None):
        """
           Erzeugt eine Zufallskarte und gibt sie als 2D-Array zurück.
           Eine 0 im Array steht für ein betretbares Feld, 1 für ein
           Hindernis, S für Start und E für Ende.

           Mit `seed` entsteht reproduzierbar immer dieselbe Karte. Dafuer
           wird ein eigener Zufallsgenerator benutzt und nicht der globale:
           sonst haenge davon, wie viele Karten schon erzeugt wurden, auch
           saemtliche Zufallsentscheidungen von neat-python ab.
        """

        rng = random.Random(seed) if seed is not None else random

        # Sicherstellen, dass es mindestens einen Pfad vom Start bis zum Ende gibt
        while True:
            #self.map = [[random.randint(0, 1) for _ in range(self.size)] for _ in range(self.size)]
            self.map = [[1 if rng.random() < 0.25 else 0 for _ in range(self.size)] for _ in range(self.size)]
            if self._is_valid():
                break

        # Start und Ende Punkte setzen
        self.map[self.start[0]][self.start[1]] = 'S'
        self.map[self.end[0]][self.end[1]] = 'E'

    def _is_valid(self):
        start, end = self.start, self.end
        queue = [start]
        visited = set(queue)
        while queue:
            row, col = queue.pop(0)
            if (row, col) == end:
                return True
            neighbors = self._get_neighbors(row, col)
            for neighbor in neighbors:
                if neighbor not in visited and self.map[neighbor[0]][neighbor[1]] == 0:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return False

    def _get_neighbors(self, row, col):
        neighbors = []
        if row > 0:
            neighbors.append((row-1, col))
        if row < self.size-1:
            neighbors.append((row+1, col))
        if col > 0:
            neighbors.append((row, col-1))
        if col < self.size-1:
            neighbors.append((row, col+1))
        return neighbors

    def draw_map(self, agent):
        """
            Erstellt und zeigt die GUI an.
        """

        ts = self.tilesize
        root = Tk()
        root.title('NEAT Maze')
        canvas = Canvas(root, width=self.size*ts, height=self.size*ts)
        canvas.pack()
        for row in range(self.size):
            for col in range(self.size):
                if self.map[col][row] == 'S':
                    canvas.create_rectangle(col*ts, row*ts, (col+1)*ts, (row+1)*ts, fill='red')
                elif self.map[col][row] == 'E':
                    canvas.create_rectangle(col*ts, row*ts, (col+1)*ts, (row+1)*ts, fill='blue')
                else:
                    color = 'white' if self.map[col][row] == 0 else 'gray'
                    canvas.create_rectangle(col*ts, row*ts, (col+1)*ts, (row+1)*ts, fill=color)
        # draw the agent's path
        canvas.create_oval(
                    agent.pos_x*ts+ts*0.25, 
                    agent.pos_y*ts+ts*0.25, 
                    (agent.pos_x+1)*ts-ts*0.25, 
                    (agent.pos_y+1)*ts-ts*0.25, 
                    fill='orange')

        for i in range(0,MAX_STEPS):
            inputs = agent._get_map_env()
            output = agent.activate_net(inputs)

            if agent.move(output):
                print("this is agent position  ->>>>>", agent.pos_x, agent.pos_y)
                canvas.create_oval(
                    agent.pos_x*ts+ts*0.25, 
                    agent.pos_y*ts+ts*0.25, 
                    (agent.pos_x+1)*ts-ts*0.25, 
                    (agent.pos_y+1)*ts-ts*0.25, 
                    fill='orange')


            if agent.pos_x == 0 and agent.pos_y == 0:
                    break

        root.mainloop()

class Agent:
    """
        Repräsentiert einen Agenten, der sich durch das Labyrinth bewegt.
    """
    
    def __init__(self, net):
        self.net = net
        self.pos_x = None
        self.pos_y = None
        self.goal_x = None
        self.goal_y = None
        self.map = None
        self.visited = set()
        self.fitness = 0.0

    def set_map(self, map):
        self.map = map

    def set_start(self, x, y):
        self.pos_x = x
        self.pos_y = y
        self.visited.add((x, y))

    def set_goal(self, x, y):
        self.goal_x = x
        self.goal_y = y

    def activate_net(self, inputs):
        output = self.net.activate(inputs)
        return output.index(max(output))

    def move(self, direction):
        """
            Bewegt den Agenten auf dem Labyrinth. Es muss sichergestellt werden,
            dass der Agent nur zulässige Bewegungen mehr. Die Methode gibt
            True zurück, wenn die Bewegung erfolgreich war, andernfalls False.
        """
        
        def valid_move(x, y):
            if not self._is_free(x, y):
                return False
            # Steuerung ueber ALLOW_BACKTRACK am Dateikopf.
            return ALLOW_BACKTRACK or (x, y) not in self.visited

        # TODO
        # aktuelle Position
        x = self.pos_x
        y = self.pos_y

        # Richtung bestimmen
        if direction == 0:  # oben
            nx, ny = x, y + 1
        elif direction == 1:  # unten
            nx, ny = x, y - 1
        elif direction == 2:  # links
            nx, ny = x - 1, y
        elif direction == 3:  # rechts
            nx, ny = x + 1, y
        else:
            return False

        # Bewegung prüfen
        if not valid_move(nx, ny):
            return False

        # Position aktualisieren
        self.pos_x = nx
        self.pos_y = ny

        # Feld als besucht markieren
        self.visited.add((nx, ny))


        return True

    def _get_distance(self):
        return math.sqrt((self.goal_x - self.pos_x)**2 + (self.goal_y - self.pos_y)**2)

    def _is_free(self, x, y):
        """
            Einzige Quelle dafuer, ob ein Feld begehbar ist. Wahrnehmung und
            Bewegung muessen dieselbe Antwort bekommen, sonst sieht der Agent
            ein freies Feld, kann es aber nicht betreten.

            Start- und Zielfeld tragen die Marker 'S' und 'E' statt einer 0
            und sind trotzdem begehbar. Felder ausserhalb der Karte gelten
            wie Waende als blockiert.
        """
        if x < 0 or y < 0 or x >= len(self.map) or y >= len(self.map[0]):
            return False
        return self.map[x][y] in (0, 'S', 'E')

    def _get_goal_dir(self):
        """
            Richtung zum Ziel als zwei auf [-1, 1] normierte Eingaben.

            Die Normierung ueber die Kantenlaenge der Karte sorgt dafuer, dass
            diese Werte in derselben Groessenordnung liegen wie die Wandfelder
            (0 oder 1) und sie nicht allein durch ihren Betrag ueberdecken.
        """
        spanne = len(self.map) - 1
        return [(self.goal_x - self.pos_x) / spanne,
                (self.goal_y - self.pos_y) / spanne]

    def _get_map_env(self):
        """
            Liefert den Eingabevektor fuer das neuronale Netz: pro Feld im
            Umkreis von RADIUS eine 0 (begehbar) oder eine 1 (Wand), bei
            USE_GOAL_DIR zusaetzlich zwei Werte fuer die Richtung zum Ziel.

            Reihenfolge der Felder: zeilenweise von oben nach unten, innerhalb
            einer Zeile von links nach rechts, das eigene Feld ausgelassen. Bei
            RADIUS = 1 ergibt das exakt die acht Nachbarfelder in der
            Reihenfolge der urspruenglichen Vorlage (oben links, oben mitte,
            oben rechts, mitte links, mitte rechts, unten links, unten mitte,
            unten rechts). Die Zielrichtung haengt immer hinten an.
        """
        env = []
        # map[x][y]: x = horizontal (links=-1, rechts=+1), y = vertikal (unten=-1, oben=+1)
        for dy in range(RADIUS, -RADIUS - 1, -1):
            for dx in range(-RADIUS, RADIUS + 1):
                if dx == 0 and dy == 0:
                    continue  # das eigene Feld ist keine Eingabe
                free = self._is_free(self.pos_x + dx, self.pos_y + dy)
                env.append(0 if free else 1)
        if USE_GOAL_DIR:
            env.extend(self._get_goal_dir())
        return env


    def run(self):
        """
            Führt eine Maximalanzahl von Schritten für den Agenten aus.
            Die Richtung wird vom "Gehirn", dem neuronalen Netz festgelegt.
        """
        
        # TODO
        steps = MAX_STEPS

        # Startdistanz und kleinste je erreichte Distanz zum Ziel merken
        start_dist = self._get_distance()
        best_dist = start_dist

        for _ in range(steps):

            # get inputs from maze
            inputs = self._get_map_env()

            # neural network decides direction
            direction = self.activate_net(inputs)

            # try to move
            moved = self.move(direction)

            # small penalty to encourage efficiency
            self.fitness -= 0.1

            # reward movement
            if moved:
                self.fitness += 0.1

            # naechste Annaeherung ans Ziel verfolgen
            dist = self._get_distance()
            if dist < best_dist:
                best_dist = dist

            # goal reached
            if (self.pos_x, self.pos_y) == (self.goal_x, self.goal_y):
                self.fitness += 10
                break

        # Belohnung fuers Naeherkommen: je naeher das Ziel kam, desto hoeher
        self.fitness += (start_dist - best_dist)

        return


def input_size():
    """
        Laenge des Eingabevektors, den das neuronale Netz erwartet.

        Der Wert wird bewusst nicht aus RADIUS nachgerechnet, sondern an einem Probe-Agenten gemessen.
        Damit kann die NEAT-Konfiguration nicht von dem abweichen, was _get_map_env() tatsaechlich liefert
        auch dann nicht, wenn die Wahrnehmung spaeter um weitere Eingaben waechst.
    """
    kantenlaenge = 2 * RADIUS + 1
    probe = Agent(net=None)
    probe.set_map([[0] * kantenlaenge for _ in range(kantenlaenge)])
    probe.set_goal(0, 0)
    probe.pos_x = probe.pos_y = RADIUS
    return len(probe._get_map_env())


def make_maze(seed=None):
    """
        Erzeugt reproduzierbar das Labyrinth zu einem Seed und gibt den
        fertigen MapGenerator zurueck.
    """
    generator = MapGenerator(MAP_SIZE, (0, 0), (MAP_SIZE - 1, MAP_SIZE - 1))
    generator.generate(seed)
    return generator


def seed_run(seed):
    """
        Setzt den globalen Zufallsgenerator, aus dem neat-python schoepft.

        Muss vor dem Anlegen der Population passieren, weil dort schon die
        Startgenome gewuerfelt werden. Die Karte ist davon unabhaengig, die
        bringt ihren eigenen Generator mit.
    """
    random.seed(seed)


def apply_input_size(config):
    """
        Traegt die gemessene Vektorlaenge in die NEAT-Konfiguration ein.

        num_inputs allein genuegt nicht: neat-python leitet input_keys einmalig
        im Konstruktor daraus ab, sodass eine nachtraegliche Aenderung sonst wirkungsloss bliebe.
    """
    n = input_size()
    config.genome_config.num_inputs = n
    config.genome_config.input_keys = [-i - 1 for i in range(n)]
    return config


# Creates agents with the given net and tests it on the given map
def eval_genomes(genomes, config):
    """
        Testet jedes Genom mit einem Agenten.
    """
    
    # NEUES Labyrinth pro Generation -> Netz muss generalisieren statt auswendig lernen.
    #generator.generate()
    # FESTES Labyrinth: obere Zeile auskommentieren, dann bleibt das beim Start erzeugte Labyrinth.
    map = generator.map
    config.map = map

    for genome_id, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        agent = Agent(net)
        agent.set_map(map)
        agent.set_start(MAP_SIZE-1, MAP_SIZE-1)
        agent.set_goal(0, 0)
        agent.run()
        genome.fitness = agent.fitness

    return

# Erzeugen der Karte der Größe MAP_SIZE x MAP_SIZE zum eingestellten Seed
generator = make_maze(MAZE_SEED)

# Zufallsgenerator fuer die Evolution setzen, bevor die Population entsteht
seed_run(RUN_SEED)

# Laden einer geeigneten NEAT-Konfiguration aus der Datei 'neat-config'
config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                     neat.DefaultSpeciesSet, neat.DefaultStagnation,
                     'neat-config')

# num_inputs aus der Datei durch die tatsaechliche Vektorlaenge ersetzen,
# damit RADIUS allein genuegt und nichts von Hand nachgezogen werden muss.
apply_input_size(config)

config.map = generator.map

# Erzeugen einer Population
p = neat.Population(config)

# Ein Listener, der den Status auf der Konsole loggt
p.add_reporter(neat.StdOutReporter(False))

# Statistik-Logger für die Visualisierung des Netzes
stats = neat.StatisticsReporter()
p.add_reporter(stats)

# Run until a solution is found.
winner = p.run(eval_genomes, 100) # up to X generations

#visualize.draw_net(config, winner, True)
#visualize.draw_net(config, winner, True, prune_unused=True)
#visualize.plot_stats(stats, ylog=False, view=True)
#visualize.plot_species(stats, view=True)

net = neat.nn.FeedForwardNetwork.create(winner, config)
agent = Agent(net)
agent.set_map(config.map)
agent.set_goal(0,0)
agent.set_start(MAP_SIZE-1, MAP_SIZE-1)
generator.draw_map(agent)