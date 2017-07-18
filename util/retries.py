import time
from util import logger


def retries(retries_count=0, wait_time=0.0):
    max_runs = retries_count + 1

    def decorator(func):
        def wrapper(*args, **kwargs):
            current_count = 0
            while current_count < max_runs:
                try:
                    current_count += 1
                    ret = func(*args, **kwargs)
                    return ret
                except Exception as e:
                    if current_count == max_runs:
                        raise e
                    else:
                        logger.warning("Function failed to run, retrying: %s" % func.__name__)
                        time.sleep(wait_time)

        return wrapper
    return decorator
