const API_BASE = "http://127.0.0.1:8000";

const form = document.querySelector("#task-form");
const titleInput = document.querySelector("#title");
const descriptionInput = document.querySelector("#description");
const taskList = document.querySelector("#task-list");
const message = document.querySelector("#message");
const statusFilter = document.querySelector("#status-filter");
const statsElement = document.querySelector("#stats");

function showMessage(text) {
message.textContent = text;
}

// 统一封装：所有请求都走这里，集中处理错误和 204
async function request(path, options = {}) {
const response = await fetch(`${API_BASE}${path}`, options);

if (!response.ok) {
    let detail = "Request failed";
    try {
    const data = await response.json();
    detail = data.detail ?? detail;
    } catch (_) {
    // 响应不是 JSON 时保留默认错误信息
    }
    throw new Error(detail);
}

if (response.status === 204) {
    return null;            // 204 无响应体，不能解析 JSON
}

return response.json();
}

async function loadStats() {
    try {
        const stats = await request("/stats");
        statsElement.textContent = `总任务：${stats.total} | 已完成：${stats.completed} |
未完成：${stats.pending}`;
    } catch (error) {
        statsElement.textContent = `统计加载失败：${error.message}`;
    }
}

async function loadTasks() {
try {
    showMessage("加载中...");
    const tasks = await request(buildTaskListPath());
    renderTasks(tasks);
    showMessage(`共 ${tasks.length} 个任务`);
} catch (error) {
    showMessage(`加载失败：${error.message}`);
}
await loadStats();
}

function renderTasks(tasks) {
taskList.innerHTML = "";                 // 先清空，再重建

for (const task of tasks) {
    const li = document.createElement("li");
    li.className = `task-item ${task.completed ? "task-done" : ""}`;

    const info = document.createElement("div");

    const title = document.createElement("strong");
    title.className = "task-title";
    title.textContent = task.title;        // 用 textContent，不用 innerHTML

    const desc = document.createElement("div");
    desc.textContent = task.description ?? "";

    info.append(title, desc);

    const actions = document.createElement("div");

    const toggleButton = document.createElement("button");
    toggleButton.textContent = task.completed ? "设为未完成" : "完成";
    toggleButton.addEventListener("click", () => toggleTask(task));

    const deleteButton = document.createElement("button");
    deleteButton.textContent = "删除";
    deleteButton.addEventListener("click", () => removeTask(task.id));

    actions.append(toggleButton, deleteButton);
    li.append(info, actions);
    taskList.appendChild(li);
}
}

async function createTask(event) {
const submitButton = form.querySelector('button[type="submit"]');
submitButton.disabled = true;
try {
event.preventDefault();

const title = titleInput.value.trim();
const description = descriptionInput.value.trim();

if (!title) {
    showMessage("标题不能为空");
    return;
}

try {
    await request("/tasks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, description: description || null }),
    });

    form.reset();
    await loadTasks();
} catch (error) {
    showMessage(`创建失败：${error.message}`);
}
} finally {
    submitButton.disabled = false;
}
}
async function toggleTask(task) {
try {
    await request(`/tasks/${task.id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
        title: task.title,
        description: task.description,
        completed: !task.completed,
    }),
    });

    await loadTasks();
} catch (error) {
    showMessage(`更新失败：${error.message}`);
}
}

async function removeTask(taskId) {
const confirmed = window.confirm("确认删除该任务？");
if (!confirmed) return;
try {
    await request(`/tasks/${taskId}`, { method: "DELETE" });
    await loadTasks();
} catch (error) {
    showMessage(`删除失败：${error.message}`);
}
}

function buildTaskListPath() {
const value = statusFilter.value;

  // TODO: 根据 value 返回不同 URL
switch (value) {
    case "all":
    return "/tasks?limit=100";
    case "pending":
    return "/tasks?limit=100&completed=false";
    case "completed":
    return "/tasks?limit=100&completed=true";
}
}

statusFilter.addEventListener("change", loadTasks);

form.addEventListener("submit", createTask);
loadTasks();