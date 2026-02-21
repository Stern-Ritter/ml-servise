/* global window, document */

const STORAGE = {
  userId: "ml_service_user_id",
  apiPrefix: "ml_service_api_prefix",
  token: "ml_service_access_token",
};

function cfg() {
  const base = (window.APP_CONFIG && typeof window.APP_CONFIG === "object") ? window.APP_CONFIG : {};
  const apiPrefixOverride = localStorage.getItem(STORAGE.apiPrefix);
  return {
    API_PREFIX: apiPrefixOverride || base.API_PREFIX || "/api/1.0",
    PREDICT_COST: Number(base.PREDICT_COST ?? 100),
    POLL_INTERVAL_MS: Number(base.POLL_INTERVAL_MS ?? 1200),
    POLL_TIMEOUT_MS: Number(base.POLL_TIMEOUT_MS ?? 60000),
  };
}

function el(id) {
  const node = document.getElementById(id);
  if (!node) throw new Error(`Missing element: ${id}`);
  return node;
}

function q(sel, root = document) {
  return root.querySelector(sel);
}

function qa(sel, root = document) {
  return Array.from(root.querySelectorAll(sel));
}

function setHidden(node, hidden) {
  node.classList.toggle("hidden", Boolean(hidden));
}

function fmtDateTime(v) {
  if (!v) return "—";
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return String(v);
  return d.toLocaleString();
}

function badge(text, kind) {
  const span = document.createElement("span");
  span.className = `badge${kind ? ` badge--${kind}` : ""}`;
  span.textContent = text;
  return span;
}

