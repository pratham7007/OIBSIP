const temperatureInput = document.getElementById('temperature');
const fromUnit = document.getElementById('fromUnit');
const toUnit = document.getElementById('toUnit');
const result = document.getElementById('result');
const errorBox = document.getElementById('errorBox');
const convertBtn = document.getElementById('convertBtn');

function toCelsius(value, unit) {
  switch (unit) {
    case 'c': return value;
    case 'f': return (value - 32) * 5 / 9;
    case 'k': return value - 273.15;
    default: return value;
  }
}

function fromCelsius(value, unit) {
  switch (unit) {
    case 'c': return value;
    case 'f': return (value * 9 / 5) + 32;
    case 'k': return value + 273.15;
    default: return value;
  }
}

function renderError(message) {
  errorBox.textContent = message;
  errorBox.classList.add('show');
  result.textContent = 'Result will appear here.';
}

function clearError() {
  errorBox.textContent = '';
  errorBox.classList.remove('show');
}

function convertTemperature() {
  const rawValue = temperatureInput.value.trim();

  if (rawValue === '') {
    renderError('Please enter a temperature value.');
    return;
  }

  const numericValue = Number(rawValue);
  if (Number.isNaN(numericValue)) {
    renderError('Please enter a valid numeric temperature.');
    return;
  }

  const celsius = toCelsius(numericValue, fromUnit.value);
  if (celsius < -273.15) {
    renderError('Absolute zero violation: temperature cannot be below -273.15°C.');
    return;
  }

  const converted = fromCelsius(celsius, toUnit.value);
  const formatted = Number.isInteger(converted) ? converted.toFixed(0) : converted.toFixed(2);
  clearError();
  result.textContent = `${numericValue} ${fromUnit.options[fromUnit.selectedIndex].text} = ${formatted} ${toUnit.options[toUnit.selectedIndex].text}`;
}

convertBtn.addEventListener('click', convertTemperature);
fromUnit.addEventListener('change', convertTemperature);
toUnit.addEventListener('change', convertTemperature);
temperatureInput.addEventListener('input', () => {
  if (temperatureInput.value.trim() !== '') {
    clearError();
  }
});
