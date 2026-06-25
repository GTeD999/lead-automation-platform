#!/usr/bin/env python3
import hashlib
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Optional
from urllib.parse import quote, urlparse


PHONE_RE = re.compile(r"(?:\+7|8|7)?[\s\-\(\)]*\d{3}[\s\-\(\)]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}")
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b", re.IGNORECASE)
TELEGRAM_RE = re.compile(r"(?:https?://t\.me/|t\.me/|(?<![A-Za-z0-9._%+\-])@)([A-Za-z0-9_]{5,32})")
VK_RE = re.compile(r"https?://(?:www\.)?vk\.com/[A-Za-z0-9_.]+", re.IGNORECASE)
TG_URL_RE = re.compile(r"(?:https?://t\.me/|t\.me/|@)([A-Za-z0-9_]{5,64})")
VK_SOURCE_RE = re.compile(r"(?:https?://)?(?:www\.)?vk\.com/([A-Za-z0-9_.]+)", re.IGNORECASE)
URL_RE = re.compile(r"https?://[^\s,]+", re.IGNORECASE)

INTENT_KEYWORDS = {
    "buy": ["куплю", "купить", "покупка", "приобрету"],
    "sell": ["продам", "продать", "продаю"],
    "rent": ["сниму", "арендую", "ищу помещение", "нужен офис", "нужен склад", "ищу квартиру"],
    "lease_out": ["сдам", "сдается", "сдаю", "аренда от собственника"],
    "invest": ["инвест", "доходность", "готовый арендный бизнес", "габ"],
}
COMMERCIAL_KEYWORDS = ["коммерчес", "офис", "склад", "помещение", "ритейл", "магазин", "псн", "общепит", "кофей", "производство", "габ"]
RESIDENTIAL_KEYWORDS = ["квартир", "дом", "таунхаус", "апартамент", "студ", "жк", "комнат"]

SUPABASE_URL = os.environ.get("SUPABASE_URL", "http://kong:8000").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
PORT = int(os.environ.get("PORT", "8080"))
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_NOTIFY_CHAT_ID = os.environ.get("TELEGRAM_NOTIFY_CHAT_ID", "").strip()
COLLECTOR_RUN_COMMAND = os.environ.get("COLLECTOR_RUN_COMMAND", "").strip()

PLATFORM_LABELS = {
    "telegram": "Telegram",
    "vk": "VK",
    "classified": "Доски объявлений",
    "website": "Сайты и RSS",
    "map": "Карты и справочники",
    "partner_api": "Платные API",
    "other": "Другое",
}


