import os

from datetime import date
from qgis.core import QgsVectorLayer


def format_site_name(folder_name):
    """
    Convert the filesystem-safe folder name back into a
    readable site name.
    """

    formatted_name = " ".join(
        word.capitalize()
        for word in folder_name.split()
    )

    return formatted_name.replace(
        "-",
        ":",
    )


def create_site_summary(
    site_layer_path,
    folder_path,
    folder_name,
    summary_settings=None,
):
    """
    Create the initial text summary for the analysis site.
    """

    site_layer = QgsVectorLayer(
        site_layer_path,
        "Analysis site summary",
        "ogr",
    )

    if not site_layer.isValid():
        raise ValueError(
            f"Failed to load analysis site: "
            f"{site_layer_path}"
        )

    summary_settings = (
        summary_settings or {}
    )

    readable_name = format_site_name(
        folder_name
    )

    total_area_ha = 0.0

    for feature in site_layer.getFeatures():
        geometry = feature.geometry()

        if geometry is None or geometry.isEmpty():
            continue

        total_area_ha += (
            geometry.area() / 10000
        )

    report_lines = [
        f"{readable_name}:",
        f"Area: {total_area_ha:.2f} ha",
    ]

    tariff_field = summary_settings.get(
        "tariff_zone_field"
    )

    tariff_prefix = summary_settings.get(
        "tariff_zone_prefix",
        "",
    )

    tariff_zones = []

    if (
        tariff_field
        and site_layer.fields().indexFromName(
            tariff_field
        )
        != -1
    ):
        for feature in site_layer.getFeatures():
            value = feature[tariff_field]

            if value is None:
                continue

            value_text = str(value).strip()

            if value_text in {"", "NULL"}:
                continue

            if value_text.endswith(".0"):
                value_text = value_text[:-2]

            tariff_zones.append(
                value_text
            )

        tariff_zones = sorted(
            set(tariff_zones)
        )

        for tariff_zone in tariff_zones:
            report_lines.append(
                f"Tariff zone: "
                f"{tariff_prefix}{tariff_zone}"
            )

    report_path = os.path.join(
        folder_path,
        f"prints ({folder_name}).txt",
    )

    with open(
        report_path,
        "w",
        encoding="utf-8",
    ) as report_file:
        report_file.write(
            "\n".join(report_lines) + "\n"
        )

    for line in report_lines:
        print(line)

    print(
        f"Site summary saved: {report_path}"
    )

    return {
        "report_path": report_path,
        "site_name": readable_name,
        "area_ha": total_area_ha,
        "tariff_zones": tariff_zones,
    }

def append_solar_resource_summary(
    folder_path,
    folder_name,
    solar_resource_data,
):
    """
    Append solar-resource results to the existing site summary.

    Results include the daily value, yearly value and selected
    data source. Missing values are reported explicitly.
    """

    report_path = os.path.join(
        folder_path,
        f"prints ({folder_name}).txt",
    )

    if not os.path.isfile(report_path):
        raise FileNotFoundError(
            f"Site summary does not exist: {report_path}"
        )

    parameter_order = (
        "dif",
        "dni",
        "ghi",
        "gti",
        "opta",
        "pvout",
        "temperature",
    )

    lines = [
        "",
        "Solar resource",
        "--------------",
    ]

    for key in parameter_order:

        result = solar_resource_data.get(key)

        if result is None:
            continue

        lines.append("")
        lines.append(f"{result['name']}:")

        if result["value"] is None:
            lines.append("  Value: No data available")
            lines.append("  Source: No available source")
            continue

        if result["yearly_value"] is not None:
            lines.append(
                f"  Daily average: "
                f"{result['value']:.3f} "
                f"{result['unit']}"
            )

            lines.append(
                f"  Yearly total: "
                f"{result['yearly_value']:.1f} "
                f"{result['yearly_unit']}"
            )

        else:
            lines.append(
                f"  Value: "
                f"{result['value']:.3f} "
                f"{result['unit']}"
            )

        lines.append(
            f"  Source: {result['source']}"
        )

        if result["status"] == "estimated":
            lines.append(
                "  Status: Estimated value"
            )

        if "derivation_factor" in result:
            lines.append(
                f"  Derivation: GHI × "
                f"{result['derivation_factor']}"
            )

    with open(
        report_path,
        "a",
        encoding="utf-8",
    ) as report_file:
        report_file.write(
            "\n".join(lines) + "\n"
        )

    print(
        f"Solar-resource summary appended: "
        f"{report_path}"
    )

    return report_path

