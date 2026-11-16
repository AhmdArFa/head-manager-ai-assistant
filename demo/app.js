const apiIndicator = document.getElementById("apiIndicator");
const apiStatus = document.getElementById("apiStatus");
const welcomePanel = document.getElementById("welcomePanel");
const conversation = document.getElementById("conversation");
const questionForm = document.getElementById("questionForm");
const questionInput = document.getElementById("questionInput");
const askButton = document.getElementById("askButton");
const newQuestionButton = document.getElementById("newQuestion");

function node(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined && text !== null) element.textContent = String(text);
  return element;
}

function setApiState(online) {
  apiIndicator.classList.toggle("is-online", online);
  apiIndicator.classList.toggle("is-offline", !online);
  apiStatus.textContent = online ? "API online" : "API unavailable";
}

async function checkApi() {
  try {
    const response = await fetch("/health", { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error("health check failed");
    const body = await response.json();
    setApiState(body.status === "ok");
  } catch (_error) {
    setApiState(false);
  }
}

function humanize(value) {
  return String(value).replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function renderQuestion(question) {
  const row = node("div", "question-row");
  row.append(node("div", "question-bubble", question));
  return row;
}

function renderAnswer(body) {
  const panel = node("article", "answer-panel");
  const header = node("div", "answer-header");
  const assistant = node("div", "assistant-id");
  const avatar = node("span", "assistant-avatar");
  avatar.setAttribute("aria-hidden", "true");
  avatar.innerHTML = '<svg viewBox="0 0 20 20" fill="none"><path d="M5 15V5l5 6 5-6v10M5 10h10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><circle cx="5" cy="5" r="1.5" fill="currentColor"/><circle cx="15" cy="5" r="1.5" fill="currentColor"/></svg>';
  const identityCopy = node("span");
  identityCopy.append(node("strong", "", "المساعد التنفيذي للإدارة"));
  identityCopy.append(node("small", "", "بيانات مباشرة ومعتمدة من نظام 4S ERP & CRM"));
  assistant.append(avatar, identityCopy);
  header.append(assistant, node("span", "intent-badge", humanize(body.intent || "response")));

  const content = node("div", "answer-body");
  content.append(node("p", "answer-copy", body.answer || "لم يتم استلام نص للإجابة."));
  const responseMeta = node("div", "response-meta");
  responseMeta.append(node("span", "", `طلب #${String(body.request_id || "").slice(0, 8) || "—"}`));
  responseMeta.append(node("span", "meta-separator", "·"));
  responseMeta.append(node("span", "", "تفاصيل المصدر وسجل التنفيذ بالأسفل"));
  content.append(responseMeta);

  const source = Array.isArray(body.sources) ? body.sources[0] : null;
  const evidence = node("section", "evidence-section");
  evidence.setAttribute("aria-label", "Data evidence");
  const evidenceHead = node("div", "evidence-head");
  const title = node("div", "evidence-title");
  const tableIcon = node("span");
  tableIcon.innerHTML = '<svg viewBox="0 0 16 16" fill="none" aria-hidden="true"><rect x="2.3" y="2.7" width="11.4" height="10.6" rx="1.5" stroke="currentColor" stroke-width="1.25"/><path d="M2.8 6.2h10.4M6 6.4v6.4M9.5 6.4v6.4" stroke="currentColor" stroke-width="1.1"/></svg>';
  title.append(tableIcon, node("span", "", source ? "سجلات النظام ومصدر البيانات" : "حالة الاستعلام"));
  evidenceHead.append(title);
  if (source) {
    evidenceHead.append(node("span", "source-chip", `جدول: ${source.table} · ${source.row_count} سجل`));
  } else {
    evidenceHead.append(node("span", "source-chip", "لم يتم الاستعلام"));
  }
  evidence.append(evidenceHead);
  if (Array.isArray(body.data) && body.data.length) {
    evidence.append(renderDataTable(body.data));
  } else {
    evidence.append(node("p", "empty-data", source ? "لم يُرجع الاستعلام أي سجلات." : "لم يتم تشغيل استعلام في قاعدة البيانات لهذا السؤال."));
  }
  content.append(evidence);

  if (Array.isArray(body.trace) && body.trace.length) {
    content.append(renderTrace(body.trace));
  }
  panel.append(header, content);
  return panel;
}

function renderDataTable(rows) {
  const wrap = node("div", "table-wrap");
  const table = node("table", "data-table");
  const columns = Object.keys(rows[0] || {});
  const head = node("thead");
  const headerRow = node("tr");
  columns.forEach((column) => headerRow.append(node("th", "", humanize(column))));
  head.append(headerRow);
  const body = node("tbody");
  rows.forEach((row) => {
    const tr = node("tr");
    columns.forEach((column) => {
      const value = row[column] === null || row[column] === undefined ? "—" : String(row[column]);
      const td = node("td");
      if (column === "status") {
        const statusClass = value.toLowerCase().replaceAll("_", "-");
        td.append(node("span", `value-status status-${statusClass}`, humanize(value)));
      } else {
        td.textContent = value;
      }
      tr.append(td);
    });
    body.append(tr);
  });
  table.append(head, body);
  wrap.append(table);
  return wrap;
}

function renderTrace(steps) {
  const section = node("section", "trace-section");
  const title = node("div", "trace-title");
  title.append(node("span", "", "Execution trace"));
  title.append(node("span", "", `${steps.length} steps · from API response`));
  const list = node("div", "trace-list");
  steps.forEach((step) => {
    const item = node("div", "trace-item");
    const track = node("span", "trace-track");
    const skipped = step.status === "skipped";
    track.append(node("span", skipped ? "trace-node skipped" : "trace-node", skipped ? "–" : "✓"));
    const copy = node("div", "trace-copy");
    const copyHead = node("div", "trace-copy-head");
    copyHead.append(node("strong", "", humanize(step.step || "step")));
    copyHead.append(node("code", "", step.component || "component"));
    copy.append(copyHead, node("p", "", step.detail || ""));
    item.append(track, copy);
    list.append(item);
  });
  section.append(title, list);
  return section;
}

function renderError(error) {
  const panel = node("article", "answer-panel");
  const content = node("div", "answer-body");
  const notice = node("div", "error-notice");
  const copy = node("div");
  copy.append(node("strong", "", "Couldn't reach the assistant API"));
  copy.append(document.createTextNode(`${error} Start the FastAPI app, then open this demo at /demo/.`));
  notice.append(copy);
  content.append(notice);
  panel.append(content);
  return panel;
}

async function askQuestion(question) {
  const trimmedQuestion = question.trim();
  if (trimmedQuestion.length < 2 || askButton.disabled) return;
  welcomePanel.hidden = true;
  conversation.replaceChildren(renderQuestion(trimmedQuestion));
  askButton.disabled = true;
  askButton.querySelector("span").textContent = "Working…";
  questionInput.value = "";
  try {
    const response = await fetch("/api/v1/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ question: trimmedQuestion }),
    });
    if (!response.ok) {
      let message = `Request failed (${response.status}).`;
      try {
        const details = await response.json();
        if (details.detail) message = Array.isArray(details.detail) ? "The question did not pass request validation." : String(details.detail);
      } catch (_error) { /* Keep the HTTP status as the visible explanation. */ }
      throw new Error(message);
    }
    const body = await response.json();
    setApiState(true);
    conversation.append(renderAnswer(body));
  } catch (error) {
    setApiState(false);
    conversation.append(renderError(error instanceof Error ? error.message : "Unknown connection error."));
  } finally {
    askButton.disabled = false;
    askButton.querySelector("span").textContent = "Ask assistant";
    conversation.scrollIntoView({ behavior: "smooth", block: "nearest" });
    questionInput.focus({ preventScroll: true });
  }
}

questionForm.addEventListener("submit", (event) => {
  event.preventDefault();
  askQuestion(questionInput.value);
});

questionInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    questionForm.requestSubmit();
  }
});

