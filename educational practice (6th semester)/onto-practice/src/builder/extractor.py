"""Extract a draft ontology schema from regulation text via LLM.

Stubbed: when ``OPENROUTER_API_KEY`` is absent we return a hard-coded draft that
mirrors the curated ``regulations/practice.owl``. This keeps the build pipeline
runnable end-to-end so the OWL writer is testable without API access.
"""

from __future__ import annotations

import logging
import os

from pydantic import BaseModel, ConfigDict, Field

from src.extractors.llm import make_client, parse_json_response

log = logging.getLogger(__name__)


class DraftClass(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    label_ru: str
    comment_ru: str = ""


class DraftDataProperty(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    domain: str
    range: str = "string"  # "string" | "integer" | "date"
    functional: bool = True


class DraftObjectProperty(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    domain: str
    range: str
    functional: bool = False


class DraftRule(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: str
    source: str = ""


class OntologyDraft(BaseModel):
    model_config = ConfigDict(extra="ignore")
    classes: list[DraftClass] = Field(default_factory=list)
    object_properties: list[DraftObjectProperty] = Field(default_factory=list)
    data_properties: list[DraftDataProperty] = Field(default_factory=list)
    rules: list[DraftRule] = Field(default_factory=list)


def extract_draft(regulation_text: str) -> OntologyDraft:
    """Produce a draft ontology schema from regulation text."""
    if _llm_available():
        try:
            return _llm_extract(regulation_text)
        except NotImplementedError:
            log.warning("LLM extractor not implemented yet — using stub draft")
    return _stub_draft()


def _llm_available() -> bool:
    return bool(os.getenv("OPENROUTER_API_KEYS") or os.getenv("OPENROUTER_API_KEY"))


_DRAFT_PROMPT = """Ты ассистент-онтолог. Перед тобой текст методических рекомендаций
по организации практики студентов вуза. Извлеки черновик OWL-онтологии в JSON.

Схема:
{
  "classes": [{"name": "EnglishCamelCase", "label_ru": "русская метка", "comment_ru": "1 предложение"}],
  "object_properties": [{"name": "camelCase", "domain": "ClassName", "range": "ClassName", "functional": false}],
  "data_properties": [{"name": "camelCase", "domain": "ClassName", "range": "string|integer|date", "functional": true}],
  "rules": [{"id": "R-XX", "name": "название", "description": "формулировка для проверки", "source": "стр. N или раздел"}]
}

Требования:
- Имена классов/свойств — на английском (EnglishCamelCase для классов, camelCase для свойств).
- 6–10 классов: Order, Student, Supervisor, PracticeLocation, и т.д.
- Минимум 5 правил (R-01..R-NN), каждое — конкретное проверяемое условие из текста регламента.
- Возвращай ТОЛЬКО JSON без markdown.
"""


def _llm_extract(regulation_text: str) -> OntologyDraft:
    from src.extractors.llm import (
        QuotaExhaustedError,
        get_pool,
        is_quota_exhausted_error,
    )

    model = os.environ.get("LLM_MODEL_TEXT", "deepseek/deepseek-chat-v3.1:free")
    log.info("extracting ontology draft via %s (%d chars input)", model, len(regulation_text))

    pool = get_pool()
    while True:
        try:
            client = make_client()
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": _DRAFT_PROMPT},
                    {"role": "user", "content": regulation_text},
                ],
                max_tokens=6000,
                temperature=0,
            )
            break
        except QuotaExhaustedError:
            log.warning("All keys exhausted on text extraction; using stub draft")
            return _stub_draft()
        except Exception as e:  # noqa: BLE001
            if is_quota_exhausted_error(e):
                pool.mark_exhausted(client.api_key)
                continue
            log.warning("LLM call failed (%s); falling back to stub", e)
            return _stub_draft()

    content = (resp.choices[0].message.content or "") if resp.choices else ""
    data = parse_json_response(content)
    if data is None:
        log.warning("LLM returned non-JSON; falling back to stub draft")
        return _stub_draft()
    try:
        return OntologyDraft.model_validate(data)
    except Exception as e:  # noqa: BLE001
        log.warning("LLM draft failed validation (%s); falling back to stub", e)
        return _stub_draft()


def _stub_draft() -> OntologyDraft:
    return OntologyDraft(
        classes=[
            DraftClass(name="Order", label_ru="Приказ", comment_ru="Приказ ректора"),
            DraftClass(name="Assignment", label_ru="Запись о направлении"),
            DraftClass(name="Student", label_ru="Студент"),
            DraftClass(name="Supervisor", label_ru="Руководитель"),
            DraftClass(name="PracticeLocation", label_ru="Место практики"),
            DraftClass(name="Department", label_ru="Кафедра"),
        ],
        object_properties=[
            DraftObjectProperty(name="hasAssignment", domain="Order", range="Assignment"),
            DraftObjectProperty(
                name="forStudent", domain="Assignment", range="Student", functional=True
            ),
            DraftObjectProperty(
                name="atLocation", domain="Assignment", range="PracticeLocation", functional=True
            ),
            DraftObjectProperty(
                name="supervisedBy", domain="Assignment", range="Supervisor", functional=True
            ),
            DraftObjectProperty(
                name="inDepartment", domain="Supervisor", range="Department", functional=True
            ),
        ],
        data_properties=[
            DraftDataProperty(name="orderNumber", domain="Order"),
            DraftDataProperty(name="orderDate", domain="Order", range="date"),
            DraftDataProperty(name="practiceStart", domain="Order", range="date"),
            DraftDataProperty(name="practiceEnd", domain="Order", range="date"),
            DraftDataProperty(name="programCode", domain="Order"),
            DraftDataProperty(name="practiceType", domain="Order"),
            DraftDataProperty(name="studentName", domain="Student"),
            DraftDataProperty(name="studentGroup", domain="Student"),
            DraftDataProperty(name="recordBookNumber", domain="Student"),
            DraftDataProperty(name="studentCourse", domain="Student", range="integer"),
            DraftDataProperty(name="locationOrganization", domain="PracticeLocation"),
            DraftDataProperty(name="locationAddress", domain="PracticeLocation"),
            DraftDataProperty(name="supervisorName", domain="Supervisor"),
            DraftDataProperty(name="supervisorPosition", domain="Supervisor"),
            DraftDataProperty(name="departmentName", domain="Department"),
        ],
        rules=[
            DraftRule(
                id="R-01",
                name="Заполнение обязательных полей",
                description="ФИО / группа / зач.№ / место / адрес / руководитель / кафедра",
                source="Приложения 1–3",
            ),
            DraftRule(
                id="R-02",
                name="Корректное направление подготовки",
                description="programCode ∈ {09.03.01, 09.04.01}",
                source="стр. 2",
            ),
            DraftRule(
                id="R-03",
                name="Корректные сроки",
                description="practiceStart ≤ practiceEnd",
                source="здравый смысл",
            ),
            DraftRule(
                id="R-04",
                name="Минимальный срок подготовки приказа",
                description="practiceStart - orderDate ≥ 30 дней",
                source="стр. 9",
            ),
            DraftRule(
                id="R-05",
                name="Назначен один руководитель",
                description="supervisedBy: exactly 1",
                source="стр. 6",
            ),
            DraftRule(
                id="R-06",
                name="Уникальные зачётные книжки",
                description="recordBookNumber unique across students in the order",
                source="здравый смысл",
            ),
            DraftRule(
                id="R-07",
                name="Указан тип практики",
                description="practiceType ∈ {учебная, производственная}",
                source="стр. 3",
            ),
        ],
    )
