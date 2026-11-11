package com.oasis.internship;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Typeface;
import android.graphics.Paint;
import android.os.Bundle;
import android.text.TextUtils;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.BaseAdapter;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.TextView;
import android.widget.Toast;

import java.util.ArrayList;
import java.util.List;

public class ToDoActivity extends Activity {
    private AppDatabase database;
    private long userId;
    private TaskAdapter adapter;
    private TextView emptyView;
    private ListView listView;
    private boolean redirecting;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        setContentView(R.layout.activity_todo);
        database = new AppDatabase(this);
        emptyView = findViewById(R.id.emptyTasks);
        listView = findViewById(R.id.taskList);
        adapter = new TaskAdapter();
        listView.setAdapter(adapter);
        findViewById(R.id.addTaskButton).setOnClickListener(v -> showAddTask());
        findViewById(R.id.logoutButton).setOnClickListener(v -> logout());
    }

    @Override protected void onResume() {
        super.onResume();
        userId = SessionStore.userId(this);
        if (userId <= 0) {
            if (!redirecting) {
                redirecting = true;
                startActivity(new Intent(this, LoginActivity.class));
                finish();
            }
            return;
        }
        String name = database.userName(userId);
        if (name.isEmpty()) {
            SessionStore.clear(this);
            startActivity(new Intent(this, LoginActivity.class));
            finish();
            return;
        }
        ((TextView) findViewById(R.id.welcomeText)).setText(name + "'s tasks");
        refreshTasks();
    }

    private void refreshTasks() {
        List<AppDatabase.Task> tasks = database.tasksFor(userId);
        adapter.setTasks(tasks);
        emptyView.setVisibility(tasks.isEmpty() ? View.VISIBLE : View.GONE);
        listView.setVisibility(tasks.isEmpty() ? View.GONE : View.VISIBLE);
    }

    private void showAddTask() {
        LinearLayout form = new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);
        int padding = (int) (20 * getResources().getDisplayMetrics().density);
        form.setPadding(padding, 0, padding, 0);
        EditText title = new EditText(this);
        title.setHint("Task name");
        title.setSingleLine(true);
        EditText notes = new EditText(this);
        notes.setHint("Notes (optional)");
        notes.setMinLines(2);
        form.addView(title);
        form.addView(notes);
        new AlertDialog.Builder(this).setTitle("Add a task").setView(form)
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Save", (dialog, which) -> {
                    String taskName = title.getText().toString().trim();
                    if (taskName.isEmpty()) {
                        Toast.makeText(this, "A task name is required.", Toast.LENGTH_SHORT).show();
                        return;
                    }
                    if (database.addTask(userId, taskName, notes.getText().toString().trim()) > 0) {
                        refreshTasks();
                    } else {
                        Toast.makeText(this, "Could not save this task.", Toast.LENGTH_SHORT).show();
                    }
                }).show();
    }

    private void logout() {
        SessionStore.clear(this);
        Intent intent = new Intent(this, LoginActivity.class);
        intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_NEW_TASK);
        startActivity(intent);
        finish();
    }

    @Override protected void onDestroy() {
        if (database != null) database.close();
        super.onDestroy();
    }

    private final class TaskAdapter extends BaseAdapter {
        private final List<AppDatabase.Task> tasks = new ArrayList<>();

        void setTasks(List<AppDatabase.Task> items) {
            tasks.clear();
            tasks.addAll(items);
            notifyDataSetChanged();
        }

        @Override public int getCount() { return tasks.size(); }
        @Override public Object getItem(int position) { return tasks.get(position); }
        @Override public long getItemId(int position) { return tasks.get(position).id; }

        @Override public View getView(int position, View convertView, ViewGroup parent) {
            View row = convertView == null
                    ? LayoutInflater.from(ToDoActivity.this).inflate(R.layout.row_task, parent, false)
                    : convertView;
            AppDatabase.Task task = tasks.get(position);
            CheckBox checkBox = row.findViewById(R.id.taskComplete);
            checkBox.setOnCheckedChangeListener(null);
            String label = TextUtils.isEmpty(task.notes) ? task.title : task.title + "\n" + task.notes;
            checkBox.setText(label);
            checkBox.setTextSize(15);
            checkBox.setTypeface(null, Typeface.NORMAL);
            checkBox.setPaintFlags(task.completed
                    ? checkBox.getPaintFlags() | Paint.STRIKE_THRU_TEXT_FLAG
                    : checkBox.getPaintFlags() & ~Paint.STRIKE_THRU_TEXT_FLAG);
            checkBox.setChecked(task.completed);
            checkBox.setOnCheckedChangeListener((button, checked) -> {
                database.setCompleted(userId, task.id, checked);
                refreshTasks();
            });
            row.findViewById(R.id.deleteTask).setOnClickListener(v -> {
                database.deleteTask(userId, task.id);
                refreshTasks();
            });
            return row;
        }
    }
}
