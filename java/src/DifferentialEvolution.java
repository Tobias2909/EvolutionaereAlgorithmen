package src;

import io.jenetics.Alterer;
import io.jenetics.AltererResult;
import io.jenetics.DoubleChromosome;
import io.jenetics.DoubleGene;
import io.jenetics.Genotype;
import io.jenetics.Optimize;
import io.jenetics.Phenotype;
import io.jenetics.Selector;
import io.jenetics.engine.Codec;
import io.jenetics.engine.Codecs;
import io.jenetics.engine.Engine;
import io.jenetics.engine.EvolutionResult;
import io.jenetics.util.DoubleRange;
import io.jenetics.util.ISeq;
import io.jenetics.util.MSeq;
import io.jenetics.util.Seq;
import src.Optimizer;

import java.util.Random;
import java.util.function.Function;

/**
 * Differential Evolution (DE/rand/1/bin) on top of Jenetics.
 *
 * Jenetics has no built-in DE. The trick: an Alterer receives the population
 * already evaluated (fitness values present on each Phenotype), so a custom
 * Alterer can do the full DE step — mutation, crossover, AND the per-individual
 * greedy replacement — inside one call. The Engine is reduced to a thin shell:
 *   - selector: identity (returns the population unchanged)
 *   - offspringFraction: 1.0 (whole population becomes "offspring", no survivors)
 *   - alterer: DEAlterer (does everything)
 *
 * Classic DE algorithm (per generation, for every target index i):
 *   1) Pick three other distinct individuals a, b, c.
 *   2) Mutate:   v = x_a + F * (x_b - x_c)            (vector arithmetic)
 *   3) Crossover (binomial): for each dim j, take v[j] with prob CR, else x_i[j].
 *                            One forced index j_rand guarantees ≥1 changed gene.
 *   4) Select:   if f(trial) < f(x_i) replace x_i with trial, else keep x_i.
 */
public class DifferentialEvolution implements Optimizer {
    private final int dimensions;
    private final double min;
    private final double max;
    private final int populationSize;
    private final long generations;
    // F = scaling factor for the difference vector (typical 0.4 .. 1.0)
    private final double F;
    // CR = crossover probability per gene (typical 0.1 .. 1.0)
    private final double CR;

    public DifferentialEvolution(int dimensions, double min, double max,
                                 int populationSize, long generations,
                                 double F, double CR) {
        this.dimensions = dimensions;
        this.min = min;
        this.max = max;
        this.populationSize = populationSize;
        this.generations = generations;
        this.F = F;
        this.CR = CR;
    }

    // Convenience ctor: default F=0.8, CR=0.9 — robust defaults from the DE literature.
    public DifferentialEvolution(int dimensions, double min, double max,
                                 int populationSize, long generations) {
        this(dimensions, min, max, populationSize, generations, 0.8, 0.9);
    }

    @Override
    public double[] optimize(Function<double[], Double> f) {
        // DE/rand/1 needs 3 distinct "donors" different from the target, so N >= 4.
        if (populationSize < 4) {
            throw new IllegalArgumentException("DE needs populationSize >= 4");
        }

        // Same representation as GeneticAlgorithm: one DoubleChromosome of length `dimensions`,
        // each gene bounded to [min, max]. The codec decodes a Genotype back to double[].
        Codec<double[], DoubleGene> codec = Codecs.ofVector(new DoubleRange(min, max), dimensions);

        // Identity selector: hand the population back as-is, trimmed to the count Engine asks for.
        // We don't want Jenetics to do tournament/roulette selection — DE handles selection itself
        // (inside the alterer, after evaluating each trial).
        Selector<DoubleGene, Double> identity = (pop, count, opt) -> {
            MSeq<Phenotype<DoubleGene, Double>> out = MSeq.ofLength(count);
            for (int i = 0; i < count; i++) out.set(i, pop.get(i));
            return out.toISeq();
        };

        // The actual DE step. All evolution logic lives in here.
        DEAlterer alterer = new DEAlterer(f, F, CR, min, max);

        // Wire up the Engine. With offspringFraction=1.0 the survivor stream is empty,
        // so each generation = (identity-selected population) -> DEAlterer -> next population.
        Engine<DoubleGene, Double> engine = Engine
                .builder(f, codec)
                .populationSize(populationSize)
                .optimize(Optimize.MINIMUM)
                .selector(identity)
                .offspringFraction(1.0)
                .alterers(alterer)
                .build();

        // Run for `generations` ticks, logging best/worst/average to CSV each generation
        // (same format as GeneticAlgorithm so plots stay comparable), then return the best.
        try (CsvWriter csv = new CsvWriter("output_de.csv")) {
            return codec.decode(
                    engine.stream()
                            .limit(generations)
                            .peek(res -> {
                                double avg = res.population()
                                        .stream()
                                        .mapToDouble(Phenotype::fitness)
                                        .average()
                                        .orElse(0.0);
                                csv.writeLine(res.generation(), res.bestFitness(), res.worstFitness(), avg);
                            })
                            .collect(EvolutionResult.toBestGenotype())
            );
        }
    }

