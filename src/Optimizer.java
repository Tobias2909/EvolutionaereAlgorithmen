import java.util.function.Function;

public interface Optimizer {
    double[] optimize(Function<double[], Double> f);
}
