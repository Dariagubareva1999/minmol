"use strict";

const institutions = [
  ["Министерство культуры ЛНР", "Региональный орган управления культурой"],
  ["Луганская академическая филармония", "г. Луганск"],
  ["Луганский государственный академический русский драматический театр имени П. Луспекаева", "г. Луганск"],
  ["Луганский академический театр кукол", "г. Луганск"],
  ["Луганский государственный цирк", "г. Луганск"],
  ["Луганский художественный музей", "г. Луганск"],
  ["Луганский краеведческий музей", "г. Луганск"],
  ["Государственный музей истории города Луганска", "г. Луганск"],
  ["Луганская республиканская универсальная научная библиотека имени М. Горького", "г. Луганск"],
  ["Луганская республиканская библиотека для детей", "г. Луганск"],
  ["Луганский государственный институт культуры и искусств", "г. Луганск"],
  ["Станично-Луганский дворец культуры", "пгт Станица Луганская"],
  ["Алчевский городской Дворец культуры", "г. Алчевск"],
  ["Краснодонский городской Дворец культуры имени «Молодой гвардии»", "г. Краснодон"],
  ["Свердловский городской Дворец культуры имени 50-летия Победы", "г. Свердловск"],
  ["Республиканский дворец культуры имени В. Даля", "ЛНР"]
];
const key = "feedback-book.v1";
const $ = id => document.getElementById(id);
const escape = value => String(value).replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#039;"}[char]));
const read = () => { try { return JSON.parse(localStorage.getItem(key)) || []; } catch { return []; } };
const save = data => localStorage.setItem(key, JSON.stringify(data));

function fillInstitutions() {
  const options = institutions.map(([name, place]) => `<option value="${escape(name)}">${escape(name)} — ${escape(place)}</option>`).join("");
  $("institution").innerHTML = `<option value="" disabled selected>Выберите учреждение</option>${options}`;
  $("filter").innerHTML += institutions.map(([name]) => `<option value="${escape(name)}">${escape(name)}</option>`).join("");
}
function render() {
  const data = read(); const filter = $("filter").value;
  const published = data.filter(item => item.published !== false);
  $("count").textContent = published.length;
  const shown = filter === "all" ? published : published.filter(item => item.institution === filter);
  $("message-list").innerHTML = shown.length ? shown.slice().reverse().map(item => `<article class="message"><header><span>${escape(item.institution)}</span><span>${escape(item.date || "Дата не указана")}</span></header><h3><span class="tag">${escape(item.type)}</span> · ${escape(item.topic)}</h3><p>${escape(item.message)}</p></article>`).join("") : `<div class="empty">В этой категории пока нет открытых обращений.</div>`;
}
function toast(message) { $("toast").textContent = message; $("toast").classList.add("show"); setTimeout(() => $("toast").classList.remove("show"), 3200); }

fillInstitutions(); render();
$("message").addEventListener("input", event => $("length").textContent = event.target.value.length);
$("filter").addEventListener("change", render);
$("accessibility").addEventListener("click", () => document.body.classList.toggle("large-text"));
const modal = $("admin-modal");
function adminList() {
  const items = read();
  $("admin-list").innerHTML = items.length ? items.slice().reverse().map((item, index) => `<article class="admin-item"><b>${escape(item.institution)}</b><small>${escape(item.type)} · ${escape(item.topic)}</small><p>${escape(item.message)}</p><button type="button" data-remove="${items.length - 1 - index}">Удалить</button></article>`).join("") : `<p class="privacy">Обращений пока нет.</p>`;
  document.querySelectorAll("[data-remove]").forEach(button => button.addEventListener("click", () => { const items = read(); items.splice(Number(button.dataset.remove), 1); save(items); adminList(); render(); toast("Обращение удалено"); }));
}
$("admin-open").addEventListener("click", () => { modal.classList.add("show"); modal.setAttribute("aria-hidden", "false"); $("admin-login").hidden = false; $("admin-panel").classList.remove("show"); });
$("admin-close").addEventListener("click", () => { modal.classList.remove("show"); modal.setAttribute("aria-hidden", "true"); });
$("admin-login").addEventListener("submit", event => { event.preventDefault(); if ($("admin-login-name").value === "admin" && $("admin-password").value === "admin123") { event.target.hidden = true; $("admin-panel").classList.add("show"); adminList(); } else toast("Неверный логин или пароль"); });
$("admin-logout").addEventListener("click", () => { $("admin-panel").classList.remove("show"); $("admin-login").hidden = false; $("admin-login").reset(); });
$("feedback-form").addEventListener("submit", event => {
  event.preventDefault();
  const message = $("message").value.trim();
  if (message.length < 15) { toast("Сообщение должно содержать не менее 15 символов"); $("message").focus(); return; }
  const data = read(); const item = {institution: $("institution").value, type: document.querySelector("input[name=type]:checked").value, topic: $("topic").value, date: $("date").value, message, published: $("publish").checked, created: new Date().toISOString()};
  data.push(item); save(data); event.target.reset(); $("institution").selectedIndex = 0; $("length").textContent = "0"; render(); toast("Обращение принято. Спасибо за открытость!"); location.hash = "messages";
});
