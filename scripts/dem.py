import os
import shutil
import processing

import pandas as pd

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
    QgsRectangle,
    QgsRasterLayer
)


def select_dem_tiles(
    site_extent,
    data_path,
    dem_path,
    temp_path,
    dem_index_crs,
):
    """
    Select DEM tiles using Anna's CSV coordinate-selection rule.

    Transform the search extent into the DEM index CRS,
    then copy matching files into temp/clip.
    """

    index_crs = QgsCoordinateReferenceSystem(dem_index_crs)

    if not index_crs.isValid():
        raise ValueError(
            f"Invalid DEM index CRS: {dem_index_crs}"
        )

    source_crs = site_extent["crs"]

    if not source_crs.isValid():
        raise ValueError(
            "The site extent has no valid CRS."
        )

    search_extent = QgsRectangle(
        site_extent["x_min"],
        site_extent["y_min"],
        site_extent["x_max"],
        site_extent["y_max"],
    )

    if source_crs != index_crs:
        transform = QgsCoordinateTransform(
            source_crs,
            index_crs,
            QgsProject.instance().transformContext(),
        )

        search_extent = transform.transformBoundingBox(
            search_extent
        )

    # Read the existing DEM index.
    csv_path = os.path.join(
        data_path,
        "DEM_masterfile.csv",
    )

    index = pd.read_csv(csv_path)

    required_columns = {"x", "y", "FILENAME"}
    missing_columns = required_columns - set(index.columns)

    if missing_columns:
        raise ValueError(
            f"DEM index is missing columns: "
            f"{', '.join(sorted(missing_columns))}"
        )

    index["x"] = pd.to_numeric(index["x"], errors="raise")
    index["y"] = pd.to_numeric(index["y"], errors="raise")

    # Preserve Anna's strict point-within-extent selection.
    selected = index.loc[
        (index["x"] > search_extent.xMinimum())
        & (index["x"] < search_extent.xMaximum())
        & (index["y"] > search_extent.yMinimum())
        & (index["y"] < search_extent.yMaximum())
    ]

    if selected.empty:
        raise ValueError(
            "No DEM index coordinates fall inside the search extent."
        )

    if selected["FILENAME"].isna().any():
        raise ValueError(
            "A selected DEM index row has no filename."
        )

    filenames = selected["FILENAME"].drop_duplicates().tolist()

    clip_path = os.path.join(temp_path, "clip")
    os.makedirs(clip_path, exist_ok=True)

    print(
        f"DEM tiles selected: {len(filenames)} "
        f"(index CRS: {index_crs.authid()})"
    )

    tile_paths = []

    for number, filename in enumerate(filenames, start=1):
        source_path = os.path.join(dem_path, filename)
        destination_path = os.path.join(clip_path, filename)

        if not os.path.isfile(source_path):
            raise FileNotFoundError(
                f"DEM tile not found: {source_path}"
            )

        if os.path.isfile(destination_path):
            action = "Already present"
        else:
            os.makedirs(
                os.path.dirname(destination_path),
                exist_ok=True,
            )

            shutil.copy(source_path, destination_path)
            action = "Copied"

        tile_paths.append(destination_path)

        print(
            f"DEM tile {number}/{len(filenames)}: "
            f"{action} — {filename}"
        )

    return tile_paths

def merge_dem_tiles(
    dem_tile_paths,
    temp_path,
):
    """
    Merge the selected DEM tiles into one elevation raster.

    Preserve their source CRS. Reprojection is not performed here.
    """

    if not dem_tile_paths:
        raise ValueError(
            "No DEM tiles are available to merge."
        )

    for tile_path in dem_tile_paths:
        if not os.path.isfile(tile_path):
            raise FileNotFoundError(
                f"DEM tile not found: {tile_path}"
            )

    merged_raster_path = os.path.join(
        temp_path,
        "merged_raster.tif",
    )

    print(
        f"Merging {len(dem_tile_paths)} DEM tiles..."
    )

    processing.run(
        "gdal:merge",
        {
            "INPUT": dem_tile_paths,
            "PCT": False,
            "SEPARATE": False,
            "DATA_TYPE": 5,  # Float32: preserve decimal elevations.
            "OUTPUT": merged_raster_path,
        },
    )

    print(
        f"DEM tiles merged: {merged_raster_path}"
    )

    return merged_raster_path

def clip_dem_to_site(
    merged_dem_path,
    site_layer_path,
    folder_path,
    target_crs,
):
    """
    Clip the merged DEM to the analysis estate and output
    it in the resolved working CRS.
    """

    if not os.path.isfile(merged_dem_path):
        raise FileNotFoundError(
            f"Merged DEM not found: {merged_dem_path}"
        )

    clipped_raster_path = os.path.join(
        folder_path,
        "raster_clipped.tif",
    )

    print("Clipping DEM to the analysis estate...")

    processing.run(
        "gdal:cliprasterbymasklayer",
        {
            "INPUT": merged_dem_path,
            "MASK": site_layer_path,
            "TARGET_CRS": target_crs,
            "NODATA": -9999,
            "ALPHA_BAND": False,
            "CROP_TO_CUTLINE": True,
            "KEEP_RESOLUTION": False,
            "SET_RESOLUTION": False,
            "MULTITHREADING": False,
            "DATA_TYPE": 0,  # Preserve the input data type.
            "OUTPUT": clipped_raster_path,
        },
    )

    clipped_raster = QgsRasterLayer(
        clipped_raster_path,
        "Clipped DEM",
        "gdal",
    )

    if not clipped_raster.isValid():
        raise RuntimeError(
            f"Failed to load clipped DEM: {clipped_raster_path}"
        )

    if clipped_raster.crs() != target_crs:
        raise RuntimeError(
            "The clipped DEM does not use the requested working CRS."
        )

    print(
        f"DEM clipped ({clipped_raster.crs().authid()}): "
        f"{clipped_raster_path}"
    )

    return clipped_raster_path