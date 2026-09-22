import math
import os

import numpy as np
import processing

from osgeo import gdal

from qgis.core import (
    QgsCoordinateTransform,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsWkbTypes,
)


def calculate_average_wind_speed(
    site_layer_path,
    data_path,
    temp_path,
    wind_settings,
):
    """
    Calculate the mean wind-speed value covering the analysis site.

    This preserves Anna's feature-mean approach while keeping the
    country-specific source and field names outside this module.

    Returns
    -------
    dict
        Wind-speed result and its source information.
    """

    unavailable_result = {
        "value": None,
        "unit": "m/s",
        "height_m": None,
        "source": None,
        "status": "missing",
        "output_path": None,
    }

    if not wind_settings:
        print(
            "Average wind speed unavailable: "
            "no country data source configured."
        )
        return unavailable_result

    source_path = os.path.join(
        data_path,
        wind_settings["source"],
    )

    if not os.path.isfile(source_path):
        raise FileNotFoundError(
            f"Configured wind-speed layer does not exist: "
            f"{source_path}"
        )

    source = QgsVectorLayer(
        source_path,
        "Wind-speed source",
        "ogr",
    )

    if not source.isValid():
        raise ValueError(
            f"Failed to load wind-speed layer: "
            f"{source_path}"
        )

    site = QgsVectorLayer(
        site_layer_path,
        "Analysis site",
        "ogr",
    )

    if not site.isValid():
        raise ValueError(
            f"Failed to load analysis site: "
            f"{site_layer_path}"
        )

    if site.geometryType() != QgsWkbTypes.PolygonGeometry:
        raise ValueError(
            "Wind-speed analysis requires a polygon site."
        )

    value_field = wind_settings["value_field"]

    field_names = {
        field.name()
        for field in source.fields()
    }

    if value_field not in field_names:
        raise ValueError(
            f"Wind-speed field '{value_field}' does not exist "
            f"in {source_path}"
        )

    output_path = os.path.join(
        temp_path,
        "wind_map_clipped.shp",
    )

    processing.run(
        "native:clip",
        {
            "INPUT": source,
            "OVERLAY": site,
            "OUTPUT": output_path,
        },
    )

    clipped = QgsVectorLayer(
        output_path,
        "Wind speed at analysis site",
        "ogr",
    )

    if not clipped.isValid():
        raise RuntimeError(
            f"Failed to load clipped wind-speed layer: "
            f"{output_path}"
        )

    values = []

    for feature in clipped.getFeatures():
        value = feature[value_field]

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            continue

        values.append(numeric_value)

    if not values:
        print(
            "Average wind speed unavailable: "
            "no local wind-speed values."
        )

        unavailable_result["height_m"] = (
            wind_settings["measurement_height_m"]
        )
        unavailable_result["source"] = (
            wind_settings["source_name"]
        )
        unavailable_result["output_path"] = output_path

        return unavailable_result

    average_value = sum(values) / len(values)

    result = {
        "value": average_value,
        "unit": "m/s",
        "height_m": wind_settings["measurement_height_m"],
        "source": wind_settings["source_name"],
        "status": "available",
        "output_path": output_path,
    }

    print(
        f"Average wind speed at "
        f"{result['height_m']} m: "
        f"{result['value']:.2f} {result['unit']}"
    )

    return result

