package com.oasis.internship;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteConstraintException;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import android.util.Base64;

import java.security.SecureRandom;
import java.util.ArrayList;
import java.util.List;

import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;

final class AppDatabase extends SQLiteOpenHelper {
    private static final String DB_NAME = "oasis_tasks.db";
    private static final int DB_VERSION = 1;
    private static final int PBKDF2_ITERATIONS = 210_000;
    private static final int SALT_BYTES = 16;
    private static final int HASH_BITS = 256;
    private static final SecureRandom RANDOM = new SecureRandom();

    AppDatabase(Context context) {
        super(context, DB_NAME, null, DB_VERSION);
    }

    @Override public void onConfigure(SQLiteDatabase db) {
        super.onConfigure(db);
        db.setForeignKeyConstraintsEnabled(true);
    }

    @Override public void onCreate(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE users (" +
                "id INTEGER PRIMARY KEY AUTOINCREMENT, " +
                "name TEXT NOT NULL, email TEXT NOT NULL COLLATE NOCASE UNIQUE, " +
                "password_salt TEXT NOT NULL, password_hash TEXT NOT NULL)");
        db.execSQL("CREATE TABLE tasks (" +
                "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, " +
                "title TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '', completed INTEGER NOT NULL DEFAULT 0, " +
                "FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)");
        db.execSQL("CREATE INDEX tasks_user_id_idx ON tasks(user_id)");
    }

    @Override public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
        throw new IllegalStateException("No migration defined for database version " + oldVersion);
    }

    long register(String name, String email, char[] password) throws Exception {
        byte[] salt = new byte[SALT_BYTES];
        RANDOM.nextBytes(salt);
        ContentValues values = new ContentValues();
        values.put("name", name);
        values.put("email", email);
        values.put("password_salt", Base64.encodeToString(salt, Base64.NO_WRAP));
        values.put("password_hash", derive(password, salt));
        try {
            return getWritableDatabase().insertOrThrow("users", null, values);
        } catch (SQLiteConstraintException duplicate) {
            return -1;
        }
    }

    long authenticate(String email, char[] password) throws Exception {
        SQLiteDatabase db = getReadableDatabase();
        try (Cursor cursor = db.query("users", new String[]{"id", "password_salt", "password_hash"},
                "email = ?", new String[]{email}, null, null, null)) {
            if (!cursor.moveToFirst()) return -1;
            byte[] salt = Base64.decode(cursor.getString(1), Base64.NO_WRAP);
            byte[] stored = Base64.decode(cursor.getString(2), Base64.NO_WRAP);
            byte[] candidate = Base64.decode(derive(password, salt), Base64.NO_WRAP);
            return constantTimeEquals(stored, candidate) ? cursor.getLong(0) : -1;
        }
    }

    String userName(long userId) {
        try (Cursor cursor = getReadableDatabase().query("users", new String[]{"name"},
                "id = ?", new String[]{Long.toString(userId)}, null, null, null)) {
            return cursor.moveToFirst() ? cursor.getString(0) : "";
        }
    }

    long addTask(long userId, String title, String notes) {
        ContentValues values = new ContentValues();
        values.put("user_id", userId);
        values.put("title", title);
        values.put("notes", notes);
        return getWritableDatabase().insert("tasks", null, values);
    }

    List<Task> tasksFor(long userId) {
        List<Task> tasks = new ArrayList<>();
        try (Cursor cursor = getReadableDatabase().query("tasks",
                new String[]{"id", "title", "notes", "completed"}, "user_id = ?",
                new String[]{Long.toString(userId)}, null, null, "completed ASC, id DESC")) {
            while (cursor.moveToNext()) {
                tasks.add(new Task(cursor.getLong(0), cursor.getString(1),
                        cursor.getString(2), cursor.getInt(3) != 0));
            }
        }
        return tasks;
    }

    void setCompleted(long userId, long taskId, boolean completed) {
        ContentValues values = new ContentValues();
        values.put("completed", completed ? 1 : 0);
        getWritableDatabase().update("tasks", values, "id = ? AND user_id = ?",
                new String[]{Long.toString(taskId), Long.toString(userId)});
    }

    void deleteTask(long userId, long taskId) {
        getWritableDatabase().delete("tasks", "id = ? AND user_id = ?",
                new String[]{Long.toString(taskId), Long.toString(userId)});
    }

    private static String derive(char[] password, byte[] salt) throws Exception {
        PBEKeySpec spec = new PBEKeySpec(password, salt, PBKDF2_ITERATIONS, HASH_BITS);
        try {
            byte[] hash = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256")
                    .generateSecret(spec).getEncoded();
            return Base64.encodeToString(hash, Base64.NO_WRAP);
        } finally {
            spec.clearPassword();
        }
    }

    private static boolean constantTimeEquals(byte[] left, byte[] right) {
        if (left.length != right.length) return false;
        int difference = 0;
        for (int i = 0; i < left.length; i++) difference |= left[i] ^ right[i];
        return difference == 0;
    }

    static final class Task {
        final long id;
        final String title;
        final String notes;
        final boolean completed;

        Task(long id, String title, String notes, boolean completed) {
            this.id = id;
            this.title = title;
            this.notes = notes;
            this.completed = completed;
        }
    }
}
