import java.io.FileWriter;
import java.io.IOException;

public class CsvWriter {

    private FileWriter writer;

    public CsvWriter() throws IOException {
        writer = new FileWriter("output.csv");

        // write header
        writer.write("generation,best,worst,average\n");
    }

    // write one row per generation
    public void writeLine(long generation, double best, double worst, double average) throws IOException {
        writer.write(generation + "," + best + "," + worst + "," + average + "\n");
    }

    // close file (IMPORTANT)
    public void close() throws IOException {
        writer.close();
    }
}
