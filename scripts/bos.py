import os
import processing

from qgis.core import (
    QgsVectorLayer,
    QgsWkbTypes,
)


def calculate_vector_area_hectares(
    layer_path,
):
    """
    Calculate the total polygon area in hectares.
    """

    layer = QgsVectorLayer(
        layer_path,
        "BoS analysis area",
        "ogr",
    )

    if not layer.isValid():
        raise ValueError(
            f"Failed to load BoS analysis area: "
            f"{layer_path}"
        )

    if layer.geometryType() != QgsWkbTypes.PolygonGeometry:
        raise ValueError(
            "BoS analysis requires polygon geometry."
        )

    if (
        not layer.crs().isValid()
        or layer.crs().isGeographic()
    ):
        raise ValueError(
            "BoS area calculation requires a valid "
            "projected CRS."
        )

    total_square_metres = 0.0

    for feature in layer.getFeatures():
        geometry = feature.geometry()

        if geometry.isEmpty():
            continue

        total_square_metres += geometry.area()

    return total_square_metres / 10000


def prepare_bos_analysis(
    analysis_layer_path,
    bos_settings,
):
    """
    Prepare BoS analysis for the complete estate/custom polygon.

    BoS is performed regardless of the remaining solar candidate
    area or the size of the analysis polygon.
    """

    result = {
        "status": "skipped",
        "analysis_area_ha": 0.0,
        "reason": None,
    }

    if not bos_settings:
        result["reason"] = (
            "No country BoS configuration is available."
        )

        print(
            f"BoS analysis skipped: "
            f"{result['reason']}"
        )

        return result

    analysis_area_ha = (
        calculate_vector_area_hectares(
            analysis_layer_path
        )
    )

    result["analysis_area_ha"] = (
        analysis_area_ha
    )

    result["status"] = "ready"

    print(
        "BoS analysis enabled for complete "
        f"analysis site: {analysis_area_ha:.2f} ha."
    )

    return result

def prepare_bos_landcover(
    analysis_layer_path,
    data_path,
    temp_path,
    bos_settings,
):
    """
    Prepare the base land-cover polygons for BoS analysis.

    Raster cells touching the complete estate/custom polygon are
    included and then clipped back to its exact boundary.
    """

    landcover_path = os.path.join(
        data_path,
        bos_settings["landcover_raster"],
    )

    if not os.path.isfile(landcover_path):
        raise FileNotFoundError(
            f"Configured BoS land-cover raster does not exist: "
            f"{landcover_path}"
        )

    analysis_layer = QgsVectorLayer(
        analysis_layer_path,
        "BoS analysis site",
        "ogr",
    )

    if not analysis_layer.isValid():
        raise ValueError(
            f"Failed to load BoS analysis site: "
            f"{analysis_layer_path}"
        )

    if (
        analysis_layer.geometryType()
        != QgsWkbTypes.PolygonGeometry
    ):
        raise ValueError(
            "BoS land-cover analysis requires polygons."
        )

    clipped_raster_path = os.path.join(
        temp_path,
        "bos_landcover_clipped.tif",
    )

    processing.run(
        "gdal:cliprasterbymasklayer",
        {
            "INPUT": landcover_path,
            "MASK": analysis_layer,
            "SOURCE_CRS": None,
            "TARGET_CRS": None,
            "TARGET_EXTENT": None,
            "NODATA": 0,
            "ALPHA_BAND": False,
            "CROP_TO_CUTLINE": True,
            "KEEP_RESOLUTION": True,
            "SET_RESOLUTION": False,
            "X_RESOLUTION": None,
            "Y_RESOLUTION": None,
            "MULTITHREADING": True,
            "OPTIONS": "",
            "DATA_TYPE": 0,
            "EXTRA": (
                "-wo CUTLINE_ALL_TOUCHED=TRUE"
            ),
            "OUTPUT": clipped_raster_path,
        },
    )

    pixel_polygon_path = os.path.join(
        temp_path,
        "bos_landcover_pixels.shp",
    )

    processing.run(
        "native:pixelstopolygons",
        {
            "INPUT_RASTER": clipped_raster_path,
            "RASTER_BAND": 1,
            "FIELD_NAME": "VALUE",
            "OUTPUT": pixel_polygon_path,
        },
    )

    site_landcover_path = os.path.join(
        temp_path,
        "bos_landcover_site.shp",
    )

    processing.run(
        "native:clip",
        {
            "INPUT": pixel_polygon_path,
            "OVERLAY": analysis_layer,
            "OUTPUT": site_landcover_path,
        },
    )

    processing.run(
        "native:createspatialindex",
        {
            "INPUT": site_landcover_path,
        },
    )

    site_landcover = QgsVectorLayer(
        site_landcover_path,
        "BoS land-cover base",
        "ogr",
    )

    if not site_landcover.isValid():
        raise RuntimeError(
            f"Failed to load BoS land-cover polygons: "
            f"{site_landcover_path}"
        )

    if "VALUE" not in {
        field.name()
        for field in site_landcover.fields()
    }:
        raise RuntimeError(
            "BoS land-cover polygons have no VALUE field."
        )

    print(
        "BoS base land-cover prepared: "
        f"{site_landcover.featureCount()} features."
    )

    return {
        "raster_path": clipped_raster_path,
        "pixel_polygon_path": pixel_polygon_path,
        "landcover_path": site_landcover_path,
        "feature_count": site_landcover.featureCount(),
    }

