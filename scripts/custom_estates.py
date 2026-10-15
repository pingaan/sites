import os

import pandas as pd

from qgis.core import (
    QgsCoordinateTransform,
    QgsDataSourceUri,
    QgsDistanceArea,
    QgsFeatureRequest,
    QgsGeometry,
    QgsProject,
    QgsVectorLayer,
)


def get_combined_geometry(layer):
    """
    Return one combined geometry containing every feature
    in a vector layer.
    """

    geometries = []

    for feature in layer.getFeatures():
        geometry = feature.geometry()

        if geometry is None or geometry.isEmpty():
            continue

        if not geometry.isGeosValid():
            geometry = geometry.makeValid()

        if not geometry.isEmpty():
            geometries.append(geometry)

    if not geometries:
        raise ValueError(
            "The analysis layer contains no usable geometry."
        )

    combined = QgsGeometry.unaryUnion(
        geometries
    )

    if not combined.isGeosValid():
        combined = combined.makeValid()

    return combined


def read_estate_names(
    csv_file,
    feature_ids,
):
    """
    Find estate names corresponding to estate feature IDs.

    The existing estate CSV and shapefile are expected to
    use the same row order, as in Anna's original logic.
    """

    wanted_ids = set(feature_ids)
    estate_names = {}

    columns = [
        "BOROUGH",
        "SECTOR",
        "SEGMENT",
    ]

    for chunk in pd.read_csv(
        csv_file,
        usecols=columns,
        dtype=str,
        keep_default_na=False,
        chunksize=10000,
    ):
        matching_indices = (
            chunk.index.intersection(
                wanted_ids
            )
        )

        for row_index in matching_indices:
            row = chunk.loc[row_index]

            name_parts = [
                row["BOROUGH"].strip(),
                row["SECTOR"].strip(),
                row["SEGMENT"].strip(),
            ]

            estate_name = " ".join(
                part
                for part in name_parts
                if part
            )

            if estate_name:
                estate_names[int(row_index)] = (
                    estate_name.upper()
                )

        if wanted_ids.issubset(
            estate_names.keys()
        ):
            break

    return estate_names

def create_postgis_estates_layer(
    estate_config,
):
    """
    Open the configured national estate table through the
    QGIS PostgreSQL provider.
    """

    password = os.environ.get(
        "SITES_DB_PASSWORD"
    )

    if not password:
        raise RuntimeError(
            "SITES_DB_PASSWORD has not been set."
        )

    required_settings = {
        "schema",
        "table",
        "geometry_column",
        "key_column",
        "group_fields",
    }

    missing_settings = (
        required_settings
        - set(estate_config)
    )

    if missing_settings:
        raise ValueError(
            "Estate configuration is missing: "
            + ", ".join(
                sorted(missing_settings)
            )
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
        estate_config["schema"],
        estate_config["table"],
        estate_config["geometry_column"],
        "",
        estate_config["key_column"],
    )

    estates = QgsVectorLayer(
        uri.uri(False),
        "National estates",
        "postgres",
    )

    if not estates.isValid():
        raise RuntimeError(
            "Failed to load the PostGIS estate table "
            f"{estate_config['schema']}."
            f"{estate_config['table']}."
        )

    return estates

