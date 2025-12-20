"""
Модуль для пошуку районного суду за адресою
"""
import json
import os
from typing import Dict, List, Optional
from fuzzywuzzy import fuzz, process


class CourtFinder:
    """Клас для пошуку районних судів за адресою"""

    def __init__(self, courts_db_path: str = None):
        """
        Ініціалізація пошукача судів

        Args:
            courts_db_path: Шлях до JSON файлу з базою даних судів
        """
        if courts_db_path is None:
            # За замовчуванням використовуємо базу даних з директорії data
            current_dir = os.path.dirname(os.path.abspath(__file__))
            courts_db_path = os.path.join(
                os.path.dirname(current_dir), 'data', 'courts.json'
            )

        self.courts_db_path = courts_db_path
        self.courts = []
        self.load_courts()

    def load_courts(self):
        """Завантаження бази даних судів"""
        try:
            with open(self.courts_db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.courts = data.get('courts', [])
        except FileNotFoundError:
            print(f"Помилка: Файл {self.courts_db_path} не знайдено")
            self.courts = []
        except json.JSONDecodeError:
            print(f"Помилка: Неможливо прочитати JSON з файлу {self.courts_db_path}")
            self.courts = []

    def normalize_for_comparison(self, text: str) -> str:
        """Нормалізація тексту для порівняння"""
        if not text:
            return ""

        text = text.lower().strip()

        # Видалити типові префікси
        text = text.replace("м.", "").replace("м ", "")
        text = text.replace("с.", "").replace("смт.", "")
        text = text.replace("обл.", "").replace("область", "")
        text = text.replace("район", "").strip()

        # Видалити зайві пробіли
        text = " ".join(text.split())

        return text

    def find_court_by_address(self, address_dict: Dict[str, str]) -> Optional[Dict[str, any]]:
        """
        Пошук суду за адресою

        Args:
            address_dict: Словник з компонентами адреси
                - oblast: Область
                - district: Район
                - city: Місто/населений пункт

        Returns:
            Словник з інформацією про суд або None
        """
        if not self.courts:
            return None

        oblast = address_dict.get('oblast', '').strip()
        district = address_dict.get('district', '').strip()
        city = address_dict.get('city', '').strip()

        if not oblast and not city:
            return None

        best_match = None
        best_score = 0

        for court in self.courts:
            score = self._calculate_match_score(
                court, oblast, district, city
            )

            if score > best_score:
                best_score = score
                best_match = court

        # Повернути результат тільки якщо є достатньо хороше співпадіння
        if best_score > 50:  # Поріг 50%
            return {
                'court_name': best_match['name'],
                'court_code': best_match['code'],
                'court_type': best_match['type'],
                'court_address': best_match['address'],
                'court_phone': best_match.get('phone', ''),
                'match_score': best_score
            }

        return None

    def _calculate_match_score(
        self, court: Dict, oblast: str, district: str, city: str
    ) -> float:
        """
        Розрахунок оцінки співпадіння суду з адресою

        Args:
            court: Інформація про суд
            oblast: Область
            district: Район
            city: Місто

        Returns:
            Оцінка співпадіння (0-100)
        """
        score = 0
        total_weight = 0

        jurisdiction = court.get('jurisdiction', {})

        # Перевірка області (вага 40%)
        oblast_weight = 40
        if oblast:
            oblast_normalized = self.normalize_for_comparison(oblast)
            oblast_matches = jurisdiction.get('oblast', [])

            oblast_scores = []
            for oblast_match in oblast_matches:
                oblast_match_normalized = self.normalize_for_comparison(oblast_match)
                ratio = fuzz.ratio(oblast_normalized, oblast_match_normalized)
                oblast_scores.append(ratio)

            if oblast_scores:
                score += max(oblast_scores) * oblast_weight / 100
            total_weight += oblast_weight

        # Перевірка району (вага 35%)
        district_weight = 35
        if district:
            district_normalized = self.normalize_for_comparison(district)
            district_matches = jurisdiction.get('districts', [])

            district_scores = []
            for district_match in district_matches:
                district_match_normalized = self.normalize_for_comparison(district_match)
                ratio = fuzz.ratio(district_normalized, district_match_normalized)
                district_scores.append(ratio)

            if district_scores:
                score += max(district_scores) * district_weight / 100
            total_weight += district_weight

        # Перевірка міста (вага 25%)
        city_weight = 25
        if city:
            city_normalized = self.normalize_for_comparison(city)

            # Перевірка з містом суду
            court_city_normalized = self.normalize_for_comparison(
                court.get('city', '')
            )
            city_score = fuzz.ratio(city_normalized, court_city_normalized)

            # Також перевірка з населеними пунктами в юрисдикції
            settlement_matches = jurisdiction.get('settlements', [])
            for settlement in settlement_matches:
                settlement_normalized = self.normalize_for_comparison(settlement)
                ratio = fuzz.ratio(city_normalized, settlement_normalized)
                city_score = max(city_score, ratio)

            score += city_score * city_weight / 100
            total_weight += city_weight

        # Нормалізувати оцінку
        if total_weight > 0:
            return (score / total_weight) * 100

        return 0

    def find_courts_by_oblast(self, oblast: str) -> List[Dict[str, str]]:
        """
        Знайти всі суди в області

        Args:
            oblast: Назва області

        Returns:
            Список судів
        """
        oblast_normalized = self.normalize_for_comparison(oblast)
        results = []

        for court in self.courts:
            court_oblast_normalized = self.normalize_for_comparison(
                court.get('oblast', '')
            )

            if fuzz.ratio(oblast_normalized, court_oblast_normalized) > 80:
                results.append({
                    'name': court['name'],
                    'code': court['code'],
                    'type': court['type'],
                    'address': court['address'],
                    'phone': court.get('phone', '')
                })

        return results

    def find_court_by_name(self, name: str) -> Optional[Dict[str, str]]:
        """
        Знайти суд за назвою

        Args:
            name: Назва суду (може бути неточною)

        Returns:
            Інформація про суд або None
        """
        if not name:
            return None

        # Використання fuzzywuzzy для нечіткого пошуку
        court_names = [court['name'] for court in self.courts]
        best_match = process.extractOne(name, court_names, scorer=fuzz.token_sort_ratio)

        if best_match and best_match[1] > 70:  # Поріг схожості 70%
            # Знайти повну інформацію про суд
            for court in self.courts:
                if court['name'] == best_match[0]:
                    return {
                        'name': court['name'],
                        'code': court['code'],
                        'type': court['type'],
                        'address': court['address'],
                        'phone': court.get('phone', ''),
                        'match_score': best_match[1]
                    }

        return None

    def get_all_courts(self) -> List[Dict[str, str]]:
        """Отримати список всіх судів"""
        return [
            {
                'name': court['name'],
                'code': court['code'],
                'type': court['type'],
                'oblast': court.get('oblast', ''),
                'city': court.get('city', ''),
                'address': court['address'],
                'phone': court.get('phone', '')
            }
            for court in self.courts
        ]

    def get_statistics(self) -> Dict[str, any]:
        """Отримати статистику по базі судів"""
        total_courts = len(self.courts)

        # Підрахунок за типами
        types_count = {}
        oblasts_count = {}

        for court in self.courts:
            court_type = court.get('type', 'Невідомо')
            types_count[court_type] = types_count.get(court_type, 0) + 1

            oblast = court.get('oblast', 'Невідомо')
            oblasts_count[oblast] = oblasts_count.get(oblast, 0) + 1

        return {
            'total_courts': total_courts,
            'courts_by_type': types_count,
            'courts_by_oblast': oblasts_count
        }


# Приклад використання
if __name__ == "__main__":
    finder = CourtFinder()

    # Тест 1: Пошук за адресою
    print("=== Тест 1: Пошук суду за адресою ===")
    test_addresses = [
        {
            'oblast': 'Київ',
            'district': 'Шевченківський район',
            'city': 'Київ'
        },
        {
            'oblast': 'Львівська область',
            'district': 'Франківський район',
            'city': 'Львів'
        },
        {
            'oblast': 'Дніпропетровська область',
            'city': 'Дніпро',
            'district': 'Центральний район'
        }
    ]

    for addr in test_addresses:
        result = finder.find_court_by_address(addr)
        if result:
            print(f"\nАдреса: {addr}")
            print(f"Знайдено: {result['court_name']}")
            print(f"Адреса суду: {result['court_address']}")
            print(f"Оцінка співпадіння: {result['match_score']:.1f}%")
        else:
            print(f"\nАдреса: {addr}")
            print("Суд не знайдено")

    # Тест 2: Статистика
    print("\n\n=== Статистика бази судів ===")
    stats = finder.get_statistics()
    print(f"Всього судів: {stats['total_courts']}")
    print(f"\nЗа типами:")
    for court_type, count in stats['courts_by_type'].items():
        print(f"  {court_type}: {count}")
