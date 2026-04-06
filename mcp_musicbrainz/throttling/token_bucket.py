import time
import threading
from functools import wraps
from typing import Callable, Any

class LocalTokenBucket:
    """
    Thread-safe Token Bucket for API rate limiting compliance.
    Allows for small bursts but maintains a strict average requests-per-second limit.
    """
    def __init__(self, rate: float = 1.0, capacity: float = 3.0):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_check = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self) -> bool:
        """
        Non-blocking check for a token. 
        Returns True if request can proceed, False if throttled.
        """
        with self._lock:
            now = time.monotonic()
            passed = now - self.last_check
            self.last_check = now
            
            # Refill tokens based on time elapsed
            self.tokens = min(self.capacity, self.tokens + (passed * self.rate))
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

    def get_retry_after(self) -> float:
        """Calculates seconds until the next token is likely available."""
        return 1.0 / self.rate

global_limiter = LocalTokenBucket(rate=1.0, capacity=3.0)

def rate_limited(func: Callable) -> Callable:
    """
    A decorator that protects MusicBrainz API calls from rate-limit bans.
    Returns a semantic error string if throttled, allowing LLM agents to gracefully pause.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not global_limiter.acquire():
            retry = global_limiter.get_retry_after()
            return f"Error: MusicBrainz Rate Limit reached. Please retry in {retry:.1f}s."
        
        return func(*args, **kwargs)
    
    return wrapper