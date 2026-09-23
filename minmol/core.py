from __future__ import annotations

import json
import os
import re
import uuid
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path


MONTHS = (
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
)

TARGETS = (
    {
        "id": "01",
        "report_row": "01",
        "code": "1П",
        "name": "Участники проектов и программ, направленных на патриотическое воспитание",
        "report_name": "Общая численность молодых людей в возрасте от 14 до 35 лет включительно, принявших участие в проектах и программах, направленных на патриотическое воспитание, реализованных органами местного самоуправления, исполнительными органами субъекта Российской Федерации и финансируемыми ими организациями, на конец отчетного месяца/года нарастающим итогом с начала отчетного года, человек",
        "section": "ПРОЕКТЫ И ПРОГРАММЫ, НАПРАВЛЕННЫЕ НА ПАТРИОТИЧЕСКОЕ ВОСПИТАНИЕ, РЕАЛИЗОВАННЫЕ ОРГАНАМИ МЕСТНОГО САМОУПРАВЛЕНИЯ",
    },
    {
        "id": "02",
        "report_row": "02",
        "code": "2ПРОФ",
        "name": "Участники мероприятий, направленных на профессиональное и личностное развитие",
        "report_name": "Общая численность молодых людей в возрасте от 14 до 35 лет включительно, принявших участие в проектах и программах, направленных на профессиональное, личностное развитие, реализованных органами местного самоуправления, исполнительными органами субъекта Российской Федерации и финансируемыми ими организациями, на конец отчетного месяца/года нарастающим итогом с начала отчетного года, человек",
        "section": "ПРОЕКТЫ И ПРОГРАММЫ, НАПРАВЛЕННЫЕ НА ПРОФЕССИОНАЛЬНОЕ, ЛИЧНОСТНОЕ РАЗВИТИЕ, РЕАЛИЗОВАННЫЕ ОРГАНАМИ МЕСТНОГО САМОУПРАВЛЕНИЯ",
    },
    {
        "id": "03",
        "report_row": "05",
        "code": "3С",
        "name": "Молодые семьи в мероприятиях по продвижению традиционных ценностей",
        "report_name": "Фактическое количество молодых семей, принявших участие в мероприятиях, направленных на продвижение традиционных духовно-нравственных ценностей, в проектах и программах, направленных на патриотическое воспитание, вовлечение в добровольческую и общественную деятельность, реализованных органами местного самоуправления, исполнительными органами субъектов Российской Федерации и финансируемыми ими организациями, на конец отчетного месяца/года нарастающим итогом с начала года, единица",
        "section": "ПРОЕКТЫ И ПРОГРАММЫ ДЛЯ МОЛОДЫХ СЕМЕЙ, НАПРАВЛЕННЫЕ НА ПРОДВИЖЕНИЕ ТРАДИЦИОННЫХ ДУХОВНО-НРАВСТВЕННЫХ ЦЕННОСТЕЙ",
    },
    {
        "id": "04",
        "report_row": "03",
        "code": "4ДМ",
        "name": "Участники мероприятий на базе инфраструктуры молодежной политики",
        "report_name": "Фактическая численность молодых людей в возрасте от 14 до 35 лет включительно, принявших участие в проектах и программах, реализованных объектами инфраструктуры молодежной политики субъекта Российской Федерации, на конец отчетного месяца/года нарастающим итогом с начала отчетного года, человек",
        "section": "ПРОЕКТЫ И ПРОГРАММЫ, ПРОВОДИМЫЕ НА БАЗЕ ИНФРАСТРУКТУРЫ МОЛОДЕЖНОЙ ПОЛИТИКИ",
    },
    {
        "id": "05",
        "report_row": "04",
        "code": "5В",
        "name": "Участники добровольческой и общественной деятельности",
        "report_name": "Общая численность населения субъекта Российской Федерации в возрасте от 14 до 35 лет включительно, вовлеченного в добровольческую и общественную деятельность в России, на конец отчетного месяца/года нарастающим итогом с начала отчетного года, человек",
        "section": "ПРОЕКТЫ И ПРОГРАММЫ, НАПРАВЛЕННЫЕ НА ВОВЛЕЧЕНИЕ В ДОБРОВОЛЬЧЕСКУЮ И ОБЩЕСТВЕННУЮ ДЕЯТЕЛЬНОСТЬ",
    },
)

