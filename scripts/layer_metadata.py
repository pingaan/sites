import json
import os
import time

from datetime import (
    datetime,
    timezone,
)

from pathlib import Path

import psycopg2


CACHE_MAX_AGE_SECONDS = 24 * 60 * 60


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


def load_database_environment():
    """
    Load the existing Sites database configuration.
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


def serialise_value(value):
    """
    Convert database values into JSON-safe values.
    """

    if isinstance(value, datetime):
        return value.isoformat()

    return value


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


def update_layer_metadata_cache():
    """
    Download the complete layer catalogue into a local JSON file.

    The existing cache is replaced only after a successful query
    and successful JSON write.
    """

    load_database_environment()

    password = os.environ.get(
        "SITES_DB_PASSWORD"
    )

    if not password:
        raise RuntimeError(
            "SITES_DB_PASSWORD is not configured."
        )

    connection = None

    try:
        connection = psycopg2.connect(
            host=os.environ.get(
                "SITES_DB_HOST",
                "127.0.0.1",
            ),
            port=int(
                os.environ.get(
                    "SITES_DB_PORT",
                    "5433",
                )
            ),
            dbname=os.environ.get(
                "SITES_DB_NAME",
                "sites",
            ),
            user=os.environ.get(
                "SITES_DB_USER",
                "sites_app",
            ),
            password=password,
            connect_timeout=10,
            application_name=(
                "Sovra metadata cache update"
            ),
        )

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    schema_name,
                    table_name,
                    country_code,
                    layer_type,
                    data_column,
                    translation_key,
                    dataset_name,
                    provider,
                    source_url,
                    source_updated_at,
                    migrated_at,
                    record_count,
                    srid,
                    geometry_type,
                    migration_status,
                    metadata_updated_at
                FROM metadata.layer_catalog
                ORDER BY
                    country_code,
                    layer_type,
                    table_name
                """
            )

            column_names = [
                description.name
                for description in cursor.description
            ]

            layers = []

            for database_row in cursor.fetchall():
                layer = {}

                for column_name, value in zip(
                    column_names,
                    database_row,
                ):
                    layer[column_name] = (
                        serialise_value(value)
                    )

                layers.append(
                    layer
                )

        payload = {
            "format_version": 1,
            "generated_at": (
                datetime.now(
                    timezone.utc
                ).isoformat()
            ),
            "layers": layers,
        }

        cache_path = metadata_cache_path()

        cache_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = cache_path.with_suffix(
            ".json.part"
        )

        temporary_path.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        os.replace(
            temporary_path,
            cache_path,
        )

        return cache_path

    finally:
        if connection is not None:
            connection.close()


def fetch_layer_metadata(
    country_code,
):
    """
    Read one country's metadata exclusively from the local cache.

    No database connection is attempted here.
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
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
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