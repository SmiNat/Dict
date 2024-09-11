import logging
from typing import NoReturn

from fastapi.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)


def integrity_error_handler(exc_info: IntegrityError) -> NoReturn:
    logger.debug(
        f"⚠️  Unique constraint violated. ERROR: {str(exc_info.orig).strip("\n").replace("\n", ". ")}"
    )
    message = str(exc_info.orig)[str(exc_info.orig).find("DETAIL:") + 8 :].strip()
    raise HTTPException(400, f"Unique constraint violated. {message}")
