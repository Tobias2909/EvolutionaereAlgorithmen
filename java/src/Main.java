package src;

import java.util.function.Function;

public class Main {
    public static void main(String[] args) {
        Function<double[], Double> f = Functions.ACKLEY;

        //src.Optimizer algorithm = new src.HillClimb(new double[]{4.5, -4.0}, 1, 20);
        //src.Optimizer algorithm = new src.GeneticAlgorithm(2, -5.12, 5.12, 50, 100);
        Optimizer algorithm = new DifferentialEvolution(2, -5.12, 5.12, 50, 100);

        double[] result = algorithm.optimize(f);

        System.out.println("Minimum gefunden bei:");
        for (double v : result) System.out.println("  " + v);
        System.out.println("f(x) = " + f.apply(result));
    }
}
