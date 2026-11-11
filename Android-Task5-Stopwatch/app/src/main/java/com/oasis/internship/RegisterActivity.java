package com.oasis.internship;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Patterns;
import android.widget.EditText;
import android.widget.Toast;

import java.util.Arrays;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class RegisterActivity extends Activity {
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private AppDatabase database;
    private EditText nameField;
    private EditText emailField;
    private EditText passwordField;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        setContentView(R.layout.activity_register);
        database = new AppDatabase(this);
        nameField = findViewById(R.id.registerName);
        emailField = findViewById(R.id.registerEmail);
        passwordField = findViewById(R.id.registerPassword);
        findViewById(R.id.registerButton).setOnClickListener(v -> register());
        findViewById(R.id.backToLogin).setOnClickListener(v -> finish());
    }

    private void register() {
        String name = nameField.getText().toString().trim();
        String email = emailField.getText().toString().trim().toLowerCase(java.util.Locale.ROOT);
        char[] password = passwordField.getText().toString().toCharArray();
        passwordField.setText("");
        if (name.isEmpty() || !Patterns.EMAIL_ADDRESS.matcher(email).matches() || password.length < 8) {
            Arrays.fill(password, '\0');
            Toast.makeText(this, "Enter your name, a valid email, and a password of at least 8 characters.",
                    Toast.LENGTH_LONG).show();
            return;
        }
        findViewById(R.id.registerButton).setEnabled(false);
        worker.execute(() -> {
            long id = -1;
            boolean failed = false;
            try {
                id = database.register(name, email, password);
            } catch (Exception ex) {
                failed = true;
            } finally {
                Arrays.fill(password, '\0');
            }
            final long userId = id;
            final boolean databaseError = failed;
            mainHandler.post(() -> {
                if (isFinishing() || isDestroyed()) return;
                findViewById(R.id.registerButton).setEnabled(true);
                if (userId > 0) {
                    SessionStore.start(this, userId);
                    startActivity(new Intent(this, ToDoActivity.class));
                    finish();
                } else {
                    Toast.makeText(this, databaseError ? "Unable to create the account right now."
                            : "An account with that email already exists.", Toast.LENGTH_LONG).show();
                }
            });
        });
    }

    @Override protected void onDestroy() {
        worker.shutdownNow();
        if (database != null) database.close();
        super.onDestroy();
    }
}
