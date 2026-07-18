# ============================================================
# CREATIONAL PATTERNS — Python Reference
# ============================================================
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
import threading, copy

# ── 1. Singleton ─────────────────────────────────────────────
class Singleton:
    """Only one instance exists."""
    _instance: Singleton | None = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

# Singleton via metaclass (cleaner)
class SingletonMeta(type):
    _instances: dict = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class DatabaseConnection(metaclass=SingletonMeta):
    def __init__(self, host: str = "localhost"):
        self.host = host
        self.connected = False

    def connect(self):
        self.connected = True
        print(f"Connected to {self.host}")

# ── 2. Factory Method ────────────────────────────────────────
class Notification(ABC):
    @abstractmethod
    def send(self, message: str) -> bool: ...

class EmailNotification(Notification):
    def __init__(self, email: str):
        self.email = email
    def send(self, message: str) -> bool:
        print(f"Email → {self.email}: {message}")
        return True

class SMSNotification(Notification):
    def __init__(self, phone: str):
        self.phone = phone
    def send(self, message: str) -> bool:
        print(f"SMS → {self.phone}: {message}")
        return True

class PushNotification(Notification):
    def __init__(self, token: str):
        self.token = token
    def send(self, message: str) -> bool:
        print(f"Push → {self.token[:8]}…: {message}")
        return True

def notification_factory(channel: str, **kwargs) -> Notification:
    """Factory function"""
    registry = {
        "email": EmailNotification,
        "sms":   SMSNotification,
        "push":  PushNotification,
    }
    cls = registry.get(channel)
    if cls is None:
        raise ValueError(f"Unknown channel: {channel!r}")
    return cls(**kwargs)

# ── 3. Abstract Factory ──────────────────────────────────────
class Button(ABC):
    @abstractmethod
    def render(self) -> str: ...

class TextField(ABC):
    @abstractmethod
    def render(self) -> str: ...

class UIFactory(ABC):
    @abstractmethod
    def create_button(self) -> Button: ...
    @abstractmethod
    def create_text_field(self) -> TextField: ...

class WindowsButton(Button):
    def render(self) -> str: return "[Windows Button]"

class WindowsTextField(TextField):
    def render(self) -> str: return "[Windows TextField]"

class MacButton(Button):
    def render(self) -> str: return "[Mac Button ◉]"

class MacTextField(TextField):
    def render(self) -> str: return "[Mac TextField ◻]"

class WindowsFactory(UIFactory):
    def create_button(self) -> Button: return WindowsButton()
    def create_text_field(self) -> TextField: return WindowsTextField()

class MacFactory(UIFactory):
    def create_button(self) -> Button: return MacButton()
    def create_text_field(self) -> TextField: return MacTextField()

def build_ui(factory: UIFactory):
    btn = factory.create_button()
    txt = factory.create_text_field()
    print(btn.render(), txt.render())

# ── 4. Builder ───────────────────────────────────────────────
from dataclasses import dataclass, field as dc_field

@dataclass
class Pizza:
    size: str = "medium"
    crust: str = "thin"
    toppings: list[str] = dc_field(default_factory=list)
    sauce: str = "tomato"
    extra_cheese: bool = False

    def __str__(self):
        tops = ", ".join(self.toppings) or "none"
        return (f"{self.size} pizza | crust:{self.crust} | "
                f"sauce:{self.sauce} | toppings:{tops} | "
                f"extra cheese:{self.extra_cheese}")

class PizzaBuilder:
    def __init__(self):
        self._pizza = Pizza()

    def size(self, s: str)          -> "PizzaBuilder": self._pizza.size = s;          return self
    def crust(self, c: str)         -> "PizzaBuilder": self._pizza.crust = c;         return self
    def sauce(self, s: str)         -> "PizzaBuilder": self._pizza.sauce = s;         return self
    def extra_cheese(self)          -> "PizzaBuilder": self._pizza.extra_cheese = True; return self
    def topping(self, t: str)       -> "PizzaBuilder": self._pizza.toppings.append(t); return self
    def build(self) -> Pizza:        return copy.deepcopy(self._pizza)

# ── 5. Prototype ─────────────────────────────────────────────
class DocumentTemplate:
    def __init__(self, title: str, content: str, styles: dict):
        self.title   = title
        self.content = content
        self.styles  = styles

    def clone(self) -> "DocumentTemplate":
        return copy.deepcopy(self)

    def __str__(self):
        return f"Document({self.title!r})"

# ── Demo ──────────────────────────────────────────────────────
if __name__ == "__main__":
    # Singleton
    db1 = DatabaseConnection("db.example.com")
    db2 = DatabaseConnection()
    print(db1 is db2)   # True

    # Factory
    n = notification_factory("email", email="alice@example.com")
    n.send("Welcome!")

    # Abstract factory
    build_ui(WindowsFactory())
    build_ui(MacFactory())

    # Builder
    pizza = (PizzaBuilder()
             .size("large").crust("thick")
             .sauce("bbq").topping("chicken")
             .topping("onion").extra_cheese()
             .build())
    print(pizza)

    # Prototype
    template = DocumentTemplate("Report", "## Content", {"font": "Arial"})
    doc1 = template.clone()
    doc1.title = "Report Q1"
    doc2 = template.clone()
    doc2.title = "Report Q2"
    print(doc1, doc2)