KEYWORDS = {
    "01": (
        "патриот", "истори", "памят", "геро", "отечеств", "родин",
        "символик", "традиц", "наслед", "музе", "краевед", "поисков", "археолог", "военн",
        "экологи", "субботник", "дерев", "берег", "отход", "туризм", "экскурси", "поход",
        "межнацион", "межконфессион", "экстремизм", "терроризм", "межрегион", "международ",
    ),
    "02": (
        "професс", "профориент", "карьер", "трудоустр", "предприним", "образован", "просвещ",
        "научн", "обучен", "лекци", "семинар", "тренинг", "мастер-класс", "конференц", "форум",
        "конкурс", "одаренн", "талант", "наставнич", "стажиров", "практик", "компетенц",
        "саморазвит", "личност", "инициатив", "проектирован", "госстарт", "профпоток",
    ),
    "03": (
        "молодая семья", "молодые семьи", "семь", "семейн", "материн", "отцов", "день отца",
        "день матери", "брак", "репродуктив", "родител", "детско-родитель", "многодет",
    ),
    "04": (
        "дом молодежи", "дом молодёжи", "молодежный центр", "молодёжный центр", "центр юность",
        "мбу юность", "лгмц", "инфраструктур", "молодежное пространство", "молодёжное пространство",
    ),
    "05": (
        "волонтер", "волонтёр", "доброволь", "общественн", "благотвор", "гуманитар", "помощ",
        "донор", "активист", "молодежный совет", "молодёжный совет", "общественное объединение",
        "акци", "субботник", "уборк", "благоустрой", "возложение", "возложени",
    ),
}

DEFAULT_REPORT_SETTINGS = {
    "appendix_1_title": "ПРИЛОЖЕНИЕ 1",
    "appendix_1_subtitle": "Сведения о реализации молодежной политики",
    "appendix_1_columns": ["Наименование компоненты показателя", "№ строки", "Значение нарастающим итогом"],
    "appendix_2_title": "ПРИЛОЖЕНИЕ 2. ЖУРНАЛ МЕРОПРИЯТИЙ",
    "appendix_2_columns": ["№ п/п", "Дата проведения", "Наименование мероприятия / проекта", "Количество участников", "Ссылка на публикацию"],
}

DEFAULT_CARD_LABELS = {
    "date": "Дата (ДД.ММ.ГГГГ)",
    "time": "Время",
    "place": "Место",
    "name": "Название",
    "description": "Краткое описание",
    "participants": "Участники / семьи",
    "link": "Ссылка",
}


def default_data(year: int | None = None) -> dict:
    year = year or date.today().year
    return {
        "version": 1,
        "organization": "Администрация городского округа муниципальное образование городской округ город Луганск Луганской Народной Республики",
        "year": year,
        "targets": [
            {
                "id": item["id"],
                "name": item["name"],
                "code": item["code"],
                "report_row": item["report_row"],
                "report_name": item["report_name"],
                "section": item["section"],
                "keywords": list(KEYWORDS.get(item["id"], ())),
                "plan": [0] * 12,
            }
            for item in TARGETS
        ],
        "events": [],
        "report_settings": deepcopy(DEFAULT_REPORT_SETTINGS),
        "card_labels": deepcopy(DEFAULT_CARD_LABELS),
        "custom_fields": [],
        "press_release_settings": {
            "base_url": "https://api.deepseek.com/chat/completions",
            "model": "deepseek-flash",
            "instruction": "Подготовь профессиональный пресс-релиз на русском языке по данным мероприятия. Не выдумывай факты. Добавь заголовок, лид и основной текст.",
        },
    }


