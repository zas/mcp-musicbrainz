from abc import ABC, abstractmethod

class RateLimiter(ABC):
    @abstractmethod
    async def acquire(self) -> bool:
        """Attempt to acquire a token. Returns True if successful."""
        ...

    @abstractmethod
    def get_retry_after(self) -> float:
        """Returns the number of seconds to wait."""
        ...