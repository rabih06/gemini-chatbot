# modulo6_cli.py
# Módulo 6: Interfaz de Línea de Comandos y Orquestador

import os
import time
from typing import Optional
from modulo1_configuracion import BotProfile, DoubleLinkedList
from modulo2_contexto import MAX_CONTEXT_MESSAGES
from modulo3_restauracion import StateStack
from modulo4_persistencia import PersistenceManager
from modulo5_errores import ErrorLog

DEFAULT_MODEL = "gemini-1.5-flash"
DEFAULT_TEMPERATURE = 0.7

# Intento de importar API real de Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class GeminiService:
    @staticmethod
    def get_response(bot: BotProfile, user_message: str) -> str:
        if not GEMINI_AVAILABLE:
            return GeminiService._simulate(bot, user_message, "Librería no instalada")
        if not bot.api_key or bot.api_key.startswith("DEFAULT"):
            return GeminiService._simulate(bot, user_message, "API Key inválida")
        try:
            genai.configure(api_key=bot.api_key)
            history = bot.message_queue.get_all_messages()
            model = genai.GenerativeModel(
                model_name=bot.model,
                system_instruction=bot.system_instruction
            )
            chat = model.start_chat(history=[
                {"role": m["role"], "parts": [m["content"]]} for m in history[:-1]
            ])
            response = chat.send_message(
                user_message,
                generation_config={"temperature": bot.temperature}
            )
            return response.text
        except Exception as e:
            return GeminiService._simulate(bot, user_message, f"Error API: {e}")

    @staticmethod
    def _simulate(bot: BotProfile, user_message: str, motivo: str = "") -> str:
        time.sleep(0.3)
        msg = f"[SIMULACIÓN] Respuesta para: '{user_message[:50]}...'. Modelo: {bot.model}, Temp: {bot.temperature}"
        if motivo:
            msg += f" ({motivo})"
        return msg