def prepare_bos_wetland(
    analysis_layer_path,
    landcover_layer_path,
    data_path,
    temp_path,
    bos_settings,
):
    """
    Combine wetland land-cover classes with the separate wet-soil
    dataset and dissolve overlaps into one coverage layer.
    """

    landcover = QgsVectorLayer(
        landcover_layer_path,
        "BoS land cover",
        "ogr",
    )

    if not landcover.isValid():
        raise ValueError(
            f"Failed to load BoS land-cover layer: "
            f"{landcover_layer_path}"
        )

    wetland_values = bos_settings[
        "class_groups"
    ]["Wetland"]

    value_list = ", ".join(
        str(value)
        for value in wetland_values
    )

    wetland_expression = (
        f"\"VALUE\" IN ({value_list})"
    )

    landcover_wetland_path = os.path.join(
        temp_path,
        "bos_landcover_wetland.shp",
    )

    processing.run(
        "native:extractbyexpression",
        {
            "INPUT": landcover,
            "EXPRESSION": wetland_expression,
            "OUTPUT": landcover_wetland_path,
        },
    )

    wet_soil_source_path = os.path.join(
        data_path,
        bos_settings["wet_soil_layer"],
    )

    if not os.path.isfile(wet_soil_source_path):
        raise FileNotFoundError(
            f"Configured wet-soil layer does not exist: "
            f"{wet_soil_source_path}"
        )

    wet_soil_source = QgsVectorLayer(
        wet_soil_source_path,
        "Wet soil",
        "ogr",
    )

    if not wet_soil_source.isValid():
        raise ValueError(
            f"Failed to load wet-soil layer: "
            f"{wet_soil_source_path}"
        )

    analysis_layer = QgsVectorLayer(
        analysis_layer_path,
        "BoS analysis site",
        "ogr",
    )

    if not analysis_layer.isValid():
        raise ValueError(
            f"Failed to load BoS analysis site: "
            f"{analysis_layer_path}"
        )

    wet_soil_site_path = os.path.join(
        temp_path,
        "bos_wet_soil_site.shp",
    )

    processing.run(
        "native:clip",
        {
            "INPUT": wet_soil_source,
            "OVERLAY": analysis_layer,
            "OUTPUT": wet_soil_site_path,
        },
    )

    merged_wetland_path = os.path.join(
        temp_path,
        "bos_wetland_merged.shp",
    )

    processing.run(
        "native:mergevectorlayers",
        {
            "LAYERS": [
                landcover_wetland_path,
                wet_soil_site_path,
            ],
            "OUTPUT": merged_wetland_path,
        },
    )

    dissolved_wetland_path = os.path.join(
        temp_path,
        "bos_wetland.shp",
    )

    processing.run(
        "native:dissolve",
        {
            "INPUT": merged_wetland_path,
            "FIELD": [],
            "OUTPUT": dissolved_wetland_path,
        },
    )

    processing.run(
        "native:createspatialindex",
        {
            "INPUT": dissolved_wetland_path,
        },
    )

    wetland_layer = QgsVectorLayer(
        dissolved_wetland_path,
        "BoS wetland",
        "ogr",
    )

    if not wetland_layer.isValid():
        raise RuntimeError(
            f"Failed to load BoS wetland layer: "
            f"{dissolved_wetland_path}"
        )

    wetland_area_ha = (
        calculate_vector_area_hectares(
            dissolved_wetland_path
        )
    )

    print(
        "BoS wetland coverage prepared: "
        f"{wetland_area_ha:.2f} ha."
    )

    return {
        "status": (
            "available"
            if wetland_area_ha > 0
            else "empty"
        ),
        "output_path": dissolved_wetland_path,
        "area_ha": wetland_area_ha,
        "landcover_wetland_path": (
            landcover_wetland_path
        ),
        "wet_soil_path": wet_soil_site_path,
    }

