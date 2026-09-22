import os

from qgis.core import (
    QgsUnitTypes,
    QgsVectorLayer,
)


def normalise_numeric_value(value):
    """
    Convert a QGIS attribute value into a float.

    Return None for null, empty or non-numeric values.
    """

    if value is None:
        return None

    if hasattr(value, "isNull") and value.isNull():
        return None

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return None

        value = value.replace(
            ",",
            ".",
        )

    try:
        return float(value)

    except (TypeError, ValueError):
        return None


def read_voltage_kv(
    feature,
    field_name,
    divisor,
):
    """
    Read and convert one voltage attribute to kilovolts.
    """

    if not field_name:
        return None

    field_names = feature.fields().names()

    if field_name not in field_names:
        return None

    value = normalise_numeric_value(
        feature[field_name]
    )

    if value is None:
        return None

    if divisor <= 0:
        raise ValueError(
            "Voltage divisor must be greater than zero."
        )

    return value / divisor


def find_country_layer_output(
    country_layer_outputs,
    layer_name,
):
    """
    Find an already clipped country-layer output by its
    configured display name.
    """

    for layer_output in country_layer_outputs:

        definition = layer_output.get(
            "definition",
            {},
        )

        if definition.get("name") == layer_name:
            return layer_output

    return None


def calculate_nearest_feature(
    analysis_layer,
    infrastructure_layer,
):
    """
    Find the infrastructure feature with the shortest
    geometry-to-geometry distance from the analysis site.

    The country layers have already been clipped locally, so a
    complete comparison is preferable to an approximate
    bounding-box nearest-neighbour search.
    """

    site_geometries = []

    for feature in analysis_layer.getFeatures():

        geometry = feature.geometry()

        if geometry is None or geometry.isEmpty():
            continue

        site_geometries.append(
            geometry
        )

    if not site_geometries:
        raise ValueError(
            "The analysis site contains no usable geometries."
        )

    nearest_feature = None
    minimum_distance = None

    for infrastructure_feature in (
        infrastructure_layer.getFeatures()
    ):

        infrastructure_geometry = (
            infrastructure_feature.geometry()
        )

        if (
            infrastructure_geometry is None
            or infrastructure_geometry.isEmpty()
        ):
            continue

        for site_geometry in site_geometries:

            distance = site_geometry.distance(
                infrastructure_geometry
            )

            if distance < 0:
                continue

            if (
                minimum_distance is None
                or distance < minimum_distance
            ):
                minimum_distance = distance
                nearest_feature = infrastructure_feature

                if minimum_distance == 0:
                    break

        if minimum_distance == 0:
            break

    return minimum_distance, nearest_feature


def analyse_grid_proximity(
    analysis_layer_path,
    country_layer_outputs,
    grid_settings,
):
    """
    Calculate distances from the complete analysis site to the
    configured local power-line and transformer layers.

    Return structured results for reporting.
    """

    if not grid_settings:
        print(
            "Grid-proximity analysis skipped: "
            "no country configuration."
        )

        return {
            "status": "unavailable",
            "results": [],
        }

    analysis_layer = QgsVectorLayer(
        analysis_layer_path,
        "Grid proximity analysis site",
        "ogr",
    )

    if not analysis_layer.isValid():
        raise ValueError(
            f"Failed to load grid-proximity analysis site: "
            f"{analysis_layer_path}"
        )

    if not analysis_layer.crs().isValid():
        raise ValueError(
            "The grid-proximity analysis site has no valid CRS."
        )

    if analysis_layer.crs().isGeographic():
        raise ValueError(
            "Grid-proximity analysis requires a projected CRS."
        )

    distance_to_metres = (
        QgsUnitTypes.fromUnitToUnitFactor(
            analysis_layer.crs().mapUnits(),
            QgsUnitTypes.DistanceMeters,
        )
    )

    crossing_distance_m = float(
        grid_settings.get(
            "crossing_distance_m",
            0.0,
        )
    )

    results = []

    configured_layers = grid_settings.get(
        "layers",
        [],
    )

    for layer_settings in configured_layers:

        layer_name = layer_settings["name"]

        layer_output = find_country_layer_output(
            country_layer_outputs=country_layer_outputs,
            layer_name=layer_name,
        )

        if layer_output is None:
            print(
                f"Grid layer unavailable: {layer_name}"
            )
            continue

        output_path = layer_output.get(
            "output_path"
        )

        if (
            not output_path
            or not os.path.isfile(output_path)
        ):
            print(
                f"Grid layer has no local output: "
                f"{layer_name}"
            )
            continue

        infrastructure_layer = QgsVectorLayer(
            output_path,
            layer_name,
            "ogr",
        )

        if not infrastructure_layer.isValid():
            raise ValueError(
                f"Failed to load local grid layer: "
                f"{output_path}"
            )

        if infrastructure_layer.featureCount() == 0:
            print(
                f"Grid layer has no local features: "
                f"{layer_name}"
            )
            continue

        if not infrastructure_layer.crs().isValid():
            raise ValueError(
                f"Grid layer has no valid CRS: "
                f"{layer_name}"
            )

        if infrastructure_layer.crs() != analysis_layer.crs():
            raise ValueError(
                f"Grid layer CRS does not match the "
                f"analysis site: {layer_name}"
            )

        distance, nearest_feature = (
            calculate_nearest_feature(
                analysis_layer=analysis_layer,
                infrastructure_layer=infrastructure_layer,
            )
        )

        if (
            distance is None
            or nearest_feature is None
        ):
            print(
                f"Grid layer has no usable geometry: "
                f"{layer_name}"
            )
            continue

        distance_m = (
            distance
            * distance_to_metres
        )

        layer_type = layer_settings.get(
            "type",
            "grid_infrastructure",
        )

        divisor = float(
            layer_settings.get(
                "voltage_divisor",
                1.0,
            )
        )

        result = {
            "name": layer_name,
            "type": layer_type,
            "distance_m": distance_m,
            "crossing": (
                distance_m
                < crossing_distance_m
            ),
            "voltage_kv": None,
            "primary_voltage_kv": None,
            "secondary_voltage_kv": None,
        }

        if layer_type == "transformer_station":

            result["primary_voltage_kv"] = (
                read_voltage_kv(
                    feature=nearest_feature,
                    field_name=layer_settings.get(
                        "primary_voltage_field"
                    ),
                    divisor=divisor,
                )
            )

            result["secondary_voltage_kv"] = (
                read_voltage_kv(
                    feature=nearest_feature,
                    field_name=layer_settings.get(
                        "secondary_voltage_field"
                    ),
                    divisor=divisor,
                )
            )

        else:
            result["voltage_kv"] = read_voltage_kv(
                feature=nearest_feature,
                field_name=layer_settings.get(
                    "voltage_field"
                ),
                divisor=divisor,
            )

        results.append(result)

        if result["crossing"]:
            distance_text = "crossing the analysis area"

        elif distance_m < 1000:
            distance_text = f"{distance_m:.0f} m"

        else:
            distance_text = (
                f"{distance_m / 1000:.2f} km"
            )

        print(
            f"Nearest {layer_name}: {distance_text}"
        )

    if not results:
        print(
            "No configured grid infrastructure was found "
            "within the available local context data."
        )

        return {
            "status": "no_features",
            "results": [],
            "crossing_distance_m": crossing_distance_m,
        }

    return {
        "status": "available",
        "results": results,
        "crossing_distance_m": crossing_distance_m,
    }