    /**
     * Performs one DE/rand/1/bin generation on the entire population.
     *
     * The Alterer contract: take the current population (fitness-evaluated), return
     * the next population wrapped in AltererResult. Because every returned Phenotype
     * already carries a fitness value, Jenetics skips re-evaluation — we only call
     * the fitness function once per trial, which is exactly the DE budget.
     */
    private static final class DEAlterer implements Alterer<DoubleGene, Double> {
        private final Function<double[], Double> fitness;
        private final double F;
        private final double CR;
        private final double min;
        private final double max;
        private final Random rng = new Random();

        DEAlterer(Function<double[], Double> fitness, double F, double CR, double min, double max) {
            this.fitness = fitness;
            this.F = F;
            this.CR = CR;
            this.min = min;
            this.max = max;
        }

        @Override
        public AltererResult<DoubleGene, Double> alter(Seq<Phenotype<DoubleGene, Double>> population, long generation) {
            final int N = population.size();
            // Safety net: if Engine ever passes <4 individuals, fall back to no-op.
            if (N < 4) {
                return new AltererResult<>(toISeq(population), 0);
            }
            // Number of dimensions = length of the (single) chromosome in any individual.
            final int D = population.get(0).genotype().chromosome().length();

            // Buffer for next generation. We fill slot `i` either with a successful trial
            // or with the unchanged parent x_i.
            MSeq<Phenotype<DoubleGene, Double>> next = MSeq.ofLength(N);
            int alterations = 0;

            // -------- Iterate over every target individual x_i --------
            for (int i = 0; i < N; i++) {
                // STEP 1: pick three random indices a, b, c, all distinct from each other and from i.
                // The do/while loops just keep redrawing until uniqueness holds.
                int a, b, c;
                do { a = rng.nextInt(N); } while (a == i);
                do { b = rng.nextInt(N); } while (b == i || b == a);
                do { c = rng.nextInt(N); } while (c == i || c == a || c == b);

                // Unpack the four involved individuals into plain double[] for arithmetic.
                double[] xi = toArray(population.get(i));
                double[] xa = toArray(population.get(a));
                double[] xb = toArray(population.get(b));
                double[] xc = toArray(population.get(c));

                // STEP 2 + 3: build the trial vector by combining mutation and binomial crossover.
                // j_rand is the dimension that is FORCED to come from the mutant, guaranteeing
                // the trial differs from x_i in at least one gene (otherwise CR=0 would do nothing).
                int jrand = rng.nextInt(D);
                double[] trial = new double[D];
                for (int j = 0; j < D; j++) {
                    if (j == jrand || rng.nextDouble() < CR) {
                        // Mutation formula: v_j = x_a,j + F * (x_b,j - x_c,j)
                        double v = xa[j] + F * (xb[j] - xc[j]);
                        // Bound handling: clip to [min, max]. Simple and good enough for now;
                        // alternatives are "reflect" or "reinit" if clipping turns out to bias edges.
                        if (v < min) v = min;
                        if (v > max) v = max;
                        trial[j] = v;
                    } else {
                        // Crossover: keep gene from target x_i.
                        trial[j] = xi[j];
                    }
                }

                // STEP 4: greedy selection. Evaluate trial, replace parent iff strictly better.
                // Using `<` (not `<=`) is the standard DE choice — keeps the population from
                // drifting on equal-fitness plateaus.
                double trialFit = fitness.apply(trial);
                if (trialFit < population.get(i).fitness()) {
                    // Wrap the trial back into a Jenetics Phenotype, fitness pre-filled so the
                    // Engine doesn't re-call f on it. `generation` is the current gen counter.
                    next.set(i, Phenotype.of(toGenotype(trial), generation, trialFit));
                    alterations++;
                } else {
                    // Trial lost — carry parent unchanged into next generation.
                    next.set(i, population.get(i));
                }
            }

            // `alterations` is informational only (Jenetics statistics); the meaningful payload
            // is the new population sequence.
            return new AltererResult<>(next.toISeq(), alterations);
        }

        // ---- Conversion helpers between Jenetics' Phenotype/Genotype and raw double[] ----

        // Phenotype -> double[]: read each gene out of the single DoubleChromosome.
        private double[] toArray(Phenotype<DoubleGene, Double> p) {
            DoubleChromosome chr = (DoubleChromosome) p.genotype().chromosome();
            double[] a = new double[chr.length()];
            for (int i = 0; i < a.length; i++) a[i] = chr.get(i).doubleValue();
            return a;
        }

        // double[] -> Genotype: wrap each value in a bounded DoubleGene so the chromosome
        // remembers its [min, max] range (Jenetics needs this for any later in-engine ops).
        private Genotype<DoubleGene> toGenotype(double[] v) {
            DoubleGene[] genes = new DoubleGene[v.length];
            for (int i = 0; i < v.length; i++) genes[i] = DoubleGene.of(v[i], min, max);
            return Genotype.of(DoubleChromosome.of(genes));
        }

        // Defensive copy: turn the incoming Seq into an immutable ISeq for the no-op path.
        private static ISeq<Phenotype<DoubleGene, Double>> toISeq(Seq<Phenotype<DoubleGene, Double>> pop) {
            MSeq<Phenotype<DoubleGene, Double>> m = MSeq.ofLength(pop.size());
            for (int i = 0; i < pop.size(); i++) m.set(i, pop.get(i));
            return m.toISeq();
        }
    }
}
