# ============================================================
# CONTROL FLOW — Python Reference
# ============================================================

# ── 1. if / elif / else ──────────────────────────────────────
score = 85

if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 70:
    grade = "C"
else:
    grade = "F"

# Ternary (one-liner)
result = "pass" if score >= 60 else "fail"

# match-case (Python 3.10+)
command = "quit"
match command:
    case "quit" | "exit":
        print("Goodbye!")
    case "hello":
        print("Hello!")
    case _:
        print(f"Unknown: {command}")

# ── 2. for loop ──────────────────────────────────────────────
# range
for i in range(5):         # 0,1,2,3,4
    print(i)

for i in range(2, 10, 2):  # 2,4,6,8
    print(i)

# iterate list
fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    print(fruit)

# enumerate (index + value)
for idx, fruit in enumerate(fruits, start=1):
    print(f"{idx}. {fruit}")

# zip (iterate multiple)
names = ["Alice", "Bob", "Charlie"]
scores = [90, 85, 78]
for name, score in zip(names, scores):
    print(f"{name}: {score}")

# dict iteration
person = {"name": "Alice", "age": 30}
for key, value in person.items():
    print(f"{key} = {value}")

# ── 3. while loop ────────────────────────────────────────────
count = 0
while count < 5:
    print(count)
    count += 1

# while with break/continue
i = 0
while True:
    if i == 3:
        i += 1
        continue     # ข้ามรอบนี้
    if i == 6:
        break        # ออกจากลูป
    print(i)
    i += 1

# ── 4. break / continue / else ───────────────────────────────
# else ของ loop จะทำงานเมื่อ loop จบตามปกติ (ไม่มี break)
for n in range(2, 10):
    for x in range(2, n):
        if n % x == 0:
            break
    else:
        print(f"{n} is prime")

# ── 5. List / Dict / Set comprehension ───────────────────────
# List comprehension
squares  = [x**2 for x in range(10)]
filtered = [x for x in range(20) if x % 2 == 0]
nested   = [x*y for x in range(3) for y in range(3)]

# Dict comprehension
word_len = {word: len(word) for word in ["python", "java", "go"]}

# Set comprehension
unique_lens = {len(word) for word in ["hi", "hello", "hey"]}

# Generator expression (ประหยัด memory)
total = sum(x**2 for x in range(1000))

# ── 6. Walrus operator := (Python 3.8+) ──────────────────────
import re
data = "Phone: 081-234-5678"
if m := re.search(r"\d{3}-\d{3}-\d{4}", data):
    print(f"Found: {m.group()}")

# ── 7. pass / continue / break / return ──────────────────────
def placeholder():
    pass   # ฟังก์ชันเปล่า ยังไม่ implement

# ── 8. Exception handling ────────────────────────────────────
try:
    result = 10 / 0
except ZeroDivisionError as e:
    print(f"Error: {e}")
except (TypeError, ValueError) as e:
    print(f"Type/Value error: {e}")
else:
    print("No error!")     # ทำงานเมื่อไม่มี exception
finally:
    print("Always runs")   # ทำงานเสมอ
