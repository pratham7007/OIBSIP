package com.oasis.internship;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.widget.Button;
import android.widget.TextView;

import java.util.ArrayList;
import java.util.Locale;

public class StopwatchActivity extends Activity {
    private static final String RUNNING = "running";
    private static final String ELAPSED = "elapsed";
    private static final String STARTED_AT = "started_at";
    private static final String LAPS = "laps";
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final ArrayList<Long> laps = new ArrayList<>();
    private final Runnable ticker = new Runnable() {
        @Override public void run() {
            updateDisplay();
            if (running) handler.postDelayed(this, 40);
        }
    };
    private TextView display;
    private TextView lapList;
    private Button startButton;
    private Button pauseButton;
    private Button lapButton;
    private boolean running;
    private long elapsedBeforeStart;
    private long startedAt;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        setContentView(R.layout.activity_stopwatch);
        display = findViewById(R.id.stopwatchDisplay);
        lapList = findViewById(R.id.lapList);
        startButton = findViewById(R.id.startStopwatch);
        pauseButton = findViewById(R.id.pauseStopwatch);
        lapButton = findViewById(R.id.lapStopwatch);
        if (state != null) {
            running = state.getBoolean(RUNNING);
            elapsedBeforeStart = state.getLong(ELAPSED);
            startedAt = state.getLong(STARTED_AT);
            long[] savedLaps = state.getLongArray(LAPS);
            if (savedLaps != null) for (long lap : savedLaps) laps.add(lap);
        }
        startButton.setOnClickListener(v -> start());
        pauseButton.setOnClickListener(v -> pause());
        findViewById(R.id.resetStopwatch).setOnClickListener(v -> reset());
        lapButton.setOnClickListener(v -> recordLap());
        updateButtons();
        renderLaps();
        updateDisplay();
    }

    private void start() {
        if (running) return;
        startedAt = SystemClock.elapsedRealtime();
        running = true;
        updateButtons();
        updateDisplay();
        handler.removeCallbacks(ticker);
        handler.post(ticker);
    }

    private void pause() {
        if (!running) return;
        elapsedBeforeStart += SystemClock.elapsedRealtime() - startedAt;
        running = false;
        handler.removeCallbacks(ticker);
        updateButtons();
        updateDisplay();
    }

    private void reset() {
        running = false;
        elapsedBeforeStart = 0;
        startedAt = 0;
        laps.clear();
        handler.removeCallbacks(ticker);
        updateDisplay();
        renderLaps();
        updateButtons();
    }

    private long elapsedNow() {
        return elapsedBeforeStart + (running ? SystemClock.elapsedRealtime() - startedAt : 0);
    }

    private void recordLap() {
        if (!running) return;
        laps.add(elapsedNow());
        renderLaps();
    }

    private void updateDisplay() {
        long millis = elapsedNow();
        long hours = millis / 3_600_000;
        long minutes = millis / 60_000 % 60;
        long seconds = millis / 1_000 % 60;
        long fractional = millis % 1_000;
        display.setText(String.format(Locale.getDefault(), "%02d:%02d:%02d.%03d",
                hours, minutes, seconds, fractional));
    }

    private void renderLaps() {
        StringBuilder text = new StringBuilder();
        for (int i = 0; i < laps.size(); i++) {
            long lap = laps.get(i);
            text.append(String.format(Locale.getDefault(), "Lap %d     %02d:%02d:%02d.%03d",
                    i + 1, lap / 3_600_000, lap / 60_000 % 60, lap / 1_000 % 60, lap % 1_000));
            if (i < laps.size() - 1) text.append('\n');
        }
        lapList.setText(text.toString());
    }

    private void updateButtons() {
        startButton.setEnabled(!running);
        pauseButton.setEnabled(running);
        lapButton.setEnabled(running);
    }

    @Override protected void onResume() {
        super.onResume();
        if (running) {
            handler.removeCallbacks(ticker);
            handler.post(ticker);
        }
    }

    @Override protected void onPause() {
        handler.removeCallbacks(ticker);
        super.onPause();
    }

    @Override protected void onSaveInstanceState(Bundle outState) {
        outState.putBoolean(RUNNING, running);
        outState.putLong(ELAPSED, elapsedBeforeStart);
        outState.putLong(STARTED_AT, startedAt);
        long[] savedLaps = new long[laps.size()];
        for (int i = 0; i < laps.size(); i++) savedLaps[i] = laps.get(i);
        outState.putLongArray(LAPS, savedLaps);
        super.onSaveInstanceState(outState);
    }
}
