import os

import numpy as np
import processing

from osgeo import gdal

from qgis.core import (
    QgsVectorLayer,
)


gdal.UseExceptions()


def find_soil_layer_output(
    country_layer_outputs,
    layer_name,
):
    """
    Find the already prepared local soil-type layer.
    """

    for layer_output in country_layer_outputs:

        definition = layer_output.get(
            "definition",
            {},
        )

        if definition.get("name") == layer_name:
            return layer_output

    return None


def read_clipped_depth_values(
    raster_path,
    mask_path,
    output_path,
    configured_nodata,
    band_number,
):
    """
    Clip a small portion of the soil-depth raster and return
    its valid values.

    The national raster is never loaded into memory.
    """

    processing.run(
        "gdal:cliprasterbymasklayer",
        {
            "INPUT": raster_path,
            "MASK": mask_path,
            "SOURCE_CRS": None,
            "TARGET_CRS": None,
            "TARGET_EXTENT": None,
            "NODATA": configured_nodata,
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
            "OUTPUT": output_path,
        },
    )

    dataset = gdal.Open(
        output_path,
        gdal.GA_ReadOnly,
    )

    if dataset is None:
        raise RuntimeError(
            f"Failed to open clipped soil-depth raster: "
            f"{output_path}"
        )

    band = dataset.GetRasterBand(
        band_number
    )

    if band is None:
        dataset = None

        raise ValueError(
            f"Soil-depth raster has no band "
            f"{band_number}."
        )

    values = band.ReadAsArray()

    raster_nodata = band.GetNoDataValue()

    band = None
    dataset = None

    if values is None:
        return np.array(
            [],
            dtype=float,
        )

    values = values.astype(
        float,
        copy=False,
    )

    valid_mask = np.isfinite(values)

    if raster_nodata is not None:

        if np.isnan(raster_nodata):
            valid_mask &= ~np.isnan(values)

        else:
            valid_mask &= (
                values != raster_nodata
            )

    if configured_nodata is not None:
        valid_mask &= (
            values != configured_nodata
        )

    return values[valid_mask]