def normalize_data(data: dict) -> dict:
    result = default_data(int(data.get("year") or date.today().year))
    result["organization"] = str(data.get("organization") or result["organization"])
    defaults_by_id = {item["id"]: item for item in result["targets"]}
    normalized_targets = []
    for incoming in data.get("targets", []):
        target_id = str(incoming.get("id") or uuid.uuid4())
        fallback = defaults_by_id.get(target_id, {})
        raw_plan = list(incoming.get("plan", []))[:12]
        raw_keywords = incoming.get("keywords", fallback.get("keywords", []))
        if isinstance(raw_keywords, str):
            raw_keywords = [item.strip() for item in raw_keywords.split(",") if item.strip()]
        normalized_targets.append({
            "id": target_id,
            "name": str(incoming.get("name") or fallback.get("name") or "Новый целевой показатель"),
            "code": str(incoming.get("code") or fallback.get("code") or target_id),
            "report_row": str(incoming.get("report_row") or fallback.get("report_row") or len(normalized_targets) + 1),
            "report_name": str(incoming.get("report_name") or fallback.get("report_name") or incoming.get("name") or "Новый целевой показатель"),
            "section": str(incoming.get("section") or fallback.get("section") or incoming.get("name") or "НОВЫЙ РАЗДЕЛ"),
            "keywords": [str(item).strip().lower() for item in raw_keywords if str(item).strip()],
            "plan": [safe_int(value) for value in raw_plan] + [0] * (12 - len(raw_plan)),
        })
    result["targets"] = normalized_targets or result["targets"]
    valid_target_ids = {item["id"] for item in result["targets"]}
    for raw in data.get("events", []):
        event = {
            "id": str(raw.get("id") or uuid.uuid4()),
            "date": str(raw.get("date") or ""),
            "time": str(raw.get("time") or ""),
            "place": str(raw.get("place") or ""),
            "name": str(raw.get("name") or ""),
            "description": str(raw.get("description") or ""),
            "target_ids": [str(x) for x in raw.get("target_ids", []) if str(x) in valid_target_ids],
            "auto_classify": bool(raw.get("auto_classify", False)),
            "participants": None if raw.get("participants") in (None, "") else max(0, safe_int(raw.get("participants"))),
            "link": str(raw.get("link") or ""),
            "custom_fields": {str(key): str(value or "") for key, value in raw.get("custom_fields", {}).items()},
            "press_release": str(raw.get("press_release") or ""),
        }
        result["events"].append(event)
    incoming_reports = data.get("report_settings", {})
    for key, default_value in DEFAULT_REPORT_SETTINGS.items():
        value = incoming_reports.get(key, default_value)
        if isinstance(default_value, list):
            values = [str(item) for item in value][:len(default_value)] if isinstance(value, list) else []
            result["report_settings"][key] = values + default_value[len(values):]
        else:
            result["report_settings"][key] = str(value or default_value)
    result["card_labels"].update({
        key: str(value or DEFAULT_CARD_LABELS[key])
        for key, value in data.get("card_labels", {}).items()
        if key in DEFAULT_CARD_LABELS
    })
    result["custom_fields"] = [
        {"id": str(item.get("id") or uuid.uuid4()), "label": str(item.get("label") or "Дополнительное поле")}
        for item in data.get("custom_fields", [])
    ]
    press_settings = data.get("press_release_settings", {})
    result["press_release_settings"].update({
        key: str(press_settings.get(key) or value)
        for key, value in result["press_release_settings"].items()
    })
    return result


def safe_int(value) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    match = re.search(r"-?\d[\d\s]*", str(value or ""))
    return int(match.group(0).replace(" ", "")) if match else 0


def parse_event_date(value: str) -> date | None:
    text = str(value or "").strip()
    patterns = (
        (r"^(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})$", False),
        (r"^(\d{4})-(\d{1,2})-(\d{1,2})$", True),
    )
    for pattern, year_first in patterns:
        match = re.match(pattern, text)
        if not match:
            continue
        values = [int(x) for x in match.groups()]
        year, month, day = values if year_first else (values[2], values[1], values[0])
        try:
            return date(year, month, day)
        except ValueError:
            return None
    return None


def event_month(event: dict) -> int | None:
    parsed = parse_event_date(event.get("date", ""))
    return reporting_period(parsed)[1] if parsed else None


def reporting_period(value: date) -> tuple[int, int]:
    """Return the report year and zero-based month; the new period starts on the 25th."""
    if value.day < 25:
        return value.year, value.month - 1
    if value.month == 12:
        return value.year + 1, 0
    return value.year, value.month


def reporting_period_bounds(year: int, month: int) -> tuple[date, date]:
    current_start = date(year, month + 1, 1)
    previous_day = current_start - timedelta(days=1)
    start = date(previous_day.year, previous_day.month, 25)
    end = date(year, month + 1, 24)
    return start, end


