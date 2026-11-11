package com.oasis.internship;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        setContentView(R.layout.activity_main);
        findViewById(R.id.openConverter).setOnClickListener(v -> open(UnitConverterActivity.class));
        findViewById(R.id.openTodo).setOnClickListener(v -> {
            if (SessionStore.userId(this) > 0) open(ToDoActivity.class);
            else open(LoginActivity.class);
        });
        findViewById(R.id.openCalculator).setOnClickListener(v -> open(CalculatorActivity.class));
        findViewById(R.id.openQuiz).setOnClickListener(v -> open(QuizActivity.class));
        findViewById(R.id.openStopwatch).setOnClickListener(v -> open(StopwatchActivity.class));
    }

    private void open(Class<?> screen) {
        startActivity(new Intent(this, screen));
    }
}
