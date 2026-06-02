"""Build docs/onto-practice.pdf — project description + usage instructions for the customer.

Pure Python via reportlab, no system dependencies, embeds DejaVu Sans for Cyrillic.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT = ROOT / "docs" / "onto-practice.pdf"


def _register_fonts() -> str:
    """Register Cyrillic-capable fonts. DejaVu ships with most Linux distros."""
    base = Path("/usr/share/fonts/truetype/dejavu")
    sans = base / "DejaVuSans.ttf"
    sans_bold = base / "DejaVuSans-Bold.ttf"
    mono = base / "DejaVuSansMono.ttf"
    if not sans.exists():
        return "Helvetica"
    pdfmetrics.registerFont(TTFont("DejaVu", str(sans)))
    if sans_bold.exists():
        pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(sans_bold)))
    if mono.exists():
        pdfmetrics.registerFont(TTFont("DejaVuMono", str(mono)))
    return "DejaVu"


def _styles(font: str) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle(
            name="Title", parent=base["Title"], fontName=f"{font}-Bold" if font == "DejaVu" else "Helvetica-Bold",
            fontSize=22, leading=26, spaceAfter=14, textColor=colors.HexColor("#1a1d24"),
        ),
        "H1": ParagraphStyle(
            name="H1", parent=base["Heading1"], fontName=f"{font}-Bold" if font == "DejaVu" else "Helvetica-Bold",
            fontSize=16, leading=20, spaceBefore=18, spaceAfter=8, textColor=colors.HexColor("#1a1d24"),
        ),
        "H2": ParagraphStyle(
            name="H2", parent=base["Heading2"], fontName=f"{font}-Bold" if font == "DejaVu" else "Helvetica-Bold",
            fontSize=13, leading=17, spaceBefore=12, spaceAfter=6, textColor=colors.HexColor("#1a1d24"),
        ),
        "Body": ParagraphStyle(
            name="Body", parent=base["BodyText"], fontName=font, fontSize=10.5, leading=15,
            spaceAfter=8, textColor=colors.HexColor("#1a1d24"),
        ),
        "Code": ParagraphStyle(
            name="Code", parent=base["Code"],
            fontName="DejaVuMono" if font == "DejaVu" else "Courier",
            fontSize=9, leading=12,
            backColor=colors.HexColor("#f6f7f9"), borderPadding=6, leftIndent=8, rightIndent=8,
            spaceBefore=4, spaceAfter=8,
        ),
        "Muted": ParagraphStyle(
            name="Muted", parent=base["BodyText"], fontName=font, fontSize=9.5, leading=13,
            spaceAfter=8, textColor=colors.HexColor("#6b7280"),
        ),
    }


def _bullet(text: str, st: ParagraphStyle) -> Paragraph:
    return Paragraph(f"• {text}", st)


def _table(rows: list[list[str]], font: str, col_widths=None) -> Table:
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f6f7f9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1a1d24")),
        ("FONTNAME", (0, 0), (-1, -1), font),
        ("FONTNAME", (0, 0), (-1, 0), f"{font}-Bold" if font == "DejaVu" else "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("LEADING", (0, 0), (-1, -1), 13),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e5e7eb")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def build() -> None:
    font = _register_fonts()
    s = _styles(font)
    doc = SimpleDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title="onto-practice — описание проекта",
    )

    story: list = []

    story.append(Paragraph("onto-practice", s["Title"]))
    story.append(Paragraph(
        "Прототип системы автоматической проверки приказов о направлении на практику "
        "студентов на соответствие регламенту кафедры через OWL-онтологию и встроенный "
        "ризонер.", s["Body"]))
    story.append(Paragraph(
        "Регламент-источник: «Методические рекомендации по организации и проведению "
        "практики обучающихся ФИТ» НГУ (направления 09.03.01 / 09.04.01).", s["Muted"]))

    # ─────────────────────────────────────────────────────────
    story.append(Paragraph("1. Что делает система", s["H1"]))
    story.append(Paragraph(
        "Принимает PDF, DOCX или TXT с приказом ректора о направлении студентов "
        "на практику и выдаёт HTML-отчёт: какие пункты регламента нарушены, "
        "по каким студентам, со ссылкой на пункт регламента.", s["Body"]))
    story.append(_bullet("Извлечение фактов из документа делает LLM (через сервис OpenRouter).", s["Body"]))
    story.append(_bullet("Применение правил делает классический OWL DL-ризонер HermiT.", s["Body"]))
    story.append(_bullet("Сами правила хранятся в OWL-файле — онтологии регламента, которую можно "
                         "редактировать в Protégé без правок кода ядра.", s["Body"]))

    story.append(Paragraph("2. Архитектура — два пайплайна", s["H1"]))
    story.append(Paragraph(
        "Система состоит из двух независимых процессов. Они идут по разному поводу, "
        "разными командами, имеют разные SLA.", s["Body"]))

    story.append(Paragraph("2.1. Build-time — построение онтологии (один раз на регламент)", s["H2"]))
    story.append(Paragraph(
        "PDF регламента → текст → LLM извлекает черновик онтологии (классы, свойства, "
        "правила) → аналитик дорабатывает черновик в Protégé → итоговый "
        "<b>practice.owl</b>, который кладётся в <code>regulations/</code>.", s["Body"]))
    story.append(Paragraph(
        "Этап выполняется один раз на каждый регламент. Чтобы добавить регламент "
        "другой кафедры — кладём ещё один <code>.owl</code> в ту же папку.", s["Muted"]))

    story.append(Paragraph("2.2. Runtime — проверка одного приказа", s["H2"]))
    story.append(Paragraph(
        "Пользователь загружает PDF/DOCX/TXT приказа → пайплайн извлекает данные "
        "(OCR + структурирование текстом) → факты подгружаются в копию онтологии "
        "как individuals → HermiT прогоняет правила → отчёт сохраняется и "
        "отображается.", s["Body"]))

    story.append(Paragraph("3. Стек технологий", s["H1"]))
    story.append(_table([
        ["Компонент", "Технология"],
        ["Веб-сервер", "FastAPI + Jinja2 + минимальный CSS"],
        ["Онтология", "OWL 2 / RDF-XML, читается через owlready2"],
        ["DL-ризонер", "HermiT (Java, поднимается owlready2 автоматически)"],
        ["Извлечение данных из PDF/DOCX/TXT", "PyMuPDF + Microsoft Word OCR (опционально) + python-docx"],
        ["Удалённый OCR (для сканов)", "OpenRouter, модель baidu/qianfan-ocr-fast"],
        ["Структурирование текста в JSON", "OpenRouter, модель inclusionai/ling-2.6-1t (с fallback-цепочкой)"],
        ["Управление LLM-ключами", "in-memory pool с ротацией на дневной лимит и upstream rate-limit"],
    ], font, col_widths=[5.5 * cm, 11 * cm]))

    story.append(Paragraph("4. Правила проверки (R-01..R-07)", s["H1"]))
    story.append(Paragraph(
        "Правила хранятся в онтологии как индивиды класса ViolationRule. "
        "Проверки реализованы в <code>src/core/checker.py</code>.", s["Body"]))
    story.append(_table([
        ["ID", "Правило", "Источник в регламенте"],
        ["R-01", "Заполнены все обязательные поля по студенту", "Приложения 1–3"],
        ["R-02", "Программа подготовки ∈ {09.03.01, 09.04.01}", "стр. 2"],
        ["R-03", "Дата начала ≤ даты окончания практики", "здравый смысл"],
        ["R-04", "От даты приказа до начала практики ≥ 30 дней", "стр. 9"],
        ["R-05", "Назначен один руководитель от НГУ", "стр. 6"],
        ["R-06", "Номера зачётных книжек уникальны", "здравый смысл"],
        ["R-07", "Указан тип практики (учебная / производственная)", "стр. 3"],
    ], font, col_widths=[1.5 * cm, 9.5 * cm, 5.5 * cm]))

    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────
    story.append(Paragraph("5. Инструкция: проверка приказа", s["H1"]))
    story.append(Paragraph("Аудитория: сотрудник учебно-методического отдела.", s["Muted"]))

    story.append(Paragraph("Шаг 1. Открыть веб-приложение", s["H2"]))
    story.append(Paragraph(
        "Перейти по адресу системы. На главной странице — форма загрузки.", s["Body"]))

    story.append(Paragraph("Шаг 2. Подготовить файл приказа", s["H2"]))
    story.append(Paragraph(
        "Поддерживаются три формата:", s["Body"]))
    story.append(_bullet("<b>.docx</b> или <b>.txt</b> — самое лучшее качество. Если у вас "
                         "сканированный PDF — откройте его в Word, Word автоматически "
                         "распознает текст, сохраните как .docx и используйте его.", s["Body"]))
    story.append(_bullet("<b>.pdf</b> — система прогонит свой OCR; качество распознавания "
                         "русских фамилий на сканах низкого разрешения хуже, чем у Word.", s["Body"]))

    story.append(Paragraph("Шаг 3. Загрузить и подождать", s["H2"]))
    story.append(_bullet("DOCX/TXT — обработка ~30–60 секунд.", s["Body"]))
    story.append(_bullet("PDF (скан) — 2–7 минут на бесплатных моделях.", s["Body"]))
    story.append(_bullet("Страница автоматически обновляется. По готовности появится отчёт.", s["Body"]))

    story.append(Paragraph("Шаг 4. Прочитать отчёт", s["H2"]))
    story.append(Paragraph(
        "Отчёт состоит из четырёх блоков:", s["Body"]))
    story.append(_bullet("<b>Сводка</b> — число студентов, число нарушений, статус ризонера.", s["Body"]))
    story.append(_bullet("<b>Параметры приказа</b> — что распарсено: номер, период, направление, тип.", s["Body"]))
    story.append(_bullet("<b>Нарушения</b> — таблица: код правила, студент, описание, ссылка на "
                         "пункт регламента. Ошибки выделены красной полосой слева, "
                         "предупреждения — оранжевой.", s["Body"]))
    story.append(_bullet("<b>Применённые правила</b> — справка по всем R-01..R-07 с описанием "
                         "и источником в регламенте.", s["Body"]))

    story.append(Paragraph("Шаг 5. Что делать с нарушениями", s["H2"]))
    story.append(_bullet("R-04 (срок): согласовать перенос приказа на более раннюю дату или "
                         "перенести начало практики.", s["Body"]))
    story.append(_bullet("R-01 / R-05 (пустые поля): сверить с реальным документом — иногда "
                         "это OCR-пропуск; если действительно не заполнено — дополнить приказ.", s["Body"]))
    story.append(_bullet("R-02 (программа): проверить код в шапке приказа — возможно опечатка.", s["Body"]))

    story.append(Paragraph("6. Инструкция: обновление онтологии", s["H1"]))
    story.append(Paragraph("Аудитория: аналитик / эксперт по регламенту.", s["Muted"]))

    story.append(Paragraph("Когда нужно обновлять онтологию", s["H2"]))
    story.append(_bullet("Регламент кафедры обновился — новые правила, новые требования к полям.", s["Body"]))
    story.append(_bullet("Появилась новая образовательная программа — расширили список допустимых "
                         "направлений в R-02.", s["Body"]))
    story.append(_bullet("Поменялась форма приказа — например, добавилась колонка.", s["Body"]))

    story.append(Paragraph("Как обновить", s["H2"]))
    story.append(_bullet("Открыть страницу <b>Онтология</b> → нажать «скачать» рядом с draft.", s["Body"]))
    story.append(_bullet("Открыть скачанный <code>practice.draft.owl</code> в Protégé.", s["Body"]))
    story.append(_bullet("Доработать по чек-листу из инструкции <code>/ontology/workflow</code> "
                         "(она доступна как ссылка на странице Онтология).", s["Body"]))
    story.append(_bullet("Сохранить как <code>practice.owl</code> в формате RDF/XML.", s["Body"]))
    story.append(_bullet("Вернуться на страницу Онтология, в форме <b>«Загрузить новую финальную "
                         "онтологию»</b> выбрать файл и нажать «Загрузить».", s["Body"]))
    story.append(_bullet("Старая версия автоматически бэкапится в <code>var/backups/</code>.", s["Body"]))
    story.append(_bullet("Следующая проверка приказа использует уже новую онтологию.", s["Body"]))

    story.append(Paragraph("Чтобы получить совершенно новый черновик из обновлённого регламента", s["H2"]))
    story.append(Paragraph(
        "Это разовая команда у разработчика — пайплайн читает PDF регламента, "
        "вызывает LLM, кладёт черновик в <code>var/drafts/</code> откуда его можно "
        "скачать через интерфейс:", s["Body"]))
    story.append(Paragraph("python scripts/build_ontology.py путь/к/новому/регламенту.pdf", s["Code"]))

    story.append(PageBreak())

    # ─────────────────────────────────────────────────────────
    story.append(Paragraph("7. Ограничения текущей реализации", s["H1"]))
    story.append(Paragraph(
        "Прототип построен на бесплатных моделях OpenRouter — это влияет на "
        "качество и скорость:", s["Body"]))
    story.append(_bullet("<b>Точность распознавания фамилий</b> на скан-PDF — около 50–70%. "
                         "Word OCR (для DOCX) даёт ~90%. Платные модели типа GPT-5-nano или "
                         "Mistral OCR дают 95–99%.", s["Body"]))
    story.append(_bullet("<b>Дневной лимит</b> бесплатного OpenRouter — 50 запросов на ключ. "
                         "В системе ротация по 5 ключам = 250 запросов в день, ~25 приказов.", s["Body"]))
    story.append(_bullet("<b>Иногда зависают</b> запросы к перегруженным провайдерам моделей. "
                         "Логируется, выставлены timeout/retry, в худшем случае — "
                         "загрузить файл заново.", s["Body"]))

    story.append(Paragraph("Что меняется при переходе на платный тариф", s["H2"]))
    story.append(Paragraph(
        "Один тот же ключ OpenRouter работает и с бесплатными, и с платными моделями. "
        "Достаточно положить кредиты на счёт и поменять две строки в конфиге .env "
        "(имена моделей):", s["Body"]))
    story.append(Paragraph(
        "LLM_MODEL_VISION=mistral/mistral-ocr-latest<br/>"
        "LLM_MODEL_TEXT=openai/gpt-4o-mini", s["Code"]))
    story.append(Paragraph(
        "Один приказ обходится в 1–2 цента. $5 хватает на 250–500 приказов. "
        "Время обработки — 20–40 секунд. Никаких rate-limit.", s["Muted"]))

    story.append(Paragraph("Чего нет в прототипе (по техническому заданию)", s["H1"]))
    story.append(_bullet("Аутентификация и роли — все эндпойнты публичные.", s["Body"]))
    story.append(_bullet("База данных отчётов — отчёты лежат как JSON-файлы в <code>var/reports/</code>.", s["Body"]))
    story.append(_bullet("Редактирование онтологии через UI — только через Protégé. Загрузка "
                         "готового файла через UI — есть.", s["Body"]))
    story.append(_bullet("Production-deploy — система запускается локально через uvicorn, для "
                         "теста заказчика выставлена через Cloudflare Quick Tunnel.", s["Body"]))

    # ─────────────────────────────────────────────────────────
    story.append(Paragraph("8. Локальное развёртывание", s["H1"]))
    story.append(Paragraph("Аудитория: разработчик / системный администратор.", s["Muted"]))

    story.append(Paragraph("8.1. Что нужно из коробки", s["H2"]))
    story.append(_bullet("Linux / macOS / Windows с Python 3.11 или новее.", s["Body"]))
    story.append(_bullet("~3 ГБ свободного места (для venv с зависимостями и онтологии).", s["Body"]))
    story.append(_bullet("Доступ в интернет к https://openrouter.ai (для LLM-вызовов).", s["Body"]))
    story.append(_bullet("Java 17+ — нужна ризонеру HermiT. Если в системе Java нет, "
                         "приложение само установит её при первом запуске через "
                         "pip-пакет install-jdk в каталог <code>~/.jdk/</code>.", s["Body"]))

    story.append(Paragraph("8.2. Скачать исходники", s["H2"]))
    story.append(Paragraph(
        "Архив со всеми файлами проекта доступен по адресу "
        "<b>/docs/onto-practice-source.zip</b> на работающем сервисе. "
        "Распаковать в любую папку, дальше всё запускается из неё.", s["Body"]))

    story.append(Paragraph("8.3. Поставить зависимости и запустить", s["H2"]))
    story.append(Paragraph(
        "cd onto-practice<br/>"
        "python3 -m venv .venv<br/>"
        "source .venv/bin/activate            # Windows: .venv\\Scripts\\activate<br/>"
        "pip install -e \".[dev]\"<br/><br/>"
        "# (если нет java в PATH)<br/>"
        "python -c \"import jdk; jdk.install('17')\"<br/><br/>"
        "# .env: положить ключ OpenRouter<br/>"
        "cp .env.example .env<br/>"
        "# отредактировать .env: подставить OPENROUTER_API_KEYS=sk-or-v1-...<br/><br/>"
        "uvicorn src.web.main:app --host 0.0.0.0 --port 8000 --reload",
        s["Code"]))
    story.append(Paragraph(
        "Открыть в браузере http://localhost:8000 — должна появиться форма "
        "загрузки приказа.", s["Body"]))

    story.append(Paragraph("8.4. Регенерация черновика онтологии (по необходимости)", s["H2"]))
    story.append(Paragraph(
        "Если регламент кафедры обновился — перегенерировать LLM-черновик:", s["Body"]))
    story.append(Paragraph(
        "python scripts/build_ontology.py путь/к/regulation.pdf",
        s["Code"]))
    story.append(Paragraph(
        "Файл попадёт в <code>var/drafts/practice.draft.owl</code> и появится в "
        "интерфейсе на странице Онтология. Дальше — доводка в Protégé по разделу 6.",
        s["Body"]))

    story.append(Paragraph("8.5. Проверки и линтер", s["H2"]))
    story.append(Paragraph(
        "ruff check .       # стиль кода<br/>"
        "pytest             # тесты (опционально, минимально)",
        s["Code"]))

    story.append(Paragraph("8.6. Где что лежит", s["H2"]))
    story.append(_bullet("<code>regulations/practice.owl</code> — рабочая онтология "
                         "регламента (по ней проверяются приказы).", s["Body"]))
    story.append(_bullet("<code>.env</code> — ключи OpenRouter и имена моделей.", s["Body"]))
    story.append(_bullet("<code>var/uploads/</code> — загруженные документы.", s["Body"]))
    story.append(_bullet("<code>var/reports/</code> — отчёты по проверкам в JSON.", s["Body"]))
    story.append(_bullet("<code>var/cache/facts/</code> — кэш извлечённых фактов "
                         "по SHA256 файла (повторная загрузка идёт мгновенно).", s["Body"]))
    story.append(_bullet("<code>var/backups/</code> — бэкапы предыдущих версий "
                         "<code>practice.owl</code> при загрузке через UI.", s["Body"]))

    story.append(Paragraph("8.7. Типичные проблемы", s["H2"]))
    story.append(_bullet("«HermiT reasoner unavailable: no java»: Java не нашлась. "
                         "Запустить <code>python -c \"import jdk; jdk.install('17')\"</code> "
                         "и перезапустить uvicorn.", s["Body"]))
    story.append(_bullet("«All structure models failed»: упёрлись в дневной лимит "
                         "OpenRouter всеми ключами. Подождать сутки или пополнить "
                         "счёт ($5 даёт 1000 free req/day или платные модели за центы).", s["Body"]))
    story.append(_bullet("«No endpoints found for &lt;model&gt;»: модель сняли с "
                         "free tier. Поменять <code>LLM_MODEL_TEXT</code> или "
                         "<code>LLM_MODEL_VISION</code> в <code>.env</code> "
                         "на актуальную бесплатную модель из "
                         "<code>https://openrouter.ai/models?max_price=0</code>.", s["Body"]))

    story.append(PageBreak())

    story.append(Paragraph("9. Структура проекта", s["H1"]))
    story.append(Paragraph(
        "src/builder — build-time pipeline (PDF регламента → черновик онтологии)<br/>"
        "src/extractors — runtime pipeline (документ приказа → факты)<br/>"
        "src/core — загрузка онтологии, инжекция фактов, ризонер, отчёт<br/>"
        "src/web — FastAPI + Jinja2 шаблоны<br/>"
        "regulations/ — итоговые .owl-файлы регламентов (плагины ядра)<br/>"
        "var/drafts — LLM-черновики до доводки в Protégé<br/>"
        "var/uploads, var/reports, var/cache — runtime-данные<br/>"
        "docs — requirements, architecture, эта документация", s["Code"]))

    story.append(Paragraph("10. Контрольный пример", s["H1"]))
    story.append(Paragraph(
        "Демо-приказ — <b>№ 0145-2 от 22.01.2026</b> о направлении студентов 3 курса "
        "ПИиКН на учебную практику с 02.02.2026 по 28.05.2026.", s["Body"]))
    story.append(Paragraph(
        "Между датой приказа (22.01) и началом практики (02.02) всего 11 дней, "
        "регламент требует не менее 30. Система должна срабатывать <b>R-04</b> на "
        "этом приказе — это поддерживает любая загрузка демо-документа.", s["Body"]))

    doc.build(story)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    build()
