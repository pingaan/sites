import os
import processing

import numpy as np

from collections import defaultdict
from osgeo import gdal, ogr, osr
from qgis.core import (
    Qgis,
    QgsUnitTypes,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsRectangle
)


def create_terrain_grid(
    site_layer_path,
    temp_path,
):
    """
    Create a square work grid and clip it to the estate.

    Follow Anna's cell-size rule:
    start at 2,000 m and decrease by 50 m until a cell
    fits within both dimensions of the estate extent.
    """

    site = QgsVectorLayer(
        site_layer_path,
        "Analysis site",
        "ogr",
    )

    if not site.isValid():
        raise ValueError(
            f"Failed to load site: {site_layer_path}"
        )

    crs = site.crs()

    if not crs.isValid() or crs.isGeographic():
        raise ValueError(
            "Terrain grid creation requires a valid projected CRS."
        )

    map_units = crs.mapUnits()

    if map_units == Qgis.DistanceUnit.Unknown:
        raise ValueError(
            "The site CRS has unknown measurement units."
        )

    extent = site.extent()

    if site.featureCount() == 0 or extent.isEmpty():
        raise ValueError(
            "The site has no usable extent."
        )

    units_per_metre = QgsUnitTypes.fromUnitToUnitFactor(
        Qgis.DistanceUnit.Meters,
        map_units,
    )

    # Select the cell size using Anna's original rule.
    cell_size_metres = None

    for candidate_metres in range(2000, 49, -50):
        candidate_units = candidate_metres * units_per_metre

        if (
            extent.width() >= candidate_units
            and extent.height() >= candidate_units
        ):
            cell_size_metres = candidate_metres
            break

    if cell_size_metres is None:
        cell_size_metres = 50

        print(
            "Estate extent is narrower than 50 m; "
            "using 50 m grid cells and clipping them to the estate."
        )

    cell_size = cell_size_metres * units_per_metre

    # Ensure the grid extent can accommodate at least one full cell.
    # The estate geometry itself remains unchanged.
    grid_width = max(extent.width(), cell_size)
    grid_height = max(extent.height(), cell_size)

    # Small margin avoids floating-point rounding at the minimum size.
    margin = cell_size * 1e-6
    centre = extent.center()

    grid_extent = QgsRectangle(
        centre.x() - grid_width / 2 - margin,
        centre.y() - grid_height / 2 - margin,
        centre.x() + grid_width / 2 + margin,
        centre.y() + grid_height / 2 + margin,
    )

    print(
        f"Creating terrain grid with "
        f"{cell_size_metres} m cells..."
    )

    os.makedirs(temp_path, exist_ok=True)

    grid_path = os.path.join(
        temp_path,
        "grid.shp",
    )

    processing.run(
        "native:creategrid",
        {
            "TYPE": 2,  # Rectangle (polygon)
            "EXTENT": grid_extent,
            "HSPACING": cell_size,
            "VSPACING": cell_size,
            "HOVERLAY": 0,
            "VOVERLAY": 0,
            "CRS": crs,
            "OUTPUT": grid_path,
        },
    )

    processing.run(
        "native:createspatialindex",
        {
            "INPUT": grid_path,
        },
    )

    clipped_grid_path = os.path.join(
        temp_path,
        "grid_clipped.shp",
    )

    processing.run(
        "native:clip",
        {
            "INPUT": grid_path,
            "OVERLAY": site,
            "OUTPUT": clipped_grid_path,
        },
    )

    processing.run(
        "native:createspatialindex",
        {
            "INPUT": clipped_grid_path,
        },
    )

    clipped_grid = QgsVectorLayer(
        clipped_grid_path,
        "Terrain grid",
        "ogr",
    )

    if not clipped_grid.isValid():
        raise RuntimeError(
            "Failed to load the clipped terrain grid."
        )

    if clipped_grid.featureCount() == 0:
        raise RuntimeError(
            "The clipped terrain grid contains no features."
        )

    print(
        f"Terrain grid created: "
        f"{clipped_grid.featureCount()} features."
    )

    return clipped_grid_path

