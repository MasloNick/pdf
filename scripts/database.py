"""
Модуль для роботи з базою даних адрес України та судів
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

# Шлях до бази даних
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / 'database' / 'ukraine_addresses.db'


@contextmanager
def get_db_connection():
    """Контекстний менеджер для підключення до бази даних"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Для доступу до колонок по імені
    try:
        yield conn
    finally:
        conn.close()


def normalize_text(text: str) -> str:
    """Нормалізує текст для пошуку"""
    if not text:
        return ""
    return " ".join(text.strip().lower().split())


def find_oblast(oblast_name: str) -> Optional[Dict[str, Any]]:
    """Знаходить область за назвою"""
    if not oblast_name:
        return None

    normalized_name = normalize_text(oblast_name)

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Отримати всі області та порівняти в Python (SQLite LOWER не працює з кирилицею)
        results = cursor.execute("SELECT * FROM oblasts").fetchall()

        # Точний пошук
        for row in results:
            if normalize_text(row['name']) == normalized_name:
                return dict(row)

        # Частковий пошук
        for row in results:
            if normalized_name in normalize_text(row['name']):
                return dict(row)

        return None


def find_raion(raion_name: str, oblast_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Знаходить район за назвою"""
    if not raion_name:
        return None

    normalized_name = normalize_text(raion_name)

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if oblast_id:
            # Пошук в межах області
            results = cursor.execute(
                "SELECT * FROM raions WHERE oblast_id = ?",
                (oblast_id,)
            ).fetchall()
        else:
            # Пошук без прив'язки до області
            results = cursor.execute("SELECT * FROM raions").fetchall()

        # Точний пошук
        for row in results:
            if normalize_text(row['name']) == normalized_name:
                return dict(row)

        # Частковий пошук
        for row in results:
            if normalized_name in normalize_text(row['name']):
                return dict(row)

        return None


def find_settlement(settlement_name: str, oblast_id: Optional[int] = None,
                   raion_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Знаходить населений пункт за назвою"""
    if not settlement_name:
        return None

    normalized_name = normalize_text(settlement_name)

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Побудувати запит з урахуванням фільтрів
        query = "SELECT * FROM settlements WHERE 1=1"
        params = []

        if oblast_id:
            query += " AND oblast_id = ?"
            params.append(oblast_id)

        if raion_id:
            query += " AND raion_id = ?"
            params.append(raion_id)

        results = cursor.execute(query, params).fetchall()

        # Точний пошук
        for row in results:
            if normalize_text(row['name']) == normalized_name:
                return dict(row)

        # Частковий пошук
        for row in results:
            if normalized_name in normalize_text(row['name']):
                return dict(row)

        return None


def find_court_by_jurisdiction(oblast_name: Optional[str] = None,
                               raion_name: Optional[str] = None,
                               settlement_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Знаходить суд за юрисдикцією (адресою)

    Args:
        oblast_name: Назва області
        raion_name: Назва району
        settlement_name: Назва населеного пункту

    Returns:
        Словник з інформацією про суд або None
    """

    # Знайти ID територіальних одиниць
    oblast_id = None
    raion_id = None
    settlement_id = None

    if oblast_name:
        oblast = find_oblast(oblast_name)
        if oblast:
            oblast_id = oblast['id']

    if raion_name and oblast_id:
        raion = find_raion(raion_name, oblast_id)
        if raion:
            raion_id = raion['id']

    if settlement_name and oblast_id:
        settlement = find_settlement(settlement_name, oblast_id, raion_id)
        if settlement:
            settlement_id = settlement['id']

    # Якщо нічого не знайдено
    if not (oblast_id or raion_id or settlement_id):
        return None

    # Знайти суд за юрисдикцією
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Пріоритет пошуку: settlement > raion > oblast
        # Спочатку шукаємо найбільш специфічну юрисдикцію

        if settlement_id:
            # Пошук по населеному пункту
            result = cursor.execute(
                """
                SELECT c.* FROM courts c
                JOIN jurisdiction j ON c.id = j.court_id
                WHERE j.settlement_id = ?
                LIMIT 1
                """,
                (settlement_id,)
            ).fetchone()

            if result:
                return dict(result)

        if raion_id:
            # Пошук по району (без конкретного населеного пункту)
            result = cursor.execute(
                """
                SELECT c.* FROM courts c
                JOIN jurisdiction j ON c.id = j.court_id
                WHERE j.raion_id = ?
                LIMIT 1
                """,
                (raion_id,)
            ).fetchone()

            if result:
                return dict(result)

        if oblast_id:
            # Пошук по області
            result = cursor.execute(
                """
                SELECT c.* FROM courts c
                JOIN jurisdiction j ON c.id = j.court_id
                WHERE j.oblast_id = ?
                LIMIT 1
                """,
                (oblast_id,)
            ).fetchone()

            if result:
                return dict(result)

        return None


def search_settlements(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Пошук населених пунктів за запитом"""
    if not query:
        return []

    normalized_query = normalize_text(query)

    with get_db_connection() as conn:
        cursor = conn.cursor()

        results = cursor.execute(
            """
            SELECT s.*, o.name as oblast_name, r.name as raion_name
            FROM settlements s
            LEFT JOIN oblasts o ON s.oblast_id = o.id
            LEFT JOIN raions r ON s.raion_id = r.id
            WHERE LOWER(s.name) LIKE ?
            ORDER BY s.population DESC
            LIMIT ?
            """,
            (f"%{normalized_query}%", limit)
        ).fetchall()

        return [dict(row) for row in results]


def get_all_oblasts() -> List[Dict[str, Any]]:
    """Отримати список всіх областей"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        results = cursor.execute(
            "SELECT * FROM oblasts ORDER BY name"
        ).fetchall()
        return [dict(row) for row in results]


def get_raions_by_oblast(oblast_id: int) -> List[Dict[str, Any]]:
    """Отримати список районів області"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        results = cursor.execute(
            "SELECT * FROM raions WHERE oblast_id = ? ORDER BY name",
            (oblast_id,)
        ).fetchall()
        return [dict(row) for row in results]


def get_all_courts() -> List[Dict[str, Any]]:
    """Отримати список всіх судів"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        results = cursor.execute(
            "SELECT * FROM courts ORDER BY name"
        ).fetchall()
        return [dict(row) for row in results]
