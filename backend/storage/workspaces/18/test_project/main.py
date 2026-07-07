def greet(name):
    print(f"Hello, {name}")

def main():
    greet("World")
    calc = Calculator()
    result = calc.add(1, 2)
    print(result)

class Calculator:
    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b

if __name__ == "__main__":
    main()
