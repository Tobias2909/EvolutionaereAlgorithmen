import java.io.IOException;
import java.util.function.Function;

public class Main {
    public static void main(String[] args) throws IOException {
        Function<double[], Double> f = Functions.ACKLEY;

        //Optimizer algorithm = new HillClimb(new double[]{4.5, -4.0}, 1, 20);
        Optimizer algorithm = new GeneticAlgorithm(2, -5.12, 5.12, 50, 100);

        double[] result = algorithm.optimize(f);

        System.out.println("Minimum gefunden bei:");
        for (double v : result) System.out.println("  " + v);
        System.out.println("f(x) = " + f.apply(result));
    }
}
