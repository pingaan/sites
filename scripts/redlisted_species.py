import json
import os

import processing
import requests

from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsField,
    QgsProject,
    QgsVectorLayer,
    QgsWkbTypes,
)


def get_attribute(
    feature,
    field_name,
):
    """
    Safely read an attribute from a WFS feature.
    """

    if field_name not in feature.fields().names():
        return None

    value = feature[field_name]

    if value is None:
        return None

    if hasattr(value, "isNull") and value.isNull():
        return None

    return value


def as_text(value):
    """
    Convert values, including QDateTime values, into text
    suitable for a Shapefile.
    """

    if value is None:
        return None

    if hasattr(value, "toString"):
        try:
            return value.toString(
                "yyyy-MM-ddTHH:mm:ss"
            )
        except TypeError:
            pass

    return str(value)


def as_integer(value):
    if value is None:
        return None

    try:
        return int(value)

    except (TypeError, ValueError):
        return None


def as_float(value):
    if value is None:
        return None

    try:
        return float(value)

    except (TypeError, ValueError):
        return None


def as_boolean_integer(value):
    """
    Store boolean values as 1, 0 or NULL because Shapefile
    boolean support is inconsistent.
    """

    if value is None:
        return None

    if isinstance(value, str):
        cleaned = value.strip().lower()

        if cleaned in {
            "true",
            "1",
            "yes",
        }:
            return 1

        if cleaned in {
            "false",
            "0",
            "no",
        }:
            return 0

        return None

    return 1 if bool(value) else 0


def download_wfs_pages(
    service_url,
    wfs_version,
    type_name,
    bbox,
    source_crs,
    output_path,
    page_size=10000,
):
    """
    Download WFS features in pages and save the combined
    response as temporary GeoJSON.
    """

    all_features = []
    seen_features = set()

    start_index = 0
    page_number = 1

    while True:

        bbox_text = (
            f"{bbox.xMinimum()},"
            f"{bbox.yMinimum()},"
            f"{bbox.xMaximum()},"
            f"{bbox.yMaximum()},"
            f"{source_crs}"
        )

        parameters = {
            "service": "WFS",
            "version": wfs_version,
            "request": "GetFeature",
            "typeNames": type_name,
            "outputFormat": "application/json",
            "srsName": source_crs,
            "bbox": bbox_text,
            "count": page_size,
            "startIndex": start_index,
        }

        print(
            f"Downloading red-listed observations, "
            f"page {page_number}..."
        )

        try:
            response = requests.get(
                service_url,
                params=parameters,
                timeout=180,
                headers={
                    "User-Agent": (
                        "SolarSiteAnalysis/1.0"
                    ),
                },
            )

            response.raise_for_status()

        except requests.RequestException as error:
            raise RuntimeError(
                "Failed to download red-listed species "
                f"observations: {error}"
            ) from error

        try:
            payload = response.json()

        except requests.JSONDecodeError as error:
            raise RuntimeError(
                "The red-listed species WFS did not return "
                "valid GeoJSON."
            ) from error

        page_features = payload.get(
            "features",
            [],
        )

        new_feature_count = 0

        for feature in page_features:

            properties = feature.get(
                "properties",
                {},
            )

            feature_key = (
                feature.get("id")
                or properties.get("occurrenceId")
            )

            if feature_key is None:
                feature_key = json.dumps(
                    feature,
                    sort_keys=True,
                    ensure_ascii=False,
                )

            if feature_key in seen_features:
                continue

            seen_features.add(feature_key)
            all_features.append(feature)
            new_feature_count += 1

        print(
            f"Red-listed observations received: "
            f"{len(page_features)} "
            f"({new_feature_count} new)."
        )

        if len(page_features) < page_size:
            break

        if new_feature_count == 0:
            print(
                "WFS paging stopped because the service "
                "returned no new observations."
            )
            break

        start_index += len(page_features)
        page_number += 1

        if page_number > 100:
            raise RuntimeError(
                "Red-listed species download exceeded "
                "100 WFS pages."
            )

    geojson = {
        "type": "FeatureCollection",
        "features": all_features,
    }

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as output_file:
        json.dump(
            geojson,
            output_file,
            ensure_ascii=False,
        )

    return len(all_features)


