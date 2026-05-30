package src;

import java.io.FileWriter;
import java.io.IOException;
import java.io.UncheckedIOException;

public class CsvWriter implements AutoCloseable {

    private final FileWriter writer;

    public CsvWriter(String filename) {
        try {
            writer = new FileWriter(filename);
            writer.write("generation,best,worst,average\n");
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    public void writeLine(long generation, double best, double worst, double average) {
        try {
            writer.write(generation + "," + best + "," + worst + "," + average + "\n");
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    @Override
    public void close() {
        try {
            writer.close();
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }
}