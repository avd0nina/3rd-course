from dataclasses import dataclass
import os
import re
import ssl
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from bs4 import BeautifulSoup


FACULTY_FIT_PATH = "/faculty/fit"
GROUP_PATH_TEMPLATE = "/group/{group_number}"
GROUP_LINK_PATTERN = re.compile(r"^/group/(\d{5})$")
TIME_PATTERN = re.compile(r"^\d{1,2}:\d{2}$")
ENTITY_KEY_PATTERN = re.compile(r"[^0-9a-zа-я]+", re.IGNORECASE)
ROOM_PREFIX_PATTERN = re.compile(r"^(?:ауд\.?|аудитория)\s*", re.IGNORECASE)
TEACHER_MULTI_DOT_PATTERN = re.compile(r"\.{2,}")

DISCIPLINE_ALIASES = {
    "мат.анализ": "Математический анализ",
    "ин. яз.": "Иностранный язык",
    "алг.и структ.дан.": "Алгоритмы и структура данных",
}

BELL_END_TIMES = {
    "09:00": "10:35",
    "10:50": "12:25",
    "12:40": "14:15",
    "14:30": "16:05",
    "16:20": "17:55",
    "18:10": "19:45",
    "20:00": "21:35",
}


class NSUIntegrationError(Exception):
    pass


@dataclass(frozen=True)
class NormalizedEntity:
    raw: str
    normalized: str
    key: str


@dataclass(frozen=True)
class ParsedScheduleEntry:
    day_of_week: str
    start_time: str
    end_time: str
    subject: str
    lesson_type: str
    teacher: str
    room: str
    week: str
    group_number: str = ""
    group_key: str = ""
    discipline_raw: str = ""
    discipline_key: str = ""
    teacher_raw: str = ""
    teacher_key: str = ""
    room_raw: str = ""
    room_key: str = ""


def _clean_text(value: str) -> str:
    return " ".join(value.split())


def _entity_key(value: str) -> str:
    return ENTITY_KEY_PATTERN.sub("", value.casefold().replace("ё", "е"))


def _normalize_time(value: str) -> str:
    match = re.fullmatch(r"(\d{1,2}):(\d{2})", value.strip())
    if not match:
        return value.strip()
    hours = int(match.group(1))
    minutes = match.group(2)
    return f"{hours:02d}:{minutes}"


