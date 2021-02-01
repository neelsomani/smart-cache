def non_functional():
    print('hello')


def functional():
    elements = []
    for i in range(10**8):
        elements.append(1)
    return sum(elements)


def internally_cached_func():
    a = functional()
    non_functional()
    a += 10
    return a
