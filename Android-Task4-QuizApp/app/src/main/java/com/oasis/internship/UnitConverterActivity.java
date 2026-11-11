package com.oasis.internship;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.EditText;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import java.util.Locale;

public class UnitConverterActivity extends Activity {
    private static final String[] CATEGORIES = {"Length", "Weight", "Temperature"};
    private static final String[][] UNITS = {
            {"Millimetres (mm)", "Centimetres (cm)", "Metres (m)", "Kilometres (km)", "Inches (in)", "Feet (ft)", "Miles (mi)"},
            {"Milligrams (mg)", "Grams (g)", "Kilograms (kg)", "Ounces (oz)", "Pounds (lb)"},
            {"Celsius (°C)", "Fahrenheit (°F)", "Kelvin (K)"}
    };
    private Spinner category, from, to;
    private EditText value;
    private TextView result;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        setContentView(R.layout.activity_unit_converter);
        category = findViewById(R.id.categorySpinner);
        from = findViewById(R.id.fromSpinner);
        to = findViewById(R.id.toSpinner);
        value = findViewById(R.id.valueInput);
        result = findViewById(R.id.conversionResult);
        category.setAdapter(adapter(CATEGORIES));
        category.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                updateUnits(position);
            }
            @Override public void onNothingSelected(AdapterView<?> parent) { }
        });
        findViewById(R.id.convertButton).setOnClickListener(v -> convert());
    }

    private void updateUnits(int categoryIndex) {
        from.setAdapter(adapter(UNITS[categoryIndex]));
        to.setAdapter(adapter(UNITS[categoryIndex]));
        if (UNITS[categoryIndex].length > 1) to.setSelection(1);
        result.setText("Your result will appear here");
    }

    private ArrayAdapter<String> adapter(String[] items) {
        ArrayAdapter<String> result = new ArrayAdapter<>(this, android.R.layout.simple_spinner_item, items);
        result.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        return result;
    }

    private void convert() {
        String text = value.getText().toString().trim();
        if (text.isEmpty()) {
            Toast.makeText(this, "Enter a number to convert.", Toast.LENGTH_SHORT).show();
            return;
        }
        final double input;
        try {
            input = Double.parseDouble(text);
            if (!Double.isFinite(input)) throw new NumberFormatException();
        } catch (NumberFormatException ex) {
            Toast.makeText(this, "Enter a valid finite number.", Toast.LENGTH_SHORT).show();
            return;
        }
        int categoryIndex = category.getSelectedItemPosition();
        int fromIndex = from.getSelectedItemPosition();
        int toIndex = to.getSelectedItemPosition();
        double converted = categoryIndex == 2
                ? convertTemperature(input, fromIndex, toIndex)
                : convertLinear(input, categoryIndex, fromIndex, toIndex);
        result.setText(String.format(Locale.getDefault(), "%.6g %s = %.6g %s",
                input, shortUnit(categoryIndex, fromIndex), converted, shortUnit(categoryIndex, toIndex)));
    }

    private double convertLinear(double input, int type, int fromIndex, int toIndex) {
        double[] factors = type == 0
                ? new double[]{0.001, 0.01, 1, 1000, 0.0254, 0.3048, 1609.344}
                : new double[]{0.001, 1, 1000, 28.349523125, 453.59237};
        return input * factors[fromIndex] / factors[toIndex];
    }

    private double convertTemperature(double input, int fromIndex, int toIndex) {
        double celsius = fromIndex == 0 ? input : fromIndex == 1 ? (input - 32) * 5 / 9 : input - 273.15;
        return toIndex == 0 ? celsius : toIndex == 1 ? celsius * 9 / 5 + 32 : celsius + 273.15;
    }

    private String shortUnit(int type, int index) {
        String[] labels = type == 0
                ? new String[]{"mm", "cm", "m", "km", "in", "ft", "mi"}
                : type == 1 ? new String[]{"mg", "g", "kg", "oz", "lb"}
                : new String[]{"°C", "°F", "K"};
        return labels[index];
    }
}
