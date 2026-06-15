package de.hawhamburg.inf.ea.zug;

import io.jenetics.prog.op.Op;

/**
 *
 * @author chris
 */
public class Zug {

    public static abstract class Operation implements Op<Double> {

        protected Zug zug;

        public void setZug(Zug zug) {
            this.zug = zug;
        }

        @Override
        public int arity() {
            return 1;
        }

        @Override
        public String toString() {
            return name();
        }
    }

    public static class GetSpeed extends Operation {

        @Override
        public String name() {
            return "GET_SPEED";
        }

        @Override
        public int arity() {
            return 0;
        }

        @Override
        public Double apply(Double[] t) {
            return zug.getGeschwindigkeit();
        }

    }

    public static class GetDistance extends Operation {

        @Override
        public String name() {
            return "GET_DIST";
        }

        @Override
        public int arity() {
            return 0;
        }

        @Override
        public Double apply(Double[] t) {
            return zug.getEntfernung();
        }

    }

    public static class GetRemaining extends Operation {

        @Override
        public String name() {
            return "GET_REMAINING";
        }

        @Override
        public int arity() {
            return 0;
        }

        @Override
        public Double apply(Double[] t) {
            // Entfernung bis zum Zielbahnhof -> erlaubt "bremsen, wenn nah".
            return zug.getRestEntfernung();
        }

    }

    public static class IfElse extends Operation {

        @Override
        public String name() {
            return "IF";
        }

        @Override
        public int arity() {
            return 3;
        }

        @Override
        public Double apply(Double[] t) {
            if (t[0] > 0) { // true
                return t[1];
            } else {
                return t[2];
            }
        }

    }

    public static class SetSpeed extends Operation {

        @Override
        public String name() {
            return "SET_SPEED";
        }

        @Override
        public Double apply(Double[] v) {
            // Das GP-Programm gibt eine WUNSCH-Geschwindigkeit vor. Wie schnell
            // der Zug sie tatsaechlich annimmt, regelt tick() ueber die
            // Beschleunigung/Bremsverzoegerung.
            zug.setZielGeschwindigkeit(v[0]);
            return v[0];
        }

    }

    // Plausible (nicht physikalisch exakte) Grenzwerte:
    public  static final double ZIEL      = 1000.0; // Entfernung des Zielbahnhofs
    private static final double MAX_SPEED = 20.0;   // Maximalgeschwindigkeit
    private static final double MAX_ACCEL = 1.0;    // max. Beschleunigung pro Tick
    private static final double MAX_BRAKE = 2.0;    // max. Bremsverzoegerung pro Tick

    private double entfernung;
    private double geschwindigkeit;       // tatsaechliche (Ist-)Geschwindigkeit
    private double zielGeschwindigkeit;   // vom GP-Programm gewuenschte (Soll-)Geschwindigkeit
    private double energie;

    public void setZielGeschwindigkeit(double zielGeschwindigkeit) {
        this.zielGeschwindigkeit = zielGeschwindigkeit;
    }

    public double getEnergie() {
        return this.energie;
    }

    public double getGeschwindigkeit() {
        return geschwindigkeit;
    }

    public double getEntfernung() {
        return entfernung;
    }

    public double getRestEntfernung() {
        return ZIEL - entfernung;
    }

    /**
     * Ein Zeitschritt.
     */
    public void tick() {
        // Physiker*innen bitte wegsehen...

        // Sollgeschwindigkeit auf den erlaubten Bereich [0, MAX_SPEED] begrenzen
        // (kein Rueckwaertsfahren, nicht schneller als Maximalgeschwindigkeit).
        double soll = Math.max(0.0, Math.min(zielGeschwindigkeit, MAX_SPEED));

        // Ist-Geschwindigkeit naehert sich der Soll-Geschwindigkeit an,
        // begrenzt durch maximale Beschleunigung bzw. Bremsverzoegerung.
        double diff = soll - geschwindigkeit;
        if (diff > 0) {
            geschwindigkeit += Math.min(diff, MAX_ACCEL);  // beschleunigen
        } else {
            geschwindigkeit -= Math.min(-diff, MAX_BRAKE); // bremsen
        }

        this.entfernung += geschwindigkeit;
        this.energie += geschwindigkeit * geschwindigkeit;
    }
}
