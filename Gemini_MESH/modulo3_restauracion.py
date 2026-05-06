# modulo3_restauracion.py
# Módulo 3: Gestión de Restauración (Pila de Estados)

from typing import Optional, List, Dict

DEFAULT_TEMPERATURE = 0.7

class StateNode:
    def __init__(self, system_instruction: str, temperature: float):
        self.system_instruction = system_instruction
        self.temperature = temperature
        self.next: Optional[StateNode] = None

    def to_dict(self) -> Dict:
        return {"system_instruction": self.system_instruction, "temperature": self.temperature}

    @classmethod
    def from_dict(cls, data: Dict) -> 'StateNode':
        return cls(data.get("system_instruction", ""), data.get("temperature", DEFAULT_TEMPERATURE))


class StateStack:
    def __init__(self):
        self.top: Optional[StateNode] = None
        self.size = 0

    def is_empty(self) -> bool:
        return self.top is None

    def push(self, system_instruction: str, temperature: float) -> None:
        node = StateNode(system_instruction, temperature)
        node.next = self.top
        self.top = node
        self.size += 1

    def pop(self) -> Optional[StateNode]:
        if self.is_empty():
            return None
        popped = self.top
        self.top = self.top.next
        self.size -= 1
        popped.next = None
        return popped

    def clear(self) -> None:
        while not self.is_empty():
            self.pop()

    def to_list(self) -> List[Dict]:
        states = []
        cur = self.top
        while cur:
            states.append(cur.to_dict())
            cur = cur.next
        states.reverse()
        return states

    @classmethod
    def from_list(cls, states: List[Dict]) -> 'StateStack':
        stack = cls()
        for s in reversed(states):
            node = StateNode.from_dict(s)
            node.next = stack.top
            stack.top = node
            stack.size += 1
        return stack

    def __len__(self) -> int:
        return self.size

    def __str__(self) -> str:
        if self.is_empty():
            return "[Pila vacía]"
        lines = []
        cur = self.top
        i = self.size
        while cur:
            lines.append(f"  Estado {i}: temp={cur.temperature}, '{cur.system_instruction[:50]}...'")
            cur = cur.next
            i -= 1
        return "\n".join(lines)