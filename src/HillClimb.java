import java.util.Random;
import java.util.function.Function;

public class HillClimb implements Optimizer {
    private final double[] start;
    private final double epsilon;
    private final int samplesPerDim;
    private final Random rng = new Random();

    public HillClimb(double[] start, double epsilon, int samplesPerDim) {
        this.start = start;
        this.epsilon = epsilon;
        this.samplesPerDim = samplesPerDim;
    }

    @Override
    public double[] optimize(Function<double[], Double> f) {
        double[] x = start.clone();
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

            //Check fitness find the best of all candidates
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
