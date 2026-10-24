import os
import re

from qgis.core import (
    QgsDataSourceUri,
    QgsVectorFileWriter,
    QgsVectorLayer,
)


_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*$"
)


def _validate_identifier(value):
    if not _IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(
            f"Invalid database identifier: {value!r}"
        )

    return value


def _quote_text(value):
    return (
        "'"
        + str(value).replace("'", "''")
        + "'"
    )


def _build_subset(filter_groups):
    """
    Construct alternatives joined with OR, where the fields
    within each alternative are joined with AND.
    """

    alternatives = []

    for filter_group in filter_groups:
        conditions = []

        for field_name, field_value in (
            filter_group.items()
        ):
            field_name = _validate_identifier(
                field_name
            )

            conditions.append(
                f'"{field_name}" = '
                f"{_quote_text(field_value)}"
            )

        if conditions:
            alternatives.append(
                "("
                + " AND ".join(conditions)
                + ")"
            )

    if not alternatives:
        raise ValueError(
            "No estate lookup filters were supplied."
        )

    return " OR ".join(alternatives)


def extract_estate_from_postgis(
    estate_config,
    estate_reference,
    output_root,
    run_id,
):
    """
    Download one estate from the country-specific PostGIS
    estate table into the local analysis workspace.
    """

    password = os.environ.get(
        "SITES_DB_PASSWORD"
    )

    if not password:
        raise RuntimeError(
            "SITES_DB_PASSWORD has not been set."
        )

    schema = _validate_identifier(
        estate_config["schema"]
    )

    table = _validate_identifier(
        estate_config["table"]
    )

    geometry_column = _validate_identifier(
        estate_config["geometry_column"]
    )

    key_column = _validate_identifier(
        estate_config["key_column"]
    )

    subset = _build_subset(
        estate_reference["filter_groups"]
    )

    uri = QgsDataSourceUri()

    uri.setConnection(
        os.environ.get(
            "SITES_DB_HOST",
            "127.0.0.1",
        ),
        os.environ.get(
            "SITES_DB_PORT",
            "5433",
        ),
        os.environ.get(
            "SITES_DB_NAME",
            "sites",
        ),
        os.environ.get(
            "SITES_DB_USER",
            "sites_app",
        ),
        password,
    )

    uri.setDataSource(
        schema,
        table,
        geometry_column,
        subset,
        key_column,
    )

    estate_layer = QgsVectorLayer(
        uri.uri(False),
        "Selected estate",
        "postgres",
    )

    if not estate_layer.isValid():
        provider_error = (
            estate_layer.error().summary()
        )

        raise RuntimeError(
            "Failed to load the PostGIS table "
            f"{schema}.{table}.\n"
            f"PostGIS provider error: "
            f"{provider_error}"
        )

    feature_count = estate_layer.featureCount()

    if feature_count == 0:
        raise ValueError(
            "No estate was found for "
            f"{estate_reference['display_name']}."
        )

    print(
        f"PostGIS returned {feature_count} "
        "estate feature part(s)."
    )

    folder_path = os.path.join(
        output_root,
        estate_reference["folder_name"],
        run_id,
    )

    temp_path = os.path.join(
        folder_path,
        "temp",
    )

    os.makedirs(
        temp_path,
        exist_ok=True,
    )

    extracted_path = os.path.join(
        temp_path,
        "fastigheten_postgis.shp",
    )

    writer_result = (
        QgsVectorFileWriter.writeAsVectorFormat(
            estate_layer,
            extracted_path,
            "UTF-8",
            estate_layer.crs(),
            "ESRI Shapefile",
        )
    )

    if (
        writer_result[0]
        != QgsVectorFileWriter.NoError
    ):
        raise RuntimeError(
            "Failed to save the estate locally. "
            f"Writer error: {writer_result[0]}"
        )

    print(
        "Estate downloaded from PostGIS: "
        f"{extracted_path}"
    )

    return {
        "folder_name": estate_reference[
            "folder_name"
        ],
        "folder_path": folder_path,
        "temp_path": temp_path,
        "extracted_layers": [
            extracted_path
        ],
        "estate_reference": estate_reference[
            "display_name"
        ],
    }