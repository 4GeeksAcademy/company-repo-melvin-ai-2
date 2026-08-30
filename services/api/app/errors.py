"""Safe, user-facing error types. Messages must never include paths or secrets."""


class PersistenceError(Exception):
    """TinyDB or disk failure."""

    def __init__(self, message: str = "Could not save data. Try again later.") -> None:
        super().__init__(message)


class MailSendError(Exception):
    """Outbound email (Resend) failed."""

    def __init__(self, message: str = "Could not send email.") -> None:
        super().__init__(message)
