class EmailAlreadyRegisteredError(Exception):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"Email already registered: {email}")


class InvalidCredentialsError(Exception):
    def __init__(self, reason: str = "Invalid email or password") -> None:
        self.reason = reason
        super().__init__(reason)


class InvalidTokenError(Exception):
    def __init__(self, reason: str = "Invalid or expired token") -> None:
        self.reason = reason
        super().__init__(reason)