def analyse_custom_estates(
    analysis_layer_path,
    estate_config,
):
    """
    Find named estates genuinely intersecting a custom
    analysis polygon.

    Boundary-only contact is excluded because the
    intersection must have a measurable polygon area.
    """

    site = QgsVectorLayer(
        analysis_layer_path,
        "Custom analysis area",
        "ogr",
    )

    if not site.isValid():
        raise ValueError(
            f"Failed to load analysis layer: "
            f"{analysis_layer_path}"
        )

    if not site.crs().isValid():
        raise ValueError(
            "The custom analysis layer has no valid CRS."
        )

    estates = create_postgis_estates_layer(
        estate_config
    )

    if not estates.crs().isValid():
        raise ValueError(
            "The PostGIS estate layer has no valid CRS."
        )

    display_fields = estate_config.get(
        "display_fields",
        estate_config["group_fields"],
    )

    estate_field_names = {
        field.name()
        for field in estates.fields()
    }

    missing_display_fields = (
        set(display_fields)
        - estate_field_names
    )

    if missing_display_fields:
        raise ValueError(
            "PostGIS estate table is missing display "
            "fields: "
            + ", ".join(
                sorted(missing_display_fields)
            )
        )

    site_geometry = get_combined_geometry(
        site
    )

    transform_context = (
        QgsProject.instance().transformContext()
    )

    area_calculator = QgsDistanceArea()

    area_calculator.setSourceCrs(
        site.crs(),
        transform_context,
    )

    area_calculator.setEllipsoid(
        "WGS84"
    )

    def measure_area(geometry):
        return area_calculator.measureArea(
            geometry
        )

    site_area_square_metres = (
        measure_area(site_geometry)
    )

    if site_area_square_metres <= 0:
        raise ValueError(
            "The custom analysis area has no measurable area."
        )

    site_to_estates = QgsCoordinateTransform(
        site.crs(),
        estates.crs(),
        transform_context,
    )

    estates_to_site = QgsCoordinateTransform(
        estates.crs(),
        site.crs(),
        transform_context,
    )

    estate_search_extent = (
        site_to_estates.transformBoundingBox(
            site_geometry.boundingBox()
        )
    )

    request = QgsFeatureRequest()
    request.setFilterRect(
        estate_search_extent
    )

    intersections_by_name = {}

    for feature in estates.getFeatures(request):
        name_parts = []

        for field_name in display_fields:
            value = feature[field_name]

            if value is None:
                continue

            value_text = str(value).strip()

            if value_text in {
                "",
                "NULL",
            }:
                continue

            name_parts.append(
                value_text
            )

        estate_name = " ".join(
            name_parts
        ).upper()

        if not estate_name:
            continue
        geometry = feature.geometry()

        if geometry is None or geometry.isEmpty():
            continue

        geometry.transform(
            estates_to_site
        )

        if not geometry.isGeosValid():
            geometry = geometry.makeValid()

        if (
            geometry.isEmpty()
            or not geometry.intersects(
                site_geometry
            )
        ):
            continue

        intersection = geometry.intersection(
            site_geometry
        )

        if not intersection.isGeosValid():
            intersection = intersection.makeValid()

        if (
            intersection.isEmpty()
            or measure_area(intersection) <= 0
        ):
            continue

        intersections_by_name.setdefault(
            estate_name,
            [],
        ).append(
            intersection
        )

    geometries_by_name = (
        intersections_by_name
    )

    estate_results = []
    matched_geometries = []

    for estate_name, geometries in sorted(
        geometries_by_name.items()
    ):
        combined_intersection = (
            QgsGeometry.unaryUnion(
                geometries
            )
        )

        if not combined_intersection.isGeosValid():
            combined_intersection = (
                combined_intersection.makeValid()
            )

        overlap_square_metres = (
            measure_area(
                combined_intersection
            )
        )

        if overlap_square_metres <= 0:
            continue

        matched_geometries.append(
            combined_intersection
        )

        estate_results.append(
            {
                "estate_name": estate_name,
                "overlap_area_ha": (
                    overlap_square_metres
                    / 10000.0
                ),
                "analysis_percentage": (
                    overlap_square_metres
                    / site_area_square_metres
                    * 100.0
                ),
            }
        )

    if matched_geometries:
        matched_geometry = (
            QgsGeometry.unaryUnion(
                matched_geometries
            )
        )

        matched_area_square_metres = min(
            measure_area(
                matched_geometry
            ),
            site_area_square_metres,
        )

    else:
        matched_area_square_metres = 0.0

    unmatched_square_metres = max(
        site_area_square_metres
        - matched_area_square_metres,
        0.0,
    )

    result = {
        "status": "available",
        "estates": estate_results,
        "analysis_area_ha": (
            site_area_square_metres
            / 10000.0
        ),
        "unmatched_area_ha": (
            unmatched_square_metres
            / 10000.0
        ),
        "unmatched_percentage": (
            unmatched_square_metres
            / site_area_square_metres
            * 100.0
        ),
    }

    print(
        f"Custom analysis area intersects "
        f"{len(estate_results)} named estates."
    )

    return result