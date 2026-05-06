# modulo1_configuracion.py
# Módulo 1: TDA Configuración (Lista Enlazada Doble de Perfiles)

import base64
from typing import Optional, List, Dict
from modulo2_contexto import MessageQueue, MAX_CONTEXT_MESSAGES
from modulo3_restauracion import StateStack, DEFAULT_TEMPERATURE

# Ofuscación simple para API Keys
OBFUSCATION_KEY = "G3m1n1M3sh_S3cur3K3y_2026"

def _obfuscate(text: str) -> str:
    if not text:
        return ""
    key = OBFUSCATION_KEY
    xored = ''.join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(text))
    return base64.b64encode(xored.encode('utf-8')).decode('utf-8')

def _deobfuscate(obfuscated: str) -> str:
    if not obfuscated:
        return ""
    try:
        decoded = base64.b64decode(obfuscated.encode('utf-8')).decode('utf-8')
        key = OBFUSCATION_KEY
        return ''.join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(decoded))
    except Exception:
        return "[ERROR DECRYPT]"

class BotProfile:
    _id_counter = 0

    def __init__(self, name: str, model: str, api_key: str,
                 system_instruction: str = "", temperature: float = DEFAULT_TEMPERATURE):
        BotProfile._id_counter += 1
        self.id = BotProfile._id_counter
        self.name = name
        self.model = model
        self.api_key = api_key
        self.system_instruction = system_instruction
        self.temperature = temperature

        # Punteros de la lista doble
        self.prev: Optional[BotProfile] = None
        self.next: Optional[BotProfile] = None

        # Estructuras hijas (módulos 2 y 3)
        self.message_queue = MessageQueue()
        self.state_stack = StateStack()

    @classmethod
    def reset_id_counter(cls, value=0):
        cls._id_counter = value

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "model": self.model,
            "api_key_obfuscated": _obfuscate(self.api_key),
            "system_instruction": self.system_instruction,
            "temperature": self.temperature,
            "message_queue": self.message_queue.to_list(),
            "state_stack": self.state_stack.to_list()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'BotProfile':
        if data["id"] > cls._id_counter:
            cls._id_counter = data["id"]
        bot = cls.__new__(cls)
        bot.id = data["id"]
        bot.name = data["name"]
        bot.model = data["model"]
        bot.api_key = _deobfuscate(data.get("api_key_obfuscated", ""))
        bot.system_instruction = data.get("system_instruction", "")
        bot.temperature = data.get("temperature", DEFAULT_TEMPERATURE)
        bot.prev = None
        bot.next = None
        bot.message_queue = MessageQueue.from_list(data.get("message_queue", []))
        bot.state_stack = StateStack.from_list(data.get("state_stack", []))
        return bot

    def __str__(self):
        return (f"Bot #{self.id}: '{self.name}' | Modelo: {self.model} | "
                f"Temp: {self.temperature} | Cola: {len(self.message_queue)} msgs | "
                f"Pila: {len(self.state_stack)} estados")


class DoubleLinkedList:
    def __init__(self):
        self.head: Optional[BotProfile] = None
        self.tail: Optional[BotProfile] = None
        self.size = 0

    def is_empty(self) -> bool:
        return self.head is None

    def append(self, bot: BotProfile) -> None:
        if self.is_empty():
            self.head = self.tail = bot
        else:
            self.tail.next = bot
            bot.prev = self.tail
            self.tail = bot
        self.size += 1

    def find_by_id(self, bot_id: int) -> Optional[BotProfile]:
        cur = self.head
        while cur:
            if cur.id == bot_id:
                return cur
            cur = cur.next
        return None

    def delete_by_id(self, bot_id: int) -> bool:
        bot = self.find_by_id(bot_id)
        if not bot:
            return False
        # Liberar estructuras hijas
        bot.message_queue.clear()
        bot.state_stack.clear()
        # Desenlazar
        if bot.prev:
            bot.prev.next = bot.next
        else:
            self.head = bot.next
        if bot.next:
            bot.next.prev = bot.prev
        else:
            self.tail = bot.prev
        bot.prev = bot.next = None
        self.size -= 1
        return True

    def get_all(self) -> List[BotProfile]:
        bots = []
        cur = self.head
        while cur:
            bots.append(cur)
            cur = cur.next
        return bots

    def clear(self) -> None:
        cur = self.head
        while cur:
            nxt = cur.next
            cur.message_queue.clear()
            cur.state_stack.clear()
            cur.prev = cur.next = None
            cur = nxt
        self.head = self.tail = None
        self.size = 0

    def to_list(self) -> List[Dict]:
        return [bot.to_dict() for bot in self.get_all()]

    @classmethod
    def from_list(cls, data_list: List[Dict]) -> 'DoubleLinkedList':
        dll = cls()
        BotProfile.reset_id_counter(0)
        for data in data_list:
            bot = BotProfile.from_dict(data)
            dll.append(bot)
        return dll

    def __len__(self) -> int:
        return self.size

    def __iter__(self):
        cur = self.head
        while cur:
            yield cur
            cur = cur.next