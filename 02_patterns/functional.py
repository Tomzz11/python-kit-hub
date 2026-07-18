# ============================================================
# FUNCTIONAL PROGRAMMING — Python Reference
# ============================================================
from functools import reduce, partial, lru_cache, wraps
from itertools import chain, islice, groupby, product, combinations
from typing import TypeVar, Callable, Iterable, Any
import operator

T = TypeVar("T")
U = TypeVar("U")

# ── 1. Pure functions ────────────────────────────────────────
def add(a: int, b: int) -> int:   return a + b
def mul(a: int, b: int) -> int:   return a * b
def negate(x: int) -> int:        return -x

# ── 2. map / filter / reduce ─────────────────────────────────
nums = list(range(1, 11))

squares  = list(map(lambda x: x**2, nums))
evens    = list(filter(lambda x: x % 2 == 0, nums))
total    = reduce(operator.add, nums, 0)
product_ = reduce(operator.mul, nums[:5], 1)

print(squares)   # [1,4,9,...,100]
print(evens)     # [2,4,6,8,10]
print(total)     # 55

# ── 3. Function composition ──────────────────────────────────
def compose(*fns: Callable) -> Callable:
    """Right-to-left composition: compose(f,g,h)(x) = f(g(h(x)))"""
    def composed(x):
        for fn in reversed(fns):
            x = fn(x)
        return x
    return composed

def pipe(*fns: Callable) -> Callable:
    """Left-to-right (pipe): pipe(h,g,f)(x) = f(g(h(x)))"""
    def piped(x):
        for fn in fns:
            x = fn(x)
        return x
    return piped

double      = lambda x: x * 2
add_ten     = lambda x: x + 10
square      = lambda x: x ** 2

transform   = compose(square, add_ten, double)   # square(add_ten(double(x)))
print(transform(3))   # square(add_ten(6)) = square(16) = 256

pipeline    = pipe(double, add_ten, square)
print(pipeline(3))    # same result: 256

# ── 4. Partial application ───────────────────────────────────
def power(base: float, exp: float) -> float: return base ** exp

square_fn = partial(power, exp=2)
cube_fn   = partial(power, exp=3)
print(square_fn(4), cube_fn(3))   # 16.0  27.0

# Currying
def curry(fn: Callable) -> Callable:
    import inspect
    n_args = len(inspect.signature(fn).parameters)
    def curried(*args):
        if len(args) >= n_args:
            return fn(*args[:n_args])
        return lambda *more: curried(*(args + more))
    return curried

@curry
def add3(a: int, b: int, c: int) -> int: return a + b + c

add5 = add3(2)(3)   # partially applied
print(add5(10))     # 15

# ── 5. Memoization / caching ─────────────────────────────────
@lru_cache(maxsize=None)
def fib(n: int) -> int:
    if n < 2: return n
    return fib(n-1) + fib(n-2)

print(fib(50))

# Manual memoize
def memoize(fn: Callable) -> Callable:
    cache: dict = {}
    @wraps(fn)
    def wrapper(*args):
        if args not in cache:
            cache[args] = fn(*args)
        return cache[args]
    wrapper.cache = cache
    return wrapper

# ── 6. Itertools ─────────────────────────────────────────────
from itertools import (count, cycle, repeat,
                        chain, islice, groupby,
                        product, combinations, permutations,
                        accumulate, takewhile, dropwhile)

# Infinite → sliced
naturals = list(islice(count(1), 10))       # [1..10]
cycled   = list(islice(cycle("AB"), 6))     # ['A','B','A','B','A','B']

# Flatten nested
nested   = [[1,2], [3,4], [5,6]]
flat     = list(chain.from_iterable(nested))

# groupby (input must be sorted)
data = [("fruit","apple"), ("fruit","banana"), ("veggie","carrot")]
for key, group in groupby(data, key=lambda x: x[0]):
    items = [v for _, v in group]
    print(f"  {key}: {items}")

# combinations / product
pairs  = list(combinations("ABCD", 2))
matrix = list(product([1,2], [3,4]))

# accumulate (running total)
running = list(accumulate([1,2,3,4,5]))   # [1,3,6,10,15]

# takewhile / dropwhile
low = list(takewhile(lambda x: x < 5, [1,2,3,6,1]))  # [1,2,3]
hi  = list(dropwhile(lambda x: x < 5, [1,2,3,6,1]))  # [6,1]

# ── 7. Higher-order utilities ────────────────────────────────
def tap(fn: Callable[[T], Any]) -> Callable[[T], T]:
    """Side-effect without changing value (debug-friendly)"""
    def tapper(x: T) -> T:
        fn(x)
        return x
    return tapper

def maybe(fn: Callable[[T], U]) -> Callable[[T | None], U | None]:
    """Apply fn only if value is not None"""
    def safe(x: T | None) -> U | None:
        return fn(x) if x is not None else None
    return safe

log_value = tap(lambda x: print(f"  value: {x}"))
safe_int  = maybe(int)

result = log_value(42)           # side-effect only, returns 42
print(safe_int("10"))            # 10
print(safe_int(None))            # None

# ── 8. Immutable data transformations ────────────────────────
from copy import deepcopy

def update_nested(d: dict, keys: list, value: Any) -> dict:
    """Return new dict with nested key updated (immutable update)"""
    result = deepcopy(d)
    node = result
    for key in keys[:-1]:
        node = node[key]
    node[keys[-1]] = value
    return result

state = {"user": {"name": "Alice", "prefs": {"theme": "dark"}}}
new_state = update_nested(state, ["user", "prefs", "theme"], "light")
print(state["user"]["prefs"]["theme"])     # dark (unchanged)
print(new_state["user"]["prefs"]["theme"]) # light