def append_solar_position_summary(
    folder_path,
    folder_name,
    average_elevation,
    reference_year,
    start_month,
    start_day,
    end_month,
    end_day,
):
    """
    Append the calculated solar-position statistic to the report.
    """

    report_path = os.path.join(
        folder_path,
        f"prints ({folder_name}).txt",
    )

    if not os.path.isfile(report_path):
        raise FileNotFoundError(
            f"Site summary does not exist: {report_path}"
        )

    start_date = date(
        reference_year,
        start_month,
        start_day,
    )

    end_date = date(
        reference_year,
        end_month,
        end_day,
    )

    lines = [
        "",
        "Solar position",
        "--------------",
    ]

    if average_elevation is None:
        lines.append(
            "Average daytime solar elevation: "
            "No daylight samples available"
        )

    else:
        lines.append(
            "Average daytime solar elevation: "
            f"{average_elevation:.2f} degrees"
        )

    lines.append(
        f"Calculation period: "
        f"{start_date:%Y-%m-%d} to "
        f"{end_date:%Y-%m-%d}"
    )

    lines.append(
        "Method: Average of positive solar-elevation "
        "values sampled at every whole UTC hour"
    )

    with open(
        report_path,
        "a",
        encoding="utf-8",
    ) as report_file:
        report_file.write(
            "\n".join(lines) + "\n"
        )

    print(
        f"Solar-position summary appended: "
        f"{report_path}"
    )

    return report_path

def format_meteorological_value(
    result,
    default_precision=2,
):
    """
    Format a meteorological result using its configured precision.
    """

    if not result or result.get("value") is None:
        return None

    precision = result.get(
        "precision",
        default_precision,
    )

    primary_text = format(
        result["value"],
        "." + str(precision) + "f",
    )

    value_text = (
        f"{primary_text} "
        f"{result['unit']}"
    )

    secondary_unit = result.get(
        "secondary_unit"
    )

    secondary_multiplier = result.get(
        "secondary_multiplier"
    )

    if (
        secondary_unit is not None
        and secondary_multiplier is not None
    ):
        secondary_value = (
            result["value"]
            * secondary_multiplier
        )

        secondary_precision = result.get(
            "secondary_precision",
            2,
        )

        secondary_text = format(
            secondary_value,
            "." + str(secondary_precision) + "f",
        )

        value_text += (
            f" ({secondary_text} "
            f"{secondary_unit})"
        )

    return value_text

