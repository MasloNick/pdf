"""
Модуль для нормалізації адрес відповідно до вимог Укрпошти
"""
import re
import requests
from typing import Dict, Optional, Tuple
from fuzzywuzzy import fuzz


class AddressNormalizer:
    """Клас для нормалізації українських адрес"""

    # Скорочення типів населених пунктів відповідно до стандартів Укрпошти
    SETTLEMENT_TYPES = {
        "місто": "м.",
        "м": "м.",
        "м.": "м.",
        "місто": "м.",
        "мiсто": "м.",
        "село": "с.",
        "с": "с.",
        "с.": "с.",
        "селище": "смт.",
        "смт": "смт.",
        "смт.": "смт.",
        "селище міського типу": "смт.",
        "селище мiського типу": "смт.",
        "сел.": "с.",
        "сел": "с.",
        "селище": "с.",
    }

    # Скорочення типів вулиць
    STREET_TYPES = {
        "вулиця": "вул.",
        "вул": "вул.",
        "вул.": "вул.",
        "вулиця": "вул.",
        "вулицi": "вул.",
        "проспект": "просп.",
        "просп": "просп.",
        "просп.": "просп.",
        "пр-т": "просп.",
        "пр.": "просп.",
        "бульвар": "бульв.",
        "бульв": "бульв.",
        "бульв.": "бульв.",
        "площа": "пл.",
        "пл": "пл.",
        "пл.": "пл.",
        "провулок": "пров.",
        "пров": "пров.",
        "пров.": "пров.",
        "проїзд": "проїзд",
        "узвіз": "узвіз",
        "шосе": "шосе",
        "майдан": "майдан",
    }

    # Скорочення областей
    OBLAST_NAMES = {
        "київська": "Київська область",
        "київська область": "Київська область",
        "київська обл.": "Київська область",
        "київська обл": "Київська область",
        "дніпропетровська": "Дніпропетровська область",
        "дніпропетровська область": "Дніпропетровська область",
        "дніпропетровська обл.": "Дніпропетровська область",
        "дніпропетровська обл": "Дніпропетровська область",
        "харківська": "Харківська область",
        "харківська область": "Харківська область",
        "харківська обл.": "Харківська область",
        "харківська обл": "Харківська область",
        "львівська": "Львівська область",
        "львівська область": "Львівська область",
        "львівська обл.": "Львівська область",
        "львівська обл": "Львівська область",
        "одеська": "Одеська область",
        "одеська область": "Одеська область",
        "одеська обл.": "Одеська область",
        "одеська обл": "Одеська область",
        "вінницька": "Вінницька область",
        "вінницька область": "Вінницька область",
        "вінницька обл.": "Вінницька область",
        "вінницька обл": "Вінницька область",
        "житомирська": "Житомирська область",
        "житомирська область": "Житомирська область",
        "житомирська обл.": "Житомирська область",
        "житомирська обл": "Житомирська область",
        "запорізька": "Запорізька область",
        "запорізька область": "Запорізька область",
        "запорізька обл.": "Запорізька область",
        "запорізька обл": "Запорізька область",
        "івано-франківська": "Івано-Франківська область",
        "івано-франківська область": "Івано-Франківська область",
        "івано-франківська обл.": "Івано-Франківська область",
        "івано-франківська обл": "Івано-Франківська область",
        "полтавська": "Полтавська область",
        "полтавська область": "Полтавська область",
        "полтавська обл.": "Полтавська область",
        "полтавська обл": "Полтавська область",
        "рівненська": "Рівненська область",
        "рівненська область": "Рівненська область",
        "рівненська обл.": "Рівненська область",
        "рівненська обл": "Рівненська область",
        "сумська": "Сумська область",
        "сумська область": "Сумська область",
        "сумська обл.": "Сумська область",
        "сумська обл": "Сумська область",
        "тернопільська": "Тернопільська область",
        "тернопільська область": "Тернопільська область",
        "тернопільська обл.": "Тернопільська область",
        "тернопільська обл": "Тернопільська область",
        "закарпатська": "Закарпатська область",
        "закарпатська область": "Закарпатська область",
        "закарпатська обл.": "Закарпатська область",
        "закарпатська обл": "Закарпатська область",
        "хмельницька": "Хмельницька область",
        "хмельницька область": "Хмельницька область",
        "хмельницька обл.": "Хмельницька область",
        "хмельницька обл": "Хмельницька область",
        "черкаська": "Черкаська область",
        "черкаська область": "Черкаська область",
        "черкаська обл.": "Черкаська область",
        "черкаська обл": "Черкаська область",
        "чернівецька": "Чернівецька область",
        "чернівецька область": "Чернівецька область",
        "чернівецька обл.": "Чернівецька область",
        "чернівецька обл": "Чернівецька область",
        "чернігівська": "Чернігівська область",
        "чернігівська область": "Чернігівська область",
        "чернігівська обл.": "Чернігівська область",
        "чернігівська обл": "Чернігівська область",
    }

    # Міста зі спеціальним статусом
    SPECIAL_CITIES = {
        "київ": "м. Київ",
        "м. київ": "м. Київ",
        "м.київ": "м. Київ",
        "киев": "м. Київ",
        "дніпро": "м. Дніпро",
        "м. дніпро": "м. Дніпро",
        "дніпропетровськ": "м. Дніпро",
        "м. дніпропетровськ": "м. Дніпро",
    }

    def __init__(self, use_online_api: bool = False):
        """
        Ініціалізація нормалізатора

        Args:
            use_online_api: Використовувати онлайн API для нормалізації (наприклад, Nova Poshta)
        """
        self.use_online_api = use_online_api

    def normalize_text(self, text: str) -> str:
        """Базова нормалізація тексту"""
        if not text:
            return ""

        # Видалення зайвих пробілів
        text = " ".join(text.strip().split())

        # Заміна і на i (латинську)
        text = text.replace('і', 'і')  # Нормалізація української і

        return text

    def normalize_oblast(self, oblast: str) -> str:
        """Нормалізація назви області"""
        if not oblast:
            return ""

        oblast_lower = oblast.lower().strip()

        # Перевірка спеціальних міст
        if oblast_lower in self.SPECIAL_CITIES:
            return self.SPECIAL_CITIES[oblast_lower]

        # Перевірка областей
        if oblast_lower in self.OBLAST_NAMES:
            return self.OBLAST_NAMES[oblast_lower]

        # Якщо не знайдено точного співпадіння, шукаємо найближче
        best_match = None
        best_score = 0

        for key, value in self.OBLAST_NAMES.items():
            score = fuzz.ratio(oblast_lower, key)
            if score > best_score and score > 80:  # Поріг схожості 80%
                best_score = score
                best_match = value

        if best_match:
            return best_match

        # Якщо не знайдено, повертаємо з великої літери
        return oblast.capitalize()

    def normalize_city(self, city: str, oblast: str = "") -> str:
        """Нормалізація назви міста/населеного пункту"""
        if not city:
            return ""

        city = self.normalize_text(city)
        city_lower = city.lower().strip()

        # Перевірка спеціальних міст
        if city_lower in self.SPECIAL_CITIES:
            return self.SPECIAL_CITIES[city_lower]

        # Розбір типу населеного пункту
        parts = city_lower.split()
        if len(parts) >= 2:
            first_part = parts[0].replace(".", "").strip()

            # Перевірка, чи перше слово - тип населеного пункту
            if first_part in self.SETTLEMENT_TYPES:
                settlement_type = self.SETTLEMENT_TYPES[first_part]
                settlement_name = " ".join(parts[1:]).strip().title()
                return f"{settlement_type} {settlement_name}"

        # Якщо це велике місто без префіксу, додаємо "м."
        major_cities = [
            "київ", "харків", "одеса", "дніпро", "донецьк", "запоріжжя",
            "львів", "кривий ріг", "миколаїв", "маріуполь", "луганськ",
            "вінниця", "макіївка", "херсон", "полтава", "чернігів",
            "черкаси", "суми", "житомир", "хмельницький", "чернівці",
            "рівне", "тернопіль", "івано-франківськ", "кропивницький",
            "луцьк", "ужгород"
        ]

        if city_lower in major_cities:
            return f"м. {city.title()}"

        # За замовчуванням повертаємо з великої літери
        return city.title()

    def normalize_district(self, district: str) -> str:
        """Нормалізація назви району"""
        if not district:
            return ""

        district = self.normalize_text(district)

        # Якщо вже є "район" в кінці
        if district.lower().endswith("район"):
            parts = district.split()
            return " ".join(p.capitalize() for p in parts)

        # Додати "район" якщо його немає
        if "район" not in district.lower():
            return f"{district.title()} район"

        return district.title()

    def normalize_street(self, street: str) -> str:
        """Нормалізація назви вулиці"""
        if not street:
            return ""

        street = self.normalize_text(street)
        street_lower = street.lower().strip()

        parts = street_lower.split()
        if len(parts) >= 2:
            first_part = parts[0].replace(".", "").strip()

            # Перевірка, чи перше слово - тип вулиці
            if first_part in self.STREET_TYPES:
                street_type = self.STREET_TYPES[first_part]
                street_name = " ".join(parts[1:]).strip().title()
                return f"{street_type} {street_name}"

        # За замовчуванням додаємо "вул." якщо немає типу
        return f"вул. {street.title()}"

    def normalize_house_number(self, house: str) -> str:
        """Нормалізація номеру будинку"""
        if not house:
            return ""

        house = house.strip().upper()

        # Нормалізація літер та корпусів
        house = re.sub(r'\s+', '', house)  # Видалити пробіли
        house = house.replace("БУД.", "").replace("БУД", "")
        house = house.replace("КОРП.", "/").replace("КОРП", "/")
        house = house.replace("КВ.", ", кв. ").replace("КВ", ", кв. ")

        return house

    def parse_full_address(self, address: str) -> Dict[str, str]:
        """
        Розбір повної адреси на компоненти

        Args:
            address: Повна адреса в довільному форматі

        Returns:
            Словник з компонентами адреси
        """
        result = {
            "oblast": "",
            "district": "",
            "city": "",
            "street": "",
            "house": "",
            "apartment": "",
            "postal_code": ""
        }

        if not address:
            return result

        # Пошук індексу
        postal_match = re.search(r'\b\d{5}\b', address)
        if postal_match:
            result["postal_code"] = postal_match.group()
            address = address.replace(postal_match.group(), "").strip()

        # Розділення за комами
        parts = [p.strip() for p in address.split(',')]

        for part in parts:
            part_lower = part.lower()

            # Область
            if 'обл' in part_lower or 'область' in part_lower:
                result["oblast"] = part
            # Район
            elif 'район' in part_lower or 'р-н' in part_lower or 'р.' in part_lower:
                result["district"] = part
            # Місто/населений пункт
            elif any(prefix in part_lower for prefix in ['м.', 'с.', 'смт.', 'місто', 'село']):
                result["city"] = part
            # Вулиця
            elif any(st in part_lower for st in ['вул', 'просп', 'бульв', 'пл.', 'майдан', 'пров']):
                # Перевірка, чи є номер будинку
                house_match = re.search(r',?\s*(\d+[А-ЯA-Z]?(?:[/-]\d+[А-ЯA-Z]?)?)', part)
                if house_match:
                    result["house"] = house_match.group(1)
                    result["street"] = part[:house_match.start()].strip()
                else:
                    result["street"] = part
            # Квартира
            elif 'кв' in part_lower or 'квартира' in part_lower:
                apt_match = re.search(r'\d+', part)
                if apt_match:
                    result["apartment"] = apt_match.group()

        return result

    def normalize_address(self, address_dict: Dict[str, str]) -> Dict[str, str]:
        """
        Нормалізація всіх компонентів адреси

        Args:
            address_dict: Словник з компонентами адреси

        Returns:
            Нормалізований словник адреси
        """
        normalized = {}

        # Нормалізація області
        if 'oblast' in address_dict:
            normalized['oblast'] = self.normalize_oblast(address_dict['oblast'])

        # Нормалізація району
        if 'district' in address_dict:
            normalized['district'] = self.normalize_district(address_dict['district'])

        # Нормалізація міста
        if 'city' in address_dict or 'settlement' in address_dict:
            city = address_dict.get('city') or address_dict.get('settlement', '')
            oblast = normalized.get('oblast', '')
            normalized['city'] = self.normalize_city(city, oblast)

        # Нормалізація вулиці
        if 'street' in address_dict:
            normalized['street'] = self.normalize_street(address_dict['street'])

        # Нормалізація номеру будинку
        if 'house' in address_dict:
            normalized['house'] = self.normalize_house_number(address_dict['house'])

        # Квартира
        if 'apartment' in address_dict:
            normalized['apartment'] = address_dict['apartment'].strip()

        # Індекс
        if 'postal_code' in address_dict:
            normalized['postal_code'] = address_dict['postal_code'].strip()

        return normalized

    def format_normalized_address(self, normalized: Dict[str, str]) -> str:
        """
        Форматування нормалізованої адреси в рядок

        Args:
            normalized: Нормалізований словник адреси

        Returns:
            Відформатована адреса
        """
        parts = []

        if normalized.get('postal_code'):
            parts.append(normalized['postal_code'])

        if normalized.get('oblast'):
            parts.append(normalized['oblast'])

        if normalized.get('district'):
            parts.append(normalized['district'])

        if normalized.get('city'):
            parts.append(normalized['city'])

        if normalized.get('street'):
            street_part = normalized['street']
            if normalized.get('house'):
                street_part += f", {normalized['house']}"
            parts.append(street_part)

        if normalized.get('apartment'):
            parts.append(f"кв. {normalized['apartment']}")

        return ", ".join(parts)

    def normalize_full_address(self, address: str) -> Tuple[Dict[str, str], str]:
        """
        Повна нормалізація адреси

        Args:
            address: Адреса в довільному форматі

        Returns:
            Кортеж (словник компонентів, відформатована адреса)
        """
        # Розбір адреси
        parsed = self.parse_full_address(address)

        # Нормалізація компонентів
        normalized = self.normalize_address(parsed)

        # Форматування
        formatted = self.format_normalized_address(normalized)

        return normalized, formatted


# Приклад використання
if __name__ == "__main__":
    normalizer = AddressNormalizer()

    # Тестові адреси
    test_addresses = [
        "київська обл, м київ, вулиця хрещатик, буд 10, кв 5",
        "04070, Київ, вул Набережно-Хрещатицька 2",
        "Львівська область, місто львів, проспект свободи 1",
        "Дніпропетровська обл., Дніпро, Центральний район, вул. Воскресенська, 17",
    ]

    for addr in test_addresses:
        normalized, formatted = normalizer.normalize_full_address(addr)
        print(f"Оригінал: {addr}")
        print(f"Нормалізовано: {formatted}")
        print(f"Компоненти: {normalized}")
        print("-" * 80)