def clip_bos_vector_source(
    analysis_layer_path,
    data_path,
    temp_path,
    source_filename,
    display_name,
    output_filename,
):
    """
    Clip one configured BoS vector source to the analysis site.
    """

    source_path = os.path.join(
        data_path,
        source_filename,
    )

    if not os.path.isfile(source_path):
        raise FileNotFoundError(
            f"Configured BoS source does not exist: "
            f"{source_path}"
        )

    source = QgsVectorLayer(
        source_path,
        display_name,
        "ogr",
    )

    if not source.isValid():
        raise ValueError(
            f"Failed to load BoS source: "
            f"{source_path}"
        )

    if source.geometryType() != QgsWkbTypes.PolygonGeometry:
        raise ValueError(
            f"BoS source must contain polygons: "
            f"{display_name}"
        )

    analysis_layer = QgsVectorLayer(
        analysis_layer_path,
        "BoS analysis site",
        "ogr",
    )

    if not analysis_layer.isValid():
        raise ValueError(
            f"Failed to load BoS analysis site: "
            f"{analysis_layer_path}"
        )

    output_path = os.path.join(
        temp_path,
        output_filename,
    )

    processing.run(
        "native:clip",
        {
            "INPUT": source,
            "OVERLAY": analysis_layer,
            "OUTPUT": output_path,
        },
    )

    processing.run(
        "native:createspatialindex",
        {
            "INPUT": output_path,
        },
    )

    clipped_layer = QgsVectorLayer(
        output_path,
        display_name,
        "ogr",
    )

    if not clipped_layer.isValid():
        raise RuntimeError(
            f"Failed to load clipped BoS source: "
            f"{output_path}"
        )

    area_ha = calculate_vector_area_hectares(
        output_path
    )

    print(
        f"BoS {display_name.lower()} coverage prepared: "
        f"{area_ha:.2f} ha."
    )

    return {
        "status": (
            "available"
            if area_ha > 0
            else "empty"
        ),
        "output_path": output_path,
        "area_ha": area_ha,
        "feature_count": clipped_layer.featureCount(),
    }


def prepare_bos_override_layers(
    analysis_layer_path,
    data_path,
    temp_path,
    bos_settings,
):
    """
    Prepare rocky-terrain and peat-quarry BoS overrides.
    """

    rocky_result = clip_bos_vector_source(
        analysis_layer_path=analysis_layer_path,
        data_path=data_path,
        temp_path=temp_path,
        source_filename=bos_settings[
            "rocky_terrain_layer"
        ],
        display_name="Rocky terrain",
        output_filename="bos_rocky_terrain.shp",
    )

    peat_result = clip_bos_vector_source(
        analysis_layer_path=analysis_layer_path,
        data_path=data_path,
        temp_path=temp_path,
        source_filename=bos_settings[
            "peat_quarry_layer"
        ],
        display_name="Peat quarry",
        output_filename="bos_peat_quarry.shp",
    )

    return {
        "rocky_terrain": rocky_result,
        "peat_quarry": peat_result,
    }

def fix_bos_geometries(
    input_path,
    output_path,
):
    """
    Repair a local BoS layer before overlay operations.
    """

    processing.run(
        "native:fixgeometries",
        {
            "INPUT": input_path,
            "METHOD": 1,
            "OUTPUT": output_path,
        },
    )

    return output_path