def append_meteorology_summary(
    folder_path,
    folder_name,
    wind_speed_result,
    wind_load_result=None,
    snow_load_result=None,
    humidity_result=None,
    temperature_result=None,
    air_pressure_result=None,
    snow_depth_results=None,
):
    """
    Append currently available meteorological results.
    """

    report_path = os.path.join(
        folder_path,
        f"prints ({folder_name}).txt",
    )

    if not os.path.isfile(report_path):
        raise FileNotFoundError(
            f"Site summary does not exist: {report_path}"
        )

    lines = [
        "",
        "Meteorological data",
        "-------------------",
        "",
    ]

    if wind_speed_result["value"] is None:
        lines.append(
            "Average wind speed: No data available"
        )

        if wind_speed_result["source"]:
            lines.append(
                f"Source: {wind_speed_result['source']}"
            )

    else:
        lines.append(
            f"Average wind speed at "
            f"{wind_speed_result['height_m']} m: "
            f"{wind_speed_result['value']:.2f} "
            f"{wind_speed_result['unit']}"
        )

        lines.append(
            f"Source: {wind_speed_result['source']}"
        )

    if wind_load_result is not None:
        lines.append("")

        if not wind_load_result["values"]:
            lines.append(
                "Wind load: No data available"
            )

        else:
            for value in wind_load_result["values"]:
                lines.append(
                    f"Wind load: "
                    f"{value:.2f} "
                    f"{wind_load_result['unit']}"
                )

            lines.append(
                f"Source: "
                f"{wind_load_result['source']}"
            )

    if snow_load_result is not None:
        lines.append("")

        if not snow_load_result["values"]:
            lines.append(
                "Snow load: No data available"
            )

        else:
            for value in snow_load_result["values"]:
                lines.append(
                    f"Snow load: "
                    f"{value:.2f} "
                    f"{snow_load_result['unit']}"
                )

            lines.append(
                f"Source: "
                f"{snow_load_result['source']}"
            )

    raster_results = (
        ("Average humidity", humidity_result),
        ("Average air temperature", temperature_result),
        ("Average air pressure", air_pressure_result),
    )

    for label, result in raster_results:
        lines.append("")

        value_text = format_meteorological_value(
            result
        )

        if value_text is None:
            lines.append(
                f"{label}: No data available"
            )
            continue

        lines.append(
            f"{label}: {value_text}"
        )

        if result.get("source"):
            lines.append(
                f"Source: {result['source']}"
            )

        if result.get("sampling_method"):
            lines.append(
                f"Sampling method: "
                f"{result['sampling_method']}"
            )

    lines.append("")
    lines.append(
        "Average monthly snow depth:"
    )

    if not snow_depth_results:
        lines.append(
            "  No data available"
        )

    else:
        snow_sources = set()

        for month_name, result in (
            snow_depth_results.items()
        ):
            value_text = format_meteorological_value(
                result,
                default_precision=3,
            )

            if value_text is None:
                lines.append(
                    f"  {month_name}: "
                    "No data available"
                )
                continue

            sampling_method = result.get(
                "sampling_method"
            )

            if sampling_method:
                lines.append(
                    f"  {month_name}: "
                    f"{value_text} "
                    f"[{sampling_method}]"
                )
            else:
                lines.append(
                    f"  {month_name}: "
                    f"{value_text}"
                )

            if result.get("source"):
                snow_sources.add(
                    result["source"]
                )

        for source_name in sorted(snow_sources):
            lines.append(
                f"Source: {source_name}"
            )

    with open(
        report_path,
        "a",
        encoding="utf-8",
    ) as report_file:
        report_file.write(
            "\n".join(lines) + "\n"
        )

    print(
        f"Meteorological summary appended: "
        f"{report_path}"
    )

    return report_path

def append_municipality_politics_summary(
    folder_path,
    folder_name,
    political_result,
):
    """
    Append municipality political-control information.
    """

    report_path = os.path.join(
        folder_path,
        f"prints ({folder_name}).txt",
    )

    if not os.path.isfile(report_path):
        raise FileNotFoundError(
            f"Site summary does not exist: {report_path}"
        )

    lines = [
        "",
        "Municipality political control",
        "------------------------------",
    ]

    municipalities = political_result.get(
        "municipalities",
        [],
    )

    if not municipalities:
        lines.append(
            "No political data available"
        )

    else:
        for municipality in municipalities:
            lines.append("")
            lines.append(
                f"Municipality: "
                f"{municipality['name']}"
            )

            lines.append(
                "Ruling parties:"
            )

            for party in municipality[
                "ruling_parties"
            ]:
                influence = party[
                    "influence_percent"
                ]

                if influence is None:
                    lines.append(
                        f"  - {party['name']}"
                    )
                else:
                    lines.append(
                        f"  - {party['name']}: "
                        f"{influence:.1f}% "
                        "of municipal seats"
                    )

    source_path = political_result.get(
        "source"
    )

    if source_path:
        lines.append("")
        lines.append(
            f"Source: "
            f"{os.path.basename(source_path)}"
        )

    with open(
        report_path,
        "a",
        encoding="utf-8",
    ) as report_file:
        report_file.write(
            "\n".join(lines) + "\n"
        )

    print(
        f"Municipality political summary appended: "
        f"{report_path}"
    )

    return report_path