document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", () => {
    const question = button.getAttribute("data-question") || "";
    questionInput.value = question;
    askQuestion(question);
  });
});

newQuestionButton.addEventListener("click", () => {
  conversation.replaceChildren();
  welcomePanel.hidden = false;
  questionInput.value = "";
  questionInput.focus();
});

const themeToggle = document.getElementById("themeToggle");
const themeLabel = document.getElementById("themeLabel");
const colorSchemeMeta = document.querySelector('meta[name="color-scheme"]');

function updateThemeUI(scheme) {
  const isSystemDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const isDark = scheme === "dark" || (scheme === "light dark" && isSystemDark);
  document.documentElement.setAttribute("data-theme", isDark ? "dark" : "light");
  if (themeLabel) {
    themeLabel.textContent = isDark ? "Light mode" : "Dark mode";
  }
}

function initTheme() {
  let stored = null;
  try {
    stored = localStorage.getItem("color-scheme");
  } catch (_) {}

  if (stored === "dark" || stored === "light") {
    if (colorSchemeMeta) colorSchemeMeta.content = stored;
    updateThemeUI(stored);
  } else {
    updateThemeUI("light dark");
  }

  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      const isSystemDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      const currentMeta = colorSchemeMeta ? colorSchemeMeta.content : "light dark";
      const isCurrentlyDark = currentMeta === "dark" || (currentMeta === "light dark" && isSystemDark);
      const target = isCurrentlyDark ? "light" : "dark";

      try {
        if ((target === "dark" && isSystemDark) || (target === "light" && !isSystemDark)) {
          localStorage.removeItem("color-scheme");
          if (colorSchemeMeta) colorSchemeMeta.content = "light dark";
          updateThemeUI("light dark");
        } else {
          localStorage.setItem("color-scheme", target);
          if (colorSchemeMeta) colorSchemeMeta.content = target;
          updateThemeUI(target);
        }
      } catch (_) {
        if (colorSchemeMeta) colorSchemeMeta.content = target;
        updateThemeUI(target);
      }
    });
  }

  window.addEventListener("storage", (e) => {
    if (e.key === "color-scheme") {
      const newScheme = e.newValue || "light dark";
      if (colorSchemeMeta) colorSchemeMeta.content = newScheme;
      updateThemeUI(newScheme);
    }
  });

  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    let currentStored = null;
    try {
      currentStored = localStorage.getItem("color-scheme");
    } catch (_) {}
    if (!currentStored) {
      updateThemeUI("light dark");
    }
  });
}

initTheme();
checkApi();
