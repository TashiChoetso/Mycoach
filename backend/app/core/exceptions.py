from fastapi import HTTPException, status


class AppError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(status_code=status_code, detail={"code": code, "message": message})
        self.code = code


class Unauthorized(AppError):
    def __init__(self, message: str = "Could not authenticate") -> None:
        super().__init__(status.HTTP_401_UNAUTHORIZED, "UNAUTHORIZED", message)


class Forbidden(AppError):
    def __init__(self, message: str = "Not allowed") -> None:
        super().__init__(status.HTTP_403_FORBIDDEN, "FORBIDDEN", message)


class NotFound(AppError):
    def __init__(self, message: str = "Not found") -> None:
        super().__init__(status.HTTP_404_NOT_FOUND, "NOT_FOUND", message)


class Conflict(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(status.HTTP_409_CONFLICT, "CONFLICT", message)


class RateLimited(AppError):
    def __init__(self, message: str = "Too many requests") -> None:
        super().__init__(status.HTTP_429_TOO_MANY_REQUESTS, "RATE_LIMITED", message)


class InvalidInput(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(status.HTTP_422_UNPROCESSABLE_CONTENT, "INVALID_INPUT", message)
