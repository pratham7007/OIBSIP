package com.oasis.internship;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.view.View;
import android.widget.RadioButton;
import android.widget.RadioGroup;
import android.widget.TextView;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class QuizActivity extends Activity {
    private static final Question[] QUESTIONS = {
            new Question("Which planet is known as the Red Planet?", "Venus", "Mars", "Jupiter", "Mercury", 1),
            new Question("What is the largest ocean on Earth?", "Atlantic", "Indian", "Pacific", "Arctic", 2),
            new Question("How many sides does a hexagon have?", "Five", "Six", "Seven", "Eight", 1),
            new Question("What is the chemical symbol for gold?", "Ag", "Gd", "Go", "Au", 3),
            new Question("Which country is home to the city of Kyoto?", "China", "Japan", "Thailand", "Vietnam", 1),
            new Question("What is the capital of Canada?", "Toronto", "Vancouver", "Ottawa", "Montreal", 2),
            new Question("Which gas do plants absorb from the atmosphere?", "Oxygen", "Nitrogen", "Carbon dioxide", "Helium", 2),
            new Question("Who wrote the play Romeo and Juliet?", "Charles Dickens", "William Shakespeare", "Jane Austen", "Mark Twain", 1),
            new Question("What is the fastest land animal?", "Lion", "Cheetah", "Horse", "Leopard", 1),
            new Question("How many minutes are in two hours?", "100", "110", "120", "140", 2)
    };
    private static final int GREEN = Color.rgb(22, 126, 74);
    private static final int RED = Color.rgb(190, 43, 43);
    private static final int DEFAULT = Color.rgb(30, 41, 59);
    private final int[] order = new int[QUESTIONS.length];
    private int current;
    private int score;
    private boolean answered;
    private int selected = -1;
    private boolean active;
    private RadioGroup options;
    private RadioButton[] answerButtons;
    private TextView feedback;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        if (state != null) {
            int[] restored = state.getIntArray("order");
            if (restored != null && restored.length == order.length) System.arraycopy(restored, 0, order, 0, order.length);
            current = state.getInt("current", 0);
            score = state.getInt("score", 0);
            answered = state.getBoolean("answered", false);
            selected = state.getInt("selected", -1);
            active = state.getBoolean("active", false);
        } else {
            shuffleQuestions();
        }
        if (current >= QUESTIONS.length) showResults();
        else if (!active) showWelcome();
        else showQuestion();
    }

    private void showWelcome() {
        setContentView(R.layout.activity_quiz_welcome);
        findViewById(R.id.startQuiz).setOnClickListener(v -> {
            if (current >= QUESTIONS.length) shuffleQuestions();
            active = true;
            showQuestion();
        });
    }

    private void showQuestion() {
        if (current >= QUESTIONS.length) {
            showResults();
            return;
        }
        setContentView(R.layout.activity_quiz_question);
        Question question = QUESTIONS[order[current]];
        ((TextView) findViewById(R.id.questionCounter)).setText(
                "Question " + (current + 1) + " of " + QUESTIONS.length);
        ((TextView) findViewById(R.id.quizQuestion)).setText(question.text);
        options = findViewById(R.id.quizOptions);
        answerButtons = new RadioButton[]{
                findViewById(R.id.answer0), findViewById(R.id.answer1),
                findViewById(R.id.answer2), findViewById(R.id.answer3)};
        String[] answers = {question.a, question.b, question.c, question.d};
        for (int i = 0; i < answerButtons.length; i++) {
            answerButtons[i].setText(answers[i]);
            answerButtons[i].setTextColor(DEFAULT);
            answerButtons[i].setEnabled(!answered);
        }
        feedback = findViewById(R.id.quizFeedback);
        options.clearCheck();
        if (answered) {
            options.check(answerButtons[selected].getId());
            showFeedback(question, selected);
        }
        options.setOnCheckedChangeListener((group, checkedId) -> {
            if (answered || checkedId == -1) return;
            for (int i = 0; i < answerButtons.length; i++) {
                if (answerButtons[i].getId() == checkedId) {
                    answer(i);
                    break;
                }
            }
        });
        findViewById(R.id.nextQuestion).setEnabled(answered);
        findViewById(R.id.nextQuestion).setOnClickListener(v -> {
            current++;
            answered = false;
            selected = -1;
            showQuestion();
        });
    }

    private void answer(int answerIndex) {
        if (answered) return;
        selected = answerIndex;
        answered = true;
        Question question = QUESTIONS[order[current]];
        if (answerIndex == question.correct) score++;
        showFeedback(question, answerIndex);
        for (RadioButton button : answerButtons) button.setEnabled(false);
        findViewById(R.id.nextQuestion).setEnabled(true);
    }

    private void showFeedback(Question question, int answerIndex) {
        answerButtons[question.correct].setTextColor(GREEN);
        if (answerIndex != question.correct) answerButtons[answerIndex].setTextColor(RED);
        feedback.setText(answerIndex == question.correct ? "Correct!" : "Not quite. The correct answer is highlighted.");
        feedback.setTextColor(answerIndex == question.correct ? GREEN : RED);
    }

    private void showResults() {
        active = false;
        setContentView(R.layout.activity_quiz_results);
        int incorrect = QUESTIONS.length - score;
        ((TextView) findViewById(R.id.finalScore)).setText("Score: " + score + " / " + QUESTIONS.length);
        ((TextView) findViewById(R.id.finalBreakdown)).setText(
                "Correct: " + score + "     Incorrect: " + incorrect);
        findViewById(R.id.restartQuiz).setOnClickListener(v -> {
            shuffleQuestions();
            showWelcome();
        });
    }

    private void shuffleQuestions() {
        List<Integer> indexes = new ArrayList<>();
        for (int i = 0; i < QUESTIONS.length; i++) indexes.add(i);
        Collections.shuffle(indexes);
        for (int i = 0; i < order.length; i++) order[i] = indexes.get(i);
        current = 0;
        score = 0;
        answered = false;
        selected = -1;
        active = false;
    }

    @Override protected void onSaveInstanceState(Bundle outState) {
        outState.putIntArray("order", order);
        outState.putInt("current", current);
        outState.putInt("score", score);
        outState.putBoolean("answered", answered);
        outState.putInt("selected", selected);
        outState.putBoolean("active", active);
        super.onSaveInstanceState(outState);
    }

    private static final class Question {
        final String text, a, b, c, d;
        final int correct;

        Question(String text, String a, String b, String c, String d, int correct) {
            this.text = text;
            this.a = a;
            this.b = b;
            this.c = c;
            this.d = d;
            this.correct = correct;
        }
    }
}
