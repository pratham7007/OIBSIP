package com.oasis.internship;

import android.content.Context;
import android.content.SharedPreferences;

final class SessionStore {
    private static final String FILE = "todo_session";
    private static final String USER_ID = "user_id";

    private SessionStore() { }

    static long userId(Context context) {
        return preferences(context).getLong(USER_ID, -1);
    }

    static void start(Context context, long id) {
        preferences(context).edit().putLong(USER_ID, id).apply();
    }

    static void clear(Context context) {
        preferences(context).edit().remove(USER_ID).apply();
    }

    private static SharedPreferences preferences(Context context) {
        return context.getSharedPreferences(FILE, Context.MODE_PRIVATE);
    }
}
