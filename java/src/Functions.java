package src;

import java.util.function.Function;

public final class Functions {
    private Functions() {}

    //Sphere function: f(x) = sum(x_i^2), x_i in [-5.12, 5.12]
    public static final Function<double[], Double> SPHERE = x -> {
        double sum = 0;
        for (double xi : x) sum += xi * xi;
        return sum;
    };

    //Ackley function (formula from slide): f(x) = 20 + e - 20*exp(-0.2 * sum(x_i^2 / n)) - exp(sum(cos(2*pi*x_i) / n))
    public static final Function<double[], Double> ACKLEY = x -> {
        int n = x.length;
        double sumSq = 0;
        double sumCos = 0;
        for (double xi : x) {
            sumSq += (xi * xi) / n;
            sumCos += Math.cos(2 * Math.PI * xi) / n;
        }
        return 20 + Math.E - 20 * Math.exp(-0.2 * sumSq) - Math.exp(sumCos);
    };
}
