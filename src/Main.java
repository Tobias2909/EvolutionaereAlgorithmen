import java.util.function.Function;

public class Main {
    public static void main(String[] args) {
        Function<double[], Double> f = Functions.ACKLEY;

        // Shared parameters for both algorithms.
        int dimensions = 2;
        double min = -5.12;
        double max = 5.12;
        int populationSize = 10;
        long generations = 100;

        Optimizer ga = new GeneticAlgorithm(dimensions, min, max, populationSize, generations);
        Optimizer de = new DifferentialEvolution(dimensions, min, max, populationSize, generations);

        System.out.println("=== Genetic Algorithm (Ackley) ===");
        long gaStart = System.nanoTime();
        double[] gaResult = ga.optimize(f);
        long gaTime = System.nanoTime() - gaStart;
        printResult(gaResult, f, gaTime);

        System.out.println();
        System.out.println("=== Differential Evolution (Ackley) ===");
        long deStart = System.nanoTime();
        double[] deResult = de.optimize(f);
        long deTime = System.nanoTime() - deStart;
        printResult(deResult, f, deTime);

        System.out.println();
        System.out.println("=== Comparison ===");
        double gaFitness = f.apply(gaResult);
        double deFitness = f.apply(deResult);
        System.out.println("GA f(x) = " + gaFitness);
        System.out.println("DE f(x) = " + deFitness);
        System.out.println("Winner: " + (gaFitness < deFitness ? "GA" : deFitness < gaFitness ? "DE" : "Tie"));
    }

    private static void printResult(double[] x, Function<double[], Double> f, long nanos) {
        System.out.println("Minimum gefunden bei:");
        for (double v : x) System.out.println("  " + v);
        System.out.println("f(x) = " + f.apply(x));
        System.out.printf("time = %.3f ms%n", nanos / 1_000_000.0);
    }
}