class NSUIntegrationService:
    def __init__(
        self,
        base_url: str = "https://table.nsu.ru",
        timeout: int = 15,
        fetcher: Callable[[str], str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.fetcher = fetcher
        self._fit_groups_cache = None

    def get_fit_groups(self, refresh: bool = False) -> list[str]:
        if self._fit_groups_cache is not None and not refresh:
            return list(self._fit_groups_cache)

        html = self._fetch(FACULTY_FIT_PATH)
        soup = BeautifulSoup(html, "html.parser")
        groups = set()

        for group_link in soup.select('a.group[href^="/group/"]'):
            href = group_link.get("href", "")
            match = GROUP_LINK_PATTERN.fullmatch(href.strip())
            if not match:
                continue
            group_number = match.group(1)
            if self._is_bachelor_group(group_number):
                groups.add(group_number)

        if not groups:
            raise NSUIntegrationError("Не удалось получить список групп ФИТ с сайта НГУ.")

        self._fit_groups_cache = sorted(groups)
        return list(self._fit_groups_cache)

    def get_group_schedule(self, group_number: str) -> list[ParsedScheduleEntry]:
        group_entity = self.normalize_group_entity(group_number)
        normalized_group = group_entity.normalized
        if not re.fullmatch(r"\d{5}", normalized_group):
            raise ValueError("Номер группы должен содержать 5 цифр.")

        html = self._fetch(GROUP_PATH_TEMPLATE.format(group_number=normalized_group))
        soup = BeautifulSoup(html, "html.parser")
        schedule_table = soup.select_one("table.time-table")
        if schedule_table is None:
            raise NSUIntegrationError(f"Не удалось найти таблицу расписания для группы {normalized_group}.")

        header_row = schedule_table.find("tr")
        if header_row is None:
            raise NSUIntegrationError(f"Таблица расписания группы {normalized_group} не содержит заголовок.")

        day_headers = [
            _clean_text(th.get_text(" ", strip=True))
            for th in header_row.find_all("th")[1:]
        ]
        if not day_headers:
            raise NSUIntegrationError(f"Не удалось определить дни недели для группы {normalized_group}.")

        parsed_entries: list[ParsedScheduleEntry] = []
        for row in schedule_table.find_all("tr")[1:]:
            row_cells = row.find_all("td", recursive=False)
            if not row_cells:
                continue

            raw_start_time = _clean_text(row_cells[0].get_text(" ", strip=True))
            if not TIME_PATTERN.fullmatch(raw_start_time):
                continue

            start_time = _normalize_time(raw_start_time)
            end_time = BELL_END_TIMES.get(start_time, start_time)

            for day_name, day_cell in zip(day_headers, row_cells[1:]):
                lesson_blocks = day_cell.find_all("div", class_="cell", recursive=False)
                for lesson_block in lesson_blocks:
                    subject_node = lesson_block.find("div", class_="subject")
                    if subject_node is None:
                        continue

                    lesson_type_node = lesson_block.find("span", class_="type")
                    room_node = lesson_block.find("div", class_="room")
                    teacher_node = lesson_block.find("a", class_="tutor")
                    week_node = lesson_block.find("div", class_="week")

                    subject_text = subject_node.get("title") or subject_node.get_text(" ", strip=True)
                    discipline_entity = self.normalize_discipline_entity(subject_text)
                    teacher_raw = teacher_node.get_text(" ", strip=True) if teacher_node else ""
                    room_raw = room_node.get_text(" ", strip=True) if room_node else ""
                    teacher_entity = self.normalize_teacher_entity(teacher_raw)
                    room_entity = self.normalize_room_entity(room_raw)
                    parsed_entries.append(
                        ParsedScheduleEntry(
                            day_of_week=day_name,
                            start_time=start_time,
                            end_time=end_time,
                            subject=discipline_entity.normalized,
                            lesson_type=_clean_text(lesson_type_node.get_text(" ", strip=True)) if lesson_type_node else "",
                            teacher=teacher_entity.normalized,
                            room=room_entity.normalized,
                            week=_clean_text(week_node.get_text(" ", strip=True)) if week_node else "",
                            group_number=group_entity.normalized,
                            group_key=group_entity.key,
                            discipline_raw=discipline_entity.raw,
                            discipline_key=discipline_entity.key,
                            teacher_raw=teacher_entity.raw,
                            teacher_key=teacher_entity.key,
                            room_raw=room_entity.raw,
                            room_key=room_entity.key,
                        )
                    )

        return parsed_entries

    def _fetch(self, path: str) -> str:
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        if self.fetcher is not None:
            return self.fetcher(url)

        ssl_context = self._build_ssl_context()
        try:
            with urlopen(url, timeout=self.timeout, context=ssl_context) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset, errors="replace")
        except ssl.SSLCertVerificationError as error:
            raise NSUIntegrationError(
                "Ошибка TLS-сертификата при подключении к table.nsu.ru. "
                "Укажите путь к корпоративному корневому сертификату через NSU_CA_BUNDLE "
                "или (небезопасно) временно отключите проверку через NSU_DISABLE_SSL_VERIFY=1."
            ) from error
        except (HTTPError, URLError, TimeoutError) as error:
            reason = getattr(error, "reason", None)
            if isinstance(reason, ssl.SSLCertVerificationError):
                raise NSUIntegrationError(
                    "Ошибка TLS-сертификата при подключении к table.nsu.ru. "
                    "Укажите путь к корпоративному корневому сертификату через NSU_CA_BUNDLE "
                    "или (небезопасно) временно отключите проверку через NSU_DISABLE_SSL_VERIFY=1."
                ) from error
            raise NSUIntegrationError(f"Ошибка при запросе {url}: {error}") from error

    @staticmethod
    def _build_ssl_context() -> ssl.SSLContext:
        disable_ssl_verify = os.getenv("NSU_DISABLE_SSL_VERIFY", "").strip().lower() in {"1", "true", "yes"}
        if disable_ssl_verify:
            return ssl._create_unverified_context()

        custom_ca_bundle = os.getenv("NSU_CA_BUNDLE", "").strip()
        if custom_ca_bundle:
            return ssl.create_default_context(cafile=custom_ca_bundle)

        try:
            import certifi

            return ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            return ssl.create_default_context()

    @staticmethod
    def normalize_group_entity(group_number: str) -> NormalizedEntity:
        raw = _clean_text(group_number)
        digits_only = re.sub(r"\D", "", raw)
        normalized = digits_only if len(digits_only) == 5 else raw
        return NormalizedEntity(raw=raw, normalized=normalized, key=_entity_key(normalized))

    @staticmethod
    def normalize_discipline_entity(discipline: str) -> NormalizedEntity:
        raw = _clean_text(discipline)
        normalized = DISCIPLINE_ALIASES.get(raw.casefold(), raw)
        normalized = _clean_text(normalized)
        return NormalizedEntity(raw=raw, normalized=normalized, key=_entity_key(normalized))

    @staticmethod
    def normalize_teacher_entity(teacher: str) -> NormalizedEntity:
        raw = _clean_text(teacher)
        normalized = TEACHER_MULTI_DOT_PATTERN.sub(".", raw)
        normalized = re.sub(r"([А-ЯЁA-Z])\.\s+([А-ЯЁA-Z])\.", r"\1.\2.", normalized)
        normalized = _clean_text(normalized)
        return NormalizedEntity(raw=raw, normalized=normalized, key=_entity_key(normalized))

    @staticmethod
    def normalize_room_entity(room: str) -> NormalizedEntity:
        raw = _clean_text(room)
        normalized = ROOM_PREFIX_PATTERN.sub("", raw).strip()
        if not normalized:
            normalized = raw
        normalized = _clean_text(normalized)
        return NormalizedEntity(raw=raw, normalized=normalized, key=_entity_key(normalized))

    @staticmethod
    def _is_bachelor_group(group_number: str) -> bool:
        if len(group_number) != 5 or not group_number.isdigit():
            return False
        if group_number[2] != "2":
            return False
        group_index = int(group_number[-2:])
        return 1 <= group_index <= 17

    @staticmethod
    def compare_snapshots(current_entries: list, previous_entries: list) -> dict:
        """Compare current and previous snapshots to identify changes.
        
        Returns dict with:
        - added: lessons in current but not in previous
        - removed: lessons in previous but not in current
        - modified: lessons with same day/time but different details
        """
        def entry_key(entry):
            return (entry.day_of_week, entry.start_time, entry.end_time)
        
        current_map = {entry_key(e): e for e in current_entries}
        previous_map = {entry_key(e): e for e in previous_entries}
        
        added = [e for key, e in current_map.items() if key not in previous_map]
        removed = [e for key, e in previous_map.items() if key not in current_map]
        
        modified = []
        for key in set(current_map.keys()) & set(previous_map.keys()):
            if current_map[key].subject != previous_map[key].subject:
                modified.append({
                    'previous': previous_map[key],
                    'current': current_map[key]
                })
        
        return {
            'added': added,
            'removed': removed,
            'modified': modified,
            'has_changes': bool(added or removed or modified)
        }
