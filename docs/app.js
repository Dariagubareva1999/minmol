"use strict";

const MONTHS = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"];
const STORAGE_KEY = "minmol.web.data.v1";
const API_KEY_LOCAL = "minmol.web.apiKey";
const API_KEY_SESSION = "minmol.web.apiKey.session";
const DEFAULT_ORGANIZATION = "Администрация городского округа муниципальное образование городской округ город Луганск Луганской Народной Республики";
const TARGETS = [
  ["01", "01", "1П", "Участники проектов и программ, направленных на патриотическое воспитание", "Общая численность молодых людей в возрасте от 14 до 35 лет включительно, принявших участие в проектах и программах, направленных на патриотическое воспитание, реализованных органами местного самоуправления, исполнительными органами субъекта Российской Федерации и финансируемыми ими организациями, на конец отчетного месяца/года нарастающим итогом с начала отчетного года, человек", "ПРОЕКТЫ И ПРОГРАММЫ, НАПРАВЛЕННЫЕ НА ПАТРИОТИЧЕСКОЕ ВОСПИТАНИЕ, РЕАЛИЗОВАННЫЕ ОРГАНАМИ МЕСТНОГО САМОУПРАВЛЕНИЯ", "патриот,истори,памят,геро,отечеств,родин,символик,традиц,наслед,музе,краевед,поисков,археолог,военн,экологи,субботник,дерев,берег,отход,туризм,экскурси,поход,межнацион,межконфессион,экстремизм,терроризм,межрегион,международ"],
  ["02", "02", "2ПРОФ", "Участники мероприятий, направленных на профессиональное и личностное развитие", "Общая численность молодых людей в возрасте от 14 до 35 лет включительно, принявших участие в проектах и программах, направленных на профессиональное, личностное развитие, реализованных органами местного самоуправления, исполнительными органами субъекта Российской Федерации и финансируемыми ими организациями, на конец отчетного месяца/года нарастающим итогом с начала отчетного года, человек", "ПРОЕКТЫ И ПРОГРАММЫ, НАПРАВЛЕННЫЕ НА ПРОФЕССИОНАЛЬНОЕ, ЛИЧНОСТНОЕ РАЗВИТИЕ, РЕАЛИЗОВАННЫЕ ОРГАНАМИ МЕСТНОГО САМОУПРАВЛЕНИЯ", "професс,профориент,карьер,трудоустр,предприним,образован,просвещ,научн,обучен,лекци,семинар,тренинг,мастер-класс,конференц,форум,конкурс,одаренн,талант,наставнич,стажиров,практик,компетенц,саморазвит,личност,инициатив,проектирован,госстарт,профпоток"],
  ["03", "05", "3С", "Молодые семьи в мероприятиях по продвижению традиционных ценностей", "Фактическое количество молодых семей, принявших участие в мероприятиях, направленных на продвижение традиционных духовно-нравственных ценностей, в проектах и программах, направленных на патриотическое воспитание, вовлечение в добровольческую и общественную деятельность, реализованных органами местного самоуправления, исполнительными органами субъектов Российской Федерации и финансируемыми ими организациями, на конец отчетного месяца/года нарастающим итогом с начала года, единица", "ПРОЕКТЫ И ПРОГРАММЫ ДЛЯ МОЛОДЫХ СЕМЕЙ, НАПРАВЛЕННЫЕ НА ПРОДВИЖЕНИЕ ТРАДИЦИОННЫХ ДУХОВНО-НРАВСТВЕННЫХ ЦЕННОСТЕЙ", "молодая семья,молодые семьи,семь,семейн,материн,отцов,день отца,день матери,брак,репродуктив,родител,детско-родитель,многодет"],
  ["04", "03", "4ДМ", "Участники мероприятий на базе инфраструктуры молодежной политики", "Фактическая численность молодых людей в возрасте от 14 до 35 лет включительно, принявших участие в проектах и программах, реализованных объектами инфраструктуры молодежной политики субъекта Российской Федерации, на конец отчетного месяца/года нарастающим итогом с начала отчетного года, человек", "ПРОЕКТЫ И ПРОГРАММЫ, ПРОВОДИМЫЕ НА БАЗЕ ИНФРАСТРУКТУРЫ МОЛОДЕЖНОЙ ПОЛИТИКИ", "дом молодежи,дом молодёжи,молодежный центр,молодёжный центр,центр юность,мбу юность,лгмц,инфраструктур,молодежное пространство,молодёжное пространство"],
  ["05", "04", "5В", "Участники добровольческой и общественной деятельности", "Общая численность населения субъекта Российской Федерации в возрасте от 14 до 35 лет включительно, вовлеченного в добровольческую и общественную деятельность в России, на конец отчетного месяца/года нарастающим итогом с начала отчетного года, человек", "ПРОЕКТЫ И ПРОГРАММЫ, НАПРАВЛЕННЫЕ НА ВОВЛЕЧЕНИЕ В ДОБРОВОЛЬЧЕСКУЮ И ОБЩЕСТВЕННУЮ ДЕЯТЕЛЬНОСТЬ", "волонтер,волонтёр,доброволь,общественн,благотвор,гуманитар,помощ,донор,активист,молодежный совет,молодёжный совет,общественное объединение,акци,субботник,уборк,благоустрой,возложение,возложени"]
];
const DEFAULT_REPORTS = {
  appendix_1_title: "ПРИЛОЖЕНИЕ 1",
  appendix_1_subtitle: "Сведения о реализации молодежной политики",
  appendix_1_columns: ["Наименование компоненты показателя", "№ строки", "Значение нарастающим итогом"],
  appendix_2_title: "ПРИЛОЖЕНИЕ 2. ЖУРНАЛ МЕРОПРИЯТИЙ",
  appendix_2_columns: ["№ п/п", "Дата проведения", "Наименование мероприятия / проекта", "Количество участников", "Ссылка на публикацию"]
};
const DEFAULT_LABELS = {date: "Дата (ДД.ММ.ГГГГ)", time: "Время", place: "Место", name: "Название", description: "Краткое описание", participants: "Участники / семьи", link: "Ссылка"};
const LABEL_KEYS = Object.keys(DEFAULT_LABELS);
let state;
let activePreview = "app1";
let selectedTargetId = null;