def analyse_soil_depth_by_type(
    analysis_layer_path,
    country_layer_outputs,
    data_path,
    temp_path,
    settings,
):
    """
    Calculate soil-depth ranges for every soil type inside
    the exact estate/custom polygon.

    Return report data only. No permanent soil-depth layer is
    created.
    """

    if not settings:
        print(
            "Soil-depth analysis skipped: "
            "no country configuration."
        )

        return {
            "status": "unavailable",
            "results": [],
        }

    analysis_layer = QgsVectorLayer(
        analysis_layer_path,
        "Soil-depth analysis site",
        "ogr",
    )

    if not analysis_layer.isValid():
        raise ValueError(
            f"Failed to load soil-depth analysis site: "
            f"{analysis_layer_path}"
        )

    if not analysis_layer.crs().isValid():
        raise ValueError(
            "The soil-depth analysis site has no valid CRS."
        )

    soil_layer_name = settings[
        "soil_layer_name"
    ]

    soil_layer_output = find_soil_layer_output(
        country_layer_outputs=country_layer_outputs,
        layer_name=soil_layer_name,
    )

    if soil_layer_output is None:
        print(
            "Soil-depth analysis unavailable: "
            f"country layer not found — "
            f"{soil_layer_name}."
        )

        return {
            "status": "unavailable",
            "results": [],
        }

    soil_layer_path = soil_layer_output.get(
        "output_path"
    )

    if (
        not soil_layer_path
        or not os.path.isfile(soil_layer_path)
    ):
        print(
            "Soil-depth analysis unavailable: "
            "the local soil-type layer has no output."
        )

        return {
            "status": "unavailable",
            "results": [],
        }

    soil_layer = QgsVectorLayer(
        soil_layer_path,
        soil_layer_name,
        "ogr",
    )

    if not soil_layer.isValid():
        raise ValueError(
            f"Failed to load soil-type layer: "
            f"{soil_layer_path}"
        )

    soil_type_field = settings[
        "soil_type_field"
    ]

    if (
        soil_layer.fields().indexOf(
            soil_type_field
        )
        == -1
    ):
        raise ValueError(
            f"Soil-type layer has no field named "
            f"{soil_type_field!r}."
        )

    raster_path = os.path.join(
        data_path,
        settings["raster_source"],
    )

    if not os.path.isfile(raster_path):
        raise FileNotFoundError(
            f"Soil-depth raster does not exist: "
            f"{raster_path}"
        )

    # ---------------------------------------------------------
    # Clip soil types to the exact analysis polygon
    # ---------------------------------------------------------

    clipped_soil_path = os.path.join(
        temp_path,
        "soil_types_inside_site.shp",
    )

    processing.run(
        "native:clip",
        {
            "INPUT": soil_layer,
            "OVERLAY": analysis_layer,
            "OUTPUT": clipped_soil_path,
        },
    )

    clipped_soil_layer = QgsVectorLayer(
        clipped_soil_path,
        "Soil types inside site",
        "ogr",
    )

    if not clipped_soil_layer.isValid():
        raise RuntimeError(
            "Failed to clip the soil-type layer "
            "to the analysis site."
        )

    if clipped_soil_layer.featureCount() == 0:
        print(
            "Soil-depth analysis: no soil-type polygons "
            "intersect the analysis site."
        )

        return {
            "status": "no_features",
            "results": [],
        }

    soil_type_index = (
        clipped_soil_layer.fields().indexOf(
            soil_type_field
        )
    )

    soil_types = sorted(
        value
        for value in clipped_soil_layer.uniqueValues(
            soil_type_index
        )
        if value is not None
        and str(value).strip()
    )

    if not soil_types:
        print(
            "Soil-depth analysis: no valid soil-type "
            "values were found."
        )

        return {
            "status": "no_features",
            "results": [],
        }

    configured_nodata = settings.get(
        "nodata_value"
    )

    band_number = int(
        settings.get(
            "band",
            1,
        )
    )

    metre_multiplier = float(
        settings.get(
            "metre_multiplier",
            1.0,
        )
    )

    results = []

    # ---------------------------------------------------------
    # Calculate one depth range per soil type
    # ---------------------------------------------------------

    for number, soil_type in enumerate(
        soil_types,
        start=1,
    ):

        selected_soil_path = os.path.join(
            temp_path,
            f"soil_type_{number}_selected.shp",
        )

        processing.run(
            "native:extractbyattribute",
            {
                "INPUT": clipped_soil_layer,
                "FIELD": soil_type_field,
                "OPERATOR": 0,
                "VALUE": soil_type,
                "OUTPUT": selected_soil_path,
            },
        )

        dissolved_soil_path = os.path.join(
            temp_path,
            f"soil_type_{number}_dissolved.shp",
        )

        processing.run(
            "native:dissolve",
            {
                "INPUT": selected_soil_path,
                "FIELD": [],
                "OUTPUT": dissolved_soil_path,
            },
        )

        clipped_raster_path = os.path.join(
            temp_path,
            f"soil_depth_type_{number}.tif",
        )

        values = read_clipped_depth_values(
            raster_path=raster_path,
            mask_path=dissolved_soil_path,
            output_path=clipped_raster_path,
            configured_nodata=(
                configured_nodata
            ),
            band_number=band_number,
        )

        soil_type_text = str(
            soil_type
        )

        if values.size == 0:

            print(
                f"Soil depth — {soil_type_text}: "
                "no valid raster cells."
            )

            results.append(
                {
                    "soil_type": soil_type_text,
                    "status": "no_data",
                    "minimum_m": None,
                    "maximum_m": None,
                    "minimum_cm": None,
                    "maximum_cm": None,
                    "pixel_count": 0,
                }
            )

            continue

        values_m = (
            values
            * metre_multiplier
        )

        minimum_m = float(
            np.min(values_m)
        )

        maximum_m = float(
            np.max(values_m)
        )

        result = {
            "soil_type": soil_type_text,
            "status": "available",
            "minimum_m": minimum_m,
            "maximum_m": maximum_m,
            "minimum_cm": (
                minimum_m * 100.0
            ),
            "maximum_cm": (
                maximum_m * 100.0
            ),
            "pixel_count": int(
                values_m.size
            ),
        }

        results.append(result)

        print(
            f"Soil depth — {soil_type_text}: "
            f"{minimum_m:.0f}–{maximum_m:.0f} m "
            f"({minimum_m * 100:.0f}–"
            f"{maximum_m * 100:.0f} cm)."
        )

    available_results = [
        result
        for result in results
        if result["status"] == "available"
    ]

    if not available_results:
        status = "no_data"

    else:
        status = "available"

    return {
        "status": status,
        "results": results,
        "raster_source": raster_path,
        "source_unit": settings.get(
            "source_unit",
            "m",
        ),
    }