def extract_grid_dem_tiles(
    terrain_grid_path,
    clipped_dem_path,
    temp_path,
):
    """
    Clip the estate DEM to each grid feature's bounding rectangle.

    Return the output raster paths for subsequent terrain analysis.
    """

    grid = QgsVectorLayer(
        terrain_grid_path,
        "Terrain grid",
        "ogr",
    )

    raster = QgsRasterLayer(
        clipped_dem_path,
        "Estate DEM",
        "gdal",
    )

    if not grid.isValid():
        raise ValueError(
            f"Failed to load terrain grid: {terrain_grid_path}"
        )

    if not raster.isValid():
        raise ValueError(
            f"Failed to load estate DEM: {clipped_dem_path}"
        )

    if not grid.crs().isValid() or not raster.crs().isValid():
        raise ValueError(
            "The terrain grid and DEM must have valid CRSs."
        )

    if grid.crs() != raster.crs():
        raise ValueError(
            "The terrain grid and DEM must use the same CRS."
        )

    total_features = grid.featureCount()

    if total_features == 0:
        raise ValueError(
            "The terrain grid contains no features."
        )

    output_dir = os.path.join(
        temp_path,
        "temp_dem",
    )

    os.makedirs(output_dir, exist_ok=True)

    tile_paths = []

    for number, feature in enumerate(grid.getFeatures(), start=1):
        geometry = feature.geometry()

        if geometry.isNull() or geometry.isEmpty():
            raise ValueError(
                f"Grid feature {feature.id()} has no geometry."
            )

        bbox = geometry.boundingBox()

        extent_string = (
            f"{bbox.xMinimum()},{bbox.xMaximum()},"
            f"{bbox.yMinimum()},{bbox.yMaximum()}"
        )

        output_path = os.path.join(
            output_dir,
            f"clipped_{feature.id()}.tif",
        )

        processing.run(
            "gdal:cliprasterbyextent",
            {
                "INPUT": raster,
                "PROJWIN": extent_string,
                "DATA_TYPE": 0,
                "OUTPUT": output_path,
            },
        )

        output_raster = QgsRasterLayer(
            output_path,
            f"Grid DEM {feature.id()}",
            "gdal",
        )

        if not output_raster.isValid():
            raise RuntimeError(
                f"Failed to create grid DEM: {output_path}"
            )

        tile_paths.append(output_path)

        print(
            f"DEM clipped to grid feature "
            f"{number}/{total_features}: {output_path}"
        )

    return tile_paths

def calculate_slope_aspect(
    terrain_dem_paths,
    temp_path,
):
    """
    Calculate slope and aspect for each terrain DEM piece.

    Elevations are assumed to be in metres.
    Horizontal units are read from each raster's CRS.
    """

    if not terrain_dem_paths:
        raise ValueError(
            "No terrain DEM pieces are available."
        )

    output_dir = os.path.join(
        temp_path,
        "temp_slope_shapes",
    )

    os.makedirs(output_dir, exist_ok=True)

    results = []

    for number, dem_path in enumerate(terrain_dem_paths, start=1):

        raster = QgsRasterLayer(
            dem_path,
            "Terrain DEM",
            "gdal",
        )

        if not raster.isValid():
            raise ValueError(
                f"Failed to load terrain DEM: {dem_path}"
            )

        crs = raster.crs()

        if not crs.isValid() or crs.isGeographic():
            raise ValueError(
                "Slope calculation requires a valid projected CRS."
            )

        if crs.mapUnits() == Qgis.DistanceUnit.Unknown:
            raise ValueError(
                "The terrain DEM has unknown horizontal units."
            )

        # Elevations are in metres. Account for the horizontal
        # units of the selected working CRS.
        metres_per_unit = QgsUnitTypes.fromUnitToUnitFactor(
            crs.mapUnits(),
            Qgis.DistanceUnit.Meters,
        )

        # Release the QGIS raster before opening it through GDAL.
        raster = None

        name = os.path.splitext(os.path.basename(dem_path))[0]

        slope_path = os.path.join(
            output_dir,
            f"{name}_slope.tif",
        )

        aspect_path = os.path.join(
            output_dir,
            f"{name}_aspect.tif",
        )

        slope_dataset = gdal.DEMProcessing(
            slope_path,
            dem_path,
            "slope",
            format="GTiff",
            alg="Horn",
            slopeFormat="degree",
            scale=metres_per_unit,
            computeEdges=True,
        )

        if slope_dataset is None:
            raise RuntimeError(
                f"Slope calculation failed: {dem_path}\n"
                f"{gdal.GetLastErrorMsg()}"
            )

        slope_dataset = None

        aspect_dataset = gdal.DEMProcessing(
            aspect_path,
            dem_path,
            "aspect",
            format="GTiff",
            alg="Horn",
            computeEdges=True,
            trigonometric=False,
            zeroForFlat=False,
        )

        if aspect_dataset is None:
            raise RuntimeError(
                f"Aspect calculation failed: {dem_path}\n"
                f"{gdal.GetLastErrorMsg()}"
            )

        aspect_dataset = None

        results.append(
            {
                "dem_path": dem_path,
                "slope_path": slope_path,
                "aspect_path": aspect_path,
            }
        )

        print(
            f"Slope and aspect calculated "
            f"({number}/{len(terrain_dem_paths)}): {name}"
        )

    return results

