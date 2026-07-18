# ============================================================
# EXCEPTIONS — Python Reference
# ============================================================
from typing import Any
import logging

# ── 1. Custom exceptions ─────────────────────────────────────
class AppError(Exception):
    """Base exception สำหรับ application"""
    def __init__(self, message: str, code: int = 0):
        super().__init__(message)
        self.code    = code
        self.message = message

    def __str__(self):
        return f"[{self.code}] {self.message}"

class ValidationError(AppError):
    """Raised เมื่อ input ไม่ถูกต้อง"""
    def __init__(self, field: str, value: Any, reason: str):
        super().__init__(f"Validation failed for '{field}': {reason}", code=400)
        self.field  = field
        self.value  = value
        self.reason = reason

class NotFoundError(AppError):
    """Raised เมื่อไม่พบข้อมูล"""
    def __init__(self, resource: str, identifier: Any):
        super().__init__(f"{resource} '{identifier}' not found", code=404)

class DatabaseError(AppError):
    """Raised เมื่อ database มีปัญหา"""
    pass

# ── 2. try / except / else / finally ─────────────────────────
def safe_divide(a: float, b: float) -> float:
    try:
        result = a / b
    except ZeroDivisionError:
        raise ValueError("Cannot divide by zero") from None
    except TypeError as e:
        raise TypeError(f"Invalid operand types: {e}") from e
    else:
        return result           # ทำงานเมื่อไม่มี exception
    finally:
        pass                    # ทำงานเสมอ (cleanup)

# ── 3. Context manager + exception ───────────────────────────
class ManagedResource:
    def __init__(self, name: str):
        self.name = name

    def __enter__(self):
        print(f"Opening {self.name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"Closing {self.name}")
        if exc_type is ValueError:
            print(f"  Suppressed ValueError: {exc_val}")
            return True     # suppress exception
        return False        # re-raise other exceptions

    def work(self):
        print(f"Working with {self.name}")

# ── 4. Exception chaining ────────────────────────────────────
def fetch_user(user_id: int) -> dict:
    if user_id <= 0:
        raise ValidationError("user_id", user_id, "must be positive")
    if user_id > 1000:
        raise NotFoundError("User", user_id)
    return {"id": user_id, "name": "Alice"}

def get_user_display(user_id: int) -> str:
    try:
        user = fetch_user(user_id)
        return f"User: {user['name']}"
    except NotFoundError as e:
        raise AppError(f"Cannot display user: {e}", code=404) from e

# ── 5. Logging with exceptions ───────────────────────────────
logging.basicConfig(level=logging.DEBUG,
                    format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def process_data(data: list) -> list:
    results = []
    for i, item in enumerate(data):
        try:
            results.append(int(item) * 2)
        except (ValueError, TypeError) as e:
            logger.warning(f"Skipping item[{i}]={item!r}: {e}")
    return results

# ── 6. Exception groups (Python 3.11+) ───────────────────────
def handle_exception_group():
    try:
        raise ExceptionGroup("multiple errors", [
            ValueError("bad value"),
            TypeError("bad type"),
            KeyError("missing key"),
        ])
    except* ValueError as eg:
        print(f"ValueError(s): {eg.exceptions}")
    except* TypeError as eg:
        print(f"TypeError(s): {eg.exceptions}")

# ── 7. assert ────────────────────────────────────────────────
def calculate_bmi(weight_kg: float, height_m: float) -> float:
    assert weight_kg > 0, f"Weight must be positive, got {weight_kg}"
    assert height_m > 0, f"Height must be positive, got {height_m}"
    return weight_kg / height_m ** 2

# ── Demo ──────────────────────────────────────────────────────
if __name__ == "__main__":
    # Custom exceptions
    try:
        fetch_user(-1)
    except ValidationError as e:
        print(e)   # [400] Validation failed for 'user_id': must be positive

    try:
        fetch_user(9999)
    except NotFoundError as e:
        print(e)   # [404] User '9999' not found

    # Context manager
    with ManagedResource("database") as res:
        res.work()

    # process_data
    print(process_data(["1", "two", "3", None, "5"]))

    # Exception groups
    try:
        handle_exception_group()
    except Exception:
        pass

    print(calculate_bmi(70, 1.75))   # 22.86