class GeminiOrchestratorCLI:
    def __init__(self):
        self.bots = DoubleLinkedList()
        self.error_log = ErrorLog()
        self.persistence = PersistenceManager()
        self.current_bot: Optional[BotProfile] = None
        self.running = True
        self.last_command = ""  # Para recordar el último comando ejecutado
        self._register_commands()

    def _register_commands(self):
        self.commands = {
            "list":         (self.cmd_list,         "Listar todos los bots"),
            "select":       (self.cmd_select,       "Seleccionar un bot: select <id>"),
            "create":       (self.cmd_create,       "Crear un nuevo bot"),
            "delete":       (self.cmd_delete,       "Eliminar un bot: delete <id>"),
            "edit":         (self.cmd_edit,         "Modificar bot: edit <campo> <valor>"),
            "chat":         (self.cmd_chat,         "Enviar mensaje: chat <mensaje>"),
            "undo":         (self.cmd_undo,         "Deshacer último cambio (pila)"),
            "current":      (self.cmd_current,      "Mostrar bot actual + cola/pila"),
            "log":          (self.cmd_log,          "Mostrar registro de errores"),
            "save":         (self.cmd_save,         "Guardar todo a JSON"),
            "load":         (self.cmd_load,         "Cargar datos desde JSON"),
            "exit-chatbot": (self.cmd_exit_chatbot, "Salir del chatbot actual"),
            "clear":        (self.cmd_clear,        "Limpiar pantalla"),
            "help":         (self.cmd_help,         "Mostrar ayuda detallada"),
            "exit":         (self.cmd_exit,         "Salir del programa")
        }

    # ================================================================
    # MÉTODOS DE VISUALIZACIÓN
    # ================================================================
    def _print_banner(self):
        """Banner principal del sistema."""
        print("\n" + "="*80)
        print("  GEMINI MESH - Sistema de Orquestación de Chatbots Dinámicos")
        print("  Universidad José Antonio Páez - Ingeniería en Computación")
        print("="*80)

    def _print_commands_bar(self):
        """Barra compacta de comandos disponibles siempre visible."""
        print("-"*80)
        print("  COMANDOS: ", end="")
        commands_list = [
            "list", "select <id>", "create", "delete <id>",
            "edit <campo> <valor>", "chat <msj>", "undo",
            "current", "log", "save", "load",
            "exit-chatbot", "clear", "help", "exit"
        ]
        print(" | ".join(commands_list))
        print("-"*80)

    def _print_status_bar(self):
        """Barra de estado mostrando información relevante."""
        status_parts = []
        
        # Bot seleccionado
        if self.current_bot:
            status_parts.append(f"Bot actual: [{self.current_bot.id}] {self.current_bot.name}")
        else:
            status_parts.append("Bot actual: NINGUNO")
        
        # Total de bots
        status_parts.append(f"Total bots: {len(self.bots)}")
        
        # Errores acumulados
        status_parts.append(f"Errores: {len(self.error_log)}")
        
        # Último comando
        if self.last_command:
            status_parts.append(f"Último: {self.last_command}")
        
        print("-"*80)
        print("  " + " | ".join(status_parts))
        print("="*80)

    def _show_interface(self):
        """Muestra la interfaz completa."""
        self._print_banner()
        self._print_commands_bar()
        self._print_status_bar()

    def _prompt(self):
        """Genera el prompt según si hay bot seleccionado."""
        if self.current_bot:
            return f"gemini-mesh [{self.current_bot.name}]> "
        return "gemini-mesh> "

    # ================================================================
    # INICIALIZACIÓN
    # ================================================================
    def initialize(self):
        """Inicializa el sistema cargando datos o creando defaults."""
        self._show_interface()
        
        print("\n  [INICIO] Inicializando sistema...")
        bots, log, msg = self.persistence.load_all()
        
        if bots:
            self.bots = bots
            self.error_log = log
            print(f"  [OK] {msg}")
        else:
            print(f"  [INFO] {msg}")
            self._create_default_bots()
        
        print(f"  [READY] {len(self.bots)} bot(s) listos.")
        print(f"  [TIP] Escriba un comando de la barra superior o 'help' para más detalles.\n")

    def _create_default_bots(self):
        """Crea bots de prueba."""
        b1 = BotProfile("Code Helper", DEFAULT_MODEL, "AIzaSyDEFAULT_KEY1",
                        "Eres un asistente experto en programación.", 0.3)
        b1.message_queue.enqueue("user", "¿Cómo implemento una lista enlazada?")
        b1.message_queue.enqueue("assistant", "Te explico paso a paso...")
        self.bots.append(b1)

        b2 = BotProfile("Creative Writer", "gemini-1.5-pro", "AIzaSyDEFAULT_KEY2",
                        "Eres un asistente creativo para escritura.", 0.9)
        self.bots.append(b2)

        b3 = BotProfile("Study Buddy", DEFAULT_MODEL, "AIzaSyDEFAULT_KEY3",
                        "Eres un tutor académico que explica de forma sencilla.", 0.5)
        self.bots.append(b3)
        print("  [OK] 3 bots de prueba creados.")

    # ================================================================
    # COMANDOS DEL SISTEMA
    # ================================================================
    def cmd_list(self, _=""):
        """Lista todos los bots registrados."""
        if self.bots.is_empty():
            print("\n[INFO] No hay bots registrados. Use 'create' para añadir uno.")
            return
        
        print("\n" + "="*60)
        print("  LISTA DE CHATBOTS REGISTRADOS")
        print("="*60)
        for bot in self.bots:
            mark = "  ◄── ACTUAL" if self.current_bot and bot.id == self.current_bot.id else ""
            print(f"\n  ┌─ Bot #{bot.id}: {bot.name}")
            print(f"  ├─ Modelo: {bot.model}")
            print(f"  ├─ Temperatura: {bot.temperature}")
            print(f"  ├─ Cola de mensajes: {len(bot.message_queue)}/{MAX_CONTEXT_MESSAGES}")
            print(f"  ├─ Pila de estados: {len(bot.state_stack)}")
            print(f"  └─ System Instruction: {bot.system_instruction[:60]}...")
            if mark:
                print(f"  {mark}")
        print("="*60 + f"\n  Total: {len(self.bots)} bot(s)")

    def cmd_select(self, args=""):
        """Selecciona un bot por ID."""
        if not args:
            print("\n[ERROR] Debe especificar un ID. Ejemplo: select 1")
            return
        try:
            bot_id = int(args.strip())
        except ValueError:
            print("\n[ERROR] El ID debe ser un número entero.")
            return
        
        bot = self.bots.find_by_id(bot_id)
        if bot:
            self.current_bot = bot
            print(f"\n{'='*60}")
            print(f"  Bot #{bot.id} '{bot.name}' SELECCIONADO")
            print(f"  Modelo: {bot.model} | Temperatura: {bot.temperature}")
            print(f"  System Instruction: {bot.system_instruction[:80]}...")
            print(f"  Mensajes en contexto: {len(bot.message_queue)}/{MAX_CONTEXT_MESSAGES}")
            print(f"{'='*60}")
        else:
            print(f"\n[ERROR] No se encontró ningún bot con ID = {bot_id}")
            self.error_log.add_error("SELECT_NOT_FOUND", f"ID {bot_id} no existe")

    def cmd_create(self, _=""):
        """Crea un nuevo chatbot interactivamente."""
        print("\n" + "="*60)
        print("  CREAR NUEVO CHATBOT")
        print("="*60)
        
        name = input("  Nombre del bot: ").strip()
        if not name:
            print("[ERROR] El nombre es obligatorio."); return
        
        print("\n  Modelos disponibles: gemini-1.5-flash, gemini-1.5-pro, gemini-pro")
        model = input("  Modelo [gemini-1.5-flash]: ").strip() or DEFAULT_MODEL
        
        api_key = input("  API Key de Gemini: ").strip() or "DEFAULT_KEY"
        
        print("\n  System Instruction (prompt base del bot):")
        sys_instr = input("  ").strip() or "Eres un asistente útil y amigable."
        
        temp_str = input("   Temperatura (0.0-1.0) [0.7]: ").strip()
        try:
            temp = float(temp_str) if temp_str else DEFAULT_TEMPERATURE
            temp = max(0.0, min(1.0, temp))
        except ValueError:
            temp = DEFAULT_TEMPERATURE
        
        bot = BotProfile(name, model, api_key, sys_instr, temp)
        self.bots.append(bot)
        self.current_bot = bot
        
        print(f"\n{'='*60}")
        print(f"  Bot #{bot.id} '{bot.name}' CREADO Y SELECCIONADO")
        print(f"{'='*60}")

    def cmd_delete(self, args=""):
        """Elimina un bot por ID."""
        if not args:
            print("\n[ERROR] Uso: delete <id>"); return
        try:
            bot_id = int(args.strip())
        except ValueError:
            print("\n[ERROR] ID inválido."); return
        
        # Verificar si es el bot actual
        if self.current_bot and self.current_bot.id == bot_id:
            print(f"[INFO] Deseleccionando bot #{bot_id}...")
            self.current_bot = None
        
        if self.bots.delete_by_id(bot_id):
            print(f"\nBot #{bot_id} eliminado exitosamente (memoria liberada).")
        else:
            print(f"\n[ERROR] Bot #{bot_id} no encontrado.")
            self.error_log.add_error("DELETE_NOT_FOUND", f"ID {bot_id}")

    def cmd_edit(self, args=""):
        """Edita un campo del bot actual."""
        if not self.current_bot:
            print("\n[ERROR] No hay bot seleccionado. Use 'select <id>' primero.")
            return
        
        parts = args.split(maxsplit=1)
        if len(parts) < 1:
            print("\n[ERROR] Uso: edit <campo> <valor>")
            print("  Campos disponibles: name, model, apikey, instruction, temperature")
            print("  Ejemplo: edit name 'Mi Nuevo Bot'")
            print("  Ejemplo: edit temperature 0.9")
            return
        
        field = parts[0].lower()
        value = parts[1] if len(parts) > 1 else ""
        valid = {
            "name": "Nombre del bot",
            "model": "Modelo de Gemini",
            "apikey": "API Key",
            "instruction": "System Instruction",
            "temperature": "Temperatura (0.0-1.0)"
        }
        
        if field not in valid:
            print(f"\n[ERROR] Campo '{field}' no válido.")
            print(f"  Campos disponibles: {', '.join(valid.keys())}")
            self.error_log.add_error("EDIT_INVALID_FIELD", field)
            return
        
        # Guardar snapshot en la pila
        self.current_bot.state_stack.push(
            self.current_bot.system_instruction,
            self.current_bot.temperature
        )
        
        try:
            bot = self.current_bot
            old_value = ""
            
            if field == "name":
                if not value: raise ValueError("El nombre no puede estar vacío")
                old_value = bot.name
                bot.name = value
            elif field == "model":
                if not value: raise ValueError("El modelo no puede estar vacío")
                old_value = bot.model
                bot.model = value
            elif field == "apikey":
                if not value: raise ValueError("La API Key no puede estar vacía")
                old_value = "********"
                bot.api_key = value
            elif field == "instruction":
                old_value = bot.system_instruction[:50] + "..."
                bot.system_instruction = value
            elif field == "temperature":
                temp = float(value)
                if not 0.0 <= temp <= 1.0:
                    raise ValueError("La temperatura debe estar entre 0.0 y 1.0")
                old_value = str(bot.temperature)
                bot.temperature = temp
            
            print(f"\nCampo '{field}' ({valid[field]}) actualizado:")
            print(f"   Anterior: {old_value}")
            print(f"   Nuevo: {value if field != 'apikey' else '********'}")
            print(f" Snapshot guardado en pila. Use 'undo' para restaurar.")
            
        except ValueError as e:
            self.current_bot.state_stack.pop()  # Revertir snapshot
            print(f"\n[ERROR] {str(e)}")
        except Exception as e:
            self.current_bot.state_stack.pop()
            print(f"\n[ERROR] Error inesperado: {str(e)}")
            self.error_log.add_error("EDIT_ERROR", str(e))

    def cmd_chat(self, args=""):
        """Envía un mensaje al bot y recibe respuesta."""
        if not self.current_bot:
            print("\n[ERROR] No hay bot seleccionado. Use 'select <id>' primero.")
            return
        
        if not args:
            print("\n[ERROR] Debe escribir un mensaje. Ejemplo: chat 'Hola, ¿cómo estás?'")
            return
        
        message = args.strip()
        
        print(f"\n{'─'*60}")
        print(f"   TÚ: {message}")
        
        # Encolar mensaje del usuario
        self.current_bot.message_queue.enqueue("user", message)
        
        # Obtener respuesta de Gemini o simulación
        print(f"   {self.current_bot.name} está pensando...")
        response = GeminiService.get_response(self.current_bot, message)
        
        # Encolar la respuesta
        self.current_bot.message_queue.enqueue("assistant", response)
        
        print(f"   BOT: {response}")
        print(f"{'─'*60}")
        print(f"   Mensajes en contexto: {len(self.current_bot.message_queue)}/{MAX_CONTEXT_MESSAGES}")

    def cmd_undo(self, _=""):
        """Restaura el último estado de configuración."""
        if not self.current_bot:
            print("\n[ERROR] No hay bot seleccionado."); return
        
        if self.current_bot.state_stack.is_empty():
            print("\n[INFO] La pila está vacía, no hay estados anteriores que restaurar.")
            return
        
        prev = self.current_bot.state_stack.pop()
        old_instr = self.current_bot.system_instruction
        old_temp = self.current_bot.temperature
        
        self.current_bot.system_instruction = prev.system_instruction
        self.current_bot.temperature = prev.temperature
        
        print(f"\n{'─'*60}")
        print(f"   ESTADO RESTAURADO (quedan {len(self.current_bot.state_stack)} en pila)")
        print(f"{'─'*60}")
        print(f"  System Instruction:")
        print(f"    Antes: {old_instr[:60]}...")
        print(f"    Ahora: {prev.system_instruction[:60]}...")
        print(f"  Temperatura:")
        print(f"    Antes: {old_temp}")
        print(f"    Ahora: {prev.temperature}")
        print(f"{'─'*60}")

    def cmd_current(self, _=""):
        """Muestra toda la info del bot seleccionado."""
        if not self.current_bot:
            print("\n[INFO] No hay ningún bot seleccionado. Use 'select <id>'.")
            return
        
        bot = self.current_bot
        print(f"\n{'='*70}")
        print(f"  INFORMACIÓN DEL BOT SELECCIONADO")
        print(f"{'='*70}")
        print(f"   ID:                {bot.id}")
        print(f"   Nombre:            {bot.name}")
        print(f"   Modelo:            {bot.model}")
        print(f"   API Key:           {'*' * 30} (protegida)")
        print(f"   Temperatura:       {bot.temperature}")
        print(f"   System Instruction: {bot.system_instruction[:100]}{'...' if len(bot.system_instruction) > 100 else ''}")
        print(f"{'─'*70}")
        print(f"   COLA DE MENSAJES ({len(bot.message_queue)}/{MAX_CONTEXT_MESSAGES}):")
        print(bot.message_queue if not bot.message_queue.is_empty() else "  [Sin mensajes]")
        print(f"{'─'*70}")
        print(f"   PILA DE ESTADOS ({len(bot.state_stack)} estados guardados):")
        print(bot.state_stack if not bot.state_stack.is_empty() else "  [Sin estados guardados]")
        print(f"{'='*70}")

    def cmd_log(self, _=""):
        """Muestra el registro de errores."""
        print(f"\n{'='*70}")
        print(f"  REGISTRO DE ERRORES DEL SISTEMA")
        print(f"{'='*70}")
        if self.error_log.is_empty():
            print("   No hay errores registrados.")
        else:
            print(self.error_log)
        print(f"{'='*70}")
        print(f"  Total de errores: {len(self.error_log)}")

    def cmd_save(self, _=""):
        """Guarda todos los datos."""
        print("\n Guardando datos...")
        ok, msg = self.persistence.save_all(self.bots, self.error_log)
        if ok:
            print(f"{msg}")
        else:
            print(f"{msg}")
            self.error_log.add_error("SAVE_ERROR", msg)

    def cmd_load(self, _=""):
        """Carga datos desde archivo."""
        print("\n ADVERTENCIA: Esto sobrescribirá todos los datos actuales.")
        confirm = input("  ¿Está seguro? (s/n): ").strip().lower()
        if confirm != 's':
            print("[INFO] Carga cancelada.")
            return
        
        print(" Cargando datos...")
        bots, log, msg = self.persistence.load_all()
        if bots:
            self.bots.clear()
            self.bots = bots
            self.error_log = log
            self.current_bot = None
            print(f"{msg}")
        else:
            print(f" {msg}")
            self.error_log.add_error("LOAD_ERROR", msg)

    def cmd_exit_chatbot(self, _=""):
        """Sale del chatbot actual."""
        if self.current_bot:
            print(f"\n Saliendo del chatbot '{self.current_bot.name}'.")
            self.current_bot = None
        else:
            print("\n[INFO] No hay chatbot seleccionado.")

    def cmd_clear(self, _=""):
        """Limpia la pantalla."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def cmd_help(self, _=""):
        """Muestra ayuda detallada."""
        print(f"""
{'='*70}
  AYUDA DETALLADA - GEMINI MESH
{'='*70}

    COMANDOS BÁSICOS:
    list              - Muestra todos los chatbots registrados
    select <id>       - Selecciona un bot para interactuar con él
    create            - Crea un nuevo bot (interactivo)
    delete <id>       - Elimina un bot y libera su memoria
    exit-chatbot      - Deselecciona el bot actual

   CHAT:
    chat <mensaje>    - Envía un mensaje al bot seleccionado
                        El historial se mantiene en la cola de contexto
                        (últimos {MAX_CONTEXT_MESSAGES} mensajes)

   CONFIGURACIÓN:
    edit <campo> <valor> - Modifica un campo del bot actual
      Campos: name, model, apikey, instruction, temperature
      Ejemplo: edit name "Asistente AI"
      Ejemplo: edit temperature 0.9
    undo              - Restaura la configuración anterior (usa la pila)

   INFORMACIÓN:
    current           - Muestra todo del bot actual (cola, pila, config)
    log               - Muestra el registro de errores del sistema

    PERSISTENCIA:
    save              - Guarda todos los datos en JSON
    load              - Carga datos desde JSON (sobrescribe)

   SISTEMA:
    clear             - Limpia la pantalla
    help              - Muestra esta ayuda
    exit              - Sale del programa liberando memoria