def append_bos_summary(
    folder_path,
    folder_name,
    bos_summary,
):
    """
    Append the BoS land-cover coverage results to the
    site's existing text report.
    """

    report_path = os.path.join(
        folder_path,
        f"prints ({folder_name}).txt",
    )

    lines = [
        "",
        "BoS land-cover coverage",
        "-----------------------",
    ]

    if (
        bos_summary is None
        or bos_summary.get("status") != "available"
    ):
        lines.append(
            "No BoS land-cover data available."
        )

    else:
        lines.append(
            "Analysis area: "
            f"{bos_summary['analysis_area_ha']:.3f} ha"
        )

        group_order = (
            "Open field",
            "Peat quarry",
            "Forest",
            "Wetland",
            "Rocky terrain",
            "Other land cover",
            "No land-cover data",
        )

        areas = bos_summary.get(
            "areas_ha",
            {},
        )

        percentages = bos_summary.get(
            "percentages",
            {},
        )

        for group_name in group_order:

            area_ha = areas.get(
                group_name,
                0.0,
            )

            percentage = percentages.get(
                group_name,
                0.0,
            )

            lines.append(
                f"{group_name}: "
                f"{percentage:.2f}% "
                f"({area_ha:.3f} ha)"
            )

    with open(
        report_path,
        "a",
        encoding="utf-8",
    ) as report_file:
        report_file.write(
            "\n".join(lines) + "\n"
        )

    print(
        f"BoS summary appended: {report_path}"
    )

    return report_path

def append_project_potential_summary(
    folder_path,
    folder_name,
    project_potential,
):
    """
    Append estimated solar, wind, grid and BESS potential
    to the site's existing text report.
    """

    report_path = os.path.join(
        folder_path,
        f"prints ({folder_name}).txt",
    )

    lines = [
        "",
        "Potential of the project area",
        "-----------------------------",
        (
            "Suitable solar area: "
            f"{project_potential['solar_area_ha']:.2f} ha"
        ),
        (
            "Estimated solar capacity: "
            f"{project_potential['solar_capacity_mwp']:.2f} MWp"
        ),
        (
            "Suitable wind area: "
            f"{project_potential['wind_area_ha']:.2f} ha"
        ),
        (
            "Estimated wind turbines: "
            f"{project_potential['wind_turbines']}"
        ),
        (
            "Wind turbine capacity: "
            f"{project_potential['wind_turbine_capacity_mw']:.2f} "
            "MW per turbine"
        ),
        (
            "Estimated wind capacity: "
            f"{project_potential['wind_capacity_mw']:.2f} MW"
        ),
        (
            "Combined project capacity: "
            f"{project_potential['combined_capacity_mw']:.2f} MW"
        ),
        (
            "Estimated AC capacity: "
            f"{project_potential['estimated_ac_capacity_mw']:.2f} MW"
        ),
        (
            "Estimated BESS capacity: "
            f"{project_potential['bess_capacity_mw']:.0f} MW"
        ),
        "",
        "Potential calculation assumptions",
        (
            "Solar power density: "
            f"{project_potential['assumptions']['solar_mwp_per_hectare']:.2f} "
            "MWp/ha"
        ),
        (
            "Wind area per turbine: "
            f"{project_potential['assumptions']['wind_area_per_turbine_ha']:.2f} "
            "ha"
        ),
        (
            "Minimum area for one wind turbine: "
            f"{project_potential['assumptions']['wind_single_turbine_minimum_ha']:.2f} "
            "ha"
        ),
        (
            "DC/AC ratio: "
            f"{project_potential['assumptions']['dc_ac_ratio']:.2f}"
        ),
        (
            "BESS share of AC capacity: "
            f"{project_potential['assumptions']['bess_ac_capacity_fraction'] * 100:.1f}%"
        ),
    ]

    with open(
        report_path,
        "a",
        encoding="utf-8",
    ) as report_file:
        report_file.write(
            "\n".join(lines) + "\n"
        )

    print(
        f"Project-potential summary appended: "
        f"{report_path}"
    )

    return report_path

