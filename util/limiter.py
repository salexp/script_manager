from math import floor

import time
import sys


def limiter(requests=1, time_period=1.0):
    frequency = abs(time_period) / float(clamp(requests))

    def decorator(func):
        last_called = [0.0]

        def wrapper(*args, **kargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = frequency - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kargs)
            last_called[0] = time.time()
            return ret

        return wrapper
    return decorator


def clamp(value):
    return max(1, min(sys.maxsize, floor(value)))
