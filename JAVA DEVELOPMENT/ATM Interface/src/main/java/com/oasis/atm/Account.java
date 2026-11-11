package com.oasis.atm;

import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;
import java.security.GeneralSecurityException;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.*;

public final class Account {
    private final String id;
    private final String holder;
    private long balanceCents;
    private final byte[] pinSalt;
    private final byte[] pinHash;
    private final List<Transaction> history = new ArrayList<>();

    public Account(String id, String holder, long openingBalanceCents, char[] pin) {
        if (openingBalanceCents < 0) throw new IllegalArgumentException("Opening balance cannot be negative.");
        this.id = Objects.requireNonNull(id);
        this.holder = Objects.requireNonNull(holder);
        this.balanceCents = openingBalanceCents;
        this.pinSalt = new byte[16];
        new SecureRandom().nextBytes(pinSalt);
        this.pinHash = derive(pin, pinSalt);
    }

    public String id() { return id; }
    public String holder() { return holder; }
    public long balanceCents() { return balanceCents; }
    public List<Transaction> history() { return List.copyOf(history); }

    boolean verifyPin(char[] pin) {
        return MessageDigest.isEqual(pinHash, derive(pin, pinSalt));
    }

    void credit(long cents, String description) {
        balanceCents = Math.addExact(balanceCents, cents);
        history.add(new Transaction(description, cents));
    }

    void debit(long cents, String description) {
        balanceCents -= cents;
        history.add(new Transaction(description, -cents));
    }

    private static byte[] derive(char[] pin, byte[] salt) {
        PBEKeySpec spec = new PBEKeySpec(pin, salt, 100_000, 256);
        try {
            return SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256").generateSecret(spec).getEncoded();
        } catch (GeneralSecurityException ex) {
            throw new IllegalStateException("PIN hashing is unavailable.", ex);
        } finally {
            spec.clearPassword();
        }
    }
}
