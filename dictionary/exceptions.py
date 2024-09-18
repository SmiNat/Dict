from fastapi import HTTPException, status


class DatabaseError(Exception):
    """Exception raised when there is an issue relevant to the database
    other than unique constraint or not null error."""


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