def save_ineligible_points(
    output_path,
    rows,
    cols,
    slopes,
    aspects,
    geotransform,
    projection,
):
    """
    Save selected pixels as points using Anna's original
    pixel-corner coordinate convention.
    """

    driver = ogr.GetDriverByName("ESRI Shapefile")

    if os.path.exists(output_path):
        if driver.DeleteDataSource(output_path) != 0:
            raise RuntimeError(
                f"Could not replace: {output_path}"
            )

    dataset = driver.CreateDataSource(output_path)

    if dataset is None:
        raise RuntimeError(
            f"Could not create: {output_path}"
        )

    try:
        spatial_reference = osr.SpatialReference()

        if spatial_reference.ImportFromWkt(projection) != 0:
            raise ValueError("Could not read the raster CRS.")

        layer = dataset.CreateLayer(
            os.path.splitext(os.path.basename(output_path))[0],
            srs=spatial_reference,
            geom_type=ogr.wkbPoint,
        )

        if layer is None:
            raise RuntimeError("Could not create the point layer.")

        for name, field_type in (
            ("row", ogr.OFTInteger),
            ("col", ogr.OFTInteger),
            ("SLOPE", ogr.OFTReal),
            ("ASPECT", ogr.OFTReal),
        ):
            if layer.CreateField(ogr.FieldDefn(name, field_type)) != 0:
                raise RuntimeError(f"Could not create field: {name}")

        gt = geotransform

        for row, col in zip(rows, cols):
            row = int(row)
            col = int(col)

            point = ogr.Geometry(ogr.wkbPoint)
            point.AddPoint_2D(
                gt[0] + col * gt[1] + row * gt[2],
                gt[3] + col * gt[4] + row * gt[5],
            )

            feature = ogr.Feature(layer.GetLayerDefn())
            feature.SetField("row", row)
            feature.SetField("col", col)
            feature.SetField("SLOPE", float(slopes[row, col]))
            feature.SetField("ASPECT", float(aspects[row, col]))
            feature.SetGeometry(point)

            if layer.CreateFeature(feature) != 0:
                raise RuntimeError(
                    f"Could not write a point to: {output_path}"
                )

            feature = None
            point = None

    finally:
        layer = None
        dataset = None

