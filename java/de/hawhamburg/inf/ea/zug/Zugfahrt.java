package de.hawhamburg.inf.ea.zug;

import io.jenetics.Genotype;
import io.jenetics.Mutator;
import io.jenetics.engine.Engine;
import io.jenetics.engine.EvolutionResult;
import io.jenetics.engine.Limits;
import io.jenetics.ext.SingleNodeCrossover;
import io.jenetics.ext.util.TreeNode;
import io.jenetics.prog.ProgramChromosome;
import io.jenetics.prog.ProgramGene;
import io.jenetics.prog.op.Const;
import io.jenetics.prog.op.EphemeralConst;
import io.jenetics.prog.op.MathOp;
import io.jenetics.prog.op.Op;
import io.jenetics.util.ISeq;
import io.jenetics.util.RandomRegistry;

import java.time.Duration;

/**
 *
 * @author chris
 */
public class Zugfahrt {

    private static final double TARGET    = Zug.ZIEL; // Zielentfernung (eine Quelle: Zug.ZIEL)
    private static final int    MAX_STEPS = 100;      // Timeout = max. "Zeit"

    public static double error(Genotype<ProgramGene<Double>> ind) {
        return error(ind, false);
    }

    public static double error(Genotype<ProgramGene<Double>> ind, boolean verbose) {
        Zug zug = new Zug();
        var gene = ind.gene();

        // Setze die Zug instance bei allen Operationen UND Terminalen
        for (var op : gene.operations()) {
            if (op instanceof Zug.Operation operation) {
                operation.setZug(zug);
            }
        }
        for (var op : gene.terminals()) {
            if (op instanceof Zug.Operation operation) {
                operation.setZug(zug);
            }
        }

        int steps = 0;
        while (steps < MAX_STEPS) {
            // Wir rufen das Kontrollprogramm des Zugs auf. Je nach Zustand setzt
            // es die neue Geschwindigkeit. Der Kontroll-Loop wird durch diese
            // Schleife repraesentiert, weil das in GP schwer darstellbar ist.
            gene.eval();
            zug.tick(); // Entfernung + Energie aktualisieren
            steps++;

            if (verbose) {
                System.out.printf(
                    "Tick %3d | Geschwindigkeit %7.2f | Entfernung %8.2f | bis Ziel %8.2f%n",
                    steps, zug.getGeschwindigkeit(), zug.getEntfernung(),
                    TARGET - zug.getEntfernung());
            }

            // Episode endet erst, wenn der Zug zum Stehen kommt (oder Timeout).
            // Dadurch muss der Zug am Bahnhof bremsen statt nur durchzurauschen.
            if (zug.getGeschwindigkeit() <= 0 && steps > 1) break;  // Zug steht
        }

        // --- Gewichtete Kriterien (Gewichte zum Tunen) ---
        double wDist   = 3.0;    // Entfernung dominiert: Ankommen ist Pflicht
        double wEnergy = 0.001;  // Energie ist gross (~1000*v), daher klein gewichtet
        double wTime   = 0.1;    // gegen das "Zuckeln" mit Minimalgeschwindigkeit
        double wStop   = 5.0;    // bestraft Ankunft mit Restgeschwindigkeit -> erzwingt Bremsen

        double distanceError = Math.abs(zug.getEntfernung() - TARGET);
        double fitness = wDist * distanceError
                       + wEnergy * zug.getEnergie()
                       + wTime  * steps
                       + wStop  * zug.getGeschwindigkeit();

        // Schutz gegen NaN/Infinity (z.B. bei DIV oder ueberlaufendem MUL)
        if (!Double.isFinite(fitness)) return Double.MAX_VALUE;
        return fitness;
    }
    
    public static void main(String[] args) {
        final ISeq<Op<Double>> operations = ISeq.of(
                new Zug.SetSpeed(), 
                new Zug.IfElse(),
                MathOp.ADD, MathOp.SUB, MathOp.MUL, MathOp.DIV);
        
        final ISeq<Op<Double>> terminals = ISeq.of(
                new Zug.GetSpeed(),
                new Zug.GetDistance(),
                new Zug.GetRemaining(),   // Entfernung bis zum Ziel -> ermoeglicht "bremsen wenn nah"
                Const.of(0.0), Const.of(1.0), Const.of(2.0), Const.of(3.0),
                Const.of(-1.0), Const.of(-2.0), Const.of(-3.0)
        );
        
        final ProgramChromosome<Double> program
                = ProgramChromosome.of(10, operations, terminals);

        final Engine<ProgramGene<Double>, Double> engine = Engine
                .builder(Zugfahrt::error, program)
                .minimizing()
                .populationSize(200)
                .alterers(
                        new SingleNodeCrossover<>(),
                        new Mutator<>())
                .build();

        final EvolutionResult<ProgramGene<Double>, Double> result = engine
            .stream()
            .limit(Limits.byExecutionTime(Duration.ofSeconds(30))) // harte Obergrenze: stoppt spaetestens nach 30s
            .limit(Limits.byFixedGeneration(250))                  // ... oder nach 250 Generationen
            .collect(EvolutionResult.toBestEvolutionResult());


        final TreeNode<Op<Double>> tree = result.bestPhenotype()
                .genotype().gene().toTreeNode();

        System.out.println("Generations: " + result.totalGenerations());
        System.out.println("Function:    " + tree);

        System.out.println("\n--- Beste Zugfahrt (Tick fuer Tick) ---");
        double bestError = error(result.bestPhenotype().genotype(), true);
        System.out.println("Error:       " + bestError);
    }
}