def read_site_load_values(
    site_layer_path,
    field_name,
    result_name,
    unit,
    source_name,
):
    """
    Read unique numeric design-load values from the site layer.

    This supports country-specific fields such as WINDLOAD
    and SNOWLOAD without hard-coding their names.
    """

    result = {
        "name": result_name,
        "values": [],
        "unit": unit,
        "source": source_name,
        "field_name": field_name,
        "status": "missing",
    }

    if not field_name:
        print(
            f"{result_name} unavailable: "
            "no country field configured."
        )
        return result

    site = QgsVectorLayer(
        site_layer_path,
        "Analysis site",
        "ogr",
    )

    if not site.isValid():
        raise ValueError(
            f"Failed to load analysis site: "
            f"{site_layer_path}"
        )

    field_names = {
        field.name()
        for field in site.fields()
    }

    if field_name not in field_names:
        print(
            f"{result_name} unavailable: "
            f"field '{field_name}' does not exist."
        )
        return result

    values = []

    for feature in site.getFeatures():
        raw_value = feature[field_name]

        try:
            numeric_value = float(raw_value)
        except (TypeError, ValueError):
            continue

        if not math.isfinite(numeric_value):
            continue

        if numeric_value not in values:
            values.append(numeric_value)

    if not values:
        print(
            f"{result_name} unavailable: "
            "no valid values found."
        )
        return result

    result["values"] = values
    result["status"] = "available"

    for value in values:
        print(
            f"{result_name}: "
            f"{value:.2f} {unit} "
            f"(source: {source_name})"
        )

    return result