def extract_ineligible_terrain(
    terrain_results,
    temp_path,
    slope_thresholds,
):
    """
    Select pixels exceeding Anna's aspect-dependent slope limits.

    Return only the point shapefiles produced by this run.
    """

    if len(slope_thresholds) != 12:
        raise ValueError(
            "Exactly 12 slope thresholds are required."
        )

    if not terrain_results:
        raise ValueError("No slope/aspect results were supplied.")

    output_dir = os.path.join(temp_path, "final_points")
    os.makedirs(output_dir, exist_ok=True)

    output_paths = []

    for number, result in enumerate(terrain_results, start=1):
        slope_dataset = None
        aspect_dataset = None

        try:
            slope_dataset = gdal.Open(result["slope_path"])
            aspect_dataset = gdal.Open(result["aspect_path"])

            if slope_dataset is None or aspect_dataset is None:
                raise RuntimeError(
                    f"Could not open slope/aspect rasters: {result}"
                )

            slope_band = slope_dataset.GetRasterBand(1)
            aspect_band = aspect_dataset.GetRasterBand(1)

            slopes = slope_band.ReadAsArray()
            aspects = aspect_band.ReadAsArray()

            slope_nodata = slope_band.GetNoDataValue()
            aspect_nodata = aspect_band.GetNoDataValue()

            geotransform = slope_dataset.GetGeoTransform()
            projection = slope_dataset.GetProjection()

            if (
                slopes.shape != aspects.shape
                or geotransform != aspect_dataset.GetGeoTransform()
                or projection != aspect_dataset.GetProjection()
            ):
                raise ValueError(
                    "Slope and aspect rasters are not aligned."
                )

        finally:
            slope_band = None
            aspect_band = None
            slope_dataset = None
            aspect_dataset = None

        valid = np.isfinite(slopes) & np.isfinite(aspects)

        if slope_nodata is not None:
            valid &= slopes != slope_nodata

        if aspect_nodata is not None:
            valid &= aspects != aspect_nodata

        name = os.path.splitext(
            os.path.basename(result["dem_path"])
        )[0]

        files_created = 0

        for index, threshold in enumerate(slope_thresholds):
            aspect_ranges = (
                (index * 15, (index + 1) * 15),
                (345 - index * 15, 360 - index * 15),
            )

            for lower, upper in aspect_ranges:
                selected = (
                    valid
                    & (slopes > threshold)
                    & (aspects >= lower)
                    & (aspects <= upper)
                )

                rows, cols = np.nonzero(selected)

                if len(rows) == 0:
                    continue

                threshold_label = (
                    f"{threshold:g}".replace(".", "p")
                )

                output_path = os.path.join(
                    output_dir,
                    f"{name}_slope_gt_{threshold_label}"
                    f"_aspect_{lower}_{upper}.shp",
                )

                save_ineligible_points(
                    output_path=output_path,
                    rows=rows,
                    cols=cols,
                    slopes=slopes,
                    aspects=aspects,
                    geotransform=geotransform,
                    projection=projection,
                )

                output_paths.append(output_path)
                files_created += 1

        print(
            f"Ineligible terrain extracted "
            f"({number}/{len(terrain_results)}): "
            f"{name} — {files_created} point layers"
        )

    print(
        f"Total ineligible-terrain point layers: {len(output_paths)}"
    )

    return output_paths

def buffer_ineligible_points(
    ineligible_point_paths,
    temp_path,
):
    """
    Buffer ineligible-terrain points using Anna's parameters.

    Convert the 0.5 m distance into the source CRS's units.
    Return the polygon paths created by this run.
    """

    output_dir = os.path.join(
        temp_path,
        "final_shapes",
    )

    os.makedirs(output_dir, exist_ok=True)

    polygon_paths = []

    if not ineligible_point_paths:
        print("No ineligible terrain points to buffer.")
        return polygon_paths

    for number, point_path in enumerate(ineligible_point_paths, start=1):

        points = QgsVectorLayer(
            point_path,
            "Ineligible terrain points",
            "ogr",
        )

        if not points.isValid():
            raise ValueError(
                f"Failed to load terrain points: {point_path}"
            )

        crs = points.crs()

        if not crs.isValid() or crs.isGeographic():
            raise ValueError(
                "Point buffering requires a valid projected CRS."
            )

        if crs.mapUnits() == Qgis.DistanceUnit.Unknown:
            raise ValueError(
                "The point layer has unknown measurement units."
            )

        units_per_metre = QgsUnitTypes.fromUnitToUnitFactor(
            Qgis.DistanceUnit.Meters,
            crs.mapUnits(),
        )

        output_path = os.path.join(
            output_dir,
            os.path.basename(point_path),
        )

        processing.run(
            "native:buffer",
            {
                "INPUT": points,
                "DISTANCE": 0.5 * units_per_metre,
                "SEGMENTS": 1,
                "END_CAP_STYLE": 2,
                "JOIN_STYLE": 0,
                "MITER_LIMIT": 2,
                "DISSOLVE": False,
                "OUTPUT": output_path,
            },
        )

        polygon_paths.append(output_path)

        print(
            f"Ineligible terrain points buffered "
            f"({number}/{len(ineligible_point_paths)}): "
            f"{os.path.basename(output_path)}"
        )

    return polygon_paths