def event_in_reporting_month(event: dict, year: int, month: int) -> bool:
    parsed = parse_event_date(event.get("date", ""))
    return bool(parsed and reporting_period(parsed) == (int(year), month))


def event_is_complete(event: dict) -> bool:
    return bool(
        event.get("date")
        and event.get("time")
        and event.get("place")
        and event.get("name")
        and event.get("description")
        and event.get("participants") is not None
        and event.get("link")
        and event.get("target_ids")
    )


def build_press_release(event: dict) -> str:
    description = str(event.get("description") or "").strip()
    if not description:
        return ""
    name = str(event.get("name") or "Мероприятие").strip()
    parsed = parse_event_date(event.get("date", ""))
    action = "состоится" if parsed and parsed > date.today() else "состоялось"
    date_text = f"{event.get('date', '')} " if event.get("date") else ""
    time_text = f"в {event.get('time')} " if event.get("time") else ""
    opening = f"{date_text}{time_text}{action} мероприятие «{name}».".strip()
    paragraphs = [name, opening]
    place = str(event.get("place") or "").strip()
    if place:
        paragraphs.append(f"Место проведения: {place}.")
    paragraphs.append(description.rstrip(". ") + ".")
    if event.get("participants") is not None:
        paragraphs.append(f"В мероприятии приняли участие {event['participants']} человек.")
    if event.get("link"):
        paragraphs.append(f"Подробная информация и материалы мероприятия: {event['link']}")
    return "\n\n".join(paragraphs)


def classify_event(name: str, description: str, place: str, targets: list[dict] | None = None) -> list[str]:
    text = " ".join((name, description, place)).lower().replace("ё", "е")
    keyword_sets = (
        ((target["id"], target.get("keywords", [])) for target in targets)
        if targets is not None
        else KEYWORDS.items()
    )
    scores = {}
    for target_id, words in keyword_sets:
        normalized_words = (word.replace("ё", "е") for word in words)
        scores[target_id] = sum(1 for word in normalized_words if word in text)
    return [target_id for target_id, score in scores.items() if score > 0]


def target_actuals(data: dict, target_id: str) -> list[int]:
    actuals = [0] * 12
    report_year = int(data["year"])
    for event in data.get("events", []):
        parsed = parse_event_date(event.get("date", ""))
        if parsed and reporting_period(parsed)[0] == report_year and target_id in event.get("target_ids", []):
            actuals[reporting_period(parsed)[1]] += max(0, safe_int(event.get("participants")))
    return actuals


def calculate_target(data: dict, target_id: str) -> list[dict]:
    target = next(item for item in data["targets"] if item["id"] == target_id)
    cumulative_plan = [safe_int(value) for value in target["plan"]]
    actual = target_actuals(data, target_id)
    rows = []
    previous_plan = 0
    previous_balance = 0
    actual_cumulative = 0
    for month in range(12):
        monthly_plan = cumulative_plan[month] - previous_plan
        required = monthly_plan + previous_balance
        balance = required - actual[month]
        actual_cumulative += actual[month]
        rows.append({
            "month": month,
            "cumulative_plan": cumulative_plan[month],
            "monthly_plan": monthly_plan,
            "actual": actual[month],
            "actual_cumulative": actual_cumulative,
            "balance": balance,
            "required": required,
        })
        previous_plan = cumulative_plan[month]
        previous_balance = balance
    return rows


class DataStore:
    def __init__(self, path: Path):
        self.path = path
        self.data = self.load()

    def load(self) -> dict:
        if not self.path.exists():
            return default_data()
        try:
            with self.path.open("r", encoding="utf-8") as stream:
                return normalize_data(json.load(stream))
        except (OSError, ValueError, TypeError):
            backup = self.path.with_suffix(".поврежден.json")
            try:
                os.replace(self.path, backup)
            except OSError:
                pass
            return default_data()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        with temp.open("w", encoding="utf-8") as stream:
            json.dump(self.data, stream, ensure_ascii=False, indent=2)
        os.replace(temp, self.path)

    def snapshot(self) -> dict:
        return deepcopy(self.data)
