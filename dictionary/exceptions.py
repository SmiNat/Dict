from fastapi import HTTPException, status


class DatabaseError(Exception):
    """Exception raised when there is an issue relevant to the database
    other than unique constraint or not null error."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.headers = headers

    def __str__(self) -> str:
        if self.status_code:
            return f"{self.message}"
        return f"{self.message}"

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return (
            f"{class_name}(message={self.message!r}, status_code={self.status_code!r})"
        )


class DatabaseConstraintError(HTTPException):
    """Exception raised when database unique constraint or not null error."""

    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: str = "Database constraint violated.",
        extra_data: str | None = None,
        headers: dict[str, str] | None = None,  # {"WWW-Authenticate": "Bearer"}
    ) -> None:
        self.status_code = status_code
        self.detail = detail if not extra_data else detail + " " + extra_data
        self.headers = headers