def merge_ineligible_polygons_by_cell(
    ineligible_polygon_paths,
    temp_path,
    target_crs,
):
    """
    Group ineligible-terrain polygons by grid-cell identifier
    and merge each group into one shapefile.
    """

    output_dir = os.path.join(
        temp_path,
        "merged",
    )

    os.makedirs(output_dir, exist_ok=True)

    files_by_cell = defaultdict(list)

    for polygon_path in ineligible_polygon_paths:
        filename = os.path.basename(polygon_path)
        parts = filename.split("_", 2)

        if (
            len(parts) != 3
            or parts[0] != "clipped"
            or not parts[1].isdigit()
        ):
            raise ValueError(
                f"Unexpected terrain polygon filename: {filename}"
            )

        cell_id = parts[1]
        files_by_cell[cell_id].append(polygon_path)

    merged_paths = []

    if not files_by_cell:
        print("No ineligible terrain polygons to merge.")
        return merged_paths

    cell_ids = sorted(files_by_cell, key=int)

    for number, cell_id in enumerate(cell_ids, start=1):
        output_path = os.path.join(
            output_dir,
            f"merged_{cell_id}.shp",
        )

        processing.run(
            "native:mergevectorlayers",
            {
                "LAYERS": files_by_cell[cell_id],
                "CRS": target_crs,
                "OUTPUT": output_path,
            },
        )

        processing.run(
            "native:createspatialindex",
            {
                "INPUT": output_path,
            },
        )

        merged_paths.append(output_path)

        print(
            f"Ineligible polygons merged "
            f"({number}/{len(cell_ids)}): "
            f"grid cell {cell_id}"
        )

    return merged_paths

def dissolve_ineligible_polygons(
    merged_ineligible_paths,
    temp_path,
):
    """
    Dissolve the merged ineligible polygons for each grid cell.
    Preserve the input CRS.
    """

    output_dir = os.path.join(
        temp_path,
        "dissolved",
    )

    os.makedirs(output_dir, exist_ok=True)

    dissolved_paths = []

    if not merged_ineligible_paths:
        print("No ineligible terrain polygons to dissolve.")
        return dissolved_paths

    for number, merged_path in enumerate(
        merged_ineligible_paths,
        start=1,
    ):
        filename = os.path.splitext(
            os.path.basename(merged_path)
        )[0]

        cell_id = filename.removeprefix("merged_")

        output_path = os.path.join(
            output_dir,
            f"dissolved_{cell_id}.shp",
        )

        processing.run(
            "native:dissolve",
            {
                "INPUT": merged_path,
                "FIELD": [],
                "OUTPUT": output_path,
            },
        )

        processing.run(
            "native:createspatialindex",
            {
                "INPUT": output_path,
            },
        )

        dissolved_paths.append(output_path)

        print(
            f"Ineligible polygons dissolved "
            f"({number}/{len(merged_ineligible_paths)}): "
            f"grid cell {cell_id}"
        )

    return dissolved_paths

def buffer_ineligible_polygons(
    dissolved_ineligible_paths,
    temp_path,
):
    """
    Expand each dissolved ineligible-terrain layer by 1 metre.

    Convert the buffer distance into the layer CRS's units.
    """

    output_dir = os.path.join(
        temp_path,
        "buffered",
    )

    os.makedirs(output_dir, exist_ok=True)

    buffered_paths = []

    if not dissolved_ineligible_paths:
        print("No ineligible terrain polygons to buffer.")
        return buffered_paths

    for number, dissolved_path in enumerate(
        dissolved_ineligible_paths,
        start=1,
    ):
        layer = QgsVectorLayer(
            dissolved_path,
            "Dissolved ineligible terrain",
            "ogr",
        )

        if not layer.isValid():
            raise ValueError(
                f"Failed to load ineligible terrain: {dissolved_path}"
            )

        crs = layer.crs()

        if not crs.isValid() or crs.isGeographic():
            raise ValueError(
                "Terrain buffering requires a valid projected CRS."
            )

        if crs.mapUnits() == Qgis.DistanceUnit.Unknown:
            raise ValueError(
                "The terrain layer has unknown measurement units."
            )

        units_per_metre = QgsUnitTypes.fromUnitToUnitFactor(
            Qgis.DistanceUnit.Meters,
            crs.mapUnits(),
        )

        filename = os.path.splitext(
            os.path.basename(dissolved_path)
        )[0]

        cell_id = filename.removeprefix("dissolved_")

        output_path = os.path.join(
            output_dir,
            f"buffered_{cell_id}.shp",
        )

        processing.run(
            "native:buffer",
            {
                "INPUT": layer,
                "DISTANCE": 1.0 * units_per_metre,
                "SEGMENTS": 5,
                "END_CAP_STYLE": 0,
                "JOIN_STYLE": 0,
                "MITER_LIMIT": 2,
                "DISSOLVE": False,
                "OUTPUT": output_path,
            },
        )

        processing.run(
            "native:createspatialindex",
            {
                "INPUT": output_path,
            },
        )

        buffered_paths.append(output_path)

        print(
            f"Ineligible terrain buffered by 1 m "
            f"({number}/{len(dissolved_ineligible_paths)}): "
            f"grid cell {cell_id}"
        )

    return buffered_paths