def append_grid_proximity_summary(
    folder_path,
    folder_name,
    grid_proximity_result,
):
    """
    Append power-line and transformer proximity information
    to the site's existing text report.
    """

    report_path = os.path.join(
        folder_path,
        f"prints ({folder_name}).txt",
    )

    lines = [
        "",
        "Power-line and transformer information",
        "--------------------------------------",
    ]

    if (
        grid_proximity_result is None
        or grid_proximity_result.get("status")
        == "unavailable"
    ):
        lines.append(
            "Grid-proximity data is not configured "
            "for this country."
        )

    elif (
        grid_proximity_result.get("status")
        == "no_features"
    ):
        lines.append(
            "No configured grid infrastructure was found "
            "within the available surrounding context data."
        )

    else:
        results = grid_proximity_result.get(
            "results",
            [],
        )

        for result in results:

            name = result["name"]
            distance_m = result["distance_m"]

            if result.get("crossing"):
                distance_text = (
                    "crossing or within the configured "
                    "proximity threshold"
                )

            elif distance_m < 1000:
                distance_text = (
                    f"{distance_m:.0f} m"
                )

            else:
                distance_text = (
                    f"{distance_m / 1000:.2f} km"
                )

            details = [
                f"{name}: {distance_text}"
            ]

            voltage_kv = result.get(
                "voltage_kv"
            )

            if voltage_kv is not None:
                details.append(
                    f"voltage {voltage_kv:.0f} kV"
                )

            primary_voltage_kv = result.get(
                "primary_voltage_kv"
            )

            if primary_voltage_kv is not None:
                details.append(
                    "primary voltage "
                    f"{primary_voltage_kv:.0f} kV"
                )

            secondary_voltage_kv = result.get(
                "secondary_voltage_kv"
            )

            if secondary_voltage_kv is not None:
                details.append(
                    "secondary voltage "
                    f"{secondary_voltage_kv:.0f} kV"
                )

            lines.append(
                "; ".join(details)
            )

        crossing_distance_m = (
            grid_proximity_result.get(
                "crossing_distance_m"
            )
        )

        if crossing_distance_m is not None:
            lines.extend(
                [
                    "",
                    (
                        "Configured crossing/proximity "
                        "threshold: "
                        f"{crossing_distance_m:.0f} m"
                    ),
                ]
            )

        lines.append(
            "Distances are limited to infrastructure "
            "available within the processed context area."
        )

    with open(
        report_path,
        "a",
        encoding="utf-8",
    ) as report_file:
        report_file.write(
            "\n".join(lines) + "\n"
        )

    print(
        f"Grid-proximity summary appended: "
        f"{report_path}"
    )

    return report_path