function uid(prefix) {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

function defaultData(year = new Date().getFullYear()) {
  return {
    version: 1, organization: DEFAULT_ORGANIZATION, year,
    targets: TARGETS.map(([id, report_row, code, name, report_name, section, words]) => ({id, report_row, code, name, report_name, section, keywords: words.split(","), plan: Array(12).fill(0)})),
    events: [], report_settings: JSON.parse(JSON.stringify(DEFAULT_REPORTS)), card_labels: {...DEFAULT_LABELS}, custom_fields: [],
    press_release_settings: {base_url: "https://api.deepseek.com/chat/completions", model: "deepseek-flash", instruction: "Подготовь профессиональный пресс-релиз на русском языке по данным мероприятия. Не выдумывай факты. Добавь заголовок, лид и основной текст."}
  };
}

function integer(value) {
  if (typeof value === "boolean") return Number(value);
  if (typeof value === "number") return Math.trunc(value) || 0;
  const match = String(value ?? "").match(/-?\d[\d\s]*/);
  return match ? Number(match[0].replaceAll(" ", "")) : 0;
}

function normalizeData(raw) {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) throw new Error("Корневой элемент JSON должен быть объектом.");
  const result = defaultData(integer(raw.year) || new Date().getFullYear());
  result.organization = String(raw.organization || result.organization);
  const defaults = Object.fromEntries(result.targets.map(target => [target.id, target]));
  if (Array.isArray(raw.targets) && raw.targets.length) {
    result.targets = raw.targets.map((item, index) => {
      const id = String(item.id || uid("target"));
      const fallback = defaults[id] || {};
      const keywords = Array.isArray(item.keywords) ? item.keywords : String(item.keywords || "").split(",");
      const plan = Array.isArray(item.plan) ? item.plan.slice(0, 12).map(value => Math.max(0, integer(value))) : [];
      return {id, name: String(item.name || fallback.name || "Новый целевой показатель"), code: String(item.code || fallback.code || id), report_row: String(item.report_row || fallback.report_row || index + 1), report_name: String(item.report_name || fallback.report_name || item.name || "Новый целевой показатель"), section: String(item.section || fallback.section || item.name || "НОВЫЙ РАЗДЕЛ"), keywords: keywords.map(String).map(word => word.trim().toLowerCase()).filter(Boolean), plan: plan.concat(Array(12 - plan.length).fill(0))};
    });
  }
  const validIds = new Set(result.targets.map(target => target.id));
  result.events = (Array.isArray(raw.events) ? raw.events : []).map(item => ({
    id: String(item.id || uid("event")), date: String(item.date || ""), time: String(item.time || ""), place: String(item.place || ""), name: String(item.name || ""), description: String(item.description || ""),
    target_ids: (Array.isArray(item.target_ids) ? item.target_ids : []).map(String).filter(id => validIds.has(id)), auto_classify: Boolean(item.auto_classify),
    participants: item.participants === null || item.participants === undefined || item.participants === "" ? null : Math.max(0, integer(item.participants)), link: String(item.link || ""),
    custom_fields: item.custom_fields && typeof item.custom_fields === "object" ? Object.fromEntries(Object.entries(item.custom_fields).map(([key, value]) => [String(key), String(value || "")])) : {}, press_release: String(item.press_release || "")
  }));
  const reports = raw.report_settings && typeof raw.report_settings === "object" ? raw.report_settings : {};
  for (const [key, fallback] of Object.entries(DEFAULT_REPORTS)) {
    if (Array.isArray(fallback)) {
      const incoming = Array.isArray(reports[key]) ? reports[key].slice(0, fallback.length).map(String) : [];
      result.report_settings[key] = incoming.concat(fallback.slice(incoming.length));
    } else result.report_settings[key] = String(reports[key] || fallback);
  }
  if (raw.card_labels && typeof raw.card_labels === "object") for (const key of LABEL_KEYS) result.card_labels[key] = String(raw.card_labels[key] || DEFAULT_LABELS[key]);
  result.custom_fields = (Array.isArray(raw.custom_fields) ? raw.custom_fields : []).map(field => ({id: String(field.id || uid("field")), label: String(field.label || "Дополнительное поле")}));
  const press = raw.press_release_settings && typeof raw.press_release_settings === "object" ? raw.press_release_settings : {};
  for (const key of Object.keys(result.press_release_settings)) result.press_release_settings[key] = String(press[key] || result.press_release_settings[key]);
  return result;
}

function load() {
  try { return normalizeData(JSON.parse(localStorage.getItem(STORAGE_KEY))) } catch (error) { return defaultData(); }
}
function save(message) { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); if (message) toast(message); }
function byId(id) { return document.getElementById(id); }
function node(tag, text, className) { const element = document.createElement(tag); if (text !== undefined) element.textContent = String(text); if (className) element.className = className; return element; }
function option(value, text) { const item = node("option", text); item.value = value; return item; }
function replaceSelect(select, items, selected) { select.replaceChildren(...items.map(item => option(item[0], item[1]))); if (selected !== undefined) select.value = String(selected); }
function toast(message) { const item = byId("toast"); item.textContent = message; item.classList.add("show"); clearTimeout(toast.timer); toast.timer = setTimeout(() => item.classList.remove("show"), 2800); }
function download(blob, filename) { const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = filename; document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(link.href), 1000); }

