package com.oasis.guess;

import java.util.*;

public final class NumberGuessingGame {
    private static final Scanner INPUT = new Scanner(System.in);
    private static final Random RANDOM = new Random(Long.getLong("oasis.game.seed", System.nanoTime()));
    private static final Map<Integer, Integer> SCORES = new LinkedHashMap<>();

    private NumberGuessingGame() {}

    public static void main(String[] args) {
        System.out.println("=== Number Guessing Game ===");
        while (true) {
            Difficulty difficulty = chooseDifficulty();
            if (difficulty == null || !playRound(difficulty)) break;
            if (!INPUT.hasNextLine()) break;
            System.out.print("Play again? (y/n): ");
            if (!INPUT.nextLine().trim().equalsIgnoreCase("y")) break;
        }
        System.out.println("\nRound summary");
        SCORES.forEach((round, attempts) -> System.out.printf("Round %d — guessed in %s%n",
                round, attempts < 0 ? "no attempts" : attempts + (attempts == 1 ? " attempt" : " attempts")));
        System.out.println("Thanks for playing!");
    }

    private static boolean playRound(Difficulty difficulty) {
        int answer = RANDOM.nextInt(difficulty.maximum()) + 1;
        int used = 0;
        boolean won = false;
        System.out.printf("%nI picked a number from 1 to %d. You have %d attempts.%n",
                difficulty.maximum(), difficulty.attempts());
        while (used < difficulty.attempts()) {
            System.out.printf("Attempt %d/%d — your guess: ", used + 1, difficulty.attempts());
            if (!INPUT.hasNextLine()) return false;
            Integer guess = readInteger();
            if (guess == null) {
                System.out.println("Please enter a whole number.");
                continue;
            }
            if (guess < 1 || guess > difficulty.maximum()) {
                System.out.printf("Choose a number between 1 and %d.%n", difficulty.maximum());
                continue;
            }
            used++;
            if (guess == answer) {
                System.out.println("Correct!");
                won = true;
                break;
            }
            System.out.println(guess > answer ? "Too High!" : "Too Low!");
        }
        int round = SCORES.size() + 1;
        SCORES.put(round, won ? used : -1);
        if (!won) System.out.printf("You Lost! The number was %d.%n", answer);
        return true;
    }

    private static Difficulty chooseDifficulty() {
        while (true) {
            System.out.println("Difficulty: 1) Easy (1–50, 10 attempts)  2) Medium (1–100, 7 attempts)  3) Hard (1–200, 5 attempts)");
            System.out.print("Choose 1, 2, or 3: ");
            if (!INPUT.hasNextLine()) return null;
            Integer choice = readInteger();
            if (choice != null && choice >= 1 && choice <= 3) return Difficulty.values()[choice - 1];
            System.out.println("Enter 1, 2, or 3.");
        }
    }

    private static Integer readInteger() {
        if (!INPUT.hasNextLine()) return null;
        try { return Integer.valueOf(INPUT.nextLine().trim()); }
        catch (NumberFormatException ex) { return null; }
    }

    private enum Difficulty {
        EASY(50, 10), MEDIUM(100, 7), HARD(200, 5);
        private final int maximum;
        private final int attempts;
        Difficulty(int maximum, int attempts) { this.maximum = maximum; this.attempts = attempts; }
        int maximum() { return maximum; }
        int attempts() { return attempts; }
    }
}