function getUserId() {
  const raw = localStorage.getItem(STORAGE.userId);
  if (!raw) return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

function setUserId(userId) {
  if (userId == null) {
    localStorage.removeItem(STORAGE.userId);
    return;
  }
  localStorage.setItem(STORAGE.userId, String(userId));
}

function getToken() {
  return localStorage.getItem(STORAGE.token) || null;
}

function setToken(token) {
  if (!token) {
    localStorage.removeItem(STORAGE.token);
    return;
  }
  localStorage.setItem(STORAGE.token, token);
}

function showGlobal(type, message) {
  const box = el("globalAlert");
  box.className = `alert${type ? ` alert--${type}` : ""}`;
  box.textContent = message;
  setHidden(box, false);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function clearGlobal() {
  const box = el("globalAlert");
  box.textContent = "";
  setHidden(box, true);
  box.className = "alert hidden";
}

async function apiFetch(path, init = {}) {
  const url = `${cfg().API_PREFIX}${path}`;
  const headers = { ...(init.headers || {}) };
  if (init.json !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  const token = getToken();
  if (token && !headers.Authorization) {
    headers.Authorization = `Bearer ${token}`;
  }
  const res = await fetch(url, {
    ...init,
    headers,
    body: init.json !== undefined ? JSON.stringify(init.json) : init.body,
  });

  const contentType = res.headers.get("content-type") || "";
  let data = null;
  if (contentType.includes("application/json")) {
    try { data = await res.json(); } catch { data = null; }
  } else {
    try { data = await res.text(); } catch { data = null; }
  }

  if (!res.ok) {
    const detail = (data && typeof data === "object" && "detail" in data) ? data.detail : data;
    const msg = typeof detail === "string" ? detail : JSON.stringify(detail);
    const err = new Error(msg || `HTTP ${res.status}`);
    err.status = res.status;
    err.data = data;
    if (res.status === 401 || res.status === 403) {
      setToken(null);
      setUserId(null);
    }
    throw err;
  }
  return data;
}

async function fetchUserAndBalance(userId) {
  const [user, balance] = await Promise.all([
    apiFetch(`/users/${userId}`),
    apiFetch(`/balance/${userId}`),
  ]);
  return { user, balance };
}

async function requireCurrentUserId() {
  const token = getToken();
  if (!token) return null;
  const existing = getUserId();
  if (existing) return existing;
  try {
    const me = await apiFetch("/auth/me");
    if (!me || me.id == null) throw new Error("No id");
    setUserId(me.id);
    return me.id;
  } catch {
    setToken(null);
    setUserId(null);
    return null;
  }
}

function updateAuthUI() {
  const authed = Boolean(getToken());
  qa(".auth-only").forEach((n) => setHidden(n, !authed));
  qa(".guest-only").forEach((n) => setHidden(n, authed));
  setHidden(el("btnLogout"), !authed);
  el("apiPrefixLabel").textContent = cfg().API_PREFIX;
}

function route() {
  clearGlobal();
  updateAuthUI();

  const hash = window.location.hash || "#/home";
  const page = hash.replace(/^#\//, "");
  const pages = ["home", "login", "signup", "dashboard", "predict", "history", "settings"];

  pages.forEach((p) => setHidden(el(`page-${p}`), p !== page));

  const needsAuth = ["dashboard", "predict", "history"].includes(page);
  const authed = Boolean(getToken());
  if (needsAuth && !authed) {
    window.location.hash = "#/login";
    showGlobal("danger", "Нужно войти, чтобы открыть личный кабинет.");
    return;
  }

  if (page === "dashboard") void loadDashboard();
  if (page === "predict") void loadPredictPage();
  if (page === "history") void loadHistory();
  if (page === "settings") loadSettings();
}

function formToObject(form) {
  const fd = new FormData(form);
  const obj = {};
  for (const [k, v] of fd.entries()) {
    obj[k] = v;
  }
  return obj;
}

function parseBool(v) {
  if (typeof v === "boolean") return v;
  const s = String(v ?? "").trim().toLowerCase();
  if (["1", "true", "yes", "y", "да"].includes(s)) return true;
  if (["0", "false", "no", "n", "нет", ""].includes(s)) return false;
  return null;
}

function parseNumber(v) {
  const n = Number(String(v ?? "").trim().replace(",", "."));
  return Number.isFinite(n) ? n : null;
}

function parseIntStrict(v) {
  const n = Number(String(v ?? "").trim());
  if (!Number.isFinite(n)) return null;
  if (!Number.isInteger(n)) return null;
  return n;
}

function validatePatientRow(row) {
  const errors = [];
  const out = {};

  const intFields = ["age", "physical_activity_days_per_week", "stress_level"];
  const numFields = [
    "bmi",
    "exercise_hours_per_week",
    "sedentary_hours_per_day",
    "sleep_hours_per_day",
    "heart_rate",
    "cholesterol",
    "blood_sugar",
    "triglycerides",
  ];
  const boolFields = ["smoking", "alcohol_consumption", "diabetes", "obesity", "family_history"];

  for (const f of intFields) {
    const n = parseIntStrict(row[f]);
    if (n == null) errors.push(`${f}: ожидалось целое число`);
    else out[f] = n;
  }

  for (const f of numFields) {
    const n = parseNumber(row[f]);
    if (n == null) errors.push(`${f}: ожидалось число`);
    else out[f] = n;
  }

  const gender = String(row.gender ?? "").trim().toLowerCase();
  if (!["male", "female", "other"].includes(gender)) errors.push("gender: допустимо male/female/other");
  else out.gender = gender;

  for (const f of boolFields) {
    const b = parseBool(row[f]);
    if (b == null) errors.push(`${f}: ожидалось true/false`);
    else out[f] = b;
  }

  // Simple logical constraints
  if (out.stress_level != null && (out.stress_level < 1 || out.stress_level > 10)) {
    errors.push("stress_level: диапазон 1–10");
  }

  return { ok: errors.length === 0, patient: out, errors };
}

async function ensureSufficientFunds(userId) {
  const bal = await apiFetch(`/balance/${userId}`);
  const cost = cfg().PREDICT_COST;
  if (!Number.isFinite(Number(bal.value))) return { ok: true, balance: bal };
  if (bal.value <= 0) return { ok: false, balance: bal, message: "Баланс должен быть положительным для ML‑запроса." };
  if (bal.value < cost) return { ok: false, balance: bal, message: `Недостаточно средств: нужно ${cost}, доступно ${bal.value}.` };
  return { ok: true, balance: bal };
}

async function createAndProcessTask(userId, patient) {
  const created = await apiFetch("/predict/patient", { method: "POST", json: patient });
  const patientId = Number(created.patient_id);
  const task = await apiFetch("/predict/task", { method: "POST", json: { patient_id: patientId, user_id: userId } });
  const taskId = Number(task.task_id);
  await apiFetch(`/predict/task/${taskId}/process`, { method: "POST" });
  return taskId;
}

async function pollTask(taskId) {
  const started = Date.now();
  while (Date.now() - started < cfg().POLL_TIMEOUT_MS) {
    const t = await apiFetch(`/predict/task/${taskId}`);
    if (t.status === "completed" || t.status === "failed") return t;
    await new Promise((r) => setTimeout(r, cfg().POLL_INTERVAL_MS));
  }
  return await apiFetch(`/predict/task/${taskId}`);
}

function renderAcceptedRow(tbody, idx, task) {
  const tr = document.createElement("tr");

  const statusKind = task.status === "completed" ? "ok" : (task.status === "failed" ? "danger" : "");
  const predictionText = (task.prediction === undefined || task.prediction === null) ? "—" : String(task.prediction);
  const probText = (task.probability === undefined || task.probability === null) ? "—" : String(task.probability);

  tr.innerHTML = `
    <td>${idx}</td>
    <td>${task.task_id ?? "—"}</td>
    <td></td>
    <td>${predictionText}</td>
    <td>${probText}</td>
  `;
  tr.children[2].appendChild(badge(task.status, statusKind));
  tbody.appendChild(tr);
}

function renderRejectedRow(tbody, idx, errors) {
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td>${idx}</td>
    <td>${errors.map((e) => `<div>${escapeHtml(e)}</div>`).join("")}</td>
  `;
  tbody.appendChild(tr);
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function parseCsv(text) {
  const lines = text.replaceAll("\r\n", "\n").replaceAll("\r", "\n").split("\n").filter((l) => l.trim().length > 0);
  if (lines.length < 2) return { headers: [], rows: [] };
  const headers = lines[0].split(",").map((h) => h.trim());
  const rows = lines.slice(1).map((line) => {
    const parts = line.split(","); // simple CSV (no quoted commas)
    const row = {};
    headers.forEach((h, i) => { row[h] = (parts[i] ?? "").trim(); });
    return row;
  });
  return { headers, rows };
}

async function loadDashboard() {
  const userId = await requireCurrentUserId();
  if (!userId) {
    window.location.hash = "#/login";
    showGlobal("danger", "Сессия истекла. Войдите снова.");
    return;
  }
  el("predictCostLabel").textContent = String(cfg().PREDICT_COST);
  try {
    const { user, balance } = await fetchUserAndBalance(userId);
    el("userSummary").textContent = `${user.display_name} (@${user.login}) • user_id=${user.id}`;
    el("balanceValue").textContent = `${balance.value} ${balance.currency}`;
    el("balanceMeta").textContent = `Обновлено: ${fmtDateTime(balance.updated_at)}`;
  } catch (e) {
    showGlobal("danger", `Не удалось загрузить кабинет: ${e.message}`);
  }
}

async function loadPredictPage() {
  const userId = await requireCurrentUserId();
  if (!userId) {
    window.location.hash = "#/login";
    showGlobal("danger", "Сессия истекла. Войдите снова.");
    return;
  }
  el("predictCostLabel").textContent = String(cfg().PREDICT_COST);
  try {
    const bal = await apiFetch(`/balance/${userId}`);
    showGlobal("ok", `Баланс: ${bal.value} ${bal.currency}. Стоимость ML: ${cfg().PREDICT_COST}.`);
  } catch (e) {
    showGlobal("danger", `Не удалось получить баланс: ${e.message}`);
  }
}

async function loadHistory() {
  const userId = await requireCurrentUserId();
  if (!userId) {
    window.location.hash = "#/login";
    showGlobal("danger", "Сессия истекла. Войдите снова.");
    return;
  }
  try {
    const [tx, preds] = await Promise.all([
      apiFetch(`/history/transactions/${userId}`),
      apiFetch(`/history/predicts/${userId}`),
    ]);

    const txBody = el("tableTx").querySelector("tbody");
    txBody.innerHTML = "";
    for (const t of tx) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${fmtDateTime(t.created_at)}</td>
        <td>${escapeHtml(t.type)}</td>
        <td>${escapeHtml(t.amount)}</td>
        <td>${escapeHtml(t.currency)}</td>
        <td>${escapeHtml(t.description ?? "")}</td>
      `;
      txBody.appendChild(tr);
    }

    const prBody = el("tablePred").querySelector("tbody");
    prBody.innerHTML = "";
    for (const p of preds) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${fmtDateTime(p.created_at)}</td>
        <td></td>
        <td>${escapeHtml(p.cost)}</td>
        <td>${p.prediction === undefined ? "—" : escapeHtml(p.prediction)}</td>
        <td>${p.probability === undefined ? "—" : escapeHtml(p.probability)}</td>
        <td>${escapeHtml(p.task_id)}</td>
      `;
      tr.children[1].appendChild(badge(p.status, p.status === "completed" ? "ok" : (p.status === "failed" ? "danger" : "")));
      prBody.appendChild(tr);
    }
  } catch (e) {
    showGlobal("danger", `Не удалось загрузить историю: ${e.message}`);
  }
}

function loadSettings() {
  const input = el("formApiPrefix").elements.apiPrefix;
  input.value = cfg().API_PREFIX;
  el("apiPrefixLabel").textContent = cfg().API_PREFIX;
}

function setupHandlers() {
  window.addEventListener("hashchange", route);

  el("btnLogout").addEventListener("click", () => {
    setUserId(null);
    setToken(null);
    updateAuthUI();
    window.location.hash = "#/home";
    showGlobal("ok", "Вы вышли из аккаунта.");
  });

  el("btnRefreshDashboard").addEventListener("click", () => void loadDashboard());
  el("btnRefreshPredict").addEventListener("click", () => void loadPredictPage());
  el("btnRefreshHistory").addEventListener("click", () => void loadHistory());

  el("formLogin").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    clearGlobal();
    const data = formToObject(ev.currentTarget);
    try {
      const res = await apiFetch("/auth/signin", { method: "POST", json: data });
      setUserId(Number(res.user_id));
      setToken(res.access_token);
      updateAuthUI();
      window.location.hash = "#/dashboard";
      showGlobal("ok", "Вход выполнен.");
    } catch (e) {
      showGlobal("danger", `Ошибка входа: ${e.message}`);
    }
  });

  el("formSignup").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    clearGlobal();
    const data = formToObject(ev.currentTarget);
    try {
      const res = await apiFetch("/auth/signup", { method: "POST", json: data });
      showGlobal("ok", `Пользователь создан (user_id=${res.user_id}). Теперь войдите.`);
      window.location.hash = "#/login";
    } catch (e) {
      showGlobal("danger", `Ошибка регистрации: ${e.message}`);
    }
  });

  el("formDeposit").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    clearGlobal();
    const userId = await requireCurrentUserId();
    if (!userId) {
      window.location.hash = "#/login";
      showGlobal("danger", "Сессия истекла. Войдите снова.");
      return;
    }

    const fd = new FormData(ev.currentTarget);
    const amount = parseNumber(fd.get("amount"));
    const currency = String(fd.get("currency") || "RUB");
    const description = String(fd.get("description") || "");

    if (!amount || amount <= 0) {
      showGlobal("danger", "Сумма пополнения должна быть положительной.");
      return;
    }

    try {
      await apiFetch("/balance/deposit", {
        method: "POST",
        json: { user_id: userId, amount, currency, description: description || null },
      });
      await loadDashboard();
      showGlobal("ok", "Баланс пополнен.");
      ev.currentTarget.reset();
    } catch (e) {
      showGlobal("danger", `Ошибка пополнения: ${e.message}`);
    }
  });

  el("formPredictSingle").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    clearGlobal();
    const userId = await requireCurrentUserId();
    if (!userId) {
      window.location.hash = "#/login";
      showGlobal("danger", "Сессия истекла. Войдите снова.");
      return;
    }

    const form = ev.currentTarget;
    const patient = {
      age: parseIntStrict(form.elements.age.value),
      gender: form.elements.gender.value,
      physical_activity_days_per_week: parseIntStrict(form.elements.physical_activity_days_per_week.value),
      stress_level: parseIntStrict(form.elements.stress_level.value),
      bmi: parseNumber(form.elements.bmi.value),
      exercise_hours_per_week: parseNumber(form.elements.exercise_hours_per_week.value),
      sedentary_hours_per_day: parseNumber(form.elements.sedentary_hours_per_day.value),
      sleep_hours_per_day: parseNumber(form.elements.sleep_hours_per_day.value),
      heart_rate: parseNumber(form.elements.heart_rate.value),
      cholesterol: parseNumber(form.elements.cholesterol.value),
      blood_sugar: parseNumber(form.elements.blood_sugar.value),
      triglycerides: parseNumber(form.elements.triglycerides.value),
      smoking: form.elements.smoking.checked,
      alcohol_consumption: form.elements.alcohol_consumption.checked,
      diabetes: form.elements.diabetes.checked,
      obesity: form.elements.obesity.checked,
      family_history: form.elements.family_history.checked,
    };

    const v = validatePatientRow(patient);
    if (!v.ok) {
      showGlobal("danger", `Ошибки валидации: ${v.errors.join("; ")}`);
      return;
    }

    try {
      const funds = await ensureSufficientFunds(userId);
      if (!funds.ok) {
        showGlobal("danger", funds.message);
        return;
      }

      const taskId = await createAndProcessTask(userId, v.patient);
      showGlobal("ok", `Задача отправлена. task_id=${taskId}. Ожидаем результат...`);

      const finalTask = await pollTask(taskId);
      ensureResultsVisible();
      const tbody = el("tableAccepted").querySelector("tbody");
      renderAcceptedRow(tbody, tbody.children.length + 1, finalTask);
      await loadDashboard();
    } catch (e) {
      showGlobal("danger", `Ошибка ML‑запроса: ${e.message}`);
    }
  });

  el("formPredictCsv").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    clearGlobal();
    const userId = await requireCurrentUserId();
    if (!userId) {
      window.location.hash = "#/login";
      showGlobal("danger", "Сессия истекла. Войдите снова.");
      return;
    }

    const file = ev.currentTarget.elements.file.files[0];
    if (!file) return;

    let text = "";
    try { text = await file.text(); } catch (e) {
      showGlobal("danger", `Не удалось прочитать файл: ${e.message}`);
      return;
    }

    const { rows } = parseCsv(text);
    if (!rows.length) {
      showGlobal("danger", "CSV пустой или не содержит строк данных.");
      return;
    }

    try {
      const funds = await ensureSufficientFunds(userId);
      if (!funds.ok) {
        showGlobal("danger", funds.message);
        return;
      }

      ensureResultsVisible(true);

      const acceptedBody = el("tableAccepted").querySelector("tbody");
      const rejectedBody = el("tableRejected").querySelector("tbody");
      acceptedBody.innerHTML = "";
      rejectedBody.innerHTML = "";

      const valid = [];
      rows.forEach((row, i) => {
        const v = validatePatientRow(row);
        if (!v.ok) renderRejectedRow(rejectedBody, i + 1, v.errors);
        else valid.push({ idx: i + 1, patient: v.patient });
      });

      if (!valid.length) {
        showGlobal("danger", "Нет корректных строк для обработки.");
        return;
      }

      showGlobal("ok", `Принято строк: ${valid.length}. Запускаю обработку...`);

      for (const item of valid) {
        // extra balance check before each task
        const funds2 = await ensureSufficientFunds(userId);
        if (!funds2.ok) {
          showGlobal("danger", `${funds2.message} Остановлено на строке #${item.idx}.`);
          break;
        }

        const taskId = await createAndProcessTask(userId, item.patient);
        const finalTask = await pollTask(taskId);
        renderAcceptedRow(acceptedBody, item.idx, finalTask);
      }

      await loadDashboard();
    } catch (e) {
      showGlobal("danger", `Ошибка обработки CSV: ${e.message}`);
    }
  });

  el("btnClearResults").addEventListener("click", () => {
    setHidden(el("predictResults"), true);
    el("tableAccepted").querySelector("tbody").innerHTML = "";
    el("tableRejected").querySelector("tbody").innerHTML = "";
  });

  el("formApiPrefix").addEventListener("submit", (ev) => {
    ev.preventDefault();
    const input = ev.currentTarget.elements.apiPrefix;
    const v = String(input.value || "").trim();
    if (!v.startsWith("/api/")) {
      showGlobal("danger", "API prefix должен начинаться с /api/ (например: /api/1.0).");
      return;
    }
    localStorage.setItem(STORAGE.apiPrefix, v);
    updateAuthUI();
    loadSettings();
    showGlobal("ok", "API prefix сохранён.");
  });

  el("btnResetApiPrefix").addEventListener("click", () => {
    localStorage.removeItem(STORAGE.apiPrefix);
    updateAuthUI();
    loadSettings();
    showGlobal("ok", "API prefix сброшен на значение по умолчанию.");
  });
}

function ensureResultsVisible(reset = false) {
  setHidden(el("predictResults"), false);
  if (reset) {
    el("tableAccepted").querySelector("tbody").innerHTML = "";
    el("tableRejected").querySelector("tbody").innerHTML = "";
  }
}

function main() {
  updateAuthUI();
  setupHandlers();
  route();
}

main();

