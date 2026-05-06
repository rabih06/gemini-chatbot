# modulo2_contexto.py
# Módulo 2: TDA Contexto de Conversación (Cola)

from typing import Optional, List, Dict

MAX_CONTEXT_MESSAGES = 10

class MessageNode:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
        self.next: Optional[MessageNode] = None

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'MessageNode':
        return cls(data["role"], data["content"])


class MessageQueue:
    def __init__(self, max_size: int = MAX_CONTEXT_MESSAGES):
        self.front: Optional[MessageNode] = None
        self.rear: Optional[MessageNode] = None
        self.size = 0
        self.max_size = max_size

    def is_empty(self) -> bool:
        return self.front is None

    def is_full(self) -> bool:
        return self.size >= self.max_size

    def enqueue(self, role: str, content: str) -> None:
        new_node = MessageNode(role, content)
        if self.is_full():
            self.dequeue()
        if self.is_empty():
            self.front = self.rear = new_node
        else:
            self.rear.next = new_node
            self.rear = new_node
        self.size += 1

    def dequeue(self) -> Optional[MessageNode]:
        if self.is_empty():
            return None
        removed = self.front
        self.front = self.front.next
        if self.front is None:
            self.rear = None
        self.size -= 1
        removed.next = None
        return removed

    def get_all_messages(self) -> List[Dict[str, str]]:
        msgs = []
        cur = self.front
        while cur:
            msgs.append({"role": cur.role, "content": cur.content})
            cur = cur.next
        return msgs

    def clear(self) -> None:
        while not self.is_empty():
            self.dequeue()

    def to_list(self) -> List[Dict[str, str]]:
        return self.get_all_messages()

    @classmethod
    def from_list(cls, messages: List[Dict[str, str]], max_size: int = MAX_CONTEXT_MESSAGES) -> 'MessageQueue':
        q = cls(max_size)
        for m in messages:
            q.enqueue(m["role"], m["content"])
        return q

    def __len__(self) -> int:
        return self.size

    def __str__(self) -> str:
        if self.is_empty():
            return "[Cola vacía]"
        msgs = self.get_all_messages()
        return "\n".join(
            f"  {i+1}. [{m['role']}] {m['content'][:100]}{'...' if len(m['content']) > 100 else ''}"
            for i, m in enumerate(msgs)
        )