function parseDate(value) {
  const text = String(value || "").trim();
  let match = text.match(/^(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})$/); let day; let month; let year;
  if (match) [, day, month, year] = match;
  else { match = text.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/); if (!match) return null; [, year, month, day] = match; }
  const date = new Date(Number(year), Number(month) - 1, Number(day));
  return date.getFullYear() === Number(year) && date.getMonth() === Number(month) - 1 && date.getDate() === Number(day) ? date : null;
}
function reportingPeriod(date) { return date.getDate() < 25 ? [date.getFullYear(), date.getMonth()] : date.getMonth() === 11 ? [date.getFullYear() + 1, 0] : [date.getFullYear(), date.getMonth() + 1]; }
function periodBounds(year, month) { return [new Date(year, month - 1, 25), new Date(year, month, 24)]; }
function formatDate(date) { return `${String(date.getDate()).padStart(2, "0")}.${String(date.getMonth() + 1).padStart(2, "0")}.${date.getFullYear()}`; }
function eventInMonth(event, year, month) { const date = parseDate(event.date); return date ? reportingPeriod(date)[0] === Number(year) && reportingPeriod(date)[1] === month : false; }
function eventComplete(event) { return Boolean(event.date && event.time && event.place && event.name && event.description && event.participants !== null && event.participants !== undefined && event.link && event.target_ids?.length); }
function classify(name, description, place) { const text = `${name} ${description} ${place}`.toLowerCase().replaceAll("ё", "е"); return state.targets.filter(target => target.keywords.some(word => text.includes(String(word).toLowerCase().replaceAll("ё", "е")))).map(target => target.id); }
function actuals(targetId) { const values = Array(12).fill(0); for (const event of state.events) { const date = parseDate(event.date); if (date && reportingPeriod(date)[0] === Number(state.year) && event.target_ids.includes(targetId)) values[reportingPeriod(date)[1]] += Math.max(0, integer(event.participants)); } return values; }
function calculate(target) { const facts = actuals(target.id); let previousPlan = 0; let previousBalance = 0; let cumulative = 0; return MONTHS.map((_, month) => { const cumulativePlan = integer(target.plan[month]); const monthlyPlan = cumulativePlan - previousPlan; const required = monthlyPlan + previousBalance; const balance = required - facts[month]; cumulative += facts[month]; previousPlan = cumulativePlan; previousBalance = balance; return {month, cumulative_plan: cumulativePlan, monthly_plan: monthlyPlan, actual: facts[month], actual_cumulative: cumulative, balance, required}; }); }
function sortedTargets() { return [...state.targets].sort((a, b) => { const na = /^\d+$/.test(a.report_row); const nb = /^\d+$/.test(b.report_row); return na && nb ? Number(a.report_row) - Number(b.report_row) : String(a.report_row).localeCompare(String(b.report_row), "ru"); }); }
function eventsForMonth(month) { return state.events.filter(event => eventInMonth(event, state.year, month)).sort((a, b) => (parseDate(a.date) - parseDate(b.date)) || a.time.localeCompare(b.time)); }

function renderAll() {
  byId("header-year").textContent = state.year;
  renderOverview(); renderTargets(); renderEvents(); renderForms(); renderReports(); renderPress();
}

function renderOverview() {
  byId("organization").value = state.organization; byId("report-year").value = state.year;
  const yearly = state.events.filter(event => { const date = parseDate(event.date); return date && reportingPeriod(date)[0] === Number(state.year); });
  const filled = new Set(yearly.map(event => reportingPeriod(parseDate(event.date))[1]));
  const configured = state.targets.filter(target => target.plan.some(Boolean)).length;
  const data = [[yearly.length, "Мероприятий за год"], [yearly.reduce((sum, event) => sum + integer(event.participants), 0).toLocaleString("ru-RU"), "Суммарный охват"], [`${filled.size} / 12`, "Заполнено месяцев"], [`${configured} / ${state.targets.length}`, "Показателей настроено"]];
  byId("metrics").replaceChildren(...data.map(([value, label]) => { const card = node("div", undefined, "metric"); card.append(node("b", value), node("span", label)); return card; }));
  const [year, month] = reportingPeriod(new Date()); byId("today-period").textContent = `Текущий отчет: ${MONTHS[month].toLowerCase()} ${year}`;
}

function renderTargets() {
  const targetSelect = byId("plan-target"); const currentTarget = targetSelect.value || state.targets[0]?.id;
  replaceSelect(targetSelect, state.targets.map(target => [target.id, `${target.code} — ${target.name}`]), currentTarget);
  const monthSelect = byId("plan-month"); const currentMonth = monthSelect.value || "0"; replaceSelect(monthSelect, MONTHS.map((month, index) => [index, month]), currentMonth);
  updatePlanInput();
  const body = byId("targets-table"); body.replaceChildren();
  for (const target of state.targets) for (const row of calculate(target)) {
    const tr = node("tr"); tr.dataset.target = target.id; tr.dataset.month = row.month; tr.className = "clickable";
    [target.name, MONTHS[row.month], row.cumulative_plan, row.monthly_plan, row.actual, row.actual_cumulative, row.balance, row.required].forEach((value, index) => { const td = node("td", value, index > 1 ? "num" : ""); tr.append(td); }); body.append(tr);
  }
}
function updatePlanInput() { const target = state.targets.find(item => item.id === byId("plan-target").value); if (target) byId("plan-value").value = target.plan[Number(byId("plan-month").value)] || 0; }

