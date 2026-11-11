package com.oasis.atm;

import java.util.*;

public final class Bank {
    private final Map<String, Account> accounts = new LinkedHashMap<>();

    public void addAccount(Account account) {
        if (accounts.putIfAbsent(account.id(), account) != null)
            throw new IllegalArgumentException("Account ID already exists.");
    }

    public Optional<Account> authenticate(String id, char[] pin) {
        Account account = accounts.get(id);
        return account != null && account.verifyPin(pin) ? Optional.of(account) : Optional.empty();
    }

    public synchronized String deposit(Account account, long cents) {
        if (cents <= 0) return "Amount must be greater than zero.";
        try { account.credit(cents, "Cash deposit"); }
        catch (ArithmeticException ex) { return "The amount exceeds the supported balance."; }
        return "Deposit complete.";
    }

    public synchronized String withdraw(Account account, long cents) {
        if (cents <= 0) return "Amount must be greater than zero.";
        if (account.balanceCents() < cents) return "Insufficient Funds.";
        account.debit(cents, "Cash withdrawal");
        return "Withdrawal complete.";
    }

    public synchronized String transfer(Account sender, String recipientId, long cents) {
        if (cents <= 0) return "Amount must be greater than zero.";
        Account recipient = accounts.get(recipientId);
        if (recipient == null) return "Recipient account not found.";
        if (sender == recipient) return "Choose a different recipient account.";
        if (sender.balanceCents() < cents) return "Insufficient Funds.";
        if (recipient.balanceCents() > Long.MAX_VALUE - cents) return "Recipient balance limit exceeded.";
        sender.debit(cents, "Transfer to account " + recipient.id());
        recipient.credit(cents, "Transfer from account " + sender.id());
        return "Transfer complete.";
    }
}
