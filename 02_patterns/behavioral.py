# ============================================================
# BEHAVIORAL PATTERNS — Python Reference
# ============================================================
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Callable
from collections import defaultdict

# ── 1. Observer ──────────────────────────────────────────────
class Event:
    def __init__(self, name: str, data: Any = None):
        self.name = name
        self.data = data

class EventBus:
    """Pub/Sub event bus"""
    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event: str, handler: Callable):
        self._subscribers[event].append(handler)
        return lambda: self._subscribers[event].remove(handler)  # unsubscribe fn

    def publish(self, event: Event):
        for handler in self._subscribers.get(event.name, []):
            handler(event)

# Usage
bus = EventBus()
unsubscribe = bus.subscribe("user.created", lambda e: print(f"  Email: welcome {e.data['name']}"))
bus.subscribe("user.created", lambda e: print(f"  Log: new user {e.data['id']}"))

# ── 2. Strategy ──────────────────────────────────────────────
class SortStrategy(ABC):
    @abstractmethod
    def sort(self, data: list) -> list: ...

class QuickSort(SortStrategy):
    def sort(self, data: list) -> list:
        if len(data) <= 1: return data
        pivot = data[len(data) // 2]
        left  = [x for x in data if x < pivot]
        mid   = [x for x in data if x == pivot]
        right = [x for x in data if x > pivot]
        return self.sort(left) + mid + self.sort(right)

class BubbleSort(SortStrategy):
    def sort(self, data: list) -> list:
        d = data.copy()
        n = len(d)
        for i in range(n):
            for j in range(n - i - 1):
                if d[j] > d[j+1]:
                    d[j], d[j+1] = d[j+1], d[j]
        return d

class Sorter:
    def __init__(self, strategy: SortStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: SortStrategy):
        self._strategy = strategy

    def sort(self, data: list) -> list:
        return self._strategy.sort(data)

# ── 3. Command ───────────────────────────────────────────────
class Command(ABC):
    @abstractmethod
    def execute(self): ...
    @abstractmethod
    def undo(self): ...

class TextEditor:
    def __init__(self):
        self._text = ""

    def insert(self, text: str, pos: int):
        self._text = self._text[:pos] + text + self._text[pos:]

    def delete(self, pos: int, length: int):
        self._text = self._text[:pos] + self._text[pos + length:]

    def get(self) -> str: return self._text

class InsertCommand(Command):
    def __init__(self, editor: TextEditor, text: str, pos: int):
        self._editor = editor
        self._text, self._pos = text, pos

    def execute(self): self._editor.insert(self._text, self._pos)
    def undo(self):    self._editor.delete(self._pos, len(self._text))

class CommandHistory:
    def __init__(self):
        self._history: list[Command] = []

    def execute(self, cmd: Command):
        cmd.execute()
        self._history.append(cmd)

    def undo(self):
        if self._history:
            self._history.pop().undo()

# ── 4. Chain of Responsibility ───────────────────────────────
class Request:
    def __init__(self, level: str, message: str):
        self.level   = level   # "debug" | "info" | "warning" | "error"
        self.message = message

class Handler(ABC):
    _LEVELS = {"debug": 0, "info": 1, "warning": 2, "error": 3}

    def __init__(self, level: str):
        self._level = level
        self._next: Handler | None = None

    def set_next(self, handler: "Handler") -> "Handler":
        self._next = handler
        return handler

    def handle(self, req: Request):
        if self._LEVELS[req.level] >= self._LEVELS[self._level]:
            self._process(req)
        if self._next:
            self._next.handle(req)

    @abstractmethod
    def _process(self, req: Request): ...

class ConsoleHandler(Handler):
    def _process(self, req: Request):
        print(f"  [Console/{req.level.upper()}] {req.message}")

class FileHandler(Handler):
    def _process(self, req: Request):
        print(f"  [File/{req.level.upper()}] {req.message}")

class AlertHandler(Handler):
    def _process(self, req: Request):
        print(f"  *** ALERT [{req.level.upper()}] {req.message} ***")

# ── 5. Template Method ───────────────────────────────────────
class DataProcessor(ABC):
    """Template method — กำหนดขั้นตอน, ให้ subclass implement detail"""

    def process(self, source: str) -> list:
        raw       = self._fetch(source)
        parsed    = self._parse(raw)
        validated = self._validate(parsed)
        self._save(validated)
        return validated

    @abstractmethod
    def _fetch(self, source: str) -> str: ...
    @abstractmethod
    def _parse(self, raw: str) -> list: ...

    def _validate(self, data: list) -> list:
        return [item for item in data if item]  # default: remove falsy

    def _save(self, data: list):
        print(f"  Saved {len(data)} records")

class CSVProcessor(DataProcessor):
    def _fetch(self, source: str) -> str:
        return "alice,30\nbob,25\ncharlie,35"

    def _parse(self, raw: str) -> list:
        return [{"name": r[0], "age": int(r[1])}
                for line in raw.splitlines()
                if (r := line.split(",")) and len(r) == 2]

# ── 6. Iterator ──────────────────────────────────────────────
class NumberRange:
    """Custom iterator"""
    def __init__(self, start: int, end: int, step: int = 1):
        self._start = start
        self._end   = end
        self._step  = step

    def __iter__(self):
        current = self._start
        while current < self._end:
            yield current
            current += self._step

# ── 7. State ─────────────────────────────────────────────────
class TrafficLight:
    _transitions = {"red": "green", "green": "yellow", "yellow": "red"}
    _actions     = {"red": "Stop",  "green": "Go",     "yellow": "Caution"}

    def __init__(self):
        self._state = "red"

    @property
    def state(self): return self._state

    def next(self):
        self._state = self._transitions[self._state]
        print(f"  → {self._state.upper()}: {self._actions[self._state]}")

# ── Demo ──────────────────────────────────────────────────────
if __name__ == "__main__":
    # Observer
    print("Observer:")
    bus.publish(Event("user.created", {"id": 1, "name": "Alice"}))

    # Strategy
    print("\nStrategy:")
    sorter = Sorter(QuickSort())
    print(sorter.sort([5, 3, 8, 1, 9, 2]))
    sorter.set_strategy(BubbleSort())
    print(sorter.sort([5, 3, 8, 1, 9, 2]))

    # Command + undo
    print("\nCommand:")
    editor  = TextEditor()
    history = CommandHistory()
    history.execute(InsertCommand(editor, "Hello", 0))
    history.execute(InsertCommand(editor, " World", 5))
    print(editor.get())   # Hello World
    history.undo()
    print(editor.get())   # Hello

    # Chain of responsibility
    print("\nChain:")
    console = ConsoleHandler("debug")
    file_h  = FileHandler("warning")
    alert   = AlertHandler("error")
    console.set_next(file_h).set_next(alert)
    console.handle(Request("info",    "App started"))
    console.handle(Request("error",   "Disk full!"))

    # Template method
    print("\nTemplate:")
    print(CSVProcessor().process("data.csv"))

    # Iterator
    print("\nIterator:")
    print(list(NumberRange(0, 20, 3)))

    # State
    print("\nState:")
    light = TrafficLight()
    for _ in range(4): light.next()
