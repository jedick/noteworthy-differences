import time
import functools
import random


def retry_with_backoff(
    max_retries=5, base_delay=2, backoff_factor=2, exceptions=(Exception,)
):
    """
    Decorator to retry a function with exponential backoff.

    Args:
        max_retries (int): Maximum number of retries before giving up.
        base_delay (float): Initial delay in seconds before retrying.
        backoff_factor (float): Multiplier for delay after each failure.
        exceptions (tuple): Exception types to catch and retry on.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            attempt = 0
            while attempt < max_retries:
                try:
                    # Pass args and kwargs
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt >= max_retries:
                        # Raise the last exception if max retries reached
                        raise
                    print(
                        f"[Retry {attempt}/{max_retries}] Error: {e}. Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                    # Exponential backoff with jitter
                    delay *= backoff_factor + random.uniform(0, 1)

        return wrapper

    return decorator
