import os

from qgis.core import (
    QgsDataSourceUri,
    QgsVectorFileWriter,
    QgsVectorLayer,
)


def _sql_text(value):
    """
    Safely quote a text value for a PostgreSQL subset expression.
    """

    return "'" + str(value).replace("'", "''") + "'"


def extract_estate_from_postgis(
    match,
    output_root,
    run_id,
    schema="se",
):
    """
    Find an estate through PostGIS and download its matching
    feature parts to the local analysis workspace.
    """

    password = os.environ.get(
        "SITES_DB_PASSWORD"
    )

    if not password:
        raise RuntimeError(
            "SITES_DB_PASSWORD has not been set."
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

    borough, sector, segment = match

    subset = (
        f'"borough" = {_sql_text(borough)} '
        f'AND "sector" = {_sql_text(sector)} '
        f'AND "segment" = {_sql_text(segment)}'
    )

    uri.setDataSource(
        schema,
        "estates",
        "geom",
        subset,
        "id",
    )

    estate_layer = QgsVectorLayer(
        uri.uri(False),
        "Selected estate",
        "postgres",
    )

    if not estate_layer.isValid():
        raise RuntimeError(
            "Failed to connect to the PostGIS "
            "estate table."
        )

    feature_count = estate_layer.featureCount()

    if feature_count == 0:
        raise ValueError(
            "No estate was found for "
            f"{' '.join(match)}."
        )

    print(
        f"PostGIS returned {feature_count} "
        "estate feature part(s)."
    )

    folder_name = (
        " ".join(match)
        .replace(":", "-")
    )

    folder_path = os.path.join(
        output_root,
        folder_name,
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
            "Failed to save the selected estate "
            f"locally. Writer error: "
            f"{writer_result[0]}"
        )

    print(
        "Estate downloaded from PostGIS: "
        f"{extracted_path}"
    )

    return {
        "folder_name": folder_name,
        "folder_path": folder_path,
        "temp_path": temp_path,
        "extracted_layers": [
            extracted_path
        ],
    }