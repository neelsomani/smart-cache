""" Example usage of the SmartCache """
import logging
import time

import module
from smart_cache import SmartCache


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    module = SmartCache(module)
    start_time = time.time()
    module.internally_cached_func()
    end_time = time.time()
    print(f'Time to complete first execution: {end_time - start_time} secs')
    module.internally_cached_func()  # Note the second execution is instant
    print(f'Time to complete second execution: {time.time() - end_time} secs')
