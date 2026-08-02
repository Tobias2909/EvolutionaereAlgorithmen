import random
from tkinter import Tk, Canvas
import neat
import math
import visualize

# Kantenlänge des Labyrinths
MAP_SIZE = 25

# Maximale Schrittzahl pro Agent (Training und Visualisierung nutzen denselben Wert)
MAX_STEPS = MAP_SIZE * MAP_SIZE//4


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
    
    def generate(self):
        """
           Erzeugt eine Zufallskarte und gibt sie als 2D-Array zurück.
           Eine 0 im Array steht für ein betretbares Feld, 1 für ein
           Hindernis, S für Start und E für Ende.
        """
        
        # Sicherstellen, dass es mindestens einen Pfad vom Start bis zum Ende gibt
        while True:
            #self.map = [[random.randint(0, 1) for _ in range(self.size)] for _ in range(self.size)]
            self.map = [[1 if random.random() < 0.25 else 0 for _ in range(self.size)] for _ in range(self.size)]
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
             # MIT Backtracking: besuchte Felder wieder betretbar -> Agent kann aus Sackgassen zurueck
             #return x >= 0 and x < len(self.map) and y >= 0 and y < len(self.map[0]) and self.map[x][y] != 1 and self.map[x][y] == 0
             # OHNE Backtracking: besuchte Felder gesperrt (obere Zeile auskommentieren, diese aktivieren)
             return x >= 0 and x < len(self.map) and y >= 0 and y < len(self.map[0]) and self.map[x][y] != 1 and (x,y) not in self.visited and self.map[x][y] == 0
        
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

    def _get_map_env(self):
        env = []
        def get_value(x, y):
            if x < 0 or y < 0 or x >= len(self.map) or y >= len(self.map[0]):
                return 1 # value for out-of-bounds indices
            elif self.map[x][y] == 'E' or self.map[x][y] == 'S':
                return 0
            else:
                return self.map[x][y]
        # map[x][y]: x = horizontal (links=-1, rechts=+1), y = vertikal (unten=-1, oben=+1)
        env.append(get_value(self.pos_x - 1, self.pos_y + 1)) # oben links
        env.append(get_value(self.pos_x, self.pos_y + 1)) # oben mitte
        env.append(get_value(self.pos_x + 1, self.pos_y + 1)) # oben rechts
        env.append(get_value(self.pos_x - 1, self.pos_y)) # mitte links
        env.append(get_value(self.pos_x + 1, self.pos_y)) # mitte rechts
        env.append(get_value(self.pos_x - 1, self.pos_y - 1)) # unten links
        env.append(get_value(self.pos_x, self.pos_y - 1)) # unten mitte
        env.append(get_value(self.pos_x + 1, self.pos_y - 1)) # unten rechts
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

# Erzeugen einer Zufallskarte der Größe MAP_SIZE x MAP_SIZE
generator = MapGenerator(MAP_SIZE, (0, 0), (MAP_SIZE-1, MAP_SIZE-1))
generator.generate()

# Laden einer geeigneten NEAT-Konfiguration aus der Datei 'neat-config'
config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                     neat.DefaultSpeciesSet, neat.DefaultStagnation,
                     'neat-config')
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