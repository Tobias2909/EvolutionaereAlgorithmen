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

/**
 *
 * @author chris
 */
public class Zugfahrt {

    public static double error(Genotype<ProgramGene<Double>> ind) {
        Zug zug = new Zug();
        
        // Setze die Zug instance bei allen Operationen und Terminalen
        for (var op : ind.gene().operations()) {
            if (op instanceof Zug.Operation operation) {
                operation.setZug(zug);
            }
        }
        
        for (var op : ind.gene().terminals()) {
            if (op instanceof Zug.Operation operation) {
                operation.setZug(zug);
            }
        }
        
        var gene = ind.gene();
        for (int i = 0; i < 100; i++) { // Maximal 100 Schritte
            // Wir rufen das Kontrollprogramm des Zugs auf.
            // Je nach Entfernung (und ggfls. aktueller Geschwindigkeit) soll
            // das Programm die neue Geschwindigkeit des Zuges setzen.
            // Der Kontroll-Loop wird durch die For-Schleife hier repräsentiert,
            // weil dies in GP schwierig als Operation darzustellen ist.
            gene.eval();
            
            // Wir lassen Entfernung und Energie aktualisieren
            zug.tick();
            if (zug.getEntfernung() - 1000.0 >= 0) {
                break;
            }
        }
        
        return Math.abs(zug.getEntfernung() - 1000) + zug.getEnergie();
    }
    
    public static void main(String[] args) {
        final ISeq<Op<Double>> operations = ISeq.of(
                new Zug.SetSpeed(), 
                new Zug.IfElse(),
                MathOp.ADD, MathOp.SUB);
        
        final ISeq<Op<Double>> terminals = ISeq.of(
                new Zug.GetSpeed(), 
                new Zug.GetDistance(), 
                Const.of(0.0), Const.of(1.0), Const.of(2.0), Const.of(3.0),
                Const.of(-1.0), Const.of(-2.0), Const.of(-3.0)
        );
        
        final ProgramChromosome<Double> program
                = ProgramChromosome.of(10, operations, terminals);

        final Engine<ProgramGene<Double>, Double> engine = Engine
                .builder(Zugfahrt::error, program)
                .minimizing()
                .alterers(
                        new SingleNodeCrossover<>(),
                        new Mutator<>())
                .build();
        
        final EvolutionResult<ProgramGene<Double>, Double> result = engine
            .stream()
            .limit(Limits.byFixedGeneration(10))
            .collect(EvolutionResult.toBestEvolutionResult());


        final TreeNode<Op<Double>> tree = result.bestPhenotype()
                .genotype().gene().toTreeNode();

        System.out.println("Generations: " + result.totalGenerations());
        System.out.println("Function:    " + tree);
        System.out.println("Error:       " + error(result.bestPhenotype().genotype()));
    }
}
