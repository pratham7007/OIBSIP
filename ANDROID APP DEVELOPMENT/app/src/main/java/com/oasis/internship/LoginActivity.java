package com.oasis.internship;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.widget.EditText;
import android.widget.Toast;

import java.util.Arrays;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class LoginActivity extends Activity {
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private AppDatabase database;
    private EditText emailField;
    private EditText passwordField;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        if (SessionStore.userId(this) > 0) {
            showTasks();
            return;
        }
        setContentView(R.layout.activity_login);
        database = new AppDatabase(this);
        emailField = findViewById(R.id.loginEmail);
        passwordField = findViewById(R.id.loginPassword);
        findViewById(R.id.loginButton).setOnClickListener(v -> login());
        findViewById(R.id.registerLink).setOnClickListener(v ->
                startActivity(new Intent(this, RegisterActivity.class)));
    }

    private void login() {
        String email = emailField.getText().toString().trim();
        char[] password = passwordField.getText().toString().toCharArray();
        passwordField.setText("");
        if (email.isEmpty() || password.length == 0) {
            Arrays.fill(password, '\0');
            Toast.makeText(this, "Enter your email and password.", Toast.LENGTH_SHORT).show();
            return;
        }
        findViewById(R.id.loginButton).setEnabled(false);
        worker.execute(() -> {
            long id = -1;
            boolean failed = false;
            try {
                id = database.authenticate(email, password);
            } catch (Exception ex) {
                failed = true;
            } finally {
                Arrays.fill(password, '\0');
            }
            final long userId = id;
            final boolean databaseError = failed;
            mainHandler.post(() -> {
                if (isFinishing() || isDestroyed()) return;
                findViewById(R.id.loginButton).setEnabled(true);
                if (userId > 0) {
                    SessionStore.start(this, userId);
                    showTasks();
                } else {
                    Toast.makeText(this, databaseError ? "Unable to sign in right now." : "Incorrect email or password.",
                            Toast.LENGTH_SHORT).show();
                }
            });
        });
    }

    private void showTasks() {
        startActivity(new Intent(this, ToDoActivity.class));
        finish();
    }

    @Override protected void onDestroy() {
        worker.shutdownNow();
        if (database != null) database.close();
        super.onDestroy();
    }
}