def calculate_site_raster_mean(
    site_layer_path,
    data_path,
    temp_path,
    raster_settings,
    output_name,
):
    """
    Calculate the mean raster value inside the analysis site.

    If the estate is too small to capture a raster cell during
    clipping, sample the source cell containing its centroid.
    """

    result = {
        "name": None,
        "value": None,
        "unit": None,
        "source": None,
        "status": "missing",
        "output_path": None,
        "precision": 2,
        "secondary_unit": None,
        "secondary_multiplier": None,
        "secondary_precision": 2,
        "sampling_method": None,
    }

    if not raster_settings:
        print(
            "Meteorological raster unavailable: "
            "no source configured."
        )
        return result

    result["name"] = raster_settings["name"]
    result["unit"] = raster_settings["unit"]
    result["source"] = raster_settings["source_name"]
    result["precision"] = raster_settings.get(
        "precision",
        2,
    )
    result["secondary_unit"] = raster_settings.get(
        "secondary_unit"
    )
    result["secondary_multiplier"] = raster_settings.get(
        "secondary_multiplier"
    )
    result["secondary_precision"] = raster_settings.get(
        "secondary_precision",
        2,
    )

    source_path = os.path.join(
        data_path,
        raster_settings["source"],
    )

    if not os.path.isfile(source_path):
        raise FileNotFoundError(
            f"Configured meteorological raster does not exist: "
            f"{source_path}"
        )

    site = QgsVectorLayer(
        site_layer_path,
        "Meteorological analysis site",
        "ogr",
    )

    if not site.isValid():
        raise ValueError(
            f"Failed to load analysis site: "
            f"{site_layer_path}"
        )

    if site.geometryType() != QgsWkbTypes.PolygonGeometry:
        raise ValueError(
            "Meteorological raster analysis requires "
            "a polygon site."
        )

    output_path = os.path.join(
        temp_path,
        output_name,
    )

    processing.run(
        "gdal:cliprasterbymasklayer",
        {
            "INPUT": source_path,
            "MASK": site,
            "SOURCE_CRS": None,
            "TARGET_CRS": None,
            "TARGET_EXTENT": None,
            "NODATA": -9999,
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

    raster_values = None
    no_data_value = None

    if dataset is not None:
        band = dataset.GetRasterBand(1)

        if band is not None:
            raster_values = band.ReadAsArray()
            no_data_value = band.GetNoDataValue()

        dataset = None

    mean_value = None

    if (
        raster_values is not None
        and raster_values.size > 0
    ):
        valid_pixels = np.isfinite(
            raster_values
        )

        if (
            no_data_value is not None
            and math.isfinite(no_data_value)
        ):
            valid_pixels &= ~np.isclose(
                raster_values,
                no_data_value,
            )

        if np.any(valid_pixels):
            mean_value = float(
                np.mean(
                    raster_values[valid_pixels]
                )
            )

            result["sampling_method"] = (
                "polygon raster mean"
            )

    if mean_value is None:
        print(
            f"{result['name']}: clipped raster contained "
            "no valid cells; sampling the centroid cell."
        )

        mean_value = sample_raster_at_site_centroid(
            raster_path=source_path,
            site_layer=site,
        )

        result["sampling_method"] = (
            "site centroid raster cell"
        )

    if mean_value is None:
        print(
            f"{result['name']}: "
            "no meteorological raster value available."
        )

        result["output_path"] = output_path
        return result

    result["value"] = mean_value
    result["status"] = "available"
    result["output_path"] = output_path

    primary_format = (
        "."
        + str(result["precision"])
        + "f"
    )

    primary_text = format(
        mean_value,
        primary_format,
    )

    value_text = (
        f"{primary_text} "
        f"{result['unit']}"
    )

    if (
        result["secondary_unit"] is not None
        and result["secondary_multiplier"] is not None
    ):
        secondary_value = (
            mean_value
            * result["secondary_multiplier"]
        )

        secondary_format = (
            "."
            + str(result["secondary_precision"])
            + "f"
        )

        secondary_text = format(
            secondary_value,
            secondary_format,
        )

        value_text += (
            f" ({secondary_text} "
            f"{result['secondary_unit']})"
        )

    print(
        f"{result['name']}: {value_text} "
        f"[{result['sampling_method']}]"
    )

    return result

def sample_raster_at_site_centroid(
    raster_path,
    site_layer,
):
    """
    Sample the source raster cell containing the site centroid.

    This is used when a site is smaller than the raster resolution
    and clipping does not capture a complete raster cell.
    """

    raster_layer = QgsRasterLayer(
        raster_path,
        "Meteorological source",
    )

    if not raster_layer.isValid():
        raise ValueError(
            f"Failed to load meteorological raster: "
            f"{raster_path}"
        )

    geometries = [
        feature.geometry()
        for feature in site_layer.getFeatures()
        if (
            feature.hasGeometry()
            and not feature.geometry().isEmpty()
        )
    ]

    if not geometries:
        return None

    site_geometry = QgsGeometry.unaryUnion(
        geometries
    )

    if site_geometry.isEmpty():
        return None

    centroid = site_geometry.centroid()

    if centroid.isEmpty():
        return None

    centroid_point = QgsPointXY(
        centroid.asPoint()
    )

    if site_layer.crs() != raster_layer.crs():
        coordinate_transform = QgsCoordinateTransform(
            site_layer.crs(),
            raster_layer.crs(),
            QgsProject.instance(),
        )

        centroid_point = coordinate_transform.transform(
            centroid_point
        )

    dataset = gdal.Open(
        raster_path,
        gdal.GA_ReadOnly,
    )

    if dataset is None:
        raise RuntimeError(
            f"Failed to open meteorological raster: "
            f"{raster_path}"
        )

    inverse_transform = gdal.InvGeoTransform(
        dataset.GetGeoTransform()
    )

    if inverse_transform is None:
        dataset = None
        return None

    pixel_x_float, pixel_y_float = (
        gdal.ApplyGeoTransform(
            inverse_transform,
            centroid_point.x(),
            centroid_point.y(),
        )
    )

    pixel_x = math.floor(pixel_x_float)
    pixel_y = math.floor(pixel_y_float)

    if (
        pixel_x < 0
        or pixel_y < 0
        or pixel_x >= dataset.RasterXSize
        or pixel_y >= dataset.RasterYSize
    ):
        dataset = None
        return None

    band = dataset.GetRasterBand(1)

    sample = band.ReadAsArray(
        pixel_x,
        pixel_y,
        1,
        1,
    )

    no_data_value = band.GetNoDataValue()

    dataset = None

    if sample is None or sample.size == 0:
        return None

    value = float(sample[0, 0])

    if not math.isfinite(value):
        return None

    if (
        no_data_value is not None
        and math.isfinite(no_data_value)
        and math.isclose(
            value,
            no_data_value,
            rel_tol=0.0,
            abs_tol=1e-12,
        )
    ):
        return None

    return value