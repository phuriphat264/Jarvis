class BaseTokenCounter:
    def count_text(self, text: str) -> int:
        raise NotImplementedError

    def count_messages(self, messages: list[dict]) -> int:
        raise NotImplementedError

class SimpleTokenCounter(BaseTokenCounter):
    """
    A simple token counter approximation.
    In the future, this can be replaced with tiktoken.
    Assumption: ~4 characters per token for English/Code, slightly less for Thai.
    We'll use a conservative estimate of 3 chars per token.
    """
    def count_text(self, text: str) -> int:
        if not text:
            return 0
        return len(text) // 3

    def count_messages(self, messages: list[dict]) -> int:
        total = 0
        for msg in messages:
            # Each message has overhead (role, etc.)
            total += 4 
            total += self.count_text(msg.get("content", ""))
        # Add 3 for the assistant reply prime
        total += 3
        return total
