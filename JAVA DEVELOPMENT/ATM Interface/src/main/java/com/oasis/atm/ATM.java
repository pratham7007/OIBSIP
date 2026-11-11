package com.oasis.atm;

import java.util.*;

public final class ATM {
    private final Bank bank;
    private final Scanner input;

    public ATM(Bank bank, Scanner input) {
        this.bank = bank;
        this.input = input;
    }

    public void start() {
        System.out.println("=== Oasis ATM ===");
        Account account = login();
        if (account == null) {
            System.out.println("Access denied after 3 incorrect attempts.");
            return;
        }
        System.out.println("Welcome, " + account.holder() + ".");
        boolean running = true;
        while (running) {
            System.out.println("\n1) Transaction History  2) Withdraw  3) Deposit  4) Transfer  5) Balance  6) Quit");
            System.out.print("Select an option: ");
            String choice = input.nextLine().trim();
            switch (choice) {
                case "1" -> showHistory(account);
                case "2" -> System.out.println(bank.withdraw(account, readCents("Withdrawal amount: ")));
                case "3" -> System.out.println(bank.deposit(account, readCents("Deposit amount: ")));
                case "4" -> {
                    System.out.print("Recipient account ID: ");
                    String recipient = input.nextLine().trim();
                    System.out.println(bank.transfer(account, recipient, readCents("Transfer amount: ")));
                }
                case "5" -> printBalance(account);
                case "6" -> running = false;
                default -> System.out.println("Choose an option from 1 to 6.");
            }
        }
        System.out.println("Goodbye.");
    }

    private Account login() {
        for (int attempt = 1; attempt <= 3; attempt++) {
            System.out.print("User ID: ");
            String id = input.nextLine().trim();
            System.out.print("PIN: ");
            char[] pin = input.nextLine().toCharArray();
            Optional<Account> account = bank.authenticate(id, pin);
            Arrays.fill(pin, '\0');
            if (account.isPresent()) return account.get();
            System.out.printf("Invalid credentials (%d/3).%n", attempt);
        }
        return null;
    }

    private void showHistory(Account account) {
        List<Transaction> history = account.history();
        if (history.isEmpty()) System.out.println("No transactions in this session.");
        else history.forEach(System.out::println);
    }

    private static void printBalance(Account account) {
        System.out.printf("Available balance: $%.2f%n", account.balanceCents() / 100.0);
    }

    private long readCents(String prompt) {
        System.out.print(prompt);
        try {
            long cents = new java.math.BigDecimal(input.nextLine().trim()).movePointRight(2).longValueExact();
            return cents;
        } catch (NumberFormatException | ArithmeticException ex) {
            System.out.println("Enter a valid amount with at most two decimal places.");
            return 0;
        }
    }
}