def run_bos_difference(
    input_path,
    overlay_path,
    output_path,
):
    """
    Subtract one prepared BoS layer from another.
    """

    processing.run(
        "native:difference",
        {
            "INPUT": input_path,
            "OVERLAY": overlay_path,
            "OUTPUT": output_path,
        },
    )

    return output_path

def create_non_overlapping_bos_layers(
    landcover_path,
    wetland_path,
    rocky_terrain_path,
    peat_quarry_path,
    temp_path,
):
    """
    Create mutually exclusive BoS coverage layers.

    Priority:
        1. Peat quarry
        2. Wetland
        3. Rocky terrain
        4. Remaining base land cover
    """

    fixed_landcover_path = os.path.join(
        temp_path,
        "bos_fixed_landcover.shp",
    )

    fixed_wetland_path = os.path.join(
        temp_path,
        "bos_fixed_wetland.shp",
    )

    fixed_rocky_path = os.path.join(
        temp_path,
        "bos_fixed_rocky.shp",
    )

    fixed_peat_path = os.path.join(
        temp_path,
        "bos_fixed_peat.shp",
    )

    fix_bos_geometries(
        landcover_path,
        fixed_landcover_path,
    )

    fix_bos_geometries(
        wetland_path,
        fixed_wetland_path,
    )

    fix_bos_geometries(
        rocky_terrain_path,
        fixed_rocky_path,
    )

    fix_bos_geometries(
        peat_quarry_path,
        fixed_peat_path,
    )

    # ---------------------------------------------------------
    # Highest priority: peat quarry
    # ---------------------------------------------------------

    final_peat_path = os.path.join(
        temp_path,
        "bos_final_peat_quarry.shp",
    )

    processing.run(
        "native:dissolve",
        {
            "INPUT": fixed_peat_path,
            "FIELD": [],
            "OUTPUT": final_peat_path,
        },
    )

    # ---------------------------------------------------------
    # Wetland minus peat quarry
    # ---------------------------------------------------------

    final_wetland_path = os.path.join(
        temp_path,
        "bos_final_wetland.shp",
    )

    run_bos_difference(
        input_path=fixed_wetland_path,
        overlay_path=final_peat_path,
        output_path=final_wetland_path,
    )

    # ---------------------------------------------------------
    # Rocky terrain minus peat and wetland
    # ---------------------------------------------------------

    rocky_without_peat_path = os.path.join(
        temp_path,
        "bos_rocky_without_peat.shp",
    )

    run_bos_difference(
        input_path=fixed_rocky_path,
        overlay_path=final_peat_path,
        output_path=rocky_without_peat_path,
    )

    final_rocky_path = os.path.join(
        temp_path,
        "bos_final_rocky.shp",
    )

    run_bos_difference(
        input_path=rocky_without_peat_path,
        overlay_path=final_wetland_path,
        output_path=final_rocky_path,
    )

    # ---------------------------------------------------------
    # Base land cover minus all override layers
    # ---------------------------------------------------------

    landcover_without_peat_path = os.path.join(
        temp_path,
        "bos_landcover_without_peat.shp",
    )

    run_bos_difference(
        input_path=fixed_landcover_path,
        overlay_path=final_peat_path,
        output_path=landcover_without_peat_path,
    )

    landcover_without_wetland_path = os.path.join(
        temp_path,
        "bos_landcover_without_wetland.shp",
    )

    run_bos_difference(
        input_path=landcover_without_peat_path,
        overlay_path=final_wetland_path,
        output_path=landcover_without_wetland_path,
    )

    final_landcover_path = os.path.join(
        temp_path,
        "bos_final_landcover.shp",
    )

    run_bos_difference(
        input_path=landcover_without_wetland_path,
        overlay_path=final_rocky_path,
        output_path=final_landcover_path,
    )

    final_paths = {
        "Peat quarry": final_peat_path,
        "Wetland": final_wetland_path,
        "Rocky terrain": final_rocky_path,
        "Base land cover": final_landcover_path,
    }

    areas_ha = {}

    for layer_name, layer_path in final_paths.items():
        processing.run(
            "native:createspatialindex",
            {
                "INPUT": layer_path,
            },
        )

        areas_ha[layer_name] = (
            calculate_vector_area_hectares(
                layer_path
            )
        )

        print(
            f"BoS priority layer — {layer_name}: "
            f"{areas_ha[layer_name]:.2f} ha."
        )

    return {
        "layers": final_paths,
        "areas_ha": areas_ha,
        "total_area_ha": sum(
            areas_ha.values()
        ),
    }

