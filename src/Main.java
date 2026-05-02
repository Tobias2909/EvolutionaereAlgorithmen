import java.util.Random;
import java.util.function.Function;

public class Main {
    public static void main(String[] args) {
        //Sphere function: f(x) = sum(x_i^2), x_i in [-5.12, 5.12]
        Function<double[], Double> sphere = x -> {
            double sum = 0;
            for (double xi : x) sum += xi * xi;
            return sum;
        };

        //Ackley function (formula from slide): f(x) = 20 + e - 20*exp(-0.2 * sum(x_i^2 / n)) - exp(sum(cos(2*pi*x_i) / n))
        Function<double[], Double> ackley = x -> {
            int n = x.length;
            double sumSq = 0;
            double sumCos = 0;
            for (double xi : x) {
                sumSq += (xi * xi) / n;
                sumCos += Math.cos(2 * Math.PI * xi) / n;
            }
            return 20 + Math.E - 20 * Math.exp(-0.2 * sumSq) - Math.exp(sumCos);
        };

        //Pick the function to optimise
        Function<double[], Double> f = sphere;

        //Start positions (within [-5.12, 5.12]), step size, samples per dimension
        double[] start = {4.5, -4.0};
        double epsilon = 0.1;
        int samplesPerDim = 20;

        double[] result = hillClimb(start, epsilon, samplesPerDim, f);

        System.out.println("Minimum gefunden bei:");
        for (double v : result) System.out.println("  " + v);
        System.out.println("f(x) = " + f.apply(result));
    }

    static double[] hillClimb(double[] x, double epsilon, int samplesPerDim, Function<double[], Double> f) {
        Random rng = new Random();
        //Check how many start positions we have
        int n = x.length;
        while (true) {
            //Generate samplesPerDim random neighbors per coordinate
            int total = n * samplesPerDim;
            double[][] neighbors = new double[total][];
            int idx = 0;
            for (int q = 0; q < n; q++) {
                //Do samplePerDim steps per startpositions
                for (int s = 0; s < samplesPerDim; s++) {
                    //rng returns [0,1). With *2-1 we get [-1,1] and epsilon scales it
                    double xi = (rng.nextDouble() * 2 - 1) * epsilon;
                    //copy x so we know later from what start it came
                    neighbors[idx] = x.clone();
                    //Store a coordinate from the step in a random direction
                    neighbors[idx][q] += xi;
                    idx++;
                }
            }

            //Check fitness — find the best of all candidates
            double[] xStar = neighbors[0];
            double xStarVal = f.apply(xStar);
            for (int i = 1; i < total; i++) {
                double v = f.apply(neighbors[i]);
                if (v < xStarVal) {
                    xStar = neighbors[i];
                    xStarVal = v;
                }
            }

            //Check if the best is getting better or worse | better -> keep going | worse -> return
            if (xStarVal < f.apply(x)) {
                x = xStar;
            } else {
                return x;
            }
        }
    }
}
