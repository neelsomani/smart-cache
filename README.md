# smart-cache
A Python library that analyzes your module and automatically caches purely functional sections using [side effect](https://en.wikipedia.org/wiki/Side_effect_(computer_science)) analysis. Previous work: https://dl.acm.org/doi/10.1145/960116.53996

See this code in action by looking at `module.py`, then running `example.py`.

Here is an example of the kinds of optimizations that are within scope of this project:

```
def example_1():
    lst = []
    for i in range(10**7):
        lst.append(i)
    return lst

def example_2():
    print('Hello world!')

def main_function():
    a = 0  # The first three lines are a purely functional section
    for i in range(10**7):
        a += 1
    print(a)  # Non-pure function call
    print(i)  # Non-pure function call
    lst = example_1()  # Pure function call
    example_2()  # Non-pure function call
    return lst
```

would become something like:

```
from functools import lru_cache

@lru_cache(maxsize=None)
def example_1():
    lst = []
    for i in range(10**7):
        lst.append(i)
    return lst

def example_2():
    print('Hello world!')

@lru_cache(maxsize=None)
def _generated_pure_function():
    a = 0
    for i in range(10**7):
        a += 1
    return a, i

def main_function():
    a, i = _generated_pure_function()
    print(a)
    print(i)
    lst = example_1()
    example_2()
    return lst
```

where running `main_function` in this modified AST will cache the function outputs after the first call, so subsequent calls are faster. A more sophisticated version might fully substitute the variables `lst`, `a`, and `i` with their literal values if the results are referentially transparent.

To check functions with parameters, you would need to have type hints. Under the hood for my proof of concept, I don't actually use `lru_cache` and instead implement a simple memo myself.