def summarise_bos_coverage(
    analysis_layer_path,
    bos_priority_result,
    bos_settings,
):
    """
    Calculate final BoS hectares and percentages.

    Percentages use the complete estate/custom-polygon area.
    Unknown land-cover classes are retained as Other land cover.
    """

    analysis_area_ha = (
        calculate_vector_area_hectares(
            analysis_layer_path
        )
    )

    areas_ha = {
        "Open field": 0.0,
        "Peat quarry": bos_priority_result[
            "areas_ha"
        ]["Peat quarry"],
        "Forest": 0.0,
        "Wetland": bos_priority_result[
            "areas_ha"
        ]["Wetland"],
        "Rocky terrain": bos_priority_result[
            "areas_ha"
        ]["Rocky terrain"],
        "Other land cover": 0.0,
        "No land-cover data": 0.0,
    }

    base_landcover_path = (
        bos_priority_result["layers"][
            "Base land cover"
        ]
    )

    base_landcover = QgsVectorLayer(
        base_landcover_path,
        "BoS base land cover",
        "ogr",
    )

    if not base_landcover.isValid():
        raise ValueError(
            f"Failed to load final BoS land cover: "
            f"{base_landcover_path}"
        )

    field_names = {
        field.name()
        for field in base_landcover.fields()
    }

    if "VALUE" not in field_names:
        raise ValueError(
            "Final BoS land cover has no VALUE field."
        )

    open_field_values = set(
        bos_settings["class_groups"][
            "Open field"
        ]
    )

    forest_values = set(
        bos_settings["class_groups"][
            "Forest"
        ]
    )

    for feature in base_landcover.getFeatures():
        geometry = feature.geometry()

        if geometry.isEmpty():
            continue

        area_ha = geometry.area() / 10000

        try:
            landcover_value = int(
                float(feature["VALUE"])
            )
        except (TypeError, ValueError):
            areas_ha[
                "Other land cover"
            ] += area_ha
            continue

        if landcover_value in open_field_values:
            areas_ha["Open field"] += area_ha

        elif landcover_value in forest_values:
            areas_ha["Forest"] += area_ha

        else:
            areas_ha[
                "Other land cover"
            ] += area_ha

    classified_area_ha = sum(
        areas_ha.values()
    )

    uncovered_area_ha = (
        analysis_area_ha
        - classified_area_ha
    )

    # Ignore tiny differences caused by overlay precision.
    if uncovered_area_ha > 0.000001:
        areas_ha[
            "No land-cover data"
        ] = uncovered_area_ha

    elif uncovered_area_ha < -0.000001:
        print(
            "Warning: BoS classified area exceeds the "
            f"analysis area by "
            f"{abs(uncovered_area_ha):.6f} ha."
        )

    percentages = {}

    for group_name, area_ha in areas_ha.items():
        if analysis_area_ha > 0:
            percentage = (
                area_ha
                / analysis_area_ha
                * 100
            )
        else:
            percentage = 0.0

        percentages[group_name] = percentage

        print(
            f"BoS {group_name}: "
            f"{percentage:.2f}% "
            f"({area_ha:.3f} ha)"
        )

    return {
        "status": "available",
        "analysis_area_ha": analysis_area_ha,
        "areas_ha": areas_ha,
        "percentages": percentages,
    }

