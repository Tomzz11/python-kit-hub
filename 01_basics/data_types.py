# ============================================================
# DATA TYPES — Python Reference
# ============================================================

# ── 1. Numbers ───────────────────────────────────────────────
x_int   = 42
x_float = 3.14
x_complex = 2 + 3j

print(type(x_int))        # <class 'int'>
print(type(x_float))      # <class 'float'>
print(10 // 3)            # 3  (floor division)
print(10 % 3)             # 1  (modulo)
print(2 ** 8)             # 256 (power)

# ── 2. String ────────────────────────────────────────────────
name = "Python"
multi = """หลาย
บรรทัด"""

# f-string (แนะนำ)
greeting = f"Hello, {name}! version {3.12:.1f}"
print(greeting)

# string methods ที่ใช้บ่อย
s = "  hello world  "
print(s.strip())          # "hello world"
print(s.upper())          # "  HELLO WORLD  "
print(s.replace("world", "Python"))
print("hello".startswith("he"))  # True
print(",".join(["a", "b", "c"])) # "a,b,c"
print("a,b,c".split(","))        # ['a', 'b', 'c']

# ── 3. List ──────────────────────────────────────────────────
fruits = ["apple", "banana", "cherry"]
fruits.append("date")
fruits.insert(1, "avocado")
fruits.remove("banana")
print(fruits[0])          # apple
print(fruits[-1])         # date
print(fruits[1:3])        # slice

# List comprehension
squares = [x**2 for x in range(10)]
evens   = [x for x in range(20) if x % 2 == 0]

# ── 4. Tuple ─────────────────────────────────────────────────
point = (10, 20)          # immutable
x, y = point              # unpacking
rgb = (255, 128, 0)
r, g, b = rgb

# ── 5. Dictionary ────────────────────────────────────────────
person = {
    "name": "Alice",
    "age": 30,
    "skills": ["Python", "SQL"]
}
person["email"] = "alice@example.com"    # add key
age = person.get("age", 0)              # safe get
print(person.keys())
print(person.values())
print(person.items())

# Dict comprehension
squares_dict = {x: x**2 for x in range(5)}

# ── 6. Set ───────────────────────────────────────────────────
a = {1, 2, 3, 4}
b = {3, 4, 5, 6}
print(a | b)   # union       → {1,2,3,4,5,6}
print(a & b)   # intersection → {3,4}
print(a - b)   # difference   → {1,2}

# ── 7. Boolean & None ────────────────────────────────────────
flag = True
empty = None
print(bool([]))           # False (empty list)
print(bool([0]))          # True  (non-empty list)
print(flag is not None)   # True

# ── 8. Type conversion ───────────────────────────────────────
print(int("42"))          # 42
print(float("3.14"))      # 3.14
print(str(100))           # "100"
print(list("abc"))        # ['a','b','c']
print(tuple([1, 2, 3]))   # (1,2,3)
