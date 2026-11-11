const storageKey = 'oasis-level2-tasks';
const form = document.querySelector('#todo-form');
const input = document.querySelector('#task-input');
const pendingList = document.querySelector('#pending-list');
const completedList = document.querySelector('#completed-list');
const pendingCount = document.querySelector('#pending-count');
const completedCount = document.querySelector('#completed-count');
const storageMessage = document.querySelector('#storage-message');
let tasks = loadTasks();

function loadTasks() {
  try {
    const stored = localStorage.getItem(storageKey);
    if (!stored) return [];
    const parsed = JSON.parse(stored);
    if (!Array.isArray(parsed)) throw new Error('Saved task data has an unexpected format.');
    return parsed.filter((task) =>
      task && typeof task.id === 'string' && typeof task.text === 'string' &&
      typeof task.completed === 'boolean' && typeof task.createdAt === 'string'
    );
  } catch (error) {
    storageMessage.textContent = `Could not read saved tasks: ${error.message}`;
    return [];
  }
}

function persistTasks() {
  try {
    localStorage.setItem(storageKey, JSON.stringify(tasks));
    storageMessage.textContent = '';
  } catch (error) {
    storageMessage.textContent = `Could not save tasks in this browser: ${error.message}`;
  }
}

function formatTime(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Date unavailable' : date.toLocaleString();
}

function buildTask(task) {
  const item = document.createElement('li');
  item.className = `todo-item${task.completed ? ' done' : ''}`;
  item.dataset.id = task.id;

  const text = document.createElement('span');
  text.className = 'todo-text';
  text.textContent = task.text;
  const meta = document.createElement('span');
  meta.className = 'todo-meta';
  meta.textContent = `Added ${formatTime(task.createdAt)}${task.completedAt ? ` · Completed ${formatTime(task.completedAt)}` : ''}`;
  text.append(meta);

  const actions = document.createElement('span');
  actions.className = 'todo-actions';
  const toggle = document.createElement('button');
  toggle.type = 'button';
  toggle.dataset.action = 'toggle';
  toggle.textContent = task.completed ? 'Reopen' : 'Complete';
  toggle.setAttribute('aria-label', `${task.completed ? 'Reopen' : 'Complete'}: ${task.text}`);
  const edit = document.createElement('button');
  edit.type = 'button';
  edit.dataset.action = 'edit';
  edit.textContent = 'Edit';
  edit.setAttribute('aria-label', `Edit: ${task.text}`);
  const remove = document.createElement('button');
  remove.type = 'button';
  remove.dataset.action = 'delete';
  remove.textContent = 'Delete';
  remove.setAttribute('aria-label', `Delete: ${task.text}`);
  actions.append(toggle, edit, remove);
  item.append(text, actions);
  return item;
}

function renderList(list, items, emptyMessage) {
  list.replaceChildren();
  if (!items.length) {
    const empty = document.createElement('li');
    empty.className = 'empty';
    empty.textContent = emptyMessage;
    list.append(empty);
    return;
  }
  items.forEach((task) => list.append(buildTask(task)));
}

function render() {
  const pending = tasks.filter((task) => !task.completed);
  const completed = tasks.filter((task) => task.completed);
  pendingCount.textContent = `${pending.length} pending`;
  completedCount.textContent = `${completed.length} completed`;
  renderList(pendingList, pending, 'All caught up. Add a task to get started.');
  renderList(completedList, completed, 'Completed tasks will appear here.');
}

form.addEventListener('submit', (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) {
    input.focus();
    return;
  }
  tasks.unshift({ id: crypto.randomUUID(), text, completed: false, createdAt: new Date().toISOString() });
  persistTasks();
  render();
  form.reset();
  input.focus();
});

document.querySelector('.todo-columns').addEventListener('click', (event) => {
  const button = event.target.closest('button[data-action]');
  const item = button?.closest('.todo-item');
  if (!button || !item) return;
  const task = tasks.find((entry) => entry.id === item.dataset.id);
  if (!task) return;

  if (button.dataset.action === 'toggle') {
    task.completed = !task.completed;
    task.completedAt = task.completed ? new Date().toISOString() : null;
  } else if (button.dataset.action === 'delete') {
    tasks = tasks.filter((entry) => entry.id !== task.id);
  } else if (button.dataset.action === 'edit') {
    const editor = document.createElement('form');
    editor.className = 'todo-form';
    editor.style.margin = '0';
    const field = document.createElement('input');
    field.className = 'field';
    field.maxLength = 240;
    field.value = task.text;
    field.setAttribute('aria-label', 'Edit task');
    const save = document.createElement('button');
    save.type = 'submit';
    save.className = 'button small';
    save.textContent = 'Save';
    editor.append(field, save);
    item.replaceChildren(editor);
    field.focus();
    field.select();
    editor.addEventListener('submit', (submitEvent) => {
      submitEvent.preventDefault();
      const updatedText = field.value.trim();
      if (!updatedText) {
        field.focus();
        return;
      }
      task.text = updatedText;
      persistTasks();
      render();
    });
    return;
  }
  persistTasks();
  render();
});

window.addEventListener('storage', (event) => {
  if (event.key === storageKey) {
    tasks = loadTasks();
    render();
  }
});

render();
