package com.oasis.atm;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public record Transaction(String description, long amountCents, LocalDateTime timestamp) {
    public Transaction(String description, long amountCents) {
        this(description, amountCents, LocalDateTime.now());
    }
    @Override public String toString() {
        return timestamp.format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm"))
                + " | " + description + " | " + (amountCents >= 0 ? "+" : "-")
                + String.format("$%.2f", Math.abs(amountCents) / 100.0);
    }
}
