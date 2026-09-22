import pandas as pd

from qgis.core import (
    QgsCoordinateTransform,
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


def analyse_custom_estates(
    analysis_layer_path,
    estates_layer_path,
    csv_file,
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

    if site.crs().isGeographic():
        raise ValueError(
            "Custom-estate overlap calculations require "
            "a projected working CRS."
        )

    estates = QgsVectorLayer(
        estates_layer_path,
        "National estates",
        "ogr",
    )

    if not estates.isValid():
        raise ValueError(
            f"Failed to load estate layer: "
            f"{estates_layer_path}"
        )

    if not estates.crs().isValid():
        raise ValueError(
            "The national estate layer has no valid CRS."
        )

    site_geometry = get_combined_geometry(
        site
    )

    site_area_square_metres = (
        site_geometry.area()
    )

    if site_area_square_metres <= 0:
        raise ValueError(
            "The custom analysis area has no measurable area."
        )

    transform_context = (
        QgsProject.instance().transformContext()
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

    intersections_by_id = {}

    for feature in estates.getFeatures(request):
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
            or intersection.area() <= 0
        ):
            continue

        intersections_by_id[
            int(feature.id())
        ] = intersection

    estate_names = read_estate_names(
        csv_file=csv_file,
        feature_ids=intersections_by_id.keys(),
    )

    geometries_by_name = {}

    for feature_id, geometry in (
        intersections_by_id.items()
    ):
        estate_name = estate_names.get(
            feature_id
        )

        if estate_name is None:
            continue

        geometries_by_name.setdefault(
            estate_name,
            [],
        ).append(geometry)

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
            combined_intersection.area()
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
            matched_geometry.area(),
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