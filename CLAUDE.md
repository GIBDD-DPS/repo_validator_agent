# CLAUDE.md — AI CTO Assistant

## 🧠 О проекте

**AI CTO Assistant** — это не очередной анализатор кода. Это **прогнозная платформа технического долга**, которая отвечает на четыре главных вопроса CTO/тимлида:

1. **Насколько всё плохо?** — AI-вердикт + прогноз деградации.
2. **Что критично?** — только топ-3 риска (без шума).
3. **Что делать первым?** — action engine с приоритетами.
4. **Что я выиграю?** — бизнес-метрики: $, потеря скорости, риск масштабирования.

## ✨ Ключевые фичи (почему это заслуживает звезду)

- **🧠 AI Verdict + Drift Prediction** — предсказываем, через сколько месяцев упадёт maintainability.
- **🎯 Только 3 риска** — никакого списка из 100 проблем, только то, что реально важно.
- **⚡ Action Engine** — «Fix First / Fix Next / Optional» с конкретными шагами.
- **💰 Business Layer** — техдолг в деньгах, потеря скорости (velocity), риск для команды.
- **🏆 Геймификация** — очки, бейджи, сертификат качества, локальный лидерборд.
- **💬 AI-чат с ролями** (аналитик / архитектор / безопасник / казначей) — задавайте вопросы по отчёту.
- **🔧 GitHub-автофиксы** — создание PR с исправлениями, установка метки качества, публикация issue.
- **📊 Глобальный лидерборд** — сравнивайте свой репозиторий с другими.
- **📦 Всё в одном виджете** — работает как обычный HTML-блок, встраивается в WordPress Elementor или любой сайт.
- **🔐 API ключ** — для приватных репозиториев (опционально).

## 🚀 Демо

> Живой пример: [https://prizolov.ru/repo-validator/](https://prizolov.ru/repo-validator/)  
> Вставьте URL любого GitHub-репозитория и получите CTO-отчёт за 30 секунд.

## 🧱 Архитектура
─────────────────────────────────────────────────────┐
│ Frontend (Виджет)                                  │
│ – HTML/CSS/JS, Progressive Disclosure              │
│ – Уровни 1–4: Verdict, Risks, Action, Business     │
│ – Уровень 5: Deep tabs (AST, Security, Git, Deps)  │
└─────────────────────┬──────────────────────────────┘
│ REST API
▼
┌─────────────────────────────────────────────────────┐
│ Backend (Amvera.io)                                 │
│ – Клонирование GitHub репозиториев                  │
│ – AST / Линтеры / Git-статистика                    │
│ – Анализ зависимостей и уязвимостей                 │
│ – AI-генерация прогнозов (LLM + эвристики)          │
│ – Глобальное хранилище метрик для лидерборда        │
└─────────────────────────────────────────────────────┘


## 📦 Установка и использование

### Как обычный HTML-виджет (для любого сайта)

1. Скопируйте полный код из файла `widget.html` (он самодостаточный — CSS, JS, разметка).
2. Вставьте в любую HTML-страницу или в виджет «HTML» в WordPress + Elementor.
3. Нажмите «Анализировать» — всё работает.

### Как плагин для WordPress + Elementor (рекомендуется)

1. Создайте папку `/wp-content/plugins/prizolov-repo-ai/`.
2. Внутри создайте `prizolov-repo-ai.php` и `widget.php` (шаблон плагина есть в документации).
3. Активируйте плагин, в Elementor появится виджет «Prizolov Repo Validator».

### API ключ (для приватных репозиториев)

- Получите API ключ у администратора сервиса.
- Вставьте в поле «API ключ» и нажмите «Сохранить» — ключ хранится в `localStorage`.

## 🛠️ Как внести вклад (и почему это выгодно)

Проект открыт для контрибьюций, особенно в следующих направлениях:

- **Улучшение прогнозной модели** — добавить реальную регрессию на основе истории репозитория.
- **Поддержка GitLab / Bitbucket**.
- **Новые языки** (Go, Rust, PHP) в анализаторе.
- **Интеграция с Jira / Linear** — экспорт задач.
- **GitHub Action** для автоматического комментирования PR.

Формат contribution:
1. Форк репозитория.
2. Создайте ветку `feature/your-idea`.
3. Сделайте изменения (JavaScript/CSS/HTML).
4. Откройте Pull Request с описанием.

## 🧪 Технологии

- **Frontend** — Vanilla JS + jQuery (для AJAX), Chart.js (графики), HTML5/CSS3.
- **Backend API** — Python/FastAPI (хостинг Amvera.io).
- **Анализ кода** — AST (Python), линтеры (flake8, bandit), GitPython.

## 📄 Лицензия

MIT — свободно используйте, модифицируйте, встраивайте в свои продукты.  
Только не забывайте ставить звёздочку 🌟, если проект вам помог.

## 👤 Контакты

- Автор: Dm.Andreyanov / Prizolov Market
- Сайт: [https://prizolov.ru](https://prizolov.ru)

---

# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

**⭐ Если вы дочитали до сюда, вы уже потенциальный звёздочник. Нажмите звезду — это лучшая награда для opensource-проекта.**
