import secrets
import string

from datetime import datetime


RUN_ID_CHARACTERS = (
    string.ascii_letters
    + string.digits
    + "_"
)


def create_run_id(
    random_length=8,
):
    """
    Create a sortable, filesystem-safe analysis run ID.

    Example:
        260923-221530-as85DF_y
    """

    timestamp = datetime.now().strftime(
        "%y%m%d-%H%M%S"
    )

    random_part = "".join(
        secrets.choice(
            RUN_ID_CHARACTERS
        )
        for _ in range(random_length)
    )

    return (
        f"{timestamp}-{random_part}"
    )