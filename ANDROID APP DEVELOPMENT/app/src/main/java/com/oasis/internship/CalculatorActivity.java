package com.oasis.internship;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.GridLayout;
import android.widget.TextView;

import java.math.BigDecimal;

public class CalculatorActivity extends Activity {
    private final StringBuilder expression = new StringBuilder();
    private TextView display;
    private boolean showingError;
    private boolean resultShown;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        setContentView(R.layout.activity_calculator);
        display = findViewById(R.id.calculatorDisplay);
        GridLayout grid = findViewById(R.id.calculatorGrid);
        for (int i = 0; i < grid.getChildCount(); i++) {
            View button = grid.getChildAt(i);
            button.setOnClickListener(v -> press((String) v.getTag()));
        }
    }

    private void press(String key) {
        if ("C".equals(key)) {
            expression.setLength(0);
            showingError = false;
            resultShown = false;
            render();
            return;
        }
        if ("⌫".equals(key)) {
            if (showingError || resultShown) expression.setLength(0);
            else if (expression.length() > 0) expression.deleteCharAt(expression.length() - 1);
            showingError = false;
            resultShown = false;
            render();
            return;
        }
        if ("=".equals(key)) {
            calculate();
            return;
        }
        if (key.length() == 1 && Character.isDigit(key.charAt(0)) || ".".equals(key)) {
            appendDigit(key);
        } else {
            appendOperator(key);
        }
        render();
    }

    private void appendDigit(String key) {
        if (showingError || resultShown) {
            expression.setLength(0);
            showingError = false;
            resultShown = false;
        }
        if (".".equals(key)) {
            int start = expression.length();
            while (start > 0 && (Character.isDigit(expression.charAt(start - 1))
                    || expression.charAt(start - 1) == '.')) start--;
            if (expression.substring(start).contains(".")) return;
            if (start == expression.length()) expression.append('0');
        }
        expression.append(key);
    }

    private void appendOperator(String key) {
        if (showingError) {
            expression.setLength(0);
            showingError = false;
        }
        if (resultShown) resultShown = false;
        char operator = "×".equals(key) ? '*' : "÷".equals(key) ? '/' : key.charAt(0);
        if (expression.length() == 0) {
            if (operator == '-') expression.append(operator);
            return;
        }
        char last = expression.charAt(expression.length() - 1);
        if (isOperator(last)) {
            if (expression.length() == 1 && last == '-') return;
            if (operator == '-' && last != '-') expression.append(operator);
            else expression.setCharAt(expression.length() - 1, operator);
        } else {
            expression.append(operator);
        }
    }

    private void calculate() {
        if (expression.length() == 0) return;
        try {
            double value = new ExpressionParser(expression.toString()).parse();
            if (!Double.isFinite(value)) throw new ArithmeticException();
            expression.setLength(0);
            expression.append(BigDecimal.valueOf(value).stripTrailingZeros().toPlainString());
            showingError = false;
            resultShown = true;
            render();
        } catch (RuntimeException error) {
            display.setText("Error");
            showingError = true;
            resultShown = false;
        }
    }

    private void render() {
        display.setText(expression.length() == 0 ? "0" : expression.toString());
    }

    private static boolean isOperator(char value) {
        return value == '+' || value == '-' || value == '*' || value == '/';
    }

    private static final class ExpressionParser {
        private final String source;
        private int index;

        ExpressionParser(String source) { this.source = source; }

        double parse() {
            double value = expression();
            if (index != source.length()) throw new IllegalArgumentException("Unexpected token");
            return value;
        }

        private double expression() {
            double value = term();
            while (index < source.length()) {
                char op = source.charAt(index);
                if (op != '+' && op != '-') break;
                index++;
                double right = term();
                value = op == '+' ? value + right : value - right;
            }
            return value;
        }

        private double term() {
            double value = number();
            while (index < source.length()) {
                char op = source.charAt(index);
                if (op != '*' && op != '/') break;
                index++;
                double right = number();
                if (op == '/' && right == 0) throw new ArithmeticException("Division by zero");
                value = op == '*' ? value * right : value / right;
            }
            return value;
        }

        private double number() {
            boolean negative = false;
            if (index < source.length() && (source.charAt(index) == '-' || source.charAt(index) == '+')) {
                negative = source.charAt(index++) == '-';
            }
            int start = index;
            boolean decimal = false;
            while (index < source.length()) {
                char c = source.charAt(index);
                if (Character.isDigit(c)) index++;
                else if (c == '.' && !decimal) {
                    decimal = true;
                    index++;
                } else break;
            }
            if (start == index) throw new IllegalArgumentException("Number expected");
            double value = Double.parseDouble(source.substring(start, index));
            return negative ? -value : value;
        }
    }
}