def append_soil_depth_summary(
    folder_path,
    folder_name,
    soil_depth_result,
    settings=None,
):
    """
    Append soil-depth ranges for each soil type to the
    site's existing text report.
    """

    report_path = os.path.join(
        folder_path,
        f"prints ({folder_name}).txt",
    )

    lines = [
        "",
        "Soil depth by soil type",
        "-----------------------",
    ]

    if settings is None:
        settings = {}

    metre_precision = settings.get(
        "metre_precision",
        0,
    )

    centimetre_precision = settings.get(
        "centimetre_precision",
        0,
    )

    if not soil_depth_result:
        lines.append(
            "Soil-depth analysis was not performed."
        )

    elif soil_depth_result.get("status") != "available":
        lines.append(
            soil_depth_result.get(
                "message",
                "No soil-depth information was available "
                "for the analysis site.",
            )
        )

    else:
        results = soil_depth_result.get(
            "results",
            [],
        )

        if not results:
            lines.append(
                "No soil types with valid soil-depth data "
                "were found."
            )

        for result in results:
            soil_type = result.get(
                "soil_type",
                "Unknown soil type",
            )

            if result.get("status") != "available":
                lines.append(
                    f"{soil_type}: no valid soil-depth data"
                )
                continue

            minimum_m = result["minimum_m"]
            maximum_m = result["maximum_m"]
            minimum_cm = result["minimum_cm"]
            maximum_cm = result["maximum_cm"]

            minimum_m_text = format(
                minimum_m,
                f".{metre_precision}f",
            )

            maximum_m_text = format(
                maximum_m,
                f".{metre_precision}f",
            )

            minimum_cm_text = format(
                minimum_cm,
                f".{centimetre_precision}f",
            )

            maximum_cm_text = format(
                maximum_cm,
                f".{centimetre_precision}f",
            )

            lines.append(
                f"{soil_type}: "
                f"{minimum_m_text}–{maximum_m_text} m "
                f"({minimum_cm_text}–{maximum_cm_text} cm)"
            )

        lines.extend(
            [
                "",
                (
                    "Source: SGU Jorddjupsmodell. Values represent "
                    "estimated depth to bedrock."
                ),
            ]
        )

    with open(
        report_path,
        "a",
        encoding="utf-8",
    ) as report_file:
        report_file.write(
            "\n".join(lines) + "\n"
        )

    print(
        f"Soil-depth summary appended: {report_path}"
    )

    return report_path

def append_custom_estates_summary(
    folder_path,
    folder_name,
    custom_estates_result,
):
    """
    Append estates intersecting a custom analysis polygon
    to the site's text report.
    """

    if custom_estates_result is None:
        return None

    report_path = os.path.join(
        folder_path,
        f"prints ({folder_name}).txt",
    )

    lines = [
        "",
        "Estates intersecting the custom analysis area",
        "----------------------------------------------",
    ]

    status = custom_estates_result.get(
        "status"
    )

    if status == "available":
        estates = custom_estates_result.get(
            "estates",
            [],
        )

        if estates:
            for estate in estates:
                estate_name = estate[
                    "estate_name"
                ]

                overlap_area_ha = estate[
                    "overlap_area_ha"
                ]

                analysis_percentage = estate[
                    "analysis_percentage"
                ]

                lines.extend(
                    [
                        estate_name,
                        (
                            f"Overlap: "
                            f"{overlap_area_ha:.2f} ha "
                            f"({analysis_percentage:.2f}% "
                            f"of analysis area)"
                        ),
                        "",
                    ]
                )

        else:
            lines.extend(
                [
                    (
                        "No named estate geometries intersect "
                        "the custom analysis area."
                    ),
                    "",
                ]
            )

        unmatched_area_ha = (
            custom_estates_result.get(
                "unmatched_area_ha",
                0.0,
            )
        )

        unmatched_percentage = (
            custom_estates_result.get(
                "unmatched_percentage",
                0.0,
            )
        )

        lines.append(
            "Unregistered or unmatched area: "
            f"{unmatched_area_ha:.2f} ha "
            f"({unmatched_percentage:.2f}%)"
        )

    elif status == "error":
        lines.append(
            "Estate identification failed: "
            f"{custom_estates_result.get('error', 'unknown error')}"
        )

    else:
        lines.append(
            "Estate identification is unavailable "
            "for this analysis area."
        )

    with open(
        report_path,
        "a",
        encoding="utf-8",
    ) as report_file:
        report_file.write(
            "\n".join(lines) + "\n"
        )

    print(
        f"Custom-estate summary appended: "
        f"{report_path}"
    )

    return report_path