HTML = """<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Novactiv Leads</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f3ee;
      --panel: #fffdf9;
      --panel-2: #f0ebe3;
      --ink: #171511;
      --muted: #716b61;
      --soft: #e9dfcf;
      --line: #ded5c8;
      --accent: #1f6f5f;
      --accent-2: #1a4d7a;
      --accent-dark: #154f45;
      --gold: #a8792a;
      --danger: #a33a2a;
      --shadow: 0 18px 48px rgba(44, 34, 20, 0.10);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--ink);
    }
    a { color: var(--accent-2); text-decoration: none; }
    a:hover { text-decoration: underline; }
    .app-shell {
      min-height: 100vh;
    }
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 22px 32px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
      position: sticky;
      top: 0;
      z-index: 5;
    }
    .brand { display: grid; gap: 2px; }
    h1 {
      margin: 0;
      font-size: 22px;
      font-weight: 760;
      letter-spacing: 0;
    }
    .brand-sub {
      color: var(--muted);
      font-size: 13px;
    }
    main {
      display: grid;
      gap: 20px;
      padding: 24px;
      max-width: 1440px;
      margin: 0 auto;
    }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }
    .section-inner { padding: 18px; }
    .hero {
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.65fr);
      min-height: 238px;
      overflow: hidden;
      background:
        linear-gradient(112deg, rgba(23, 21, 17, 0.96), rgba(31, 111, 95, 0.90)),
        url("https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1800&q=75");
      background-size: cover;
      background-position: center;
      color: #fffdf9;
    }
    .hero-copy {
      display: grid;
      align-content: center;
      gap: 18px;
      padding: 32px;
    }
    .hero h2 {
      margin: 0;
      max-width: 780px;
      font-size: clamp(30px, 4vw, 58px);
      line-height: 0.98;
      letter-spacing: 0;
    }
    .hero p {
      margin: 0;
      max-width: 690px;
      color: rgba(255, 253, 249, 0.78);
      font-size: 16px;
      line-height: 1.55;
    }
    .hero-side {
      display: grid;
      align-content: end;
      gap: 12px;
      padding: 24px;
      border-left: 1px solid rgba(255,255,255,0.16);
      background: rgba(255,255,255,0.06);
      backdrop-filter: blur(10px);
    }
    .hero-action {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
    }
    .metric {
      border: 1px solid rgba(255,255,255,0.16);
      border-radius: 8px;
      padding: 14px;
      background: rgba(255,255,255,0.08);
    }
    .metric strong {
      display: block;
      font-size: 30px;
      line-height: 1;
      letter-spacing: 0;
    }
    .metric span {
      display: block;
      margin-top: 6px;
      color: rgba(255,253,249,0.68);
      font-size: 12px;
    }
    .workspace {
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) minmax(360px, 0.65fr);
      gap: 20px;
      align-items: start;
    }
    .stack { display: grid; gap: 20px; }
    h2 {
      margin: 0;
      font-size: 17px;
      letter-spacing: 0;
    }
    .section-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 16px 18px;
      border-bottom: 1px solid var(--line);
      background: #fffaf2;
      border-radius: 8px 8px 0 0;
    }
    .section-kicker {
      color: var(--muted);
      font-size: 12px;
      margin-top: 4px;
    }
    label {
      display: block;
      font-size: 13px;
      color: var(--muted);
      margin: 0 0 8px;
      font-weight: 650;
    }
    input, textarea, select {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 0 13px;
      font: inherit;
      font-size: 14px;
      background: #fff;
      color: var(--ink);
      outline: none;
      transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    input, select {
      height: 44px;
      line-height: 44px;
    }
    select {
      appearance: none;
      background-image:
        linear-gradient(45deg, transparent 50%, var(--muted) 50%),
        linear-gradient(135deg, var(--muted) 50%, transparent 50%);
      background-position:
        calc(100% - 18px) 19px,
        calc(100% - 13px) 19px;
      background-size: 5px 5px, 5px 5px;
      background-repeat: no-repeat;
      padding-right: 34px;
    }
    input:focus, textarea:focus, select:focus {
      border-color: rgba(31, 111, 95, 0.55);
      box-shadow: 0 0 0 3px rgba(31, 111, 95, 0.12);
    }
    textarea {
      min-height: 140px;
      padding: 12px 13px;
      resize: vertical;
      line-height: 1.45;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
      margin-top: 14px;
    }
    .grid:first-child { margin-top: 0; }
    .grid + label,
    input + .grid,
    select + .grid,
    textarea + .grid {
      margin-top: 14px;
    }
    .actions {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 14px;
    }
    button {
      appearance: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      min-height: 42px;
      min-width: 142px;
      border: 1px solid transparent;
      border-radius: 6px;
      background: var(--accent);
      color: #fff;
      padding: 0 16px;
      font: inherit;
      font-size: 14px;
      font-weight: 650;
      line-height: 1;
      white-space: nowrap;
      cursor: pointer;
      box-shadow: 0 10px 20px rgba(31, 111, 95, 0.16);
      transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease, box-shadow 0.15s ease;
    }
    button:hover { background: var(--accent-dark); }
    button.secondary {
      background: #ece5da;
      border-color: #dfd4c4;
      color: var(--ink);
      box-shadow: none;
    }
    button.secondary:hover { background: #e1d7c8; }
    button.ghost {
      color: #fffdf9;
      background: rgba(255,255,255,0.14);
      border-color: rgba(255,255,255,0.20);
      box-shadow: none;
    }
    button.ghost:hover { background: rgba(255,255,255,0.22); }
    button.compact {
      min-height: 34px;
      min-width: 116px;
      padding: 0 12px;
      font-size: 12px;
    }
    button:disabled {
      opacity: 0.55;
      cursor: not-allowed;
    }
    .status {
      min-height: 22px;
      font-size: 14px;
      color: var(--muted);
    }
    .status.error { color: var(--danger); }
    .status.ok { color: var(--accent-dark); }
    .preview {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 8px;
    }
    .manual-grid {
      display: grid;
      grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
      gap: 14px;
    }
    .row {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      background: #fffaf2;
    }
    .key {
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 4px;
    }
    .value {
      min-height: 20px;
      word-break: break-word;
    }
    .pill {
      display: inline-flex;
      align-items: center;
      max-width: 100%;
      padding: 5px 9px;
      margin: 0 6px 6px 0;
      border-radius: 999px;
      background: #e9f4ef;
      color: #164f45;
      font-size: 13px;
      overflow-wrap: anywhere;
    }
    .lead-list {
      display: grid;
      gap: 12px;
      max-height: 640px;
      overflow: auto;
      padding: 16px 18px 18px;
    }
    .lead-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      background: #fffdf9;
    }
    .lead-head {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      align-items: flex-start;
      margin-bottom: 8px;
    }
    .lead-title {
      font-weight: 760;
      overflow-wrap: anywhere;
    }
    .lead-meta {
      color: var(--muted);
      font-size: 12px;
    }
    .lead-text {
      color: #344054;
      font-size: 13px;
      line-height: 1.4;
      max-height: 64px;
      overflow: hidden;
    }
    .source-tools {
      display: grid;
      grid-template-columns: minmax(280px, 0.75fr) minmax(360px, 1.25fr);
      gap: 14px;
      padding: 18px;
    }
    .field-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
      align-items: end;
    }
    .field-grid .actions {
      min-height: 44px;
      margin-top: 0;
    }
    .source-tools textarea { min-height: 142px; }
    .query-list {
      display: grid;
      grid-template-columns: repeat(5, minmax(170px, 1fr));
      gap: 10px;
      padding: 16px 18px 18px;
      overflow-x: auto;
    }
    .query-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: #f8f2e8;
      min-height: 118px;
      display: grid;
      align-content: space-between;
    }
    .source-list {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 12px;
      max-height: 560px;
      overflow: auto;
      padding: 18px;
    }
    .source-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      background: #fffdf9;
      display: grid;
      gap: 10px;
      align-content: start;
    }
    .source-card.monitoring {
      border-color: rgba(31, 111, 95, 0.45);
      background: #f4fbf7;
    }
    .source-state {
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      border-radius: 999px;
      padding: 0 9px;
      background: #f1ece3;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
    }
    .source-state.monitoring {
      background: #dff2e9;
      color: #164f45;
    }
    .source-card.rejected {
      opacity: 0.72;
    }
    .source-link {
      display: block;
      overflow-wrap: anywhere;
      font-size: 13px;
    }
    .source-card .actions {
      margin-top: 0;
      justify-content: flex-start;
    }
    details {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      overflow: hidden;
    }
    summary {
      cursor: pointer;
      padding: 16px 18px;
      font-weight: 760;
      list-style: none;
      background: #fffaf2;
    }
    summary::-webkit-details-marker { display: none; }
    .suggestions-panel {
      margin: 0 18px 18px;
      box-shadow: none;
      background: #fffdf9;
    }
    .suggestions-panel summary {
      background: #f8f2e8;
    }
    .status-bar {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 10px;
      flex-wrap: wrap;
    }
    .top-chip {
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 7px 10px;
      color: var(--muted);
      background: #fffaf2;
      font-size: 12px;
    }
    @media (max-width: 900px) {
      main { padding: 14px; }
      header { padding: 16px; }
      .hero, .workspace, .source-tools, .manual-grid { grid-template-columns: 1fr; }
      .hero-copy { padding: 24px; }
      .hero-side { border-left: 0; border-top: 1px solid rgba(255,255,255,0.16); }
      .stats, .preview { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .field-grid, .grid { grid-template-columns: 1fr; }
      .query-list { grid-template-columns: repeat(2, minmax(190px, 1fr)); }
    }
  </style>
</head>
<body>
  <div class="app-shell">
    <header>
      <div class="brand">
        <h1>Novactiv Leads</h1>
        <div class="brand-sub">Автопоиск контактов по рынку недвижимости</div>
      </div>
      <div class="status-bar">
        <span class="top-chip" id="topSources">Источники: 0</span>
        <span class="top-chip" id="topMonitoring">Мониторинг: 0</span>
        <span class="top-chip" id="topLeads">Лиды: 0</span>
      </div>
    </header>
    <main>
      <section class="hero">
        <div class="hero-copy">
          <div>
            <h2>Автопоиск лидов из Telegram, VK, сайтов и баз объявлений</h2>
            <p>Собираем источники, включаем мониторинг, сохраняем найденные контакты в Supabase и сразу отправляем горячие заявки в Telegram.</p>
          </div>
          <div class="hero-action">
            <button class="ghost" id="heroRefreshBtn" type="button">Обновить данные</button>
          </div>
        </div>
        <div class="hero-side">
          <div class="stats">
            <div class="metric"><strong id="metricSources">0</strong><span>источников</span></div>
            <div class="metric"><strong id="metricMonitoring">0</strong><span>в мониторинге</span></div>
            <div class="metric"><strong id="metricLeads">0</strong><span>лидов</span></div>
            <div class="metric"><strong id="metricHot">0</strong><span>с контактами</span></div>
          </div>
        </div>
      </section>
      <div class="workspace">
        <div class="stack">
          <section>
            <div class="section-head">
              <div>
                <h2>Источники мониторинга</h2>
                <div class="section-kicker">Добавьте Telegram-каналы и нажмите “В мониторинг” — сбор запустится сразу</div>
              </div>
              <button class="secondary" id="refreshSourcesBtn" type="button">Обновить</button>
            </div>
            <div class="source-tools">
              <div class="field-grid">
                <div>
                  <label for="sourceCity">Город</label>
                  <input id="sourceCity" value="Новосибирск">
                </div>
                <div>
                  <label for="sourceTopic">Тематика</label>
                  <select id="sourceTopic">
                    <option value="commercial">Коммерческая недвижимость</option>
                    <option value="residential">Жилая недвижимость</option>
                    <option value="business">Бизнес-сообщества</option>
                    <option value="owners">Собственники и арендаторы</option>
                  </select>
                </div>
                <div>
                  <label for="sourcePlatform">Канал</label>
                  <select id="sourcePlatform">
                    <option value="all">Все каналы</option>
                    <option value="telegram">Telegram</option>
                    <option value="vk">VK</option>
                    <option value="classified">Доски объявлений</option>
                    <option value="website">Сайты и RSS</option>
                    <option value="map">Карты и справочники</option>
                    <option value="partner_api">Платные API</option>
                  </select>
                </div>
                <div class="actions">
                  <button id="queryBtn" type="button">Сгенерировать запросы</button>
                  <button class="secondary" id="runCollectorBtn" type="button">Собрать сейчас</button>
                </div>
              </div>
              <div>
                <label for="sourceLinks">Новые источники</label>
                <textarea id="sourceLinks" placeholder="@telegram, https://vk.com/group, сайт, RSS, карточка 2ГИС или API-поставщик, каждый с новой строки"></textarea>
                <div class="actions">
                  <button id="importSourcesBtn" type="button">Добавить источники</button>
                  <button class="secondary" id="testTelegramBtn" type="button">Тест в Telegram</button>
                  <div class="status" id="sourceStatus"></div>
                </div>
              </div>
            </div>
            <details class="suggestions-panel" id="suggestionsPanel">
              <summary>Поисковые подсказки</summary>
              <div class="query-list" id="queryList"></div>
            </details>
            <div class="source-list" id="sourceList"></div>
          </section>
        </div>
        <div class="stack">
          <section>
            <div class="section-head">
              <div>
                <h2>Последние лиды</h2>
                <div class="section-kicker">Новые контакты из базы</div>
              </div>
              <button class="secondary" id="refreshBtn" type="button">Обновить</button>
            </div>
            <div class="lead-list" id="leadList"></div>
          </section>
        </div>
      </div>
      <details>
        <summary>Ручное добавление лида</summary>
        <div class="section-inner manual-grid">
          <div>
            <div class="grid">
              <div>
                <label for="sourceType">Источник</label>
                <select id="sourceType">
                  <option value="manual">Вручную</option>
                  <option value="telegram">Telegram</option>
                  <option value="vk">VK</option>
                  <option value="website">Сайт</option>
                  <option value="map">Карта / справочник</option>
                  <option value="form">Форма</option>
                </select>
              </div>
              <div>
                <label for="segment">Сегмент</label>
                <select id="segment">
                  <option value="">Не определен</option>
                  <option value="commercial">Коммерческая</option>
                  <option value="residential">Жилая</option>
                  <option value="mixed">Смешанный</option>
                </select>
              </div>
            </div>
            <label for="sourceUrl">Ссылка на источник</label>
            <input id="sourceUrl" placeholder="https://...">
            <div class="grid">
              <div>
                <label for="personName">Имя</label>
                <input id="personName" placeholder="Если известно">
              </div>
              <div>
                <label for="companyName">Компания</label>
                <input id="companyName" placeholder="Если известно">
              </div>
            </div>
            <div class="grid">
              <div>
                <label for="city">Город</label>
                <input id="city" placeholder="Например, Новосибирск">
              </div>
              <div>
                <label for="intent">Намерение</label>
                <select id="intent">
                  <option value="unknown">Не определено</option>
                  <option value="buy">Купить</option>
                  <option value="sell">Продать</option>
                  <option value="rent">Арендовать</option>
                  <option value="lease_out">Сдать</option>
                  <option value="invest">Инвестировать</option>
                </select>
              </div>
            </div>
            <label for="rawText">Текст сообщения / объявления</label>
            <textarea id="rawText" placeholder="Вставьте сообщение из Telegram, VK, объявления или заметку менеджера"></textarea>
            <div class="actions">
              <button id="saveBtn">Сохранить лид</button>
              <button class="secondary" id="clearBtn" type="button">Очистить</button>
              <div class="status" id="status"></div>
            </div>
          </div>
          <div>
            <h2>Найденные контакты</h2>
            <div class="preview" id="preview"></div>
          </div>
        </div>
      </details>
    </main>
  </div>
  <script>
    const fields = ["sourceType", "sourceUrl", "segment", "personName", "companyName", "city", "intent", "rawText"];
    const $ = (id) => document.getElementById(id);
    const state = { leads: [], sources: [] };

    function payload() {
      return Object.fromEntries(fields.map((id) => [id, $(id).value.trim()]));
    }

    function esc(value) {
      return String(value || "").replace(/[&<>"']/g, (char) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      }[char]));
    }

    function safeUrl(value) {
      const url = String(value || "");
      return url.startsWith("http://") || url.startsWith("https://") ? url : "#";
    }

    function setText(id, value) {
      const element = $(id);
      if (element) element.textContent = value;
    }

    function updateMetrics() {
      const sources = state.sources || [];
      const leads = state.leads || [];
      const monitoring = sources.filter((source) => source.status === "monitoring").length;
      const hot = leads.filter((lead) => lead.phone_normalized || lead.email || lead.telegram_username || lead.vk_url).length;
      setText("metricSources", sources.length);
      setText("metricMonitoring", monitoring);
      setText("metricLeads", leads.length);
      setText("metricHot", hot);
      setText("topSources", `Источники: ${sources.length}`);
      setText("topMonitoring", `Мониторинг: ${monitoring}`);
      setText("topLeads", `Лиды: ${leads.length}`);
    }

    function renderContacts(data) {
      const contacts = data.contacts || {};
      const rows = [
        ["Телефон", contacts.phones || []],
        ["Email", contacts.emails || []],
        ["Telegram", contacts.telegram_usernames || []],
        ["VK", contacts.vk_urls || []],
      ];
      $("preview").innerHTML = rows.map(([label, values]) => `
        <div class="row">
          <div class="key">${label}</div>
          <div class="value">${values.length ? values.map((v) => `<span class="pill">${esc(v)}</span>`).join("") : "Нет"}</div>
        </div>
      `).join("");
    }

    async function preview() {
      const res = await fetch("api/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload()),
      });
      renderContacts(await res.json());
    }

    async function save() {
      $("saveBtn").disabled = true;
      $("status").className = "status";
      $("status").textContent = "Сохраняю...";
      try {
        const res = await fetch("api/leads", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload()),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Не удалось сохранить");
        $("status").className = "status ok";
        $("status").textContent = `Сохранено: ${data.lead_id}`;
        renderContacts(data);
        loadLeads();
      } catch (error) {
        $("status").className = "status error";
        $("status").textContent = error.message;
      } finally {
        $("saveBtn").disabled = false;
      }
    }

    function clearForm() {
      fields.forEach((id) => {
        if (id === "sourceType") $(id).value = "manual";
        else if (id === "intent") $(id).value = "unknown";
        else $(id).value = "";
      });
      $("status").textContent = "";
      preview();
    }

    function leadTitle(lead) {
      return lead.person_name || lead.company_name || lead.telegram_username || lead.phone_normalized || lead.email || "Без имени";
    }

    function formatDate(value) {
      if (!value) return "дата сообщения не указана";
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return value;
      return date.toLocaleString("ru-RU", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    }

    async function loadLeads() {
      const res = await fetch("api/leads");
      const data = await res.json();
      const leads = data.leads || [];
      state.leads = leads;
      updateMetrics();
      $("leadList").innerHTML = leads.length ? leads.map((lead) => `
        <div class="lead-card">
          <div class="lead-head">
            <div>
              <div class="lead-title">${esc(leadTitle(lead))}</div>
              <div class="lead-meta">${esc(lead.property_segment || "сегмент не указан")} · ${esc(lead.intent || "намерение не указано")} · score ${esc(lead.score)}</div>
            </div>
            <span class="pill">${esc(lead.status)}</span>
          </div>
          <div class="lead-text">${esc(lead.raw_text || "")}</div>
          <div class="lead-meta">
            Написал: ${esc(formatDate(lead.collected_at))} ·
            Добавлено: ${esc(formatDate(lead.created_at))} ·
            ${lead.source_url ? `<a href="${safeUrl(lead.source_url)}" target="_blank">источник</a>` : "без ссылки"}
          </div>
        </div>
      `).join("") : `<div class="status">Лидов пока нет</div>`;
    }

    function renderQueries(data) {
      const queries = data.queries || [];
      $("queryList").innerHTML = queries.map((item) => `
        <div class="query-card">
          <div class="lead-title">${esc(item.query)}</div>
          <div class="lead-meta">
            ${item.links.map((link) => `<a href="${safeUrl(link.url)}" target="_blank">${esc(link.label)}</a>`).join(" · ")}
          </div>
        </div>
      `).join("");
    }

    async function generateQueries() {
      const res = await fetch("api/source-queries", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          city: $("sourceCity").value.trim(),
          topic: $("sourceTopic").value,
          platform: $("sourcePlatform").value,
        }),
      });
      const data = await res.json();
      renderQueries(data);
      $("suggestionsPanel").open = true;
      $("sourceStatus").className = "status ok";
      $("sourceStatus").textContent = "Подсказки готовы. Откройте ссылки, выберите подходящие каналы и вставьте их выше.";
    }

    function sourceTitle(source) {
      return source.title || source.username || source.url;
    }

    async function loadSources() {
      const res = await fetch("api/sources");
      const data = await res.json();
      const sources = data.sources || [];
      state.sources = sources;
      updateMetrics();
      $("sourceList").innerHTML = sources.length ? sources.map((source) => `
        <div class="source-card ${esc(source.status || "")}" data-source-id="${esc(source.id)}">
          <div class="lead-head">
            <div>
              <div class="lead-title">${esc(sourceTitle(source))}</div>
              <div class="lead-meta">${esc(source.platform || "source")} · ${esc(source.topic || "без темы")} · ${esc(source.city || "город не указан")}</div>
            </div>
            <span class="source-state ${esc(source.status || "")}">${source.status === "monitoring" ? "Работает" : "Не запущен"}</span>
          </div>
          <a class="source-link" href="${safeUrl(source.url)}" target="_blank">${esc(source.url)}</a>
          <div class="actions">
            <button class="secondary compact source-status-btn" type="button" data-status="${source.status === "monitoring" ? "new" : "monitoring"}">
              ${source.status === "monitoring" ? "Пауза" : "В мониторинг"}
            </button>
            ${source.status === "monitoring" ? `<button class="compact source-run-btn" type="button">Собрать</button>` : ""}
          </div>
        </div>
      `).join("") : `<div class="status">Источников пока нет</div>`;
    }

    async function setSourceStatus(sourceId, status) {
      $("sourceStatus").className = "status";
      $("sourceStatus").textContent = "Обновляю...";
      try {
        const res = await fetch("api/sources/status", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id: sourceId, status }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Не удалось обновить");
        await loadSources();
        if (status === "monitoring") {
          $("sourceStatus").className = "status";
          $("sourceStatus").textContent = "Источник включен. Запускаю сбор...";
          await runCollector();
        } else {
          $("sourceStatus").className = "status ok";
          $("sourceStatus").textContent = "Мониторинг остановлен";
        }
      } catch (error) {
        $("sourceStatus").className = "status error";
        $("sourceStatus").textContent = error.message;
      }
    }

    async function importSources() {
      $("sourceStatus").className = "status";
      $("sourceStatus").textContent = "Добавляю...";
      try {
        const res = await fetch("api/sources/import", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            raw: $("sourceLinks").value,
            city: $("sourceCity").value.trim(),
            topic: $("sourceTopic").value,
            platform: $("sourcePlatform").value,
          }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Не удалось добавить");
        $("sourceStatus").className = "status ok";
        $("sourceStatus").textContent = `Добавлено: ${data.inserted}, уже было: ${data.skipped}`;
        $("sourceLinks").value = "";
        await loadSources();
      } catch (error) {
        $("sourceStatus").className = "status error";
        $("sourceStatus").textContent = error.message;
      }
    }

    async function sendTelegramTest() {
      $("sourceStatus").className = "status";
      $("sourceStatus").textContent = "Отправляю тест...";
      try {
        const res = await fetch("api/telegram/test", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ city: $("sourceCity").value.trim(), topic: $("sourceTopic").value }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Не удалось отправить");
        $("sourceStatus").className = "status ok";
        $("sourceStatus").textContent = "Тестовое уведомление отправлено";
      } catch (error) {
        $("sourceStatus").className = "status error";
        $("sourceStatus").textContent = error.message;
      }
    }

    async function runCollector() {
      $("sourceStatus").className = "status";
      $("sourceStatus").textContent = "Запускаю сбор...";
      try {
        const res = await fetch("api/collector/run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Не удалось запустить сбор");
        $("sourceStatus").className = data.exit_code === 0 ? "status ok" : "status error";
        $("sourceStatus").textContent = data.message || "Сбор завершен";
        await loadLeads();
      } catch (error) {
        $("sourceStatus").className = "status error";
        $("sourceStatus").textContent = error.message;
      }
    }

    fields.forEach((id) => $(id).addEventListener("input", preview));
    $("saveBtn").addEventListener("click", save);
    $("clearBtn").addEventListener("click", clearForm);
    $("refreshBtn").addEventListener("click", loadLeads);
    $("refreshSourcesBtn").addEventListener("click", loadSources);
    $("queryBtn").addEventListener("click", generateQueries);
    $("runCollectorBtn").addEventListener("click", runCollector);
    $("heroRefreshBtn").addEventListener("click", () => {
      loadLeads();
      loadSources();
    });
    $("importSourcesBtn").addEventListener("click", importSources);
    $("testTelegramBtn").addEventListener("click", sendTelegramTest);
    $("sourceList").addEventListener("click", (event) => {
      const button = event.target.closest(".source-status-btn");
      const runButton = event.target.closest(".source-run-btn");
      if (button) {
        const card = button.closest(".source-card");
        setSourceStatus(card.dataset.sourceId, button.dataset.status);
      }
      if (runButton) runCollector();
    });
    preview();
    loadLeads();
    loadSources();
  </script>
</body>
</html>
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_phone(value: str) -> Optional[str]:
    digits = re.sub(r"\D+", "", value)
    if len(digits) == 11 and digits[0] in ("7", "8"):
        return "+7" + digits[1:]
    if len(digits) == 10:
        return "+7" + digits
    return None


def extract_contacts(text: str) -> dict[str, list[str]]:
    phones = sorted({phone for phone in (normalize_phone(m.group(0)) for m in PHONE_RE.finditer(text)) if phone})
    emails = sorted({m.group(0).strip().lower() for m in EMAIL_RE.finditer(text)})
    telegram = sorted({m.group(1).strip().lower() for m in TELEGRAM_RE.finditer(text)})
    vk = sorted({m.group(0).strip().rstrip("/").lower() for m in VK_RE.finditer(text)})
    return {"phones": phones, "emails": emails, "telegram_usernames": telegram, "vk_urls": vk}


def detect_intent(text: str) -> str:
    low = text.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(keyword in low for keyword in keywords):
            return intent
    return "unknown"


def detect_segment(text: str) -> Optional[str]:
    low = text.lower()
    commercial = any(keyword in low for keyword in COMMERCIAL_KEYWORDS)
    residential = any(keyword in low for keyword in RESIDENTIAL_KEYWORDS)
    if commercial and residential:
        return "mixed"
    if commercial:
        return "commercial"
    if residential:
        return "residential"
    return None


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_telegram_source(value: str) -> Optional[dict[str, str]]:
    raw = value.strip().rstrip("/")
    if not raw:
        return None
    match = TG_URL_RE.search(raw)
    if not match:
        return None
    username = match.group(1).strip()
    if username.lower() in {"share", "joinchat"}:
        return None
    return {
        "platform": "telegram",
        "username": username,
        "url": f"https://t.me/{username}",
    }


def normalize_source(value: str, preferred_platform: str = "all") -> Optional[dict[str, Any]]:
    raw = value.strip().rstrip("/")
    if not raw:
        return None

    telegram = normalize_telegram_source(raw)
    if telegram:
        return telegram

    vk_match = VK_SOURCE_RE.search(raw)
    if vk_match:
        username = vk_match.group(1).strip()
        return {
            "platform": "vk",
            "username": username,
            "url": f"https://vk.com/{username}",
        }

    url_match = URL_RE.search(raw)
    if url_match:
        url = url_match.group(0).rstrip("/")
        hostname = urlparse(url).hostname or ""
        platform = preferred_platform if preferred_platform in PLATFORM_LABELS and preferred_platform != "all" else "website"
        if any(domain in hostname for domain in ("2gis.", "yandex.", "google.")):
            platform = "map"
        if any(domain in hostname for domain in ("avito.", "cian.", "domclick.", "realty.", "youla.", "move.")):
            platform = "classified"
        if platform not in {"telegram", "vk", "website", "map", "other", "classified", "partner_api"}:
            platform = "website"
        return {
            "platform": platform,
            "title": hostname or url,
            "url": url,
            "metadata": {"source_kind": platform},
        }

    if preferred_platform == "partner_api":
        return {
            "platform": "partner_api",
            "title": raw,
            "url": f"https://example.invalid/partner-api/{quote(raw)}",
            "metadata": {"source_kind": "partner_api", "provider": raw},
        }

    return None


def parser_catalog() -> list[dict[str, str]]:
    return [
        {
            "title": "Telegram intent parser",
            "status": "работает",
            "mode": "реальный сбор",
            "description": "Читает доступные аккаунту публичные каналы/чаты и ищет заявки с контактами.",
        },
        {
            "title": "VK source discovery",
            "status": "подготовлен",
            "mode": "источники и запросы",
            "description": "Добавляет VK-группы в базу; для автосбора нужен VK access token.",
        },
        {
            "title": "Classified/API intake",
            "status": "подготовлен",
            "mode": "API/CSV/RSS",
            "description": "Подходит для ads-api, Rest-App и выгрузок объявлений без ломания верстки площадок.",
        },
        {
            "title": "Website/RSS monitor",
            "status": "подготовлен",
            "mode": "сайты",
            "description": "Фиксирует сайты, RSS и формы партнеров как источники для следующего worker.",
        },
        {
            "title": "Maps/directories scan",
            "status": "подготовлен",
            "mode": "справочники",
            "description": "Для поиска собственников бизнеса, БЦ, складов, арендаторов и управляющих компаний.",
        },
    ]


def source_queries(city: str, topic: str, platform: str = "all") -> list[dict[str, Any]]:
    topic_map = {
        "commercial": ["коммерческая недвижимость", "аренда офиса", "снять помещение", "аренда склад", "бизнес недвижимость"],
        "residential": ["купить квартиру", "продать квартиру", "снять квартиру", "новостройки", "жилая недвижимость"],
        "business": ["предприниматели", "бизнес чат", "арендаторы", "кофейни", "малый бизнес"],
        "owners": ["собственник помещение", "собственник квартира", "арендатор ищет помещение", "куплю от собственника", "продам от собственника"],
    }
    platform_targets = {
        "telegram": ["telegram", "t.me", "tgstat"],
        "vk": ["vk.com", "ВКонтакте", "группа"],
        "classified": ["Авито", "ЦИАН", "Яндекс Недвижимость", "Домклик"],
        "website": ["сайт", "RSS", "форма заявки"],
        "map": ["2ГИС", "Яндекс Карты", "справочник"],
        "partner_api": ["ads-api", "rest-app", "API недвижимости"],
    }
    selected_platforms = list(platform_targets) if platform == "all" else [platform]
    queries = []
    for selected in selected_platforms:
        for phrase in topic_map.get(topic, topic_map["commercial"]):
            suffix = " ".join(platform_targets.get(selected, [selected]))
            query = f"{phrase} {city} {suffix}".strip()
            encoded = quote(query)
            links = [
                {"label": "Google", "url": f"https://www.google.com/search?q={encoded}"},
                {"label": "Яндекс", "url": f"https://yandex.ru/search/?text={encoded}"},
            ]
            if selected == "telegram":
                links.append({"label": "TGStat", "url": f"https://tgstat.ru/search?query={encoded}"})
            if selected == "vk":
                links.append({"label": "VK", "url": f"https://vk.com/search?c[section]=communities&q={encoded}"})
            queries.append({"query": query, "platform": selected, "links": links})
    return queries


def json_response(handler: BaseHTTPRequestHandler, status: int, body: dict[str, Any]) -> None:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def supabase_request(method: str, path: str, payload: Any) -> Any:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/{path}",
        data=data,
        method=method,
        headers={
            "Content-Type": "application/json",
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Prefer": "return=representation",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8")
        raise RuntimeError(f"Supabase error {error.code}: {detail}") from error


def telegram_api(method: str, payload: dict[str, Any]) -> Any:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не задан")
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}",
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        raw = response.read().decode("utf-8")
        result = json.loads(raw) if raw else {}
        if not result.get("ok"):
            raise RuntimeError(result.get("description") or "Telegram API error")
        return result.get("result")


def resolve_telegram_chat_id() -> str:
    if TELEGRAM_NOTIFY_CHAT_ID:
        return TELEGRAM_NOTIFY_CHAT_ID
    updates = telegram_api("getUpdates", {"limit": 10, "allowed_updates": ["message"]}) or []
    for update in reversed(updates):
        message = update.get("message") or {}
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        if chat_id:
            return str(chat_id)
    raise RuntimeError("Напишите /start боту, затем повторите тест")


def format_lead_notification(lead: dict[str, Any], contacts: dict[str, list[str]], lead_id: Optional[str] = None) -> str:
    title = lead.get("person_name") or lead.get("company_name") or lead.get("telegram_username") or lead.get("phone_normalized") or "Новый лид"
    contact_parts = []
    if contacts.get("phones"):
        contact_parts.append(f"тел: {contacts['phones'][0]}")
    if contacts.get("telegram_usernames"):
        contact_parts.append(f"tg: @{contacts['telegram_usernames'][0]}")
    if contacts.get("emails"):
        contact_parts.append(f"email: {contacts['emails'][0]}")
    source = lead.get("source_url") or "источник не указан"
    text = (lead.get("raw_text") or "").strip()
    if len(text) > 700:
        text = text[:700].rstrip() + "..."
    lines = [
        "Новый лид Novactiv",
        f"{title}",
        f"Сегмент: {lead.get('property_segment') or 'не определен'}",
        f"Намерение: {lead.get('intent') or 'unknown'}",
        f"Контакты: {', '.join(contact_parts) if contact_parts else 'не найдены'}",
        f"Источник: {source}",
    ]
    if lead_id:
        lines.append(f"ID: {lead_id}")
    if text:
        lines.extend(["", text])
    return "\n".join(lines)


def send_telegram_notification(text: str) -> None:
    chat_id = resolve_telegram_chat_id()
    telegram_api("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    })


def run_collector_command() -> dict[str, Any]:
    if not COLLECTOR_RUN_COMMAND:
        raise RuntimeError("COLLECTOR_RUN_COMMAND не задан на сервере")
    before = count_leads()
    completed = subprocess.run(
        COLLECTOR_RUN_COMMAND,
        shell=True,
        check=False,
        capture_output=True,
        text=True,
        timeout=240,
    )
    output = "\n".join(part.strip() for part in (completed.stdout, completed.stderr) if part.strip())
    if len(output) > 900:
        output = output[-900:]
    after = count_leads()
    found = max(after - before, 0)
    if completed.returncode == 0:
        if found:
            message = f"Сбор завершен. Новых лидов: {found}. Уведомления отправлены в Telegram."
        else:
            message = "Сбор завершен. Новых лидов нет: в подключенных источниках не найдено свежих сообщений с контактами."
    else:
        message = "Сбор завершился с ошибкой"
    return {"exit_code": completed.returncode, "message": message, "output": output}


def count_leads() -> int:
    rows = supabase_request("GET", "leads?select=id", None) or []
    return len(rows)


def build_lead(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, list[str]]]:
    raw_text = str(payload.get("rawText") or "").strip()
    contacts = extract_contacts(raw_text)
    detected_segment = detect_segment(raw_text)
    detected_intent = detect_intent(raw_text)
    segment = str(payload.get("segment") or "").strip() or detected_segment
    intent = str(payload.get("intent") or "").strip() or detected_intent
    if intent == "unknown" and detected_intent != "unknown":
        intent = detected_intent
    lead = {
        "source_url": str(payload.get("sourceUrl") or "").strip() or None,
        "raw_text": raw_text,
        "person_name": str(payload.get("personName") or "").strip() or None,
        "company_name": str(payload.get("companyName") or "").strip() or None,
        "phone_raw": contacts["phones"][0] if contacts["phones"] else None,
        "phone_normalized": contacts["phones"][0] if contacts["phones"] else None,
        "email": contacts["emails"][0] if contacts["emails"] else None,
        "telegram_username": contacts["telegram_usernames"][0] if contacts["telegram_usernames"] else None,
        "vk_url": contacts["vk_urls"][0] if contacts["vk_urls"] else None,
        "city": str(payload.get("city") or "").strip() or None,
        "property_segment": segment or None,
        "intent": intent or "unknown",
        "confidence": 0.75 if any(contacts.values()) else 0,
        "score": 50 if any(contacts.values()) else 10,
        "score_reason": "Manual intake with detected contact" if any(contacts.values()) else "Manual intake without detected contact",
        "status": "new",
        "collected_at": now(),
    }
    return lead, contacts


class Handler(BaseHTTPRequestHandler):
    def do_HEAD(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/leads", "/leads/"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            return
        self.send_response(404)
        self.end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/leads", "/leads/"):
            data = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if path.endswith("/api/leads"):
            fields = "id,person_name,company_name,phone_normalized,email,telegram_username,vk_url,property_segment,intent,status,score,raw_text,source_url,collected_at,created_at"
            leads = supabase_request("GET", f"leads?select={fields}&status=neq.not_relevant&order=created_at.desc&limit=30", None)
            json_response(self, 200, {"leads": leads or []})
            return
        if path.endswith("/api/sources"):
            fields = "id,platform,title,url,username,city,topic,status,created_at"
            sources = supabase_request("GET", f"source_discovery?select={fields}&order=created_at.desc&limit=50", None)
            json_response(self, 200, {"sources": sources or []})
            return
        json_response(self, 404, {"error": "Not found"})

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8")) if length else {}
            path = urlparse(self.path).path

            if path.endswith("/api/preview"):
                json_response(self, 200, {"contacts": extract_contacts(str(payload.get("rawText") or ""))})
                return

            if path.endswith("/api/source-queries"):
                city = str(payload.get("city") or "Новосибирск").strip()
                topic = str(payload.get("topic") or "commercial").strip()
                platform = str(payload.get("platform") or "all").strip()
                json_response(self, 200, {"queries": source_queries(city, topic, platform), "parsers": parser_catalog()})
                return

            if path.endswith("/api/sources/import"):
                raw = str(payload.get("raw") or "")
                city = str(payload.get("city") or "").strip() or None
                topic = str(payload.get("topic") or "").strip() or None
                platform = str(payload.get("platform") or "all").strip()
                candidates = []
                seen = set()
                for line in re.split(r"[\n,]+", raw):
                    source = normalize_source(line, platform)
                    if not source or source["url"] in seen:
                        continue
                    seen.add(source["url"])
                    source.update({"city": city, "topic": topic, "status": "new"})
                    candidates.append(source)
                inserted = 0
                skipped = 0
                for source in candidates:
                    try:
                        supabase_request("POST", "source_discovery", source)
                        inserted += 1
                    except RuntimeError as error:
                        if "23505" in str(error) or "duplicate" in str(error).lower():
                            skipped += 1
                        else:
                            raise
                json_response(self, 201, {"inserted": inserted, "skipped": skipped})
                return

            if path.endswith("/api/telegram/test"):
                city = str(payload.get("city") or "Новосибирск").strip()
                topic = str(payload.get("topic") or "commercial").strip()
                sample_lead = {
                    "raw_text": f"Тестовая заявка: ищу помещение под офис в городе {city}, бюджет обсуждаем, связь @novactiv_test",
                    "telegram_username": "novactiv_test",
                    "property_segment": "commercial" if topic != "residential" else "residential",
                    "intent": "rent",
                    "source_url": "http://45.92.174.232/leads/",
                    "score": 65,
                }
                contacts = extract_contacts(sample_lead["raw_text"])
                send_telegram_notification(format_lead_notification(sample_lead, contacts, "test"))
                json_response(self, 200, {"sent": True})
                return

            if path.endswith("/api/collector/run"):
                json_response(self, 200, run_collector_command())
                return

            if path.endswith("/api/sources/status"):
                source_id = str(payload.get("id") or "").strip()
                status = str(payload.get("status") or "").strip()
                if not re.fullmatch(r"[0-9a-fA-F-]{36}", source_id):
                    json_response(self, 400, {"error": "Некорректный источник"})
                    return
                if status not in {"new", "monitoring", "approved", "rejected"}:
                    json_response(self, 400, {"error": "Некорректный статус"})
                    return
                updated = supabase_request(
                    "PATCH",
                    f"source_discovery?id=eq.{source_id}",
                    {"status": status},
                )
                json_response(self, 200, {"source": updated[0] if updated else None})
                return

            if path.endswith("/api/leads"):
                lead, contacts = build_lead(payload)
                if not lead["raw_text"] and not any(contacts.values()):
                    json_response(self, 400, {"error": "Добавьте текст источника или контакт"})
                    return
                created = supabase_request("POST", "leads", lead)
                lead_id = created[0]["id"]
                record = {
                    "lead_id": lead_id,
                    "source_url": lead["source_url"],
                    "source_url_hash": stable_hash(lead["source_url"]) if lead["source_url"] else None,
                    "raw_text": lead["raw_text"],
                    "raw_payload": payload,
                    "extracted_contacts": contacts,
                    "parser_name": "lead_intake_ui",
                    "parser_version": "0.1.0",
                    "extraction_confidence": lead["confidence"],
                    "legal_basis_note": "manual intake",
                    "collected_at": now(),
                }
                supabase_request("POST", "lead_source_records", record)
                try:
                    send_telegram_notification(format_lead_notification(lead, contacts, lead_id))
                except Exception as notify_error:
                    json_response(self, 201, {"lead_id": lead_id, "contacts": contacts, "notification_error": str(notify_error)})
                    return
                json_response(self, 201, {"lead_id": lead_id, "contacts": contacts})
                return

            json_response(self, 404, {"error": "Not found"})
        except Exception as error:
            json_response(self, 500, {"error": str(error)})


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