def create_bos_coverage_layer(
    analysis_layer_path,
    bos_priority_result,
    bos_settings,
    folder_path,
    temp_path,
):
    """
    Combine the mutually exclusive BoS layers into one
    classified deliverable.

    The final layer contains:
        BOS_GROUP
        AREA_HA
        PERCENT

    Any part of the analysis area not covered by the configured
    BoS datasets is classified as "No land-cover data".
    """

    priority_layers = bos_priority_result["layers"]

    site_area_ha = calculate_vector_area_hectares(
        analysis_layer_path
    )

    if site_area_ha <= 0:
        raise ValueError(
            "Cannot create BoS coverage for an empty analysis area."
        )

    labelled_paths = []

    # ---------------------------------------------------------
    # Classify the remaining base land-cover polygons
    # ---------------------------------------------------------

    base_landcover_path = priority_layers[
        "Base land cover"
    ]

    base_layer = QgsVectorLayer(
        base_landcover_path,
        "BoS base land cover",
        "ogr",
    )

    if not base_layer.isValid():
        raise ValueError(
            f"Failed to load final BoS land cover: "
            f"{base_landcover_path}"
        )

    class_groups = bos_settings.get(
        "class_groups",
        {},
    )

    open_field_values = class_groups.get(
        "Open field",
        [],
    )

    forest_values = class_groups.get(
        "Forest",
        [],
    )

    open_field_text = ", ".join(
        str(value)
        for value in open_field_values
    )

    forest_text = ", ".join(
        str(value)
        for value in forest_values
    )

    classification_parts = ["CASE"]

    if open_field_text:
        classification_parts.append(
            f'WHEN "VALUE" IN ({open_field_text}) '
            f"THEN 'Open field'"
        )

    if forest_text:
        classification_parts.append(
            f'WHEN "VALUE" IN ({forest_text}) '
            f"THEN 'Forest'"
        )

    classification_parts.extend(
        [
            "ELSE 'Other land cover'",
            "END",
        ]
    )

    classification_expression = " ".join(
        classification_parts
    )

    labelled_base_path = os.path.join(
        temp_path,
        "bos_labelled_landcover.shp",
    )

    processing.run(
        "native:fieldcalculator",
        {
            "INPUT": base_landcover_path,
            "FIELD_NAME": "BOS_GROUP",
            "FIELD_TYPE": 2,
            "FIELD_LENGTH": 40,
            "FIELD_PRECISION": 0,
            "FORMULA": classification_expression,
            "OUTPUT": labelled_base_path,
        },
    )

    labelled_base = QgsVectorLayer(
        labelled_base_path,
        "Classified base land cover",
        "ogr",
    )

    if (
        labelled_base.isValid()
        and labelled_base.featureCount() > 0
    ):
        labelled_paths.append(
            labelled_base_path
        )

    # ---------------------------------------------------------
    # Label the three override layers
    # ---------------------------------------------------------

    override_groups = (
        "Peat quarry",
        "Wetland",
        "Rocky terrain",
    )

    for group_name in override_groups:

        source_path = priority_layers[
            group_name
        ]

        source_layer = QgsVectorLayer(
            source_path,
            group_name,
            "ogr",
        )

        if not source_layer.isValid():
            raise ValueError(
                f"Failed to load BoS priority layer: "
                f"{source_path}"
            )

        if source_layer.featureCount() == 0:
            continue

        safe_filename = (
            group_name.lower()
            .replace(" ", "_")
        )

        labelled_path = os.path.join(
            temp_path,
            f"bos_labelled_{safe_filename}.shp",
        )

        processing.run(
            "native:fieldcalculator",
            {
                "INPUT": source_path,
                "FIELD_NAME": "BOS_GROUP",
                "FIELD_TYPE": 2,
                "FIELD_LENGTH": 40,
                "FIELD_PRECISION": 0,
                "FORMULA": f"'{group_name}'",
                "OUTPUT": labelled_path,
            },
        )

        labelled_paths.append(
            labelled_path
        )

    # ---------------------------------------------------------
    # Find portions of the site with no BoS coverage
    # ---------------------------------------------------------

    no_data_path = os.path.join(
        temp_path,
        "bos_no_landcover_data.shp",
    )

    if labelled_paths:

        coverage_merged_path = os.path.join(
            temp_path,
            "bos_coverage_for_gap_check.shp",
        )

        processing.run(
            "native:mergevectorlayers",
            {
                "LAYERS": labelled_paths,
                "CRS": None,
                "OUTPUT": coverage_merged_path,
            },
        )

        coverage_mask_path = os.path.join(
            temp_path,
            "bos_coverage_mask.shp",
        )

        processing.run(
            "native:dissolve",
            {
                "INPUT": coverage_merged_path,
                "FIELD": [],
                "OUTPUT": coverage_mask_path,
            },
        )

        no_data_geometry_path = os.path.join(
            temp_path,
            "bos_no_data_geometry.shp",
        )

        run_bos_difference(
            input_path=analysis_layer_path,
            overlay_path=coverage_mask_path,
            output_path=no_data_geometry_path,
        )

    else:
        no_data_geometry_path = os.path.join(
            temp_path,
            "bos_no_data_geometry.shp",
        )

        processing.run(
            "native:savefeatures",
            {
                "INPUT": analysis_layer_path,
                "OUTPUT": no_data_geometry_path,
            },
        )

    no_data_layer = QgsVectorLayer(
        no_data_geometry_path,
        "No BoS land-cover data",
        "ogr",
    )

    if (
        no_data_layer.isValid()
        and no_data_layer.featureCount() > 0
    ):
        processing.run(
            "native:fieldcalculator",
            {
                "INPUT": no_data_geometry_path,
                "FIELD_NAME": "BOS_GROUP",
                "FIELD_TYPE": 2,
                "FIELD_LENGTH": 40,
                "FIELD_PRECISION": 0,
                "FORMULA": "'No land-cover data'",
                "OUTPUT": no_data_path,
            },
        )

        labelled_paths.append(
            no_data_path
        )

    if not labelled_paths:
        raise RuntimeError(
            "No BoS coverage geometries were created."
        )

    # ---------------------------------------------------------
    # Merge and dissolve by final BoS category
    # ---------------------------------------------------------

    combined_path = os.path.join(
        temp_path,
        "bos_coverage_combined.shp",
    )

    processing.run(
        "native:mergevectorlayers",
        {
            "LAYERS": labelled_paths,
            "CRS": None,
            "OUTPUT": combined_path,
        },
    )

    # Merging categorized coverage can create invalid polygon
    # rings or small topology errors. Repair the complete
    # combined layer before dissolving by category.
    fixed_combined_path = os.path.join(
        temp_path,
        "bos_coverage_combined_fixed.shp",
    )

    fix_bos_geometries(
        input_path=combined_path,
        output_path=fixed_combined_path,
    )

    dissolved_path = os.path.join(
        temp_path,
        "bos_coverage_dissolved.shp",
    )

    processing.run(
        "native:dissolve",
        {
            "INPUT": fixed_combined_path,
            "FIELD": ["BOS_GROUP"],
            "OUTPUT": dissolved_path,
        },
    )

    # ---------------------------------------------------------
    # Calculate area and percentage fields
    # ---------------------------------------------------------

    area_path = os.path.join(
        temp_path,
        "bos_coverage_with_area.shp",
    )

    processing.run(
        "native:fieldcalculator",
        {
            "INPUT": dissolved_path,
            "FIELD_NAME": "AREA_HA",
            "FIELD_TYPE": 0,
            "FIELD_LENGTH": 20,
            "FIELD_PRECISION": 4,
            "FORMULA": "$area / 10000",
            "OUTPUT": area_path,
        },
    )

    final_path = os.path.join(
        folder_path,
        "BoS_coverage.shp",
    )

    percentage_formula = (
        f'($area / 10000) / {site_area_ha} * 100'
    )

    processing.run(
        "native:fieldcalculator",
        {
            "INPUT": area_path,
            "FIELD_NAME": "PERCENT",
            "FIELD_TYPE": 0,
            "FIELD_LENGTH": 20,
            "FIELD_PRECISION": 2,
            "FORMULA": percentage_formula,
            "OUTPUT": final_path,
        },
    )

    processing.run(
        "native:createspatialindex",
        {
            "INPUT": final_path,
        },
    )

    final_layer = QgsVectorLayer(
        final_path,
        "BoS coverage",
        "ogr",
    )

    if not final_layer.isValid():
        raise RuntimeError(
            f"Failed to create final BoS coverage: "
            f"{final_path}"
        )

    print(
        f"Final BoS coverage saved: "
        f"{final_layer.featureCount()} categories — "
        f"{final_path}"
    )

    return final_path