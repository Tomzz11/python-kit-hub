# ============================================================
# FUNCTIONS — Python Reference
# ============================================================
from functools import wraps, reduce
from typing import Callable, Any
import time

# ── 1. Basic function ────────────────────────────────────────
def greet(name: str, greeting: str = "Hello") -> str:
    """Return a greeting string."""
    return f"{greeting}, {name}!"

print(greet("Alice"))               # Hello, Alice!
print(greet("Bob", "Hi"))           # Hi, Bob!
print(greet(name="Charlie"))        # Hello, Charlie!

# ── 2. *args and **kwargs ────────────────────────────────────
def sum_all(*args: int) -> int:
    return sum(args)

def show_info(**kwargs):
    for k, v in kwargs.items():
        print(f"  {k}: {v}")

def mixed(first, *args, sep="-", **kwargs):
    parts = [str(first)] + [str(a) for a in args]
    result = sep.join(parts)
    for k, v in kwargs.items():
        result += f" | {k}={v}"
    return result

print(sum_all(1, 2, 3, 4, 5))      # 15
show_info(name="Alice", age=30)
print(mixed(1, 2, 3, sep="+", extra="yes"))

# ── 3. Lambda ────────────────────────────────────────────────
square   = lambda x: x ** 2
add      = lambda x, y: x + y

people = [{"name": "Charlie", "age": 25},
          {"name": "Alice",   "age": 30},
          {"name": "Bob",     "age": 20}]
people.sort(key=lambda p: p["age"])

nums = [1, 2, 3, 4, 5, 6]
evens   = list(filter(lambda x: x % 2 == 0, nums))
doubled = list(map(lambda x: x * 2, nums))
total   = reduce(lambda a, b: a + b, nums)

# ── 4. Closure ───────────────────────────────────────────────
def make_counter(start: int = 0):
    count = start
    def counter():
        nonlocal count
        count += 1
        return count
    return counter

c1 = make_counter()
c2 = make_counter(10)
print(c1(), c1(), c1())   # 1 2 3
print(c2(), c2())          # 11 12

def make_multiplier(factor: float):
    return lambda x: x * factor

double = make_multiplier(2)
triple = make_multiplier(3)
print(double(5), triple(5))   # 10 15

# ── 5. Decorator ─────────────────────────────────────────────
def timer(func: Callable) -> Callable:
    """วัดเวลาการทำงานของฟังก์ชัน"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"[{func.__name__}] took {elapsed:.4f}s")
        return result
    return wrapper

def retry(times: int = 3, exceptions=(Exception,)):
    """Retry ฟังก์ชันเมื่อเกิด exception"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == times:
                        raise
                    print(f"Attempt {attempt} failed: {e}. Retrying...")
        return wrapper
    return decorator

def memoize(func: Callable) -> Callable:
    """Cache ผลลัพธ์ของฟังก์ชัน"""
    cache: dict = {}
    @wraps(func)
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]
    return wrapper

@timer
def slow_sum(n: int) -> int:
    return sum(range(n))

@memoize
def fib(n: int) -> int:
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)

print(slow_sum(1_000_000))
print(fib(40))

# ── 6. Generator function ────────────────────────────────────
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

def read_chunks(filename: str, size: int = 1024):
    """อ่านไฟล์แบบ chunk-by-chunk"""
    with open(filename, "rb") as f:
        while chunk := f.read(size):
            yield chunk

gen = fibonacci()
fibs = [next(gen) for _ in range(10)]
print(fibs)   # [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

# ── 7. Type hints ────────────────────────────────────────────
from typing import Optional, Union, list as List, dict as Dict

def process(
    items: list[int],
    multiplier: float = 1.0,
    label: Optional[str] = None
) -> dict[str, Any]:
    result = [x * multiplier for x in items]
    return {"items": result, "label": label, "total": sum(result)}

# ── 8. Recursive function ────────────────────────────────────
def factorial(n: int) -> int:
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def flatten(lst: list) -> list:
    """Flatten nested list"""
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result

print(factorial(10))
print(flatten([1, [2, [3, 4]], [5, 6]]))   # [1,2,3,4,5,6]
