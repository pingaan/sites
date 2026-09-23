import os
import processing
import re

import pandas as pd

from qgis.core import (
    Qgis,
    QgsUnitTypes,
    QgsVectorLayer,
    QgsVectorFileWriter,
    QgsWkbTypes
)


def parse_estate(estate):
    """
    Parse the estate name into BOROUGH, SECTOR and SEGMENT.

    This preserves the same parsing logic used in anna2.0.py.
    """

    parts = estate.upper().split()

    if len(parts) == 4:
        return (
            parts[0],
            parts[1] + " " + parts[2],
            parts[3],
        )

    if len(parts) == 3:
        return tuple(parts)

    raise ValueError("Invalid format of estate entry.")


def search_chunk(chunk, match):
    """
    Search one CSV chunk for the requested estate.
    """

    return chunk[
        (chunk["BOROUGH"] == match[0])
        & (chunk["SECTOR"] == match[1])
        & (chunk["SEGMENT"] == match[2])
    ]


def sequential_search(csv_file, match):
    """
    Search estates.csv in chunks and return matching row indices.
    """

    iterator = pd.read_csv(
        csv_file,
        chunksize=10000,
    )

    results = []

    for chunk in iterator:
        chunk_result = search_chunk(
            chunk,
            match,
        )

        results.append(chunk_result)

    result_df = pd.concat(results)

    if not result_df.empty:
        return result_df.index.values

    return None

def extract_estate_features(
    match,
    row_indices,
    estates_layer_path,
    output_root,
    run_id,
):
    """
    Extract the estate feature(s) corresponding to the
    matching CSV row indices.

    Returns information needed by the following processing steps.
    """

    estates = QgsVectorLayer(
        estates_layer_path,
        "estates",
        "ogr",
    )

    if not estates.isValid():
        raise ValueError(
            f"Failed to load estates layer: {estates_layer_path}"
        )

    # ---------------------------------------------------------
    # Create output directories
    # ---------------------------------------------------------

    folder_name = " ".join(match).replace(":", "-")

    folder_path = os.path.join(
        output_root,
        folder_name,
        run_id,
    )

    os.makedirs(
        folder_path,
        exist_ok=True,
    )

    temp_path = os.path.join(
        folder_path,
        "temp",
    )

    os.makedirs(
        temp_path,
        exist_ok=True,
    )

    # ---------------------------------------------------------
    # Extract matching estate feature(s)
    # ---------------------------------------------------------

    extracted_layers = []

    for row_index in row_indices:

        extracted_feature_path = os.path.join(
            temp_path,
            f"fastigheten_{row_index}.shp",
        )

        feature_id = None
        current_index = 0

        for feature in estates.getFeatures():

            if current_index == row_index:
                feature_id = feature.id()
                break

            current_index += 1

        if feature_id is None:
            print(
                f"Row index {row_index} out of range."
            )
            continue

        estates.selectByIds(
            [feature_id]
        )

        writer = QgsVectorFileWriter.writeAsVectorFormat(
            estates,
            extracted_feature_path,
            "UTF-8",
            estates.crs(),
            "ESRI Shapefile",
            onlySelected=True,
        )

        estates.removeSelection()

        if writer[0] == QgsVectorFileWriter.NoError:

            extracted_layers.append(
                extracted_feature_path
            )

        else:

            print(
                f"Error saving extracted feature "
                f"for row {row_index}. "
                f"Writer error code: {writer[0]}"
            )

    if not extracted_layers:
        raise RuntimeError(
            "No estate features were extracted."
        )

    return {
        "folder_name": folder_name,
        "folder_path": folder_path,
        "temp_path": temp_path,
        "extracted_layers": extracted_layers,
    }

