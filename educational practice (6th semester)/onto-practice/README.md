# onto-practice

Прототип системы автоматической проверки приказов о направлении на практику студентов на соответствие регламенту кафедры (ФИТ НГУ) через **OWL-онтологию + правила** и встроенный ризонер **HermiT**.

## Идея

1. **Build-time** (один раз): LLM извлекает черновик онтологии из текста регламента → ручная доводка в Protégé → `regulations/practice.owl`.
2. **Runtime** (на каждый приказ): пользователь загружает PDF → парсер извлекает факты → ризонер прогоняет правила → HTML-отчёт о нарушениях.

## Quick start

```bash
# 1. Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # вписать OPENROUTER_API_KEY (опционально — без него работает заглушка)

# 2. Установка JDK для HermiT (если java не в PATH — checker сам найдёт)
python -c "import jdk; jdk.install('17')"

# 3. (опционально) Сгенерировать черновик онтологии из регламента — результат в var/drafts/
python scripts/build_ontology.py docs/source/onto/metod_rekomend_praktika.pdf

# 4. Пересоздать финальную онтологию из скрипта (вручную доведённая версия)
python scripts/init_practice_ontology.py

# 5. Запустить веб-приложение
uvicorn src.web.main:app --reload
# → http://localhost:8000
```

## Что делает прототип

Демо-сценарий с приказом № 0145-2:

1. Загружаем `docs/source/onto/Приказ_№0145_2_от_22_01_2026_3_курс_ПИиКН.pdf` через форму
2. Получаем отчёт со списком нарушений:
   - **R-04**: между датой издания приказа (22.01.2026) и началом практики (02.02.2026) всего 11 дней, регламент требует не менее 30
   - **R-01** и **R-05**: у одного из студентов не указан руководитель практики (демонстрация)

## Режим LLM vs заглушка

- Если `OPENROUTER_API_KEY` установлен — пайплайны зовут LLM (для парсинга PDF приказа и для извлечения черновика онтологии). *На текущий момент LLM-интеграция помечена `NotImplementedError` — реальные prompts добавляются в задачу T-007/T-002.*
- Если ключа нет — используется заглушка:
  - `parse_order(pdf)` сверяет SHA256 файла с `DEMO_PDF_SHA256` и для известного приказа возвращает курированный фикстур (14 студентов с реальными ФИО из приказа)
  - для любого другого PDF возвращается минимальный плейсхолдер
  - `extract_draft(text)` возвращает hard-coded черновик онтологии, идентичный финальному `practice.owl`

Так пайплайн прогоняется end-to-end даже без LLM-доступа.

## Архитектура

```
src/
  builder/      # build-time: regulation.pdf → draft.owl
  extractors/   # runtime: order.pdf → OrderFacts (Pydantic)
  core/         # OWL load, fact injection, reasoner (HermiT), report
  web/          # FastAPI + Jinja2 + минимальный CSS
regulations/    # *.owl плагины — добавление нового регламента не требует правки ядра
scripts/        # CLI: build_ontology.py, init_practice_ontology.py
```

Подробно — `docs/architecture.md`.

## Документация

- `docs/requirements.md` — требования и MVP-скоуп (правила R-01..R-07)
- `docs/architecture.md` — архитектура, Mermaid-диаграммы, потоки данных
- `docs/backlog.md` — журнал задач T-XXX
