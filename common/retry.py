import logging
import time
import functools

logger = logging.getLogger(__name__)

def retry_on_network_error(max_attempts=3, delay_seconds=1,
                            retry_multiplier=2, exceptions=(ConnectionError, TimeoutError)):
    """
    Декоратор для повторных попыток вызова функции при сетевых ошибках.
    Полезен для любых внешних API-вызовов (Gemini, будущие интеграции и т.д.),
    не зависит от конкретного формата ответа - только от факта сетевого сбоя.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            delay = delay_seconds
            last_exception = None

            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    attempt += 1
                    logger.warning(
                        f"Попытка {attempt}/{max_attempts} вызова {func.__name__} провалилась: {e}"
                    )
                    if attempt < max_attempts:
                        time.sleep(delay)
                        delay *= retry_multiplier

            raise last_exception

        return wrapper
    return decorator