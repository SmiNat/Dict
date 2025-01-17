import logging
from typing import NoReturn

from sqlalchemy.exc import IntegrityError

from dictionary.exceptions import DatabaseConstraintError

logger = logging.getLogger(__name__)


def integrity_error_handler(exc_info: IntegrityError) -> NoReturn:
    logger.debug(
        f"⚠️  Database constraint violated. ERROR: {str(exc_info.orig).strip("\n").replace("\n", ". ")}"
    )
    message = str(exc_info.orig)[str(exc_info.orig).find("DETAIL:") + 8 :].strip()
    raise DatabaseConstraintError(extra_data=message)