def create_clean_species_layer(
    source_layer,
):
    """
    Create an in-memory point layer with predictable,
    Shapefile-safe fields.

    Full common and scientific species names are preserved.
    """

    geometry_name = QgsWkbTypes.displayString(
        source_layer.wkbType()
    )

    memory_layer = QgsVectorLayer(
        (
            f"{geometry_name}?"
            f"crs={source_layer.crs().authid()}"
        ),
        "Red-listed species observations",
        "memory",
    )

    if not memory_layer.isValid():
        raise RuntimeError(
            "Failed to create the red-listed species "
            "output layer."
        )

    fields = [
        QgsField(
            "OBS_ID",
            QVariant.String,
            len=254,
        ),
        QgsField(
            "SOURCE_URL",
            QVariant.String,
            len=254,
        ),
        QgsField(
            "PRESENT",
            QVariant.Int,
        ),
        QgsField(
            "DATASET",
            QVariant.String,
            len=254,
        ),
        QgsField(
            "START_DATE",
            QVariant.String,
            len=32,
        ),
        QgsField(
            "END_DATE",
            QVariant.String,
            len=32,
        ),
        QgsField(
            "MODIFIED",
            QVariant.String,
            len=32,
        ),
        QgsField(
            "LATITUDE",
            QVariant.Double,
            len=20,
            prec=10,
        ),
        QgsField(
            "LONGITUDE",
            QVariant.Double,
            len=20,
            prec=10,
        ),
        QgsField(
            "UNCERT_M",
            QVariant.Int,
        ),
        QgsField(
            "LOCALITY",
            QVariant.String,
            len=254,
        ),
        QgsField(
            "MUNICIP",
            QVariant.String,
            len=100,
        ),
        QgsField(
            "COUNTY",
            QVariant.String,
            len=100,
        ),
        QgsField(
            "PROVINCE",
            QVariant.String,
            len=100,
        ),
        QgsField(
            "RECORDED",
            QVariant.String,
            len=254,
        ),
        QgsField(
            "REPORTED",
            QVariant.String,
            len=254,
        ),
        QgsField(
            "HABITAT",
            QVariant.String,
            len=254,
        ),
        QgsField(
            "OCC_REMARK",
            QVariant.String,
            len=254,
        ),
        QgsField(
            "TAXON_ID",
            QVariant.Int,
        ),
        QgsField(
            "TAXON_CAT",
            QVariant.String,
            len=100,
        ),
        QgsField(
            "ORG_GROUP",
            QVariant.String,
            len=100,
        ),
        QgsField(
            "SPECIES",
            QVariant.String,
            len=254,
        ),
        QgsField(
            "SCI_NAME",
            QVariant.String,
            len=254,
        ),
        QgsField(
            "REDLIST",
            QVariant.String,
            len=10,
        ),
        QgsField(
            "PROTECTED",
            QVariant.Int,
        ),
        QgsField(
            "VERIFIED",
            QVariant.Int,
        ),
        QgsField(
            "ACTIVITY",
            QVariant.String,
            len=100,
        ),
        QgsField(
            "LIFE_STAGE",
            QVariant.String,
            len=100,
        ),
        QgsField(
            "QUANTITY",
            QVariant.Int,
        ),
        QgsField(
            "QTY_UNIT",
            QVariant.String,
            len=50,
        ),
    ]

    provider = memory_layer.dataProvider()
    provider.addAttributes(fields)
    memory_layer.updateFields()

    output_features = []

    for source_feature in source_layer.getFeatures():

        geometry = source_feature.geometry()

        if geometry is None or geometry.isEmpty():
            continue

        output_feature = QgsFeature(
            memory_layer.fields()
        )

        output_feature.setGeometry(
            geometry
        )

        output_feature.setAttributes(
            [
                as_text(
                    get_attribute(
                        source_feature,
                        "occurrenceId",
                    )
                ),
                as_text(
                    get_attribute(
                        source_feature,
                        "url",
                    )
                ),
                as_boolean_integer(
                    get_attribute(
                        source_feature,
                        "isPresentObservation",
                    )
                ),
                as_text(
                    get_attribute(
                        source_feature,
                        "datasetName",
                    )
                ),
                as_text(
                    get_attribute(
                        source_feature,
                        "startDate",
                    )
                ),
                as_text(
                    get_attribute(
                        source_feature,
                        "endDate",
                    )
                ),
                as_text(
                    get_attribute(
                        source_feature,
                        "modified",
                    )
                ),
                as_float(
                    get_attribute(
                        source_feature,
                        "decimalLatitude",
                    )
                ),
                as_float(
                    get_attribute(
                        source_feature,
                        "decimalLongitude",
                    )
                ),
                as_integer(
                    get_attribute(
                        source_feature,
                        "coordinateUncertaintyInMeters",
                    )
                ),
                as_text(
                    get_attribute(
                        source_feature,
                        "locality",
                    )
                ),
                as_text(
                    get_attribute(
                        source_feature,
                        "municipality",
                    )
                ),
                as_text(
                    get_attribute(
                        source_feature,
                        "county",
                    )
                ),
                as_text(
                    get_attribute(
                        source_feature,
                        "province",
                    )
                ),
                as_text(
                    get_attribute(
                        source_feature,
                        "recordedBy",
                    )
                ),
                as_text(
                    get_attribute(
                        source_feature,
                        "reportedBy",
                    )
                ),
                as_text(
                    get_attribute(
                        source_feature,
                        "habitat",
                    )
                ),
                as_text(
                    get_attribute(
                        source_feature,
                        "occurrenceRemarks",
                    )
                ),
                as_integer(
                    get_attribute(
                        source_feature,
                        "dyntaxaTaxonId",
                    )
                ),
                as_text(
                    get_attribute(
                        source_feature,
                        "taxonCategory",
                    )
                ),
                as_text(
                    get_attribute(
                        source_feature,
                        "organismGroup",
                    )
                ),
                as_text(
                    get_attribute(
                        source_feature,
                        "vernacularName",
                    )
                ),
                as_text(
                    get_attribute(
                        source_feature,
                        "scientificName",
                    )
                ),
                as_text(
                    get_attribute(
                        source_feature,
                        "redlistCategory",
                    )
                ),
                as_boolean_integer(
                    get_attribute(
                        source_feature,
                        "isProtectedByLaw",
                    )
                ),
                as_boolean_integer(
                    get_attribute(
                        source_feature,
                        "isVerified",
                    )
                ),
                as_text(
                    get_attribute(
                        source_feature,
                        "activity",
                    )
                ),
                as_text(
                    get_attribute(
                        source_feature,
                        "lifeStage",
                    )
                ),
                as_integer(
                    get_attribute(
                        source_feature,
                        "organismQuantity",
                    )
                ),
                as_text(
                    get_attribute(
                        source_feature,
                        "organismQuantityUnit",
                    )
                ),
            ]
        )

        output_features.append(
            output_feature
        )

    provider.addFeatures(
        output_features
    )

    memory_layer.updateExtents()

    return memory_layer


