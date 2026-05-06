# modulo5_errores.py
# Módulo 5: Registro de Errores (Log del Sistema)

from datetime import datetime
from typing import Optional, List, Dict

class ErrorEntry:
    def __init__(self, error_code: str, description: str):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.error_code = error_code
        self.description = description
        self.next: Optional[ErrorEntry] = None

    def to_dict(self) -> Dict:
        return {"timestamp": self.timestamp, "error_code": self.error_code, "description": self.description}

    @classmethod
    def from_dict(cls, data: Dict) -> 'ErrorEntry':
        e = cls(data["error_code"], data["description"])
        e.timestamp = data.get("timestamp", e.timestamp)
        return e

    def __str__(self) -> str:
        return f"[{self.timestamp}] {self.error_code}: {self.description}"


class ErrorLog:
    def __init__(self):
        self.head: Optional[ErrorEntry] = None
        self.tail: Optional[ErrorEntry] = None
        self.size = 0

    def is_empty(self) -> bool:
        return self.head is None

    def add_error(self, error_code: str, description: str) -> None:
        entry = ErrorEntry(error_code, description)
        if self.is_empty():
            self.head = self.tail = entry
        else:
            self.tail.next = entry
            self.tail = entry
        self.size += 1

    def get_all(self) -> List[ErrorEntry]:
        entries = []
        cur = self.head
        while cur:
            entries.append(cur)
            cur = cur.next
        return entries

    def clear(self) -> None:
        self.head = self.tail = None
        self.size = 0

    def to_list(self) -> List[Dict]:
        return [e.to_dict() for e in self.get_all()]

    @classmethod
    def from_list(cls, entries: List[Dict]) -> 'ErrorLog':
        log = cls()
        for e in entries:
            log.add_error(e["error_code"], e.get("description", ""))
            if log.tail:
                log.tail.timestamp = e.get("timestamp", log.tail.timestamp)
        return log

    def __len__(self) -> int:
        return self.size

    def __str__(self) -> str:
        if self.is_empty():
            return "[Log vacío]"
        return "\n".join(str(e) for e in self.get_all())