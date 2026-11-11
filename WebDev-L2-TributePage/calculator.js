const display = document.querySelector('#display');
const errorOutput = document.querySelector('#calc-error');
const keys = document.querySelector('#keys');
let expression = '';
let justEvaluated = false;

function showExpression() {
  display.textContent = expression.replaceAll('*', '×').replaceAll('/', '÷') || '0';
}

function tokenize(source) {
  const tokens = [];
  let index = 0;
  while (index < source.length) {
    if (/\s/.test(source[index])) {
      index += 1;
      continue;
    }
    const start = index;
    if (/[0-9.]/.test(source[index])) {
      let dots = 0;
      while (index < source.length && /[0-9.]/.test(source[index])) {
        if (source[index] === '.') dots += 1;
        if (dots > 1) throw new Error('A number cannot contain more than one decimal point.');
        index += 1;
      }
      const text = source.slice(start, index);
      if (text === '.') throw new Error('Enter a digit with the decimal point.');
      tokens.push({ type: 'number', value: Number(text) });
      continue;
    }
    if ('+-*/()'.includes(source[index])) {
      tokens.push({ type: source[index], value: source[index] });
      index += 1;
      continue;
    }
    throw new Error('Only numbers and +, −, ×, ÷, and parentheses are supported.');
  }
  return tokens;
}

function evaluate(source) {
  const tokens = tokenize(source);
  let cursor = 0;

  function parsePrimary() {
    const token = tokens[cursor];
    if (!token) throw new Error('Complete the expression before calculating.');
    if (token.type === 'number') {
      cursor += 1;
      return token.value;
    }
    if (token.type === '(') {
      cursor += 1;
      const value = parseExpression();
      if (tokens[cursor]?.type !== ')') throw new Error('Add a closing parenthesis.');
      cursor += 1;
      return value;
    }
    throw new Error('Enter a number where expected.');
  }

  function parseUnary() {
    if (tokens[cursor]?.type === '+') {
      cursor += 1;
      return parseUnary();
    }
    if (tokens[cursor]?.type === '-') {
      cursor += 1;
      return -parseUnary();
    }
    return parsePrimary();
  }

  function parseTerm() {
    let value = parseUnary();
    while (tokens[cursor]?.type === '*' || tokens[cursor]?.type === '/') {
      const operator = tokens[cursor++].type;
      const right = parseUnary();
      if (operator === '/' && right === 0) throw new Error('Cannot divide by zero.');
      value = operator === '*' ? value * right : value / right;
    }
    return value;
  }

  function parseExpression() {
    let value = parseTerm();
    while (tokens[cursor]?.type === '+' || tokens[cursor]?.type === '-') {
      const operator = tokens[cursor++].type;
      const right = parseTerm();
      value = operator === '+' ? value + right : value - right;
    }
    return value;
  }

  const result = parseExpression();
  if (cursor !== tokens.length) throw new Error('Check the expression and parentheses.');
  if (!Number.isFinite(result)) throw new Error('The result is outside the supported numeric range.');
  return result;
}

function calculate() {
  if (!expression) return;
  try {
    const result = evaluate(expression);
    expression = String(Number(result.toPrecision(12)));
    justEvaluated = true;
    errorOutput.textContent = '';
    showExpression();
  } catch (error) {
    errorOutput.textContent = error.message;
  }
}

function appendValue(value) {
  errorOutput.textContent = '';
  if (justEvaluated && /[0-9.(]/.test(value)) expression = '';
  justEvaluated = false;
  expression += value;
  showExpression();
}

keys.addEventListener('click', (event) => {
  const button = event.target.closest('button');
  if (!button) return;
  if (button.dataset.action === 'clear') {
    expression = '';
    justEvaluated = false;
    errorOutput.textContent = '';
    showExpression();
  } else if (button.dataset.action === 'backspace') {
    expression = expression.slice(0, -1);
    errorOutput.textContent = '';
    justEvaluated = false;
    showExpression();
  } else if (button.dataset.action === 'equals') {
    calculate();
  } else if (button.dataset.value) {
    appendValue(button.dataset.value);
  }
});

document.addEventListener('keydown', (event) => {
  if (/^[0-9.+\-*/()]$/.test(event.key)) {
    event.preventDefault();
    appendValue(event.key);
  } else if (event.key === 'Enter' || event.key === '=') {
    event.preventDefault();
    calculate();
  } else if (event.key === 'Backspace') {
    expression = expression.slice(0, -1);
    showExpression();
  } else if (event.key === 'Escape') {
    expression = '';
    errorOutput.textContent = '';
    showExpression();
  }
});
