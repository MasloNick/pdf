"""Case management module for CourtNinja CRM.

Provides in-memory case tracking with persistence via JSON files.
Each case tracks parties, documents, deadlines, fees, and status.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@dataclass
class Party:
    """A party to a case (plaintiff, defendant, third party, etc.)."""

    name: str
    role: str  # plaintiff, defendant, third_party, representative
    address: str = ""
    phone: str = ""
    email: str = ""
    edrpou: str = ""  # ЄДРПОУ code for legal entities
    inn: str = ""  # ІПН for individuals


@dataclass
class Deadline:
    """A deadline or important date in a case."""

    id: str
    title: str
    due_date: str  # ISO format YYYY-MM-DD
    case_id: str
    description: str = ""
    completed: bool = False
    reminder_days: int = 3

    @property
    def is_overdue(self) -> bool:
        return not self.completed and date.fromisoformat(self.due_date) < date.today()

    @property
    def days_left(self) -> int:
        delta = date.fromisoformat(self.due_date) - date.today()
        return delta.days

    @property
    def needs_reminder(self) -> bool:
        return not self.completed and 0 <= self.days_left <= self.reminder_days


@dataclass
class CaseNote:
    """A note or event in the case timeline."""

    id: str
    timestamp: str  # ISO format
    text: str
    author: str = "system"


@dataclass
class Case:
    """A court case."""

    id: str
    case_number: str  # Court case number e.g. "752/1234/24"
    title: str
    case_type: str  # civil, criminal, commercial, admin
    court_id: str
    court_name: str
    status: str  # new, active, hearing, appeal, closed, archived
    created_at: str = ""
    updated_at: str = ""
    description: str = ""
    parties: List[Dict] = field(default_factory=list)
    deadlines: List[Dict] = field(default_factory=list)
    notes: List[Dict] = field(default_factory=list)
    documents: List[Dict] = field(default_factory=list)
    judge: str = ""
    next_hearing: str = ""
    fee_paid: float = 0.0
    fee_required: float = 0.0
    user_id: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


CASE_TYPES = {
    "civil": "Цивільна справа",
    "criminal": "Кримінальна справа",
    "commercial": "Господарська справа",
    "admin": "Адміністративна справа",
    "admin_offense": "Справа про адмін. правопорушення",
}

CASE_STATUSES = {
    "new": "Нова",
    "active": "В провадженні",
    "hearing": "Призначено слухання",
    "suspended": "Зупинено",
    "appeal": "Апеляція",
    "cassation": "Касація",
    "closed": "Закрита",
    "archived": "Архів",
}


class CaseManager:
    """In-memory case manager with JSON persistence."""

    def __init__(self, data_file: Optional[str] = None) -> None:
        self._data_file = data_file or str(DATA_DIR / "cases.json")
        self._cases: Dict[str, Case] = {}
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._data_file):
            try:
                with open(self._data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    case = Case(**item)
                    self._cases[case.id] = case
            except (json.JSONDecodeError, TypeError, KeyError):
                self._cases = {}

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self._data_file), exist_ok=True)
        with open(self._data_file, "w", encoding="utf-8") as f:
            json.dump(
                [c.to_dict() for c in self._cases.values()],
                f,
                ensure_ascii=False,
                indent=2,
            )

    def create_case(
        self,
        case_number: str,
        title: str,
        case_type: str,
        court_id: str,
        court_name: str,
        description: str = "",
        judge: str = "",
        user_id: str = "",
    ) -> Case:
        now = datetime.now().isoformat()
        case = Case(
            id=str(uuid.uuid4())[:8],
            case_number=case_number,
            title=title,
            case_type=case_type,
            court_id=court_id,
            court_name=court_name,
            status="new",
            created_at=now,
            updated_at=now,
            description=description,
            judge=judge,
            user_id=user_id,
        )
        self._cases[case.id] = case
        self._save()
        return case

    def get_case(self, case_id: str) -> Optional[Case]:
        return self._cases.get(case_id)

    def list_cases(
        self,
        status: str = "",
        case_type: str = "",
        query: str = "",
        user_id: str = "",
    ) -> List[Case]:
        results = list(self._cases.values())
        if user_id:
            results = [c for c in results if c.user_id == user_id]
        if status:
            results = [c for c in results if c.status == status]
        if case_type:
            results = [c for c in results if c.case_type == case_type]
        if query:
            q = query.lower()
            results = [
                c for c in results
                if q in c.title.lower()
                or q in c.case_number.lower()
                or q in c.court_name.lower()
                or q in c.description.lower()
            ]
        return sorted(results, key=lambda c: c.updated_at, reverse=True)

    def update_case(self, case_id: str, **kwargs) -> Optional[Case]:
        case = self._cases.get(case_id)
        if not case:
            return None
        for key, value in kwargs.items():
            if hasattr(case, key) and key not in ("id", "created_at"):
                setattr(case, key, value)
        case.updated_at = datetime.now().isoformat()
        self._save()
        return case

    def delete_case(self, case_id: str) -> bool:
        if case_id in self._cases:
            del self._cases[case_id]
            self._save()
            return True
        return False

    def add_party(self, case_id: str, party: Dict) -> Optional[Case]:
        case = self._cases.get(case_id)
        if not case:
            return None
        case.parties.append(party)
        case.updated_at = datetime.now().isoformat()
        self._save()
        return case

    def add_deadline(self, case_id: str, title: str, due_date: str, description: str = "") -> Optional[Case]:
        case = self._cases.get(case_id)
        if not case:
            return None
        deadline = {
            "id": str(uuid.uuid4())[:8],
            "title": title,
            "due_date": due_date,
            "case_id": case_id,
            "description": description,
            "completed": False,
            "reminder_days": 3,
        }
        case.deadlines.append(deadline)
        case.updated_at = datetime.now().isoformat()
        self._save()
        return case

    def complete_deadline(self, case_id: str, deadline_id: str) -> bool:
        case = self._cases.get(case_id)
        if not case:
            return False
        for d in case.deadlines:
            if d.get("id") == deadline_id:
                d["completed"] = True
                case.updated_at = datetime.now().isoformat()
                self._save()
                return True
        return False

    def add_note(self, case_id: str, text: str, author: str = "user") -> Optional[Case]:
        case = self._cases.get(case_id)
        if not case:
            return None
        note = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": datetime.now().isoformat(),
            "text": text,
            "author": author,
        }
        case.notes.append(note)
        case.updated_at = datetime.now().isoformat()
        self._save()
        return case

    def get_upcoming_deadlines(self, days: int = 7, user_id: str = "") -> List[Dict]:
        """Get all deadlines across all cases due within N days."""
        cutoff = date.today() + timedelta(days=days)
        upcoming = []
        cases = self._cases.values()
        if user_id:
            cases = [c for c in cases if c.user_id == user_id]
        for case in cases:
            for d in case.deadlines:
                if d.get("completed"):
                    continue
                try:
                    due = date.fromisoformat(d["due_date"])
                except (ValueError, KeyError):
                    continue
                if due <= cutoff:
                    upcoming.append({
                        **d,
                        "case_title": case.title,
                        "case_number": case.case_number,
                        "days_left": (due - date.today()).days,
                        "is_overdue": due < date.today(),
                    })
        return sorted(upcoming, key=lambda x: x["due_date"])

    def stats(self, user_id: str = "") -> Dict:
        """Return case statistics."""
        cases = list(self._cases.values())
        if user_id:
            cases = [c for c in cases if c.user_id == user_id]
        by_status: Dict[str, int] = {}
        by_type: Dict[str, int] = {}
        for c in cases:
            label = CASE_STATUSES.get(c.status, c.status)
            by_status[label] = by_status.get(label, 0) + 1
            type_label = CASE_TYPES.get(c.case_type, c.case_type)
            by_type[type_label] = by_type.get(type_label, 0) + 1
        return {
            "total": len(cases),
            "by_status": by_status,
            "by_type": by_type,
        }