def download_redlisted_species(
    context_polygon_path,
    folder_path,
    temp_path,
    settings,
):
    """
    Download red-listed species observations within the
    configured analysis context and save them offline.

    The WFS request is first limited by the context bounding
    box. Features are then spatially extracted against the
    exact context polygon.
    """

    if not settings:
        print(
            "Red-listed species download skipped: "
            "no country configuration."
        )

        return {
            "status": "unavailable",
            "output_path": None,
            "feature_count": 0,
        }

    context_layer = QgsVectorLayer(
        context_polygon_path,
        "Species observation context",
        "ogr",
    )

    if not context_layer.isValid():
        raise ValueError(
            f"Failed to load species context polygon: "
            f"{context_polygon_path}"
        )

    if not context_layer.crs().isValid():
        raise ValueError(
            "The species context polygon has no valid CRS."
        )

    context_distance_m = float(
        settings.get(
            "context_distance_m",
            0.0,
        )
    )

    if context_distance_m < 0:
        raise ValueError(
            "The red-listed species context distance "
            "cannot be negative."
        )

    if context_distance_m > 0:

        if context_layer.crs().isGeographic():
            raise ValueError(
                "The red-listed species context buffer "
                "requires a projected CRS."
            )

        buffered_context_path = os.path.join(
            temp_path,
            "redlisted_species_context.shp",
        )

        processing.run(
            "native:buffer",
            {
                "INPUT": context_layer,
                "DISTANCE": context_distance_m,
                "SEGMENTS": 20,
                "END_CAP_STYLE": 0,
                "JOIN_STYLE": 0,
                "MITER_LIMIT": 2,
                "DISSOLVE": True,
                "OUTPUT": buffered_context_path,
            },
        )

        context_layer = QgsVectorLayer(
            buffered_context_path,
            "Red-listed species context",
            "ogr",
        )

        if not context_layer.isValid():
            raise RuntimeError(
                "Failed to create the temporary "
                "red-listed species context buffer."
            )

        print(
            "Red-listed species search context: "
            f"{context_distance_m:.0f} m around the "
            "analysis site."
        )

    source_crs = QgsCoordinateReferenceSystem(
        settings.get(
            "source_crs",
            "EPSG:4326",
        )
    )

    if not source_crs.isValid():
        raise ValueError(
            "The red-listed species source CRS is invalid."
        )

    context_extent = context_layer.extent()

    if context_layer.crs() != source_crs:

        transform = QgsCoordinateTransform(
            context_layer.crs(),
            source_crs,
            QgsProject.instance().transformContext(),
        )

        request_extent = (
            transform.transformBoundingBox(
                context_extent
            )
        )

    else:
        request_extent = context_extent

    downloaded_geojson_path = os.path.join(
        temp_path,
        "redlisted_species_download.geojson",
    )

    downloaded_count = download_wfs_pages(
        service_url=settings["service_url"],
        wfs_version=settings.get(
            "wfs_version",
            "2.0.0",
        ),
        type_name=settings["type_name"],
        bbox=request_extent,
        source_crs=source_crs.authid(),
        output_path=downloaded_geojson_path,
        page_size=settings.get(
            "page_size",
            10000,
        ),
    )

    if downloaded_count == 0:
        print(
            "No red-listed species observations were "
            "returned for the context extent."
        )

        return {
            "status": "no_features",
            "output_path": None,
            "feature_count": 0,
        }

    downloaded_layer = QgsVectorLayer(
        downloaded_geojson_path,
        "Downloaded red-listed species",
        "ogr",
    )

    if not downloaded_layer.isValid():
        raise RuntimeError(
            "The downloaded red-listed species GeoJSON "
            "could not be loaded."
        )

    # The WFS contains its real GeoJSON geometry plus the
    # additional GML properties "point" and "pointLocation".
    # OGR reads those properties as QVariantMap attributes,
    # which cannot be written by the reprojection algorithm.
    complex_geometry_fields = [
        field_name
        for field_name in (
            "point",
            "pointLocation",
        )
        if field_name
        in downloaded_layer.fields().names()
    ]

    sanitised_layer = downloaded_layer

    if complex_geometry_fields:

        sanitised_path = os.path.join(
            temp_path,
            "redlisted_species_sanitised.geojson",
        )

        processing.run(
            "native:deletecolumn",
            {
                "INPUT": downloaded_layer,
                "COLUMN": complex_geometry_fields,
                "OUTPUT": sanitised_path,
            },
        )

        sanitised_layer = QgsVectorLayer(
            sanitised_path,
            "Sanitised red-listed species",
            "ogr",
        )

        if not sanitised_layer.isValid():
            raise RuntimeError(
                "Failed to remove unsupported WFS "
                "geometry attributes."
            )

    reprojected_path = os.path.join(
        temp_path,
        "redlisted_species_reprojected.geojson",
    )

    processing.run(
        "native:reprojectlayer",
        {
            "INPUT": sanitised_layer,
            "TARGET_CRS": context_layer.crs(),
            "OUTPUT": reprojected_path,
        },
    )

    exact_output_path = os.path.join(
        temp_path,
        "redlisted_species_exact.geojson",
    )

    processing.run(
        "native:extractbylocation",
        {
            "INPUT": reprojected_path,
            "PREDICATE": [0],
            "INTERSECT": context_layer,
            "OUTPUT": exact_output_path,
        },
    )

    exact_layer = QgsVectorLayer(
        exact_output_path,
        "Red-listed species in context",
        "ogr",
    )

    if not exact_layer.isValid():
        raise RuntimeError(
            "Failed to create the exact species-context "
            "extraction."
        )

    if exact_layer.featureCount() == 0:
        print(
            "No red-listed species observations fall "
            "inside the exact context polygon."
        )

        return {
            "status": "no_features",
            "output_path": None,
            "feature_count": 0,
        }

    clean_layer = create_clean_species_layer(
        source_layer=exact_layer,
    )

    output_path = os.path.join(
        folder_path,
        settings.get(
            "output_filename",
            "redlisted_species.shp",
        ),
    )

    processing.run(
        "native:savefeatures",
        {
            "INPUT": clean_layer,
            "OUTPUT": output_path,
        },
    )

    processing.run(
        "native:createspatialindex",
        {
            "INPUT": output_path,
        },
    )

    final_layer = QgsVectorLayer(
        output_path,
        settings.get(
            "map_layer_name",
            "Red-listed species observations",
        ),
        "ogr",
    )

    if not final_layer.isValid():
        raise RuntimeError(
            f"Failed to create the offline species layer: "
            f"{output_path}"
        )

    feature_count = final_layer.featureCount()

    print(
        f"Red-listed species observations saved: "
        f"{feature_count} features — {output_path}"
    )

    return {
        "status": "available",
        "output_path": output_path,
        "feature_count": feature_count,
    }