{'='*70}
   TIP: Los comandos de la barra superior están siempre visibles.
   TIP: Use TAB para autocompletar (si su terminal lo soporta).
{'='*70}
""")

    def cmd_exit(self, _=""):
        """Sale del programa."""
        print(f"\n{'='*70}")
        print("  SALIENDO DE GEMINI MESH")
        print(f"{'='*70}")
        print("   Liberando memoria de todas las estructuras...")
        self.bots.clear()
        self.error_log.clear()
        self.current_bot = None
        self.running = False
        print("   Memoria liberada exitosamente.")
        print("   ¡Hasta luego!")
        print(f"{'='*70}\n")

    # ================================================================
    # BUCLE PRINCIPAL
    # ================================================================
    def run(self):
        """Ejecuta el bucle principal del CLI."""
        self.initialize()
        
        while self.running:
            try:
                print()  # Espacio antes de la interfaz
                self._show_interface()
                
                # Leer comando del usuario
                user_input = input(self._prompt()).strip()
                
                if not user_input:
                    continue
                
                # Parsear comando
                parts = user_input.split(maxsplit=1)
                cmd = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                # Recordar último comando
                self.last_command = cmd
                
                # Ejecutar comando
                if cmd in self.commands:
                    func, _ = self.commands[cmd]
                    func(args)
                else:
                    print(f"\n Comando '{cmd}' no reconocido.")
                    print("   Escriba 'help' para ver todos los comandos disponibles.")
                    self.error_log.add_error("UNKNOWN_CMD", f"Comando '{cmd}' no existe")
                
                # Pequeña pausa para legibilidad
                if cmd not in ["exit", "clear"]:
                    input("\n  Presione ENTER para continuar...")
                
            except KeyboardInterrupt:
                print("\n\n[INFO] Interrupción detectada (Ctrl+C).")
                print("[INFO] Use 'exit' para salir correctamente.")
                input("  Presione ENTER para continuar...")
            except EOFError:
                self.cmd_exit()
                break
            except Exception as e:
                print(f"\n ERROR INESPERADO: {str(e)}")
                self.error_log.add_error("UNEXPECTED", str(e))
                input("  Presione ENTER para continuar...")