# Backlog

## Todo

_(пусто)_

## Done

- [x] **Phase 1** — `docs/requirements.md`
- [x] **Phase 2** — `docs/architecture.md`
- [x] **Phase 3** — project init (структура, pyproject, env, README)
- [x] **T-001** — Builder: `pdf_to_text` через pdfplumber + чистка колонтитулов
- [x] **T-002** — Builder: `extractor` (LLM-stub, переключаемый по `OPENROUTER_API_KEY`)
- [x] **T-003** — Builder: `owl_writer` (JSON → OWL через owlready2)
- [x] **T-004** — Builder: CLI `scripts/build_ontology.py`
- [x] **T-005** — Финальная онтология `regulations/practice.owl` (через `scripts/init_practice_ontology.py`)
- [x] **T-006** — Extractors: `pdf_render` (PyMuPDF → PNG)
- [x] **T-007** — Extractors: `order_parser` (LLM-stub, фикстура по SHA256 для демо-приказа)
- [x] **T-008** — Extractors: Pydantic-модели (`Order`, `Student`, `PracticeLocation`, `Supervisor`)
- [x] **T-009** — Core: `loader` (сканирование `regulations/*.owl`, общий `World`)
- [x] **T-010** — Core: `fact_injector` (OrderFacts → individuals)
- [x] **T-011** — Core: `checker` (HermiT + 7 проверок R-01..R-07; авто-поиск Java)
- [x] **T-012** — Core: `report` (Pydantic-модели, save/load JSON)
- [x] **T-013** — Web: FastAPI каркас (`main.py`, `routes.py`)
- [x] **T-014** — Web: шаблоны Jinja2 (`base`, `index`, `report`) + CSS
- [x] **T-015** — Web: загрузка PDF, оркестрация пайплайна, redirect на отчёт
- [x] **T-016** — E2E на демо-приказе (R-04 сработало, HermiT отработал за 0.66s)
- [x] **T-017** — README обновлён

## Backlog (post-MVP, без сроков)

- F-09 — Кэш парсинга PDF по SHA256 страницы
- F-10 — Кнопка экспорта отчёта в PDF/JSON
- F-11 — История проверок в SQLite
- F-12 — Подсветка проблемных полей на превью PDF
- Реальная LLM-интеграция (заменить `NotImplementedError` в `extractor.py` и `order_parser.py`)
- pytest на core (loader, fact_injector, checker)
- Линтинг ruff + CI
