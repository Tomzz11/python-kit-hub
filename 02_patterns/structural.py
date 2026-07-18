# ============================================================
# STRUCTURAL PATTERNS — Python Reference
# ============================================================
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

# ── 1. Adapter ───────────────────────────────────────────────
class OldPaymentAPI:
    """Legacy API ที่เปลี่ยนไม่ได้"""
    def process_credit_card(self, card_number: str, amount: float) -> dict:
        return {"status": "ok", "card": card_number[-4:], "amount": amount}

class PaymentProcessor(ABC):
    @abstractmethod
    def pay(self, amount: float, method: str) -> bool: ...

class PaymentAdapter(PaymentProcessor):
    """ห่อหุ้ม OldPaymentAPI ให้ใช้งานผ่าน interface ใหม่"""
    def __init__(self, old_api: OldPaymentAPI, card_number: str):
        self._api  = old_api
        self._card = card_number

    def pay(self, amount: float, method: str) -> bool:
        result = self._api.process_credit_card(self._card, amount)
        print(f"Paid {amount} via {method}: {result}")
        return result["status"] == "ok"

# ── 2. Decorator ─────────────────────────────────────────────
class DataSource(ABC):
    @abstractmethod
    def write(self, data: str): ...
    @abstractmethod
    def read(self) -> str: ...

class FileDataSource(DataSource):
    def __init__(self, path: str):
        self._path = path
        self._data = ""
    def write(self, data: str): self._data = data
    def read(self) -> str:      return self._data

class DataSourceDecorator(DataSource):
    def __init__(self, wrappee: DataSource):
        self._wrappee = wrappee
    def write(self, data: str): self._wrappee.write(data)
    def read(self) -> str:      return self._wrappee.read()

import base64, zlib

class EncryptionDecorator(DataSourceDecorator):
    def write(self, data: str):
        encoded = base64.b64encode(data.encode()).decode()
        super().write(encoded)
    def read(self) -> str:
        encoded = super().read()
        return base64.b64decode(encoded.encode()).decode()

class CompressionDecorator(DataSourceDecorator):
    def write(self, data: str):
        compressed = base64.b64encode(zlib.compress(data.encode())).decode()
        super().write(compressed)
    def read(self) -> str:
        compressed = super().read()
        return zlib.decompress(base64.b64decode(compressed.encode())).decode()

# ── 3. Proxy ─────────────────────────────────────────────────
class ExpensiveService:
    def fetch(self, key: str) -> str:
        print(f"  [DB] Fetching '{key}'...")
        return f"data_for_{key}"

class CachingProxy:
    """Cache proxy — ดักจับ call และ cache ผลลัพธ์"""
    def __init__(self, service: ExpensiveService):
        self._service = service
        self._cache: dict[str, str] = {}

    def fetch(self, key: str) -> str:
        if key not in self._cache:
            self._cache[key] = self._service.fetch(key)
        else:
            print(f"  [Cache] HIT for '{key}'")
        return self._cache[key]

# ── 4. Facade ────────────────────────────────────────────────
class VideoEncoder:
    def encode(self, file: str, fmt: str): print(f"Encoding {file} → {fmt}")

class AudioProcessor:
    def process(self, file: str):          print(f"Processing audio: {file}")

class ThumbnailGenerator:
    def generate(self, file: str):         print(f"Generating thumbnail: {file}")

class VideoUploader:
    def upload(self, file: str, dest: str): print(f"Uploading {file} → {dest}")

class VideoPublishingFacade:
    """Facade — API เดียวซ่อนความซับซ้อนทั้งหมด"""
    def __init__(self):
        self._encoder   = VideoEncoder()
        self._audio     = AudioProcessor()
        self._thumbnail = ThumbnailGenerator()
        self._uploader  = VideoUploader()

    def publish(self, raw_file: str, destination: str = "cdn"):
        print(f"\nPublishing {raw_file}:")
        self._encoder.encode(raw_file, "mp4")
        self._audio.process(raw_file)
        self._thumbnail.generate(raw_file)
        self._uploader.upload(raw_file, destination)
        print("Done!\n")

# ── 5. Composite ─────────────────────────────────────────────
class FileSystemItem(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def size(self) -> int: ...

    def display(self, indent: int = 0):
        print(" " * indent + str(self))

class File(FileSystemItem):
    def __init__(self, name: str, size_bytes: int):
        super().__init__(name)
        self._size = size_bytes

    def size(self) -> int: return self._size
    def __str__(self):     return f"📄 {self.name} ({self._size}B)"

class Folder(FileSystemItem):
    def __init__(self, name: str):
        super().__init__(name)
        self._children: list[FileSystemItem] = []

    def add(self, item: FileSystemItem) -> "Folder":
        self._children.append(item)
        return self

    def size(self) -> int:
        return sum(c.size() for c in self._children)

    def __str__(self):
        return f"📁 {self.name}/ ({self.size()}B)"

    def display(self, indent: int = 0):
        super().display(indent)
        for child in self._children:
            child.display(indent + 2)

# ── 6. Bridge ────────────────────────────────────────────────
class Renderer(ABC):
    @abstractmethod
    def render_circle(self, x: float, y: float, r: float): ...

class SVGRenderer(Renderer):
    def render_circle(self, x, y, r):
        print(f'<circle cx="{x}" cy="{y}" r="{r}"/>')

class CanvasRenderer(Renderer):
    def render_circle(self, x, y, r):
        print(f"ctx.arc({x}, {y}, {r}, 0, 2*Math.PI)")

class Shape(ABC):
    def __init__(self, renderer: Renderer):
        self._renderer = renderer

    @abstractmethod
    def draw(self): ...

class Circle(Shape):
    def __init__(self, x: float, y: float, r: float, renderer: Renderer):
        super().__init__(renderer)
        self.x, self.y, self.r = x, y, r

    def draw(self):
        self._renderer.render_circle(self.x, self.y, self.r)

# ── Demo ──────────────────────────────────────────────────────
if __name__ == "__main__":
    # Adapter
    adapter = PaymentAdapter(OldPaymentAPI(), "4111111111111234")
    adapter.pay(250.0, "credit_card")

    # Decorator
    source = CompressionDecorator(EncryptionDecorator(FileDataSource("test")))
    source.write("Hello, Structural Patterns!")
    print(source.read())

    # Proxy
    proxy = CachingProxy(ExpensiveService())
    print(proxy.fetch("user:1"))
    print(proxy.fetch("user:1"))  # from cache

    # Facade
    VideoPublishingFacade().publish("raw_video.mov")

    # Composite
    root = Folder("project")
    src  = Folder("src").add(File("main.py", 2048)).add(File("utils.py", 1024))
    root.add(src).add(File("README.md", 512))
    root.display()
    print(f"Total: {root.size()}B")

    # Bridge
    Circle(50, 50, 30, SVGRenderer()).draw()
    Circle(50, 50, 30, CanvasRenderer()).draw()