function standardField(labelKey, input) { const label = node("label", state.card_labels[labelKey]); if (labelKey === "description" || labelKey === "name" || labelKey === "place" || labelKey === "link") label.classList.add("wide"); label.append(input); return label; }
function renderEventFormFields() {
  const container = byId("standard-event-fields"); container.className = "field-grid";
  const definitions = [["date", "text", "ДД.ММ.ГГГГ"], ["time", "time", ""], ["place", "text", ""], ["name", "text", ""], ["description", "textarea", ""], ["participants", "number", ""], ["link", "url", ""]];
  container.replaceChildren(...definitions.map(([key, type, placeholder]) => { const input = document.createElement(type === "textarea" ? "textarea" : "input"); input.id = `event-${key}`; input.dataset.field = key; if (type !== "textarea") input.type = type; else input.rows = 4; if (placeholder) input.placeholder = placeholder; if (key === "participants") input.min = "0"; return standardField(key, input); }));
  const custom = byId("custom-event-fields"); custom.className = "field-grid"; custom.replaceChildren(...state.custom_fields.map(field => { const input = document.createElement("input"); input.dataset.custom = field.id; const label = node("label", field.label, "wide"); label.append(input); return label; }));
  byId("event-date").addEventListener("input", updateEventPeriodHint);
}
function renderEvents() {
  const filter = byId("event-month-filter"); const old = filter.value || "all"; replaceSelect(filter, [["all", "Все месяцы"], ...MONTHS.map((month, index) => [index, month])], old);
  const query = byId("event-search").value.trim().toLowerCase(); const codeMap = Object.fromEntries(state.targets.map(target => [target.id, target.code]));
  const events = state.events.filter(event => { const date = parseDate(event.date); if (!date || reportingPeriod(date)[0] !== Number(state.year)) return false; if (filter.value !== "all" && reportingPeriod(date)[1] !== Number(filter.value)) return false; return !query || event.date.toLowerCase().includes(query) || event.name.toLowerCase().includes(query); }).sort((a, b) => (parseDate(a.date) - parseDate(b.date)) || a.time.localeCompare(b.time) || a.name.localeCompare(b.name, "ru"));
  const body = byId("events-table"); body.replaceChildren(...events.map(event => { const tr = node("tr", undefined, "clickable"); tr.dataset.id = event.id; const month = reportingPeriod(parseDate(event.date))[1]; [event.date, MONTHS[month], event.name, event.target_ids.map(id => codeMap[id]).filter(Boolean).join(", ") || "—", event.participants ?? ""].forEach(value => tr.append(node("td", value))); const td = node("td"); td.append(node("span", eventComplete(event) ? "Готово" : "Черновик", `status ${eventComplete(event) ? "ready" : "draft"}`)); tr.append(td); return tr; }));
  byId("events-empty").style.display = events.length ? "none" : "block";
  renderTargetChecks();
}
function renderTargetChecks(selected = []) { byId("event-target-checks").replaceChildren(...state.targets.map(target => { const label = node("label", undefined, "check"); const input = document.createElement("input"); input.type = "checkbox"; input.value = target.id; input.checked = selected.includes(target.id); label.append(input, node("span", `${target.code} — ${target.name}`)); return label; })); }
function clearEventForm() { byId("event-form").reset(); byId("event-id").value = ""; byId("auto-classify").checked = true; byId("event-form-title").textContent = "Новая карточка"; renderTargetChecks(); updateEventPeriodHint(); }
function loadEvent(id) { const event = state.events.find(item => item.id === id); if (!event) return; byId("event-id").value = event.id; byId("event-form-title").textContent = "Карточка мероприятия"; for (const key of LABEL_KEYS) byId(`event-${key}`).value = event[key] ?? ""; for (const input of byId("custom-event-fields").querySelectorAll("[data-custom]")) input.value = event.custom_fields[input.dataset.custom] || ""; byId("auto-classify").checked = event.auto_classify; renderTargetChecks(event.target_ids); updateEventPeriodHint(); document.querySelectorAll("#events-table tr").forEach(row => row.classList.toggle("selected", row.dataset.id === id)); }
function updateEventPeriodHint() { const date = byId("event-date") ? parseDate(byId("event-date").value) : null; if (!date) { byId("event-period-hint").textContent = "Укажите дату"; return; } const [year, month] = reportingPeriod(date); const [start, end] = periodBounds(year, month); byId("event-period-hint").textContent = `${MONTHS[month]} ${year}: ${formatDate(start)}–${formatDate(end)}`; }
function classifyForm() { const ids = classify(byId("event-name").value, byId("event-description").value, byId("event-place").value); byId("event-target-checks").querySelectorAll("input").forEach(input => input.checked = ids.includes(input.value)); toast(ids.length ? `Определено показателей: ${ids.length}` : "Совпадений по ключевым словам нет"); return ids; }

function renderReports() {
  const select = byId("report-month"); let selected = select.value;
  if (selected === "") { const months = state.events.map(event => parseDate(event.date)).filter(Boolean).map(reportingPeriod).filter(period => period[0] === Number(state.year)).map(period => period[1]); selected = String(months.length ? Math.max(...months) : reportingPeriod(new Date())[1]); }
  replaceSelect(select, MONTHS.map((month, index) => [index, month]), selected); updateReportPeriod(); renderPreview();
}
function updateReportPeriod() { const month = Number(byId("report-month").value); const [start, end] = periodBounds(state.year, month); byId("report-period").textContent = `Отчетный период: ${formatDate(start)}–${formatDate(end)}`; }
function renderPreview() { const month = Number(byId("report-month").value); const box = byId("report-preview"); box.replaceChildren(); const settings = state.report_settings; const title = node("div", undefined, "preview-title"); title.append(node("h2", activePreview === "app1" ? settings.appendix_1_title : settings.appendix_2_title), node("p", activePreview === "app1" ? `${settings.appendix_1_subtitle} за ${MONTHS[month].toLowerCase()} ${state.year} года` : `${state.organization} · ${byId("report-period").textContent}`)); box.append(title);
  if (activePreview === "app1") { const wrap = node("div", undefined, "table-wrap"); const table = document.createElement("table"); const head = document.createElement("thead"); const hr = document.createElement("tr"); settings.appendix_1_columns.forEach(value => hr.append(node("th", value))); head.append(hr); const body = document.createElement("tbody"); for (const target of sortedTargets()) { const tr = document.createElement("tr"); [target.report_name, target.report_row, calculate(target)[month].actual_cumulative].forEach(value => tr.append(node("td", value))); body.append(tr); } table.append(head, body); wrap.append(table); box.append(wrap); }
  else { const events = eventsForMonth(month); for (const target of sortedTargets()) { box.append(node("div", target.section, "preview-section")); const selected = events.filter(event => event.target_ids.includes(target.id)); if (!selected.length) box.append(node("p", "Нет мероприятий", "muted")); else { const list = document.createElement("ol"); selected.forEach(event => list.append(node("li", `${event.date} | ${event.name} | ${event.participants ?? "не заполнено"} | ${event.link || "не заполнено"}`))); box.append(list); } } const unassigned = events.filter(event => !event.target_ids.length); if (unassigned.length) box.append(node("p", `Внимание: не распределено по ЦП — ${unassigned.map(event => event.name).join(", ")}`, "warning")); }
}

