# modulo4_persistencia.py
# Módulo 4: Persistencia y Serialización (JSON)

import os
import json
from datetime import datetime
from typing import Optional
from modulo1_configuracion import DoubleLinkedList
from modulo5_errores import ErrorLog
from modulo2_contexto import MAX_CONTEXT_MESSAGES

CONFIG_FILE = "config.json"
DATA_FILE_DEFAULT = "gemini_mesh_data.json"


class PersistenceManager:
    def __init__(self):
        self.config = self._load_config()
        self.data_file = self.config.get("data_file", DATA_FILE_DEFAULT)

    def _load_config(self) -> dict:
        if not os.path.exists(CONFIG_FILE):
            default = {"data_file": DATA_FILE_DEFAULT}
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(default, f, indent=2)
            return default
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"data_file": DATA_FILE_DEFAULT}

    def save_all(self, bot_list: DoubleLinkedList, error_log: ErrorLog) -> tuple:
        data = {
            "version": "1.0",
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "max_context_messages": MAX_CONTEXT_MESSAGES,
            "bots": bot_list.to_list(),
            "error_log": error_log.to_list()
        }
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True, f"Datos guardados en '{self.data_file}'"
        except IOError as e:
            return False, f"Error al guardar: {str(e)}"

    def load_all(self) -> tuple:
        if not os.path.exists(self.data_file):
            return None, None, f"Archivo '{self.data_file}' no encontrado."
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            bots = DoubleLinkedList.from_list(data.get("bots", []))
            errors = ErrorLog.from_list(data.get("error_log", []))
            return bots, errors, f"Datos cargados. {len(bots)} bots restaurados."
        except (json.JSONDecodeError, IOError, KeyError) as e:
            return None, None, f"Error al cargar: {str(e)}"