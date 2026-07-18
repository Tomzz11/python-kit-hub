# ============================================================
# OOP BASICS — Python Reference
# ============================================================
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar

# ── 1. Basic class ───────────────────────────────────────────
class Animal:
    species_count: ClassVar[int] = 0  # class variable

    def __init__(self, name: str, age: int):
        self.name = name        # instance variable
        self.age  = age
        Animal.species_count += 1

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, age={self.age})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name!r}, {self.age!r})"

    def speak(self) -> str:
        return "..."

    @classmethod
    def from_dict(cls, data: dict) -> "Animal":
        return cls(data["name"], data["age"])

    @staticmethod
    def is_valid_age(age: int) -> bool:
        return 0 <= age <= 150

# ── 2. Inheritance ───────────────────────────────────────────
class Dog(Animal):
    def __init__(self, name: str, age: int, breed: str):
        super().__init__(name, age)
        self.breed = breed

    def speak(self) -> str:
        return f"{self.name} says: Woof!"

    def fetch(self, item: str) -> str:
        return f"{self.name} fetched the {item}!"

class Cat(Animal):
    def speak(self) -> str:
        return f"{self.name} says: Meow!"

# ── 3. Abstract class ────────────────────────────────────────
class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...

    @abstractmethod
    def perimeter(self) -> float: ...

    def describe(self) -> str:
        return (f"{self.__class__.__name__}: "
                f"area={self.area():.2f}, perimeter={self.perimeter():.2f}")

class Circle(Shape):
    def __init__(self, radius: float):
        self.radius = radius

    def area(self) -> float:
        import math
        return math.pi * self.radius ** 2

    def perimeter(self) -> float:
        import math
        return 2 * math.pi * self.radius

class Rectangle(Shape):
    def __init__(self, width: float, height: float):
        self.width  = width
        self.height = height

    def area(self) -> float:
        return self.width * self.height

    def perimeter(self) -> float:
        return 2 * (self.width + self.height)

# ── 4. Dunder (magic) methods ────────────────────────────────
class Vector:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __add__(self, other: "Vector") -> "Vector":
        return Vector(self.x + other.x, self.y + other.y)

    def __mul__(self, scalar: float) -> "Vector":
        return Vector(self.x * scalar, self.y * scalar)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __abs__(self) -> float:
        return (self.x**2 + self.y**2) ** 0.5

    def __str__(self) -> str:
        return f"Vector({self.x}, {self.y})"

    def __len__(self) -> int:
        return 2

# ── 5. Property ──────────────────────────────────────────────
class Temperature:
    def __init__(self, celsius: float = 0.0):
        self._celsius = celsius

    @property
    def celsius(self) -> float:
        return self._celsius

    @celsius.setter
    def celsius(self, value: float):
        if value < -273.15:
            raise ValueError("Temperature below absolute zero!")
        self._celsius = value

    @property
    def fahrenheit(self) -> float:
        return self._celsius * 9/5 + 32

    @property
    def kelvin(self) -> float:
        return self._celsius + 273.15

# ── 6. Dataclass (Python 3.7+) ───────────────────────────────
@dataclass
class Point:
    x: float
    y: float

    def distance_to(self, other: "Point") -> float:
        return ((self.x - other.x)**2 + (self.y - other.y)**2) ** 0.5

@dataclass
class Student:
    name: str
    grades: list[float] = field(default_factory=list)
    _id: int = field(default=0, init=False, repr=False)

    @property
    def average(self) -> float:
        return sum(self.grades) / len(self.grades) if self.grades else 0.0

# ── 7. Mixin pattern ─────────────────────────────────────────
class LogMixin:
    def log(self, message: str):
        print(f"[{self.__class__.__name__}] {message}")

class SerializeMixin:
    def to_dict(self) -> dict:
        return self.__dict__.copy()

class User(LogMixin, SerializeMixin):
    def __init__(self, username: str, email: str):
        self.username = username
        self.email    = email

    def login(self):
        self.log(f"{self.username} logged in")

# ── Demo ──────────────────────────────────────────────────────
if __name__ == "__main__":
    dog = Dog("Rex", 3, "Labrador")
    cat = Cat("Whiskers", 5)
    print(dog.speak())
    print(cat.speak())

    c = Circle(5)
    r = Rectangle(4, 6)
    print(c.describe())
    print(r.describe())

    v1 = Vector(1, 2)
    v2 = Vector(3, 4)
    print(v1 + v2)
    print(abs(v2))      # 5.0

    t = Temperature(100)
    print(t.fahrenheit) # 212.0

    s = Student("Alice", [90, 85, 92])
    print(s.average)    # 89.0

    u = User("alice", "alice@example.com")
    u.login()
    print(u.to_dict())