def merge_estate_features(
    extracted_layers,
    temp_path,
):
    """
    Merge the extracted estate feature(s) into one layer.
    """

    merged_layer_path = os.path.join(
        temp_path,
        "Fastigheten_merged.shp",
    )

    processing.run(
        "native:mergevectorlayers",
        {
            "LAYERS": extracted_layers,
            "OUTPUT": merged_layer_path,
        },
    )

    processing.run(
        "native:createspatialindex",
        {
            "INPUT": merged_layer_path,
        },
    )

    print(
        f"Estate features merged: "
        f"{merged_layer_path}"
    )

    return merged_layer_path

def dissolve_estate_features(
    merged_layer_path,
    temp_path,
):
    """
    Dissolve the merged estate geometry into one feature.
    """

    dissolved_layer_path = os.path.join(
        temp_path,
        "Fastigheten_dissolved.shp",
    )

    processing.run(
        "native:dissolve",
        {
            "INPUT": merged_layer_path,
            "OUTPUT": dissolved_layer_path,
        },
    )

    processing.run(
        "native:createspatialindex",
        {
            "INPUT": dissolved_layer_path,
        },
    )

    print(
        f"Estate features dissolved: "
        f"{dissolved_layer_path}"
    )

    return dissolved_layer_path

def split_estate_to_singleparts(
    dissolved_layer_path,
    temp_path,
):
    """
    Convert the dissolved estate geometry from multipart
    to singlepart features.
    """

    singleparts_layer_path = os.path.join(
        temp_path,
        "Fastigheten_singleparts.shp",
    )

    processing.run(
        "native:multiparttosingleparts",
        {
            "INPUT": dissolved_layer_path,
            "OUTPUT": singleparts_layer_path,
        },
    )

    processing.run(
        "native:createspatialindex",
        {
            "INPUT": singleparts_layer_path,
        },
    )

    print(
        f"Estate converted to singleparts: "
        f"{singleparts_layer_path}"
    )

    return singleparts_layer_path

def reproject_estate(
    singleparts_layer_path,
    temp_path,
    target_crs,
):
    """
    Reproject the estate to the working CRS for this analysis.
    """

    reprojected_layer_path = os.path.join(
        temp_path,
        "Fastigheten_reprojected.shp",
    )

    processing.run(
        "native:reprojectlayer",
        {
            "INPUT": singleparts_layer_path,
            "TARGET_CRS": target_crs,
            "OUTPUT": reprojected_layer_path,
        },
    )

    processing.run(
        "native:createspatialindex",
        {
            "INPUT": reprojected_layer_path,
        },
    )

    print(
        f"Estate reprojected to {target_crs}: "
        f"{reprojected_layer_path}"
    )

    return reprojected_layer_path

def calculate_estate_area(
    reprojected_layer_path,
    folder_path,
):
    """
    Calculate each estate part's planar area in hectares
    and save the final estate shapefile.
    """

    estate_layer = QgsVectorLayer(
        reprojected_layer_path,
        "Reprojected estate",
        "ogr",
    )

    if not estate_layer.isValid():
        raise ValueError(
            f"Failed to load estate: {reprojected_layer_path}"
        )

    crs = estate_layer.crs()

    if not crs.isValid() or crs.isGeographic():
        raise ValueError(
            "Area calculation requires a valid projected CRS."
        )

    map_units = crs.mapUnits()

    if map_units == Qgis.DistanceUnit.Unknown:
        raise ValueError(
            "The estate CRS has unknown measurement units."
        )

    # Convert squared layer units to hectares.
    metres_per_unit = QgsUnitTypes.fromUnitToUnitFactor(
        map_units,
        Qgis.DistanceUnit.Meters,
    )

    hectares_per_square_unit = metres_per_unit ** 2 / 10000

    output_layer_path = os.path.join(
        folder_path,
        "Fastigheten.shp",
    )

    processing.run(
        "native:fieldcalculator",
        {
            "INPUT": estate_layer,
            "FIELD_NAME": "area",
            "FIELD_TYPE": 0,
            "FIELD_LENGTH": 20,
            "FIELD_PRECISION": 3,
            "FORMULA": (
                f"area($geometry) * {hectares_per_square_unit!r}"
            ),
            "OUTPUT": output_layer_path,
        },
    )

    processing.run(
        "native:createspatialindex",
        {
            "INPUT": output_layer_path,
        },
    )

    print(
        f"Estate saved with area in hectares: "
        f"{output_layer_path}"
    )

    return output_layer_path

