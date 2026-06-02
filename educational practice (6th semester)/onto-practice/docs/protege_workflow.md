# Доводка LLM-черновика онтологии до финальной версии

Инструкция для аналитика. Цель: получить из `practice.draft.owl` (выход LLM)
файл `practice.owl`, по которому система реально проверяет приказы.

## 1. Что на входе

Файл `practice.draft.owl` — сырой черновик, сгенерированный LLM из текста
регламента. Скачать со страницы сервиса:

    https://<host>/ontology  →  draft / practice.draft.owl

Что в нём обычно есть (LLM):
- 6–10 классов: `Order`, `Student`, `Supervisor`, `PracticeLocation`,
  `Department`, `Assignment` и т. п.
- 5–10 объектных свойств: `hasAssignment`, `forStudent`, `atLocation` …
- 7–15 свойств данных: `orderNumber`, `practiceStart`, `studentName` …
- Несколько индивидов класса `ViolationRule` (R-01, R-02, …) — описаны
  словами, без формальной логики

Чего обычно **нет** или сделано слабо:
- классы `Violation` и `ViolationRule` без правильных аннотаций
- SWRL-правила: либо отсутствуют совсем, либо есть лишние/неточные
- русские метки `rdfs:label` и комментарии `rdfs:comment`
- ограничения по типам и кардинальности (functional, exact 1, ...)

## 2. Открыть в Protégé

1. Скачать Protégé Desktop: <https://protege.stanford.edu/>
2. `File → Open → practice.draft.owl`
3. На вкладке **Active Ontology** в правом верхнем углу проверить, что
   `Ontology IRI` непустой. Если пусто — вписать
   `http://onto-practice.local/practice.owl`.

## 3. Чек-лист доводки

Пройти по списку, отмечая что сделано.

### 3.1. Классы
- [ ] Все нужные есть: `Order`, `Assignment`, `Student`, `Supervisor`,
      `PracticeLocation`, `Department`, `ViolationRule`, `Violation`
- [ ] У каждого — `rdfs:label` на русском («Приказ», «Запись о направлении» …)
- [ ] Удалить лишние, придуманные LLM (если такие есть)
- [ ] Проверить иерархию — все классы прямые потомки `owl:Thing`,
      без случайных подклассов

### 3.2. Объектные свойства
- [ ] `hasAssignment`        : Order → Assignment
- [ ] `forStudent`            : Assignment → Student        (functional)
- [ ] `atLocation`            : Assignment → PracticeLocation (functional)
- [ ] `supervisedBy`          : Assignment → Supervisor    (functional)
- [ ] `inDepartment`          : Supervisor → Department    (functional)
- [ ] `hasViolation`          : Order → Violation
- [ ] `violatesRule`          : Violation → ViolationRule  (functional)
- [ ] `concernsAssignment`    : Violation → Assignment

### 3.3. Свойства данных
Тип везде `xsd:string`, кроме `studentCourse` (xsd:integer).

- [ ] `orderNumber`, `orderDate`, `practiceStart`, `practiceEnd`,
      `programCode`, `programName`, `practiceType` — domain `Order`
- [ ] `studentName`, `studentGroup`, `recordBookNumber`, `studentCourse` — domain `Student`
- [ ] `locationOrganization`, `locationAddress` — domain `PracticeLocation`
- [ ] `supervisorName`, `supervisorPosition` — domain `Supervisor`
- [ ] `departmentName` — domain `Department`
- [ ] `violationMessage`, `violationSeverity` — domain `Violation`
- [ ] `ruleId`, `ruleName`, `ruleDescription`, `ruleSource` — domain `ViolationRule`

Все — Functional.

### 3.4. Индивиды правил (ABox)

Должно быть ровно семь индивидов класса `ViolationRule` с заполненными
`ruleId`, `ruleName`, `ruleDescription`, `ruleSource`:

| ID    | Краткое название                       | Источник         |
|-------|----------------------------------------|------------------|
| R-01  | Заполнение обязательных полей          | Приложения 1–3   |
| R-02  | Корректное направление подготовки      | стр. 2           |
| R-03  | Корректные сроки практики              | здравый смысл    |
| R-04  | Минимальный срок подготовки приказа    | стр. 9           |
| R-05  | Назначен один руководитель от НГУ      | стр. 6           |
| R-06  | Уникальность зачётных книжек           | здравый смысл    |
| R-07  | Указан тип практики                    | стр. 3           |

LLM иногда даёт меньше или формулирует иначе — добавить недостающее, убрать
дубли.

### 3.5. SWRL-правила (опционально)

Если делаете формальный вариант через SWRL — добавить в Protégé на вкладке
`Window → Views → Rules → SWRL Rules`. Минимум:

```
# R-02: программа должна быть из разрешённого набора
Order(?o) ^ programCode(?o, ?p) ^ swrlb:notEqual(?p, "09.03.01") ^
  swrlb:notEqual(?p, "09.04.01") -> hasViolation(?o, ?v) ^ Violation(?v) ^
  violatesRule(?v, rule_R_02)
```

В прототипе SWRL-аналог реализован программно в `src/core/checker.py`
(каждое правило R-XX — отдельная функция `_check_RXX`). Это работает быстрее
и проще отлаживается, поэтому SWRL не обязателен — достаточно того, что
правила-индивиды описаны как ABox.

### 3.6. Сохранение

1. `File → Save as… → RDF/XML`
2. Имя файла строго `practice.owl`
3. Кодировка — UTF-8

## 4. Заменить файл на сервере

Локально:
```bash
cp /путь/к/practice.owl ~/profi/onto/regulations/practice.owl
# Перезапустить uvicorn:
pkill -f 'uvicorn src.web.main'
nohup .venv/bin/uvicorn src.web.main:app --host 0.0.0.0 --port 18000 \
  --log-level info > /tmp/onto-prod.log 2>&1 &
```

Через веб (если приватного доступа к серверу нет — спросить у разработчика):
1. Аналитик присылает `practice.owl` в чат
2. Разработчик кладёт файл в `regulations/`, перезапускает сервис

После перезапуска новая онтология видна на странице
`/ontology` в категории **final**, и runtime-проверка приказов сразу
использует её — никаких других правок кода не нужно.

## 5. Проверка что доводка прошла корректно

Загрузить демо-приказ на главной странице сервиса и убедиться, что в отчёте:

- появились все 7 правил `R-01..R-07` в разделе «Применённые правила»
- хотя бы одно нарушение поймано (минимум R-04 на демо-приказе срока)
- reasoner отрабатывает без ошибок (зелёный бейдж «HermiT OK»)

Если что-то поплыло — открыть `practice.owl` в Protégé снова, починить,
повторить шаг 4.