function renderForms() {
  const list = byId("target-settings-list"); if (!selectedTargetId || !state.targets.some(target => target.id === selectedTargetId)) selectedTargetId = state.targets[0]?.id || null;
  list.replaceChildren(...state.targets.map(target => { const button = node("button", undefined, `setting-item${target.id === selectedTargetId ? " active" : ""}`); button.type = "button"; button.dataset.id = target.id; button.append(node("b", `${target.code} · строка ${target.report_row}`), node("small", target.name)); return button; }));
  if (selectedTargetId) fillTargetSettings(selectedTargetId);
  const reportFields = byId("report-settings-fields"); const fields = [["appendix_1_title", "Приложение 1: заголовок"], ["appendix_1_subtitle", "Приложение 1: подзаголовок"], ["appendix_2_title", "Приложение 2: заголовок"]];
  const controls = fields.map(([key, labelText]) => labeledInput(labelText, `report-${key}`, state.report_settings[key]));
  state.report_settings.appendix_1_columns.forEach((value, index) => controls.push(labeledInput(`Приложение 1: столбец ${index + 1}`, `report-app1-col-${index}`, value)));
  state.report_settings.appendix_2_columns.forEach((value, index) => controls.push(labeledInput(`Приложение 2: столбец ${index + 1}`, `report-app2-col-${index}`, value)));
  reportFields.replaceChildren(...controls);
  byId("card-label-fields").replaceChildren(...LABEL_KEYS.map(key => labeledInput(key, `card-label-${key}`, state.card_labels[key])));
  byId("custom-fields-list").replaceChildren(...state.custom_fields.map(field => { const row = node("div", undefined, "custom-item"); row.append(node("span", field.label)); const rename = node("button", "Переименовать", "link-button"); rename.type = "button"; rename.dataset.rename = field.id; const remove = node("button", "Удалить", "link-button"); remove.type = "button"; remove.dataset.remove = field.id; row.append(rename, remove); return row; }));
}
function labeledInput(labelText, id, value) { const label = node("label", labelText); const input = document.createElement("input"); input.id = id; input.value = value; input.required = true; label.append(input); return label; }
function fillTargetSettings(id) { const target = state.targets.find(item => item.id === id); if (!target) return; byId("target-id").value = target.id; byId("target-code").value = target.code; byId("target-row").value = target.report_row; byId("target-name").value = target.name; byId("target-report-name").value = target.report_name; byId("target-section").value = target.section; byId("target-keywords").value = target.keywords.join(", "); }
function newTargetForm() { selectedTargetId = null; byId("target-settings-form").reset(); byId("target-id").value = ""; byId("target-code").value = `ЦП${state.targets.length + 1}`; byId("target-row").value = String(state.targets.length + 1).padStart(2, "0"); byId("target-name").value = "Новый целевой показатель"; byId("target-report-name").value = "Новый целевой показатель"; byId("target-section").value = "НОВЫЙ РАЗДЕЛ"; document.querySelectorAll(".setting-item").forEach(item => item.classList.remove("active")); }

function renderPress() {
  const current = byId("press-event").value; const events = [...state.events].sort((a, b) => (parseDate(a.date) || Infinity) - (parseDate(b.date) || Infinity)); replaceSelect(byId("press-event"), events.length ? events.map(event => [event.id, `${event.date} | ${event.name}`]) : [["", "Сначала добавьте мероприятие"]], events.some(event => event.id === current) ? current : events[0]?.id || "");
  byId("api-url").value = state.press_release_settings.base_url; byId("api-model").value = state.press_release_settings.model; byId("press-instruction").value = state.press_release_settings.instruction;
  const remembered = localStorage.getItem(API_KEY_LOCAL); byId("remember-key").checked = Boolean(remembered); if (!byId("api-key").value) byId("api-key").value = remembered || sessionStorage.getItem(API_KEY_SESSION) || "";
  loadPressEvent();
}
function loadPressEvent() { const event = state.events.find(item => item.id === byId("press-event").value); if (!event) { byId("press-context").textContent = "Нет мероприятий"; byId("press-description").value = ""; byId("press-text").value = ""; return; } const codes = state.targets.filter(target => event.target_ids.includes(target.id)).map(target => target.code); byId("press-context").textContent = `${event.date} ${event.time} | ${event.name} | ЦП: ${codes.join(", ") || "не определен"}`; byId("press-description").value = event.description || "Краткое описание пока не заполнено"; byId("press-text").value = event.press_release || ""; }
function saveApiSettings() { state.press_release_settings = {base_url: byId("api-url").value.trim(), model: byId("api-model").value.trim(), instruction: byId("press-instruction").value.trim()}; const key = byId("api-key").value.trim(); sessionStorage.setItem(API_KEY_SESSION, key); if (byId("remember-key").checked) localStorage.setItem(API_KEY_LOCAL, key); else localStorage.removeItem(API_KEY_LOCAL); save(); }
function pressPrompt(event) { const labels = state.card_labels; const lines = LABEL_KEYS.map(key => `${labels[key]}: ${event[key] ?? ""}`); for (const field of state.custom_fields) lines.push(`${field.label}: ${event.custom_fields[field.id] || ""}`); return `Сформируй пресс-релиз только на основании следующих данных:\n${lines.join("\n")}`; }

