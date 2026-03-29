# DATA TYPES — Python Reference

x_int = 2
x_float = 3.14
x_complex = 2 + 3j

print(type(x_int))
print(type(x_float))
print(10 // 3)
print(10 % 3)
print(2 ** 8)


name = "Python"
multi = """หลาย
บรรทัด"""
 

greeting = f"Hello, {name}! version {3.12:.1f}"
print(greeting)
 

s = "  hello world  "
print(s.strip())          
print(s.upper())          
print(s.replace("world", "Python"))
print("hello".startswith("he"))  
print(",".join(["a", "b", "c"])) 
print("a,b,c".split(","))        
 

fruits = ["apple", "banana", "cherry"]
fruits.append("date")
fruits.insert(1, "avocado")
fruits.remove("banana")
print(fruits[0])          
print(fruits[-1])         
print(fruits[1:3])       


squares = [x**2 for x in range(10)]
evens   = [x for x in range(20) if x % 2 == 0]


point = (10, 20)          
x, y = point              
rgb = (255, 128, 0)
r, g, b = rgb
 

person = {
    "name": "Alice",
    "age": 30,
    "skills": ["Python", "SQL"]
}
person["email"] = "alice@example.com"    
age = person.get("age", 0)              
print(person.keys())
print(person.values())
print(person.items())
 

squares_dict = {x: x**2 for x in range(5)}
 

a = {1, 2, 3, 4}
b = {3, 4, 5, 6}
print(a | b)   
print(a & b)   
print(a - b)   
 

flag = True
empty = None
print(bool([]))           
print(bool([0]))          
print(flag is not None)   
 

print(int("42"))          
print(float("3.14"))      
print(str(100))           
print(list("abc"))        
print(tuple([1, 2, 3]))   
