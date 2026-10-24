import json
import os
import tempfile
import time

from pathlib import Path
from urllib.request import (
    Request,
    urlopen,
)


CACHE_MAX_AGE_SECONDS = 24 * 60 * 60

DEFAULT_METADATA_URL = (
    "http://192.168.1.111:8080/"
    "layer_metadata.json"
)

MAX_DOWNLOAD_BYTES = 10 * 1024 * 1024


def metadata_cache_path():
    """
    Return the local metadata-cache location.
    """

    local_app_data = os.environ.get(
        "LOCALAPPDATA"
    )

    if not local_app_data:
        local_app_data = str(
            Path.home()
        )

    return (
        Path(local_app_data)
        / "Sovra"
        / "Cache"
        / "layer_metadata.json"
    )


def load_application_environment():
    """
    Load optional Sovra environment settings.

    SITES_LAYER_METADATA_URL may be placed in the existing
    database.env file to override the default metadata URL.
    """

    local_app_data = os.environ.get(
        "LOCALAPPDATA"
    )

    if not local_app_data:
        return

    environment_path = (
        Path(local_app_data)
        / "Sites"
        / "database.env"
    )

    if not environment_path.is_file():
        return

    for raw_line in environment_path.read_text(
        encoding="utf-8"
    ).splitlines():
        line = raw_line.strip()

        if (
            not line
            or line.startswith("#")
            or "=" not in line
        ):
            continue

        key, value = line.split(
            "=",
            1,
        )

        key = key.strip()
        value = value.strip()

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {'"', "'"}
        ):
            value = value[1:-1]

        if key:
            os.environ.setdefault(
                key,
                value,
            )


def cache_needs_refresh():
    """
    Return True when the cache is absent or over 24 hours old.
    """

    cache_path = metadata_cache_path()

    if not cache_path.is_file():
        return True

    cache_age_seconds = (
        time.time()
        - cache_path.stat().st_mtime
    )

    return (
        cache_age_seconds
        >= CACHE_MAX_AGE_SECONDS
    )


def validate_metadata_payload(
    payload,
):
    """
    Validate downloaded metadata before replacing the cache.
    """

    if not isinstance(payload, dict):
        raise ValueError(
            "The layer metadata response is not a JSON object."
        )

    if payload.get("format_version") != 1:
        raise ValueError(
            "The layer metadata format version is unsupported."
        )

    generated_at = payload.get(
        "generated_at"
    )

    if not generated_at:
        raise ValueError(
            "The layer metadata has no generation timestamp."
        )

    layers = payload.get(
        "layers"
    )

    if not isinstance(layers, list):
        raise ValueError(
            "The layer metadata has no valid layer list."
        )

    for number, layer in enumerate(
        layers,
        start=1,
    ):
        if not isinstance(layer, dict):
            raise ValueError(
                "Layer metadata entry "
                f"{number} is not a JSON object."
            )

        for required_key in (
            "schema_name",
            "table_name",
            "country_code",
            "layer_type",
        ):
            if not layer.get(
                required_key
            ):
                raise ValueError(
                    "Layer metadata entry "
                    f"{number} has no "
                    f"{required_key}."
                )

    return payload


def download_metadata_payload():
    """
    Download and validate the published metadata catalogue.
    """

    load_application_environment()

    metadata_url = os.environ.get(
        "SITES_LAYER_METADATA_URL",
        DEFAULT_METADATA_URL,
    ).strip()

    if not metadata_url:
        raise RuntimeError(
            "SITES_LAYER_METADATA_URL is empty."
        )

    request = Request(
        metadata_url,
        headers={
            "Accept": "application/json",
            "User-Agent": (
                "Sovra layer-metadata client"
            ),
        },
    )

    with urlopen(
        request,
        timeout=10,
    ) as response:
        response_data = response.read(
            MAX_DOWNLOAD_BYTES + 1
        )

    if len(response_data) > MAX_DOWNLOAD_BYTES:
        raise RuntimeError(
            "The layer metadata download is unexpectedly large."
        )

    try:
        payload = json.loads(
            response_data.decode(
                "utf-8-sig"
            )
        )

    except (
        UnicodeError,
        json.JSONDecodeError,
    ) as error:
        raise ValueError(
            "The downloaded layer metadata is not valid JSON."
        ) from error

    return validate_metadata_payload(
        payload
    )


def write_metadata_cache(
    payload,
):
    """
    Atomically replace the local metadata cache.
    """

    cache_path = metadata_cache_path()

    cache_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=cache_path.parent,
        prefix="layer_metadata.",
        suffix=".json.part",
        delete=False,
    )

    temporary_path = Path(
        temporary_handle.name
    )

    try:
        with temporary_handle:
            json.dump(
                payload,
                temporary_handle,
                ensure_ascii=False,
                indent=2,
            )

            temporary_handle.write(
                "\n"
            )

            temporary_handle.flush()

            os.fsync(
                temporary_handle.fileno()
            )

        os.replace(
            temporary_path,
            cache_path,
        )

    except Exception:
        temporary_path.unlink(
            missing_ok=True
        )

        raise

    return cache_path


def update_layer_metadata_cache():
    """
    Download the published catalogue into the local cache.

    The existing cache is replaced only after a successful
    download, validation and JSON write.
    """

    payload = download_metadata_payload()

    return write_metadata_cache(
        payload
    )


def fetch_layer_metadata(
    country_code,
):
    """
    Read one country's metadata exclusively from the local cache.

    No network or database connection is attempted here.
    """

    cache_path = metadata_cache_path()

    if not cache_path.is_file():
        return (
            {},
            (
                "The local metadata cache has not yet "
                "been downloaded."
            ),
        )

    try:
        payload = json.loads(
            cache_path.read_text(
                encoding="utf-8"
            )
        )

        validate_metadata_payload(
            payload
        )

    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        ValueError,
    ) as error:
        return (
            {},
            (
                "The local metadata cache could not "
                f"be read: {error}"
            ),
        )

    selected_country = str(
        country_code
    ).strip().upper()

    generated_at = payload.get(
        "generated_at"
    )

    metadata_by_layer = {}

    for layer in payload.get(
        "layers",
        [],
    ):
        if (
            str(
                layer.get(
                    "country_code",
                    "",
                )
            ).upper()
            != selected_country
        ):
            continue

        layer = dict(
            layer
        )

        layer["cache_generated_at"] = (
            generated_at
        )

        metadata_by_layer[
            (
                layer.get("schema_name"),
                layer.get("table_name"),
            )
        ] = layer

    return (
        metadata_by_layer,
        None,
    )