def merge_ineligible_polygons_by_aspect(
    ineligible_polygon_paths,
    temp_path,
    target_crs,
):
    """
    Merge matching eastern and western aspect sectors
    across all grid cells, following Anna's 12 aspect pairs.
    """

    output_dir = os.path.join(
        temp_path,
        "temp_dem_new",
    )

    os.makedirs(output_dir, exist_ok=True)

    aspect_paths = []

    if not ineligible_polygon_paths:
        print("No ineligible terrain polygons to merge by aspect.")
        return aspect_paths

    for index in range(12):
        east_lower = index * 15
        east_upper = (index + 1) * 15

        west_lower = 345 - index * 15
        west_upper = 360 - index * 15

        suffixes = (
            f"_aspect_{east_lower}_{east_upper}.shp",
            f"_aspect_{west_lower}_{west_upper}.shp",
        )

        matching_paths = [
            path
            for path in ineligible_polygon_paths
            if os.path.basename(path).endswith(suffixes)
        ]

        if not matching_paths:
            print(
                f"Aspect pair {index + 1}/12: "
                "no ineligible polygons."
            )
            continue

        output_path = os.path.join(
            output_dir,
            f"bad_slopes_{index + 1}.shp",
        )

        processing.run(
            "native:mergevectorlayers",
            {
                "LAYERS": matching_paths,
                "CRS": target_crs,
                "OUTPUT": output_path,
            },
        )

        processing.run(
            "native:createspatialindex",
            {
                "INPUT": output_path,
            },
        )

        aspect_paths.append(output_path)

        print(
            f"Aspect pair {index + 1}/12 merged: "
            f"{east_lower}–{east_upper}° and "
            f"{west_lower}–{west_upper}°"
        )

    return aspect_paths

def merge_buffered_ineligible_terrain(
    buffered_ineligible_paths,
    temp_path,
    target_crs,
):
    """
    Merge the buffered ineligible terrain from all grid cells.

    Return the output path, or None if no inputs exist.
    """

    if not buffered_ineligible_paths:
        print("No buffered ineligible terrain to merge.")
        return None

    output_path = os.path.join(
        temp_path,
        "big_mash_up.shp",
    )

    processing.run(
        "native:mergevectorlayers",
        {
            "LAYERS": buffered_ineligible_paths,
            "CRS": target_crs,
            "OUTPUT": output_path,
        },
    )

    processing.run(
        "native:createspatialindex",
        {
            "INPUT": output_path,
        },
    )

    print(
        f"Buffered ineligible terrain merged: {output_path}"
    )

    return output_path

def save_aspect_outputs(
    aspect_polygon_paths,
    folder_path,
):
    """
    Save the current run's aspect-pair layers in the
    estate's main output folder.
    """

    final_paths = []

    if not aspect_polygon_paths:
        print("No ineligible aspect layers to save.")
        return final_paths

    for number, source_path in enumerate(aspect_polygon_paths, start=1):
        output_path = os.path.join(
            folder_path,
            os.path.basename(source_path),
        )

        processing.run(
            "native:savefeatures",
            {
                "INPUT": source_path,
                "OUTPUT": output_path,
            },
        )

        processing.run(
            "native:createspatialindex",
            {
                "INPUT": output_path,
            },
        )

        final_paths.append(output_path)

        print(
            f"Aspect layer saved "
            f"({number}/{len(aspect_polygon_paths)}): "
            f"{output_path}"
        )

    return final_paths