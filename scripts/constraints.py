import os
import processing
import math

from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsVectorLayer,
    QgsWkbTypes,
    Qgis,
    QgsUnitTypes,
    QgsField
)


def clip_country_layers(
    layer_definitions,
    data_path,
    context_polygon_path,
    temp_path,
    target_crs,
):
    """
    Clip configured country layers to the context polygon,
    then reproject the local results to the working CRS.

    Return each output path together with its configuration.
    """

    overlay = QgsVectorLayer(
        context_polygon_path,
        "Analysis surroundings",
        "ogr",
    )

    if not overlay.isValid():
        raise ValueError(
            f"Failed to load context polygon: {context_polygon_path}"
        )

    if overlay.geometryType() != QgsWkbTypes.PolygonGeometry:
        raise ValueError(
            "The context layer must contain polygons."
        )

    if not overlay.crs().isValid():
        raise ValueError(
            "The context polygon has no valid CRS."
        )

    if overlay.featureCount() == 0:
        raise ValueError(
            "The context polygon layer is empty."
        )

    if not target_crs.isValid() or target_crs.isGeographic():
        raise ValueError(
            "Constraint processing requires a valid projected CRS."
        )

    source_output_dir = os.path.join(
        temp_path,
        "clipped_source",
    )

    output_dir = os.path.join(
        temp_path,
        "clipped",
    )

    os.makedirs(source_output_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    results = []

    for number, definition in enumerate(layer_definitions, start=1):
        filename = definition["source"]
        display_name = definition["name"]

        source_path = os.path.join(data_path, filename)

        source = QgsVectorLayer(
            source_path,
            display_name,
            "ogr",
        )

        if not source.isValid():
            raise ValueError(
                f"Configured dataset is missing or invalid: "
                f"{display_name} — {source_path}"
            )

        if not source.crs().isValid():
            raise ValueError(
                f"Dataset has no valid CRS: {source_path}"
            )

        print(
            f"Clipping country layer "
            f"{number}/{len(layer_definitions)}: {display_name}"
        )

        # Clip in the source layer's CRS. QGIS transforms
        # the overlay as needed for the operation.
        source_clip_path = os.path.join(
            source_output_dir,
            filename,
        )

        processing.run(
            "native:clip",
            {
                "INPUT": source,
                "OVERLAY": overlay,
                "OUTPUT": source_clip_path,
            },
        )

        # Reproject only the local clipped result,
        # rather than the entire national dataset.
        output_path = os.path.join(
            output_dir,
            filename,
        )

        processing.run(
            "native:reprojectlayer",
            {
                "INPUT": source_clip_path,
                "TARGET_CRS": target_crs,
                "OUTPUT": output_path,
            },
        )

        processing.run(
            "native:createspatialindex",
            {
                "INPUT": output_path,
            },
        )

        clipped = QgsVectorLayer(
            output_path,
            display_name,
            "ogr",
        )

        if not clipped.isValid():
            raise RuntimeError(
                f"Failed to load clipped dataset: {output_path}"
            )

        feature_count = clipped.featureCount()

        results.append(
            {
                "definition": definition,
                "path": output_path,
                "feature_count": feature_count,
            }
        )

        print(
            f"Clipped {display_name}: "
            f"{feature_count} features."
        )

    return results

def buffer_country_layers(
    clipped_country_layers,
    temp_path,
):
    """
    Apply the configured solar and wind buffers.

    Distances are in metres and converted to the layer CRS's units.
    Zero-distance entries retain their clipped source path.
    """

    output_dirs = {
        "solar": os.path.join(temp_path, "buffered_clipped_solar"),
        "wind": os.path.join(temp_path, "buffered_clipped_wind"),
    }

    for directory in output_dirs.values():
        os.makedirs(directory, exist_ok=True)

    results = []

    for number, item in enumerate(clipped_country_layers, start=1):
        definition = item["definition"]
        source_path = item["path"]

        layer = QgsVectorLayer(
            source_path,
            definition["name"],
            "ogr",
        )

        if not layer.isValid():
            raise ValueError(
                f"Failed to load clipped layer: {source_path}"
            )

        crs = layer.crs()

        if not crs.isValid() or crs.isGeographic():
            raise ValueError(
                "Constraint buffering requires a valid projected CRS."
            )

        if crs.mapUnits() == Qgis.DistanceUnit.Unknown:
            raise ValueError(
                f"Unknown measurement units: {source_path}"
            )

        units_per_metre = QgsUnitTypes.fromUnitToUnitFactor(
            Qgis.DistanceUnit.Meters,
            crs.mapUnits(),
        )

        layer_result = {
            "definition": definition,
            "clipped_path": source_path,
            "feature_count": item["feature_count"],
        }

        for technology in ("solar", "wind"):
            distance_m = float(
                definition[f"{technology}_buffer_m"]
            )

            if not 0 <= distance_m < float("inf"):
                raise ValueError(
                    f"Invalid {technology} buffer distance "
                    f"for {definition['name']}: {distance_m}"
                )

            if distance_m == 0:
                # No buffer is generated. Preserve access to
                # the original clipped geometry.
                layer_result[f"{technology}_path"] = source_path
                layer_result[f"{technology}_buffered"] = False
                continue

            basename = os.path.splitext(
                os.path.basename(definition["source"])
            )[0]

            output_path = os.path.join(
                output_dirs[technology],
                f"{basename}.shp",
            )

            processing.run(
                "native:buffer",
                {
                    "INPUT": layer,
                    "DISTANCE": distance_m * units_per_metre,
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

            layer_result[f"{technology}_path"] = output_path
            layer_result[f"{technology}_buffered"] = True

        results.append(layer_result)

        print(
            f"Country layer buffers prepared "
            f"({number}/{len(clipped_country_layers)}): "
            f"{definition['name']}"
        )

    return results

def save_country_layer_outputs(
    prepared_country_layers,
    folder_path,
):
    """
    Export the clipped country layers to the main output folder.

    Keep the solar and wind buffer paths available separately.
    """

    os.makedirs(folder_path, exist_ok=True)

    results = []

    for number, item in enumerate(prepared_country_layers, start=1):
        definition = item["definition"]
        source_path = item["clipped_path"]

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

        saved_layer = QgsVectorLayer(
            output_path,
            definition["name"],
            "ogr",
        )

        if not saved_layer.isValid():
            raise RuntimeError(
                f"Failed to load exported country layer: {output_path}"
            )

        result = dict(item)
        result["output_path"] = output_path

        results.append(result)

        print(
            f"Country layer saved "
            f"({number}/{len(prepared_country_layers)}): "
            f"{definition['name']} — {output_path}"
        )

    return results

def create_country_layer_centroids(
    country_layer_outputs,
    folder_path,
):
    """
    Create centroid outputs only for explicitly configured layers.

    Preserve polygon outputs and analysis-buffer paths.
    Update output_path to the centroid representation where applicable.
    """

    results = []

    for item in country_layer_outputs:
        result = dict(item)
        definition = item["definition"]

        centroid_filename = definition.get("centroid_output")

        if centroid_filename is None:
            results.append(result)
            continue

        polygon_path = item["output_path"]

        polygons = QgsVectorLayer(
            polygon_path,
            definition["name"],
            "ogr",
        )

        if not polygons.isValid():
            raise ValueError(
                f"Failed to load centroid source: {polygon_path}"
            )

        if polygons.geometryType() != QgsWkbTypes.PolygonGeometry:
            raise ValueError(
                f"Centroid conversion expects polygons: {polygon_path}"
            )

        centroid_path = os.path.join(
            folder_path,
            centroid_filename,
        )

        processing.run(
            "native:centroids",
            {
                "INPUT": polygons,
                "ALL_PARTS": False,
                "OUTPUT": centroid_path,
            },
        )

        processing.run(
            "native:createspatialindex",
            {
                "INPUT": centroid_path,
            },
        )

        centroids = QgsVectorLayer(
            centroid_path,
            definition["name"],
            "ogr",
        )

        if not centroids.isValid():
            raise RuntimeError(
                f"Failed to load centroid output: {centroid_path}"
            )

        result["polygon_output_path"] = polygon_path
        result["output_path"] = centroid_path

        results.append(result)

        print(
            f"Centroid representation created: "
            f"{definition['name']} — {centroid_path}"
        )

    return results

def subtract_solar_constraints(
    site_layer_path,
    country_layer_outputs,
    temp_path,
):
    """
    Subtract solar-buffered country layers from the analysis estate.

    Each subtraction uses the previous result.
    Save the remaining geometry as diff_area.shp.
    """

    remaining = QgsVectorLayer(
        site_layer_path,
        "Analysis estate",
        "ogr",
    )

    if not remaining.isValid():
        raise ValueError(
            f"Failed to load analysis estate: {site_layer_path}"
        )

    solar_constraints = [
        item
        for item in country_layer_outputs
        if item["solar_buffered"]
    ]

    for number, item in enumerate(solar_constraints, start=1):
        if remaining.featureCount() == 0:
            print("No estate geometry remains after solar exclusions.")
            break

        definition = item["definition"]

        constraint = QgsVectorLayer(
            item["solar_path"],
            definition["name"],
            "ogr",
        )

        if not constraint.isValid():
            raise ValueError(
                f"Failed to load solar constraint: "
                f"{item['solar_path']}"
            )

        if constraint.geometryType() != QgsWkbTypes.PolygonGeometry:
            raise ValueError(
                f"Solar constraint must contain polygons: "
                f"{definition['name']}"
            )

        if constraint.crs() != remaining.crs():
            raise ValueError(
                f"Solar constraint CRS differs from the estate: "
                f"{definition['name']}"
            )

        if constraint.featureCount() == 0:
            print(
                f"Solar constraint {number}/{len(solar_constraints)}: "
                f"{definition['name']} — no local features."
            )
            continue

        result = processing.run(
            "native:difference",
            {
                "INPUT": remaining,
                "OVERLAY": constraint,
                "OUTPUT": "memory:",
            },
        )

        remaining = result["OUTPUT"]

        if not remaining.isValid():
            raise RuntimeError(
                f"Subtraction failed for: {definition['name']}"
            )

        print(
            f"Solar constraint subtracted "
            f"({number}/{len(solar_constraints)}): "
            f"{definition['name']}"
        )

    output_path = os.path.join(
        temp_path,
        "diff_area.shp",
    )

    processing.run(
        "native:savefeatures",
        {
            "INPUT": remaining,
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
        f"Estate after solar exclusions saved: {output_path}"
    )

    return output_path

def subtract_ineligible_terrain(
    solar_remaining_path,
    filtered_ineligible_terrain_path,
    temp_path,
):
    """
    Remove filtered ineligible terrain from the remaining estate.

    If no terrain exclusion exists, copy the remaining estate.
    Save the result as almost_done_solar.shp.
    """

    remaining = QgsVectorLayer(
        solar_remaining_path,
        "Estate after solar constraints",
        "ogr",
    )

    if not remaining.isValid():
        raise ValueError(
            f"Failed to load remaining estate: {solar_remaining_path}"
        )

    output_path = os.path.join(
        temp_path,
        output_filename,
    )

    if (
        filtered_ineligible_terrain_path is None
        or remaining.featureCount() == 0
    ):
        processing.run(
            "native:savefeatures",
            {
                "INPUT": remaining,
                "OUTPUT": output_path,
            },
        )

        print(
            "Terrain subtraction skipped: no terrain exclusions "
            "or no remaining estate features."
        )

    else:
        terrain = QgsVectorLayer(
            filtered_ineligible_terrain_path,
            "Ineligible terrain",
            "ogr",
        )

        if not terrain.isValid():
            raise ValueError(
                f"Failed to load ineligible terrain: "
                f"{filtered_ineligible_terrain_path}"
            )

        if terrain.geometryType() != QgsWkbTypes.PolygonGeometry:
            raise ValueError(
                "Ineligible terrain must contain polygons."
            )

        if (
            not remaining.crs().isValid()
            or not terrain.crs().isValid()
            or terrain.crs() != remaining.crs()
        ):
            raise ValueError(
                "The estate and terrain exclusions must have "
                "the same valid CRS."
            )

        processing.run(
            "native:difference",
            {
                "INPUT": remaining,
                "OVERLAY": terrain,
                "OUTPUT": output_path,
            },
        )

    processing.run(
        "native:createspatialindex",
        {
            "INPUT": output_path,
        },
    )

    result = QgsVectorLayer(
        output_path,
        "Estate after terrain exclusions",
        "ogr",
    )

    if not result.isValid():
        raise RuntimeError(
            f"Failed to load terrain-subtraction result: {output_path}"
        )

    print(
        f"Estate after terrain exclusions saved: {output_path}"
    )

    return output_path

def process_solar_holes(
    solar_terrain_remaining_path,
    temp_path,
    fill_holes,
):
    """
    Optionally fill all interior holes, matching Anna's behaviour.

    If disabled, return the input path without changing its geometry.
    """

    if not fill_holes:
        print("Preserving interior holes in the solar candidate area.")
        return solar_terrain_remaining_path

    output_path = os.path.join(
        temp_path,
        "solar_holes_filled.shp",
    )

    processing.run(
        "native:deleteholes",
        {
            "INPUT": solar_terrain_remaining_path,
            "MIN_AREA": 0,  # QGIS: remove all interior holes.
            "OUTPUT": output_path,
        },
    )

    processing.run(
        "native:createspatialindex",
        {
            "INPUT": output_path,
        },
    )

    result = QgsVectorLayer(
        output_path,
        "Solar candidate area without holes",
        "ogr",
    )

    if not result.isValid():
        raise RuntimeError(
            f"Failed to load hole-removal result: {output_path}"
        )

    print(
        f"All interior holes filled in solar candidate area: "
        f"{output_path}"
    )

    return output_path

def shrink_solar_candidate_area(
    solar_holes_processed_path,
    temp_path,
    inward_distance_m,
):
    """
    Apply an inward buffer to the solar candidate area.

    The supplied distance is positive and expressed in metres.
    Preserve the working CRS and convert the distance to its units.
    """

    inward_distance_m = float(inward_distance_m)

    if (
        not math.isfinite(inward_distance_m)
        or inward_distance_m < 0
    ):
        raise ValueError(
            "The inward buffer distance must be finite "
            "and non-negative."
        )

    layer = QgsVectorLayer(
        solar_holes_processed_path,
        "Solar candidate area",
        "ogr",
    )

    if not layer.isValid():
        raise ValueError(
            f"Failed to load solar candidate area: "
            f"{solar_holes_processed_path}"
        )

    crs = layer.crs()

    if not crs.isValid() or crs.isGeographic():
        raise ValueError(
            "Inward buffering requires a valid projected CRS."
        )

    if crs.mapUnits() == Qgis.DistanceUnit.Unknown:
        raise ValueError(
            "The solar candidate layer has unknown measurement units."
        )

    units_per_metre = QgsUnitTypes.fromUnitToUnitFactor(
        Qgis.DistanceUnit.Meters,
        crs.mapUnits(),
    )

    output_path = os.path.join(
        temp_path,
        "buildable_solar_not_final.shp",
    )

    if inward_distance_m == 0:
        processing.run(
            "native:savefeatures",
            {
                "INPUT": layer,
                "OUTPUT": output_path,
            },
        )

    else:
        processing.run(
            "native:buffer",
            {
                "INPUT": layer,
                "DISTANCE": -inward_distance_m * units_per_metre,
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

    result = QgsVectorLayer(
        output_path,
        "Shrunk solar candidate area",
        "ogr",
    )

    if not result.isValid():
        raise RuntimeError(
            f"Failed to load inward-buffer result: {output_path}"
        )

    print(
        f"Solar inward buffer applied ({inward_distance_m:g} m): "
        f"{output_path}"
    )

    return output_path

def dissolve_solar_candidate_area(
    solar_terrain_rechecked_path,
    temp_path,
):
    """
    Dissolve the solar candidate geometry after the second
    terrain subtraction, preserving its working CRS.
    """

    output_path = os.path.join(
        temp_path,
        "almost_done_solar_igen_igen.shp",
    )

    processing.run(
        "native:dissolve",
        {
            "INPUT": solar_terrain_rechecked_path,
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

    result = QgsVectorLayer(
        output_path,
        "Dissolved solar candidate area",
        "ogr",
    )

    if not result.isValid():
        raise RuntimeError(
            f"Failed to load dissolved solar area: {output_path}"
        )

    print(
        f"Solar candidate area dissolved: {output_path}"
    )

    return output_path

def save_solar_candidate_parts(
    solar_dissolved_path,
    folder_path,
):
    """
    Convert the dissolved solar candidate area to singleparts
    and save it in the estate's main output folder.

    Each separate polygon becomes its own feature.
    """

    output_path = os.path.join(
        folder_path,
        "buildable_solar.shp",
    )

    processing.run(
        "native:multiparttosingleparts",
        {
            "INPUT": solar_dissolved_path,
            "OUTPUT": output_path,
        },
    )

    processing.run(
        "native:createspatialindex",
        {
            "INPUT": output_path,
        },
    )

    result = QgsVectorLayer(
        output_path,
        "Solar candidate parts",
        "ogr",
    )

    if not result.isValid():
        raise RuntimeError(
            f"Failed to load solar candidate parts: {output_path}"
        )

    print(
        f"Solar candidate parts saved: "
        f"{result.featureCount()} features — {output_path}"
    )

    return output_path

def subtract_wind_constraints(
    site_layer_path,
    country_layer_outputs,
    temp_path,
):
    """
    Subtract wind-buffered constraints from the original estate.

    Keep the wind assessment independent of solar exclusions.
    """

    remaining = QgsVectorLayer(
        site_layer_path,
        "Analysis estate",
        "ogr",
    )

    if not remaining.isValid():
        raise ValueError(
            f"Failed to load analysis estate: {site_layer_path}"
        )

    if not remaining.crs().isValid():
        raise ValueError(
            "The analysis estate has no valid CRS."
        )

    wind_constraints = [
        item
        for item in country_layer_outputs
        if item["wind_buffered"]
    ]

    for number, item in enumerate(wind_constraints, start=1):
        if remaining.featureCount() == 0:
            print("No estate geometry remains after wind exclusions.")
            break

        definition = item["definition"]

        constraint = QgsVectorLayer(
            item["wind_path"],
            definition["name"],
            "ogr",
        )

        if not constraint.isValid():
            raise ValueError(
                f"Failed to load wind constraint: "
                f"{item['wind_path']}"
            )

        if constraint.geometryType() != QgsWkbTypes.PolygonGeometry:
            raise ValueError(
                f"Wind constraint must contain polygons: "
                f"{definition['name']}"
            )

        if constraint.crs() != remaining.crs():
            raise ValueError(
                f"Wind constraint CRS differs from the estate: "
                f"{definition['name']}"
            )

        if constraint.featureCount() == 0:
            print(
                f"Wind constraint {number}/{len(wind_constraints)}: "
                f"{definition['name']} — no local features."
            )
            continue

        result = processing.run(
            "native:difference",
            {
                "INPUT": remaining,
                "OVERLAY": constraint,
                "OUTPUT": "memory:",
            },
        )

        remaining = result["OUTPUT"]

        if not remaining.isValid():
            raise RuntimeError(
                f"Subtraction failed for: {definition['name']}"
            )

        print(
            f"Wind constraint subtracted "
            f"({number}/{len(wind_constraints)}): "
            f"{definition['name']}"
        )

    output_path = os.path.join(
        temp_path,
        "diff_area_wind.shp",
    )

    processing.run(
        "native:savefeatures",
        {
            "INPUT": remaining,
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
        f"Estate after wind exclusions saved: {output_path}"
    )

    return output_path

def dissolve_wind_candidate_area(
    wind_remaining_path,
    temp_path,
):
    """
    Dissolve the wind candidate geometry after constraint removal.

    Preserve the working CRS and allow an empty result.
    """

    output_path = os.path.join(
        temp_path,
        "almost_done_wind_igen.shp",
    )

    processing.run(
        "native:dissolve",
        {
            "INPUT": wind_remaining_path,
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

    result = QgsVectorLayer(
        output_path,
        "Dissolved wind candidate area",
        "ogr",
    )

    if not result.isValid():
        raise RuntimeError(
            f"Failed to load dissolved wind area: {output_path}"
        )

    print(
        f"Wind candidate area dissolved: {output_path}"
    )

    return output_path

def save_wind_candidate_parts(
    wind_dissolved_path,
    folder_path,
):
    """
    Convert the dissolved wind candidate area to singleparts
    and save it in the estate's main output folder.

    Each separate polygon becomes its own feature.
    """

    output_path = os.path.join(
        folder_path,
        "buildable_wind.shp",
    )

    processing.run(
        "native:multiparttosingleparts",
        {
            "INPUT": wind_dissolved_path,
            "OUTPUT": output_path,
        },
    )

    processing.run(
        "native:createspatialindex",
        {
            "INPUT": output_path,
        },
    )

    result = QgsVectorLayer(
        output_path,
        "Wind candidate parts",
        "ogr",
    )

    if not result.isValid():
        raise RuntimeError(
            f"Failed to load wind candidate parts: {output_path}"
        )

    print(
        f"Wind candidate parts saved: "
        f"{result.featureCount()} features — {output_path}"
    )

    return output_path

def calculate_candidate_areas(
    candidate_path,
    technology,
):
    """
    Update a candidate shapefile with:
        AREA: each patch's area in hectares.
        sum_area: total candidate area in hectares.

    Works for both solar and wind.
    """

    label = technology.capitalize()

    layer = QgsVectorLayer(
        candidate_path,
        f"{label} candidate area",
        "ogr",
    )

    if not layer.isValid():
        raise ValueError(
            f"Failed to load {technology} candidates: {candidate_path}"
        )

    crs = layer.crs()

    if not crs.isValid() or crs.isGeographic():
        raise ValueError(
            "Area calculation requires a valid projected CRS."
        )

    if crs.mapUnits() == Qgis.DistanceUnit.Unknown:
        raise ValueError(
            "The candidate layer has unknown measurement units."
        )

    metres_per_unit = QgsUnitTypes.fromUnitToUnitFactor(
        crs.mapUnits(),
        Qgis.DistanceUnit.Meters,
    )

    hectares_per_square_unit = metres_per_unit ** 2 / 10000

    patch_areas = {}

    for feature in layer.getFeatures():
        geometry = feature.geometry()

        area_ha = (
            0.0
            if geometry.isNull() or geometry.isEmpty()
            else geometry.area() * hectares_per_square_unit
        )

        patch_areas[feature.id()] = area_ha

    total_area_ha = math.fsum(patch_areas.values())

    if not layer.startEditing():
        raise RuntimeError(
            f"Could not start editing the {technology} candidate layer."
        )

    try:
        field_indices = {}

        for field_name in ("AREA", "sum_area"):
            field_index = next(
                (
                    index
                    for index, field in enumerate(layer.fields())
                    if field.name().casefold() == field_name.casefold()
                ),
                -1,
            )

            if field_index == -1:
                if not layer.addAttribute(
                    QgsField(
                        field_name,
                        QVariant.Double,
                        len=20,
                        prec=6,
                    )
                ):
                    raise RuntimeError(
                        f"Could not add field: {field_name}"
                    )

                field_index = layer.fields().indexFromName(field_name)

            if layer.fields()[field_index].type() != QVariant.Double:
                raise ValueError(
                    f"Field {field_name} must be a decimal-number field."
                )

            field_indices[field_name] = field_index

        for feature_id, area_ha in patch_areas.items():
            if not layer.changeAttributeValue(
                feature_id,
                field_indices["AREA"],
                area_ha,
            ):
                raise RuntimeError(
                    f"Could not update area for feature {feature_id}."
                )

            if not layer.changeAttributeValue(
                feature_id,
                field_indices["sum_area"],
                total_area_ha,
            ):
                raise RuntimeError(
                    f"Could not update total for feature {feature_id}."
                )

        if not layer.commitChanges():
            errors = "; ".join(layer.commitErrors())
            raise RuntimeError(
                f"Could not save {technology} candidate areas: {errors}"
            )

    except Exception:
        if layer.isEditable():
            layer.rollBack()
        raise

    print(
        f"{label} candidate area: {total_area_ha:.3f} ha "
        f"across {len(patch_areas)} features."
    )

    return {
        "path": candidate_path,
        "feature_count": len(patch_areas),
        "total_area_ha": total_area_ha,
    }