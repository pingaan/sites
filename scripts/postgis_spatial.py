import os
import re

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsDataSourceUri,
    QgsGeometry,
    QgsProject,
    QgsVectorFileWriter,
    QgsVectorLayer,
)


_IDENTIFIER_PATTERN = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*$"
)


def _identifier(value):
    if not _IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(
            f"Invalid database identifier: {value!r}"
        )

    return value


def _sql_text(value):
    return (
        "'"
        + str(value).replace("'", "''")
        + "'"
    )


def extract_intersecting_features(
    dataset_config,
    intersection_layer_path,
    output_path,
    layer_name,
    allow_empty=False,
):
    """
    Download features intersecting a local polygon layer.

    The intersection geometry is transformed into the database
    layer's CRS before being sent to PostGIS.
    """

    password = os.environ.get(
        "SITES_DB_PASSWORD"
    )

    if not password:
        raise RuntimeError(
            "SITES_DB_PASSWORD has not been set."
        )

    intersection_layer = QgsVectorLayer(
        intersection_layer_path,
        "Spatial query boundary",
        "ogr",
    )

    if not intersection_layer.isValid():
        raise ValueError(
            "Failed to load the spatial query boundary: "
            f"{intersection_layer_path}"
        )

    if not intersection_layer.crs().isValid():
        raise ValueError(
            "The spatial query boundary has no valid CRS."
        )

    database_crs = QgsCoordinateReferenceSystem(
        f"EPSG:{dataset_config['srid']}"
    )

    if not database_crs.isValid():
        raise ValueError(
            "Invalid database CRS: "
            f"EPSG:{dataset_config['srid']}"
        )

    coordinate_transform = QgsCoordinateTransform(
        intersection_layer.crs(),
        database_crs,
        QgsProject.instance(),
    )

    geometries = []

    for feature in intersection_layer.getFeatures():
        if not feature.hasGeometry():
            continue

        geometry = QgsGeometry(
            feature.geometry()
        )

        if geometry.isEmpty():
            continue

        geometry.transform(
            coordinate_transform
        )

        geometries.append(geometry)

    if not geometries:
        raise ValueError(
            "The spatial query boundary contains "
            "no usable geometry."
        )

    query_geometry = QgsGeometry.unaryUnion(
        geometries
    )

    if (
        query_geometry.isNull()
        or query_geometry.isEmpty()
    ):
        raise ValueError(
            "Failed to combine the spatial query geometry."
        )

    schema = _identifier(
        dataset_config["schema"]
    )

    table = _identifier(
        dataset_config["table"]
    )

    geometry_column = _identifier(
        dataset_config["geometry_column"]
    )

    key_column = _identifier(
        dataset_config["key_column"]
    )

    srid = int(
        dataset_config["srid"]
    )

    geometry_wkt = query_geometry.asWkt(
        8
    )

    database_geometry = (
        "ST_GeomFromText("
        f"{_sql_text(geometry_wkt)}, "
        f"{srid}"
        ")"
    )

    subset = (
        f'"{geometry_column}" && '
        f"{database_geometry} "
        f'AND ST_Intersects('
        f'"{geometry_column}", '
        f"{database_geometry}"
        ")"
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

    result_layer = QgsVectorLayer(
        uri.uri(False),
        layer_name,
        "postgres",
    )

    if not result_layer.isValid():
        raise RuntimeError(
            "Failed to load the spatial PostGIS query "
            f"for {schema}.{table}."
        )

    feature_count = result_layer.featureCount()

    print(
        f"PostGIS spatial query returned "
        f"{feature_count} feature(s)."
    )

    if feature_count == 0 and not allow_empty:
        raise ValueError(
            "The PostGIS spatial query returned "
            "no features."
        )

    save_options = (
        QgsVectorFileWriter.SaveVectorOptions()
    )

    output_extension = os.path.splitext(
        output_path
    )[1].lower()

    if output_extension == ".gpkg":
        save_options.driverName = "GPKG"
        save_options.layerName = os.path.splitext(
            os.path.basename(output_path)
        )[0]

    else:
        save_options.driverName = "ESRI Shapefile"

    save_options.fileEncoding = "UTF-8"

    writer_result = (
        QgsVectorFileWriter.writeAsVectorFormatV3(
            result_layer,
            output_path,
            QgsProject.instance().transformContext(),
            save_options,
        )
    )

    if (
        writer_result[0]
        != QgsVectorFileWriter.NoError
    ):
        raise RuntimeError(
            "Failed to save the PostGIS spatial query. "
            f"Writer error: {writer_result[0]}"
        )

    return output_path

def download_country_layers_from_postgis(
    layer_definitions,
    intersection_layer_path,
    temp_path,
):
    """
    Download the spatial subset of every configured country
    layer into the local analysis workspace.

    Return the directory containing the downloaded datasets.
    """

    output_directory = os.path.join(
        temp_path,
        "postgis_country_sources",
    )

    os.makedirs(
        output_directory,
        exist_ok=True,
    )

    total = len(layer_definitions)

    for number, definition in enumerate(
        layer_definitions,
        start=1,
    ):
        if "database" not in definition:
            raise ValueError(
                "Country-layer definition has no "
                "database configuration: "
                f"{definition['name']}"
            )

        output_path = os.path.join(
            output_directory,
            definition["source"],
        )

        print(
            f"Downloading country layer "
            f"{number}/{total}: "
            f"{definition['name']}"
        )

        extract_intersecting_features(
            dataset_config=definition["database"],
            intersection_layer_path=(
                intersection_layer_path
            ),
            output_path=output_path,
            layer_name=definition["name"],
            allow_empty=True,
        )

    print(
        f"PostGIS country-layer subsets downloaded: "
        f"{total}"
    )

    return output_directory