def select_site_source(
    estate,
    custom_polygon=None,
):
    """
    Decide whether the site comes from an estate lookup
    or from a custom polygon.

    Returns
    -------
    dict
        Description of the selected source.
    """

    if estate and estate.strip():
        return {
            "type": "estate",
            "estate": estate,
        }

    if custom_polygon is not None:
        return {
            "type": "custom_polygon",
            "polygon": custom_polygon,
        }

    raise ValueError(
        "No estate or custom polygon supplied."
    )

def prepare_custom_polygon_source(
    custom_polygon_path,
    output_root,
    run_id,
    folder_name_override=None,
):
    """
    Validate and prepare an explicitly supplied custom polygon
    so it provides the same initial data structure as an estate
    extracted from the national estate dataset.

    The later merge, dissolve, singlepart, CRS and analysis
    stages can therefore be shared by both input types.
    """

    if not custom_polygon_path:
        raise ValueError(
            "No custom polygon path was supplied."
        )

    if not os.path.isfile(custom_polygon_path):
        raise FileNotFoundError(
            f"Custom polygon does not exist: "
            f"{custom_polygon_path}"
        )

    source_layer = QgsVectorLayer(
        custom_polygon_path,
        "Custom analysis polygon",
        "ogr",
    )

    if not source_layer.isValid():
        raise ValueError(
            f"Failed to load custom polygon: "
            f"{custom_polygon_path}"
        )

    if (
        source_layer.geometryType()
        != QgsWkbTypes.PolygonGeometry
    ):
        raise ValueError(
            "The custom analysis input must contain "
            "polygon geometry."
        )

    if source_layer.featureCount() == 0:
        raise ValueError(
            "The custom polygon layer contains no features."
        )

    if not source_layer.crs().isValid():
        raise ValueError(
            "The custom polygon has no valid CRS."
        )

    source_name = os.path.splitext(
        os.path.basename(custom_polygon_path)
    )[0]

    if folder_name_override:
        requested_folder_name = (
            folder_name_override
        )

    else:
        requested_folder_name = (
            f"CUSTOM {source_name}"
        )

    # Use a hyphen for cadastral designations such as
    # 19:63 because colons are invalid in Windows folders.
    requested_folder_name = (
        requested_folder_name.replace(
            ":",
            "-",
        )
    )

    folder_name = re.sub(
        r'[<>:"/\\|?*]+',
        "_",
        requested_folder_name,
    ).strip(" ._")

    if not folder_name:
        folder_name = "CUSTOM custom_polygon"

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

    prepared_polygon_path = os.path.join(
        temp_path,
        "custom_polygon_source.shp",
    )

    processing.run(
        "native:fixgeometries",
        {
            "INPUT": source_layer,
            "OUTPUT": prepared_polygon_path,
        },
    )

    prepared_layer = QgsVectorLayer(
        prepared_polygon_path,
        "Prepared custom polygon",
        "ogr",
    )

    if not prepared_layer.isValid():
        raise RuntimeError(
            "Failed to prepare the custom polygon."
        )

    if prepared_layer.featureCount() == 0:
        raise RuntimeError(
            "No polygon geometry remained after repairing "
            "the custom input."
        )

    print(
        f"Custom polygon source prepared: "
        f"{prepared_polygon_path}"
    )

    return {
        "folder_name": folder_name,
        "folder_path": folder_path,
        "temp_path": temp_path,
        "extracted_layers": [
            prepared_polygon_path,
        ],
        "source_type": "custom_polygon",
        "source_path": custom_polygon_path,
    }