function ensureDocx() { if (!window.docx) { alert("Библиотека DOCX не загрузилась. Проверьте подключение к интернету и блокировщики CDN."); return false; } return true; }
function docParagraph(text, options = {}) { return new docx.Paragraph({text: String(text ?? ""), ...options}); }
function docCell(text, bold = false) { return new docx.TableCell({children: [new docx.Paragraph({children: [new docx.TextRun({text: String(text ?? ""), bold})], alignment: docx.AlignmentType.CENTER})], verticalAlign: docx.VerticalAlign.CENTER}); }
async function exportAppendix1() { if (!ensureDocx()) return; const month = Number(byId("report-month").value); const settings = state.report_settings; const rows = [new docx.TableRow({children: settings.appendix_1_columns.map(value => docCell(value, true))}), new docx.TableRow({children: ["1", "2", "3"].map(value => docCell(value))})]; for (const target of sortedTargets()) rows.push(new docx.TableRow({children: [docCell(target.report_name), docCell(target.report_row), docCell(calculate(target)[month].actual_cumulative, true)]})); const documentFile = new docx.Document({sections: [{properties: {page: {margin: {top: 680, right: 680, bottom: 680, left: 680}}}, children: [docParagraph(settings.appendix_1_title, {heading: docx.HeadingLevel.HEADING_1, alignment: docx.AlignmentType.CENTER}), docParagraph(`${settings.appendix_1_subtitle} за ${MONTHS[month].toLowerCase()} ${state.year} года\n${state.organization}`, {alignment: docx.AlignmentType.CENTER}), new docx.Table({rows, width: {size: 100, type: docx.WidthType.PERCENTAGE}})]}]}); download(await docx.Packer.toBlob(documentFile), `Приложение_1_${state.year}_${String(month + 1).padStart(2, "0")}.docx`); }
async function exportAppendix2() { if (!ensureDocx()) return; const month = Number(byId("report-month").value); const settings = state.report_settings; const [start, end] = periodBounds(state.year, month); const children = [docParagraph(settings.appendix_2_title, {heading: docx.HeadingLevel.HEADING_1, alignment: docx.AlignmentType.CENTER}), docParagraph(`${state.organization}\nза ${MONTHS[month].toLowerCase()} ${state.year} года (${formatDate(start)}–${formatDate(end)})`, {alignment: docx.AlignmentType.CENTER})]; const events = eventsForMonth(month); for (const target of sortedTargets()) { children.push(new docx.Table({rows: [new docx.TableRow({children: [docCell(target.section, true)]})], width: {size: 100, type: docx.WidthType.PERCENTAGE}})); const selected = events.filter(event => event.target_ids.includes(target.id)); const rows = [new docx.TableRow({children: settings.appendix_2_columns.map(value => docCell(value, true))})]; if (selected.length) selected.forEach((event, index) => rows.push(new docx.TableRow({children: [index + 1, event.date, event.name, event.participants ?? "", event.link].map(value => docCell(value))}))); else rows.push(new docx.TableRow({children: Array(5).fill(0).map(() => docCell(""))})); children.push(new docx.Table({rows, width: {size: 100, type: docx.WidthType.PERCENTAGE}}), docParagraph("")); }
  const documentFile = new docx.Document({sections: [{properties: {page: {size: {orientation: docx.PageOrientation.LANDSCAPE}, margin: {top: 680, right: 680, bottom: 680, left: 680}}}, children}]}); download(await docx.Packer.toBlob(documentFile), `Приложение_2_${state.year}_${String(month + 1).padStart(2, "0")}.docx`);
}
function exportXlsx() { if (!window.XLSX) { alert("Библиотека XLSX не загрузилась. Проверьте подключение к интернету и блокировщики CDN."); return; } const book = XLSX.utils.book_new(); const summary = [[`Целевые показатели на ${state.year} год`], ["Направление", "Месяц", "План нарастающим", "Разница между нарастающими", "Реальный охват в месяц", "Реальный охват нарастающим", "Разница: необходимо - сделано", "Необходимый охват с остатком"]]; for (const target of state.targets) for (const row of calculate(target)) summary.push([target.name, MONTHS[row.month], row.cumulative_plan, row.monthly_plan, row.actual, row.actual_cumulative, row.balance, row.required]); const summarySheet = XLSX.utils.aoa_to_sheet(summary); summarySheet["!cols"] = [48, 14, 20, 24, 21, 24, 25, 27].map(wch => ({wch})); XLSX.utils.book_append_sheet(book, summarySheet, "Целевые показатели");
  for (let month = 0; month < 12; month++) { const [start, end] = periodBounds(state.year, month); const headers = [state.card_labels.date, state.card_labels.time, state.card_labels.place, state.card_labels.name, state.card_labels.description, "Соответствие ЦП", state.card_labels.participants, state.card_labels.link, "Коды ЦП", ...state.custom_fields.map(field => field.label)]; const rows = [[`Учет мероприятий за ${MONTHS[month].toLowerCase()} ${state.year} года (${formatDate(start)}–${formatDate(end)})`], headers]; for (const event of eventsForMonth(month)) { const targets = state.targets.filter(target => event.target_ids.includes(target.id)); rows.push([event.date, event.time, event.place, event.name, event.description, targets.map(target => target.name).join(", "), event.participants ?? "", event.link, targets.map(target => target.code).join(", "), ...state.custom_fields.map(field => event.custom_fields[field.id] || "")]); } const sheet = XLSX.utils.aoa_to_sheet(rows); sheet["!cols"] = [13, 13, 30, 35, 55, 45, 16, 35, 14, ...state.custom_fields.map(() => 25)].map(wch => ({wch})); sheet["!freeze"] = {xSplit: 0, ySplit: 2}; XLSX.utils.book_append_sheet(book, sheet, MONTHS[month]); }
  XLSX.writeFile(book, `Сводные_данные_${state.year}.xlsx`);
}
async function exportPressDocx() { const event = state.events.find(item => item.id === byId("press-event").value); const text = byId("press-text").value.trim(); if (!event || !text || !ensureDocx()) { if (!text) alert("Введите или сформируйте текст пресс-релиза."); return; } const paragraphs = text.split(/\n\s*\n/).filter(Boolean).map((part, index) => docParagraph(part.trim(), {alignment: index ? docx.AlignmentType.JUSTIFIED : docx.AlignmentType.CENTER, heading: index ? undefined : docx.HeadingLevel.HEADING_2})); const documentFile = new docx.Document({sections: [{children: [docParagraph("ПРЕСС-РЕЛИЗ", {heading: docx.HeadingLevel.HEADING_1, alignment: docx.AlignmentType.CENTER}), docParagraph(state.organization, {alignment: docx.AlignmentType.CENTER}), ...paragraphs, docParagraph(`Дата мероприятия: ${event.date}\nСсылка: ${event.link}`)]}]}); const safe = (event.name || "мероприятие").replace(/[<>:"/\\|?*]+/g, "_").slice(0, 80); download(await docx.Packer.toBlob(documentFile), `Пресс-релиз_${safe}.docx`); }

function bind() {
  document.querySelectorAll(".nav-item").forEach(button => button.addEventListener("click", () => { document.querySelectorAll(".nav-item").forEach(item => item.classList.toggle("active", item === button)); document.querySelectorAll(".view").forEach(view => view.classList.toggle("active", view.id === `view-${button.dataset.view}`)); byId("main-nav").classList.remove("open"); byId("nav-toggle").setAttribute("aria-expanded", "false"); window.scrollTo(0, 0); }));
  byId("nav-toggle").addEventListener("click", () => { const open = byId("main-nav").classList.toggle("open"); byId("nav-toggle").setAttribute("aria-expanded", String(open)); });
  byId("org-form").addEventListener("submit", event => { event.preventDefault(); const year = Number(byId("report-year").value); if (year < 2020 || year > 2100) return alert("Укажите год от 2020 до 2100."); state.organization = byId("organization").value.trim(); state.year = year; save("Реквизиты сохранены"); renderAll(); });
  byId("export-json").addEventListener("click", () => download(new Blob([JSON.stringify(state, null, 2)], {type: "application/json"}), `МИН_МОЛ_${state.year}.json`));
  byId("import-json").addEventListener("change", async event => { const file = event.target.files[0]; if (!file) return; try { const imported = normalizeData(JSON.parse(await file.text())); if (!confirm("Импорт заменит текущие данные. Продолжить?")) return; state = imported; save("Данные импортированы"); renderEventFormFields(); clearEventForm(); renderAll(); } catch (error) { alert(`Не удалось импортировать JSON: ${error.message}`); } finally { event.target.value = ""; } });
  byId("reset-data").addEventListener("click", () => { if (!confirm("Удалить все локальные данные и вернуть пять исходных показателей?")) return; state = defaultData(); localStorage.removeItem(STORAGE_KEY); save("Данные сброшены"); renderEventFormFields(); clearEventForm(); renderAll(); });
  byId("plan-target").addEventListener("change", updatePlanInput); byId("plan-month").addEventListener("change", updatePlanInput);
  byId("plan-form").addEventListener("submit", event => { event.preventDefault(); const target = state.targets.find(item => item.id === byId("plan-target").value); const month = Number(byId("plan-month").value); const value = Number(byId("plan-value").value); if (!Number.isInteger(value) || value < 0) return alert("План должен быть целым неотрицательным числом."); if (month && value < target.plan[month - 1] && !confirm("План меньше значения предыдущего месяца. Все равно сохранить?")) return; target.plan[month] = value; save("План сохранен"); renderTargets(); renderOverview(); });
  byId("targets-table").addEventListener("click", event => { const row = event.target.closest("tr[data-target]"); if (!row) return; byId("plan-target").value = row.dataset.target; byId("plan-month").value = row.dataset.month; updatePlanInput(); window.scrollTo({top: 0, behavior: "smooth"}); });
  byId("event-month-filter").addEventListener("change", renderEvents); byId("event-search").addEventListener("input", renderEvents); byId("new-event").addEventListener("click", clearEventForm); byId("clear-event").addEventListener("click", clearEventForm); byId("classify-now").addEventListener("click", classifyForm);
  byId("events-table").addEventListener("click", event => { const row = event.target.closest("tr[data-id]"); if (row) loadEvent(row.dataset.id); });
  byId("event-form").addEventListener("submit", event => { event.preventDefault(); const date = parseDate(byId("event-date").value); if (!date) return alert("Введите корректную дату в формате ДД.ММ.ГГГГ."); if (!byId("event-name").value.trim()) return alert("Укажите название мероприятия."); const participantText = byId("event-participants").value.trim(); if (participantText && (!/^\d+$/.test(participantText))) return alert("Количество участников должно быть целым неотрицательным числом."); const id = byId("event-id").value || uid("event"); const previous = state.events.find(item => item.id === id); const targetIds = byId("auto-classify").checked ? classifyForm() : [...byId("event-target-checks").querySelectorAll("input:checked")].map(input => input.value); const item = {id, date: formatDate(date), time: byId("event-time").value.trim(), place: byId("event-place").value.trim(), name: byId("event-name").value.trim(), description: byId("event-description").value.trim(), participants: participantText ? Number(participantText) : null, link: byId("event-link").value.trim(), target_ids: targetIds, auto_classify: byId("auto-classify").checked, custom_fields: Object.fromEntries([...byId("custom-event-fields").querySelectorAll("[data-custom]")].map(input => [input.dataset.custom, input.value.trim()])), press_release: previous?.press_release || ""}; const index = state.events.findIndex(existing => existing.id === id); if (index >= 0) state.events[index] = item; else state.events.push(item); byId("event-id").value = id; save(eventComplete(item) ? "Мероприятие готово" : "Мероприятие сохранено как черновик"); renderAll(); loadEvent(id); });
  byId("delete-event").addEventListener("click", () => { const id = byId("event-id").value; if (!id) return alert("Сначала выберите мероприятие."); if (!confirm("Удалить мероприятие без возможности отмены?")) return; state.events = state.events.filter(item => item.id !== id); save("Мероприятие удалено"); renderEventFormFields(); clearEventForm(); renderAll(); });
  byId("report-month").addEventListener("change", () => { updateReportPeriod(); renderPreview(); }); document.querySelectorAll("[data-preview]").forEach(button => button.addEventListener("click", () => { activePreview = button.dataset.preview; document.querySelectorAll("[data-preview]").forEach(item => item.classList.toggle("active", item === button)); renderPreview(); }));
  byId("export-app1").addEventListener("click", exportAppendix1); byId("export-app2").addEventListener("click", exportAppendix2); byId("export-xlsx").addEventListener("click", exportXlsx); byId("export-all").addEventListener("click", async () => { await exportAppendix1(); await new Promise(resolve => setTimeout(resolve, 350)); await exportAppendix2(); await new Promise(resolve => setTimeout(resolve, 350)); exportXlsx(); toast("Запущена загрузка трех отчетов"); });
  document.querySelectorAll("[data-formtab]").forEach(button => button.addEventListener("click", () => { document.querySelectorAll("[data-formtab]").forEach(item => item.classList.toggle("active", item === button)); document.querySelectorAll(".formtab").forEach(tab => tab.classList.toggle("active", tab.id === button.dataset.formtab)); }));
  byId("target-settings-list").addEventListener("click", event => { const item = event.target.closest("[data-id]"); if (!item) return; selectedTargetId = item.dataset.id; renderForms(); }); byId("add-target").addEventListener("click", newTargetForm);
  byId("target-settings-form").addEventListener("submit", event => { event.preventDefault(); const id = byId("target-id").value || uid("target"); const values = {id, code: byId("target-code").value.trim(), report_row: byId("target-row").value.trim(), name: byId("target-name").value.trim(), report_name: byId("target-report-name").value.trim(), section: byId("target-section").value.trim(), keywords: byId("target-keywords").value.split(",").map(word => word.trim().toLowerCase()).filter(Boolean)}; const existing = state.targets.find(target => target.id === id); if (existing) Object.assign(existing, values); else state.targets.push({...values, plan: Array(12).fill(0)}); selectedTargetId = id; save("Показатель сохранен"); renderAll(); });
  byId("delete-target").addEventListener("click", () => { const id = byId("target-id").value; if (!id) return; if (state.targets.length === 1) return alert("Должен остаться хотя бы один показатель."); if (!confirm("Удалить показатель из планов и всех карточек?")) return; state.targets = state.targets.filter(target => target.id !== id); state.events.forEach(item => item.target_ids = item.target_ids.filter(targetId => targetId !== id)); selectedTargetId = state.targets[0].id; save("Показатель удален"); renderAll(); });
  byId("report-settings").addEventListener("submit", event => { event.preventDefault(); for (const key of ["appendix_1_title", "appendix_1_subtitle", "appendix_2_title"]) state.report_settings[key] = byId(`report-${key}`).value.trim(); state.report_settings.appendix_1_columns = [0,1,2].map(index => byId(`report-app1-col-${index}`).value.trim()); state.report_settings.appendix_2_columns = [0,1,2,3,4].map(index => byId(`report-app2-col-${index}`).value.trim()); save("Формы отчетов сохранены"); renderReports(); });
  byId("card-labels-form").addEventListener("submit", event => { event.preventDefault(); LABEL_KEYS.forEach(key => state.card_labels[key] = byId(`card-label-${key}`).value.trim()); save("Названия полей сохранены"); renderEventFormFields(); clearEventForm(); renderAll(); });
  byId("add-custom-field").addEventListener("click", () => { const label = prompt("Название дополнительного поля:"); if (!label?.trim()) return; state.custom_fields.push({id: uid("field"), label: label.trim()}); save("Поле добавлено"); renderEventFormFields(); clearEventForm(); renderAll(); });
  byId("custom-fields-list").addEventListener("click", event => { const rename = event.target.closest("[data-rename]"); const remove = event.target.closest("[data-remove]"); if (rename) { const field = state.custom_fields.find(item => item.id === rename.dataset.rename); const label = prompt("Новое название:", field.label); if (label?.trim()) { field.label = label.trim(); save("Поле переименовано"); renderAll(); } } if (remove && confirm("Удалить поле и его значения из всех карточек?")) { state.custom_fields = state.custom_fields.filter(item => item.id !== remove.dataset.remove); state.events.forEach(item => delete item.custom_fields[remove.dataset.remove]); save("Поле удалено"); renderEventFormFields(); clearEventForm(); renderAll(); } });
  byId("press-event").addEventListener("change", loadPressEvent); byId("remember-key").addEventListener("change", saveApiSettings); byId("clear-key").addEventListener("click", () => { localStorage.removeItem(API_KEY_LOCAL); sessionStorage.removeItem(API_KEY_SESSION); byId("api-key").value = ""; byId("remember-key").checked = false; toast("API-ключ удален"); });
  byId("generate-press").addEventListener("click", async () => { const event = state.events.find(item => item.id === byId("press-event").value); const key = byId("api-key").value.trim(); const url = byId("api-url").value.trim(); const model = byId("api-model").value.trim(); const instruction = byId("press-instruction").value.trim(); if (!event) return alert("Выберите мероприятие."); if (!key) return alert("Введите API-ключ."); if (!url.startsWith("https://") || !model || !instruction) return alert("Укажите HTTPS URL, модель и инструкцию."); saveApiSettings(); const button = byId("generate-press"); button.disabled = true; button.textContent = "Формирование…"; try { const response = await fetch(url, {method: "POST", headers: {Authorization: `Bearer ${key}`, "Content-Type": "application/json"}, body: JSON.stringify({model, messages: [{role: "system", content: instruction}, {role: "user", content: pressPrompt(event)}], stream: false, temperature: .5})}); if (!response.ok) throw new Error(`HTTP ${response.status}: ${(await response.text()).slice(0, 700)}`); const result = await response.json(); const content = result?.choices?.[0]?.message?.content?.trim(); if (!content) throw new Error("API не вернул текст в choices[0].message.content"); event.press_release = content; byId("press-text").value = content; save("Пресс-релиз сформирован и сохранен"); } catch (error) { alert(`Не удалось выполнить запрос: ${error.message}\n\nЕсли в консоли браузера указана CORS policy, сервер API не разрешает прямые запросы с GitHub Pages. Исправить это на стороне страницы невозможно: нужен разрешенный origin или собственный прокси.`); } finally { button.disabled = false; button.textContent = "Сгенерировать"; } });
  byId("save-press").addEventListener("click", () => { const event = state.events.find(item => item.id === byId("press-event").value); if (!event) return alert("Выберите мероприятие."); event.press_release = byId("press-text").value.trim(); saveApiSettings(); save("Текст пресс-релиза сохранен"); });
  byId("copy-press").addEventListener("click", async () => { const text = byId("press-text").value.trim(); if (!text) return; try { await navigator.clipboard.writeText(text); toast("Текст скопирован"); } catch { byId("press-text").select(); document.execCommand("copy"); toast("Текст скопирован"); } }); byId("export-press").addEventListener("click", exportPressDocx);
}

state = load();
renderEventFormFields();
bind();
clearEventForm();
renderAll();
