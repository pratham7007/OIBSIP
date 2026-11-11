package com.oasis.atm;

import java.security.SecureRandom;
import java.util.*;

public final class Main {
    private Main() {}
    public static void main(String[] args) {
        Bank bank = new Bank();
        SecureRandom random = new SecureRandom();
        String alicePin = pin(random), bobPin = pin(random);
        bank.addAccount(new Account("10001", "Alex Morgan", 85_000, alicePin.toCharArray()));
        bank.addAccount(new Account("10002", "Sam Rivera", 42_500, bobPin.toCharArray()));
        System.out.println("Demo accounts (PINs are generated for this run):");
        System.out.println("User ID 10001, PIN " + alicePin + " | User ID 10002, PIN " + bobPin);
        new ATM(bank, new Scanner(System.in)).start();
    }

    private static String pin(SecureRandom random) {
        return "%04d".formatted(random.nextInt(10_000));
    }
}
