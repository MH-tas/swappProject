"""
Cisco Manager Decorators
========================
Decorator functions for performance monitoring, retry logic, and other utilities.
"""

import time
import logging
from functools import wraps
from typing import Callable

# Get loggers
logger = logging.getLogger('cisco_manager')
perf_logger = logging.getLogger('performance')

def performance_monitor(operation_name: str):
    """Decorator to monitor function performance"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                perf_logger.info(f"{operation_name} completed in {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                perf_logger.warning(f"{operation_name} failed in {execution_time:.3f}s: {e}")
                raise
        return wrapper
    return decorator

def retry_on_failure(max_attempts: int = 3, delay: float = 1.0, 
                    backoff_factor: float = 2.0):
    """Decorator to retry functions on failure"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        wait_time = delay * (backoff_factor ** attempt)
                        logger.debug(f"Attempt {attempt + 1} failed, retrying in {wait_time:.1f}s: {e}")
                        time.sleep(wait_time)
            
            logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            raise last_exception
        return wrapper
    return decorator

def cache_result(ttl: int = 60):
    """Decorator to cache function results"""
    def decorator(func: Callable) -> Callable:
        cache = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}_{str(args)}_{str(kwargs)}"
            current_time = time.time()
            
            # Check if cached result exists and is still valid
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if current_time - timestamp < ttl:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache[cache_key] = (result, current_time)
            logger.debug(f"Cached result for {func.__name__}")
            
            # Clean old cache entries
            expired_keys = [k for k, (_, ts) in cache.items() 
                          if current_time - ts > ttl]
            for key in expired_keys:
                del cache[key]
            
            return result
        return wrapper
    return decorator 