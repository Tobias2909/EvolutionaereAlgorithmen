import io.jenetics.*;
import io.jenetics.engine.Codec;
import io.jenetics.engine.Codecs;
import io.jenetics.engine.Engine;
import io.jenetics.engine.EvolutionResult;
import io.jenetics.util.DoubleRange;

import java.util.function.Function;

public class GeneticAlgorithm implements Optimizer {
    private final int dimensions;
    private final double min;
    private final double max;
    private final int populationSize;
    private final long generations;

    public GeneticAlgorithm(int dimensions, double min, double max, int populationSize, long generations) {
        this.dimensions = dimensions;
        this.min = min;
        this.max = max;
        this.populationSize = populationSize;
        this.generations = generations;
    }

    @Override
    public double[] optimize(Function<double[], Double> f) {
        //Codec maps a Genotype<DoubleGene> to a double[] in [min, max]^dimensions
        Codec<double[], DoubleGene> codec = Codecs.ofVector(new DoubleRange(min, max), dimensions);

        Engine<DoubleGene, Double> engine = Engine
                //Fitness function
                .builder(f, codec)
                //Number of candidates per generation
                .populationSize(populationSize)
                //Search for the minimum
                .optimize(Optimize.MINIMUM)
                //Selector: Select the best 3 candidates for reproduction (tournament selection is default)
                .selector(new TournamentSelector<>(3))
                //Mutator: 10% replace it with random value | MeanAlterer: 60% replace it with the mean of two parents
                .alterers(new Mutator<>(0.1), new MeanAlterer<>(0.6))
                .build();

        //Run the evolution stream for a fixed number of generations and keep the best genotype
        try (CsvWriter csv = new CsvWriter()) {
            return codec.decode(
                    engine.stream()
                            //Stop at n generations
                            .limit(generations)
                            // gather statistics
                            .peek(res -> {
                                double avg = res.population()
                                        .stream()
                                        .mapToDouble(Phenotype::fitness)
                                        .average()
                                        .orElse(0.0);
                                csv.writeLine(res.generation(), res.bestFitness(), res.worstFitness(), avg);
                            })
                            //Remember the best genotype
                            .collect(EvolutionResult.toBestGenotype())
            );
        }
    }
}
