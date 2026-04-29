class APIError(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code
        super().__init__(message)

class InsufficientBalance(APIError):
    def __init__(self, message="Insufficient available balance"):
        super().__init__(message, "insufficient_balance")

class InvalidStateTransition(Exception):
    pass
