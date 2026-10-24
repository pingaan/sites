import os

from datetime import date
from qgis.core import QgsVectorLayer

from scripts.translations import ui_text

def report_text(
    key,
    **values,
):
    """
    Return report text in the globally selected language.

    Analyses launched outside the desktop application default
    to English.
    """

    language = os.environ.get(
        "SITES_LANGUAGE",
        "en",
    )

    return ui_text(
        language,
        key,
        **values,
    )



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


def render_markdown_lines(lines):
    """
    Convert report lines into consistently structured Markdown.

    Existing underlined headings become level-two headings.
    Named subsections become level-three headings.
    Ordinary result lines become bullet points.
    """

    subsection_names = {
        report_text(
            "report_potential_calculation_assumptions"
        ),
        (
            report_text(
                "report_average_monthly_snow_depth"
            )
            + ":"
        ),
        (
            report_text(
                "report_ruling_parties"
            )
            + ":"
        ),
    }

    rendered_lines = []
    index = 0

    while index < len(lines):
        line = str(
            lines[index]
        ).replace(
            "\u00a0",
            " ",
        ).rstrip()

        if not line:
            rendered_lines.append("")
            index += 1
            continue

        if index + 1 < len(lines):
            next_line = str(
                lines[index + 1]
            ).strip()

            if (
                next_line
                and set(next_line) == {"-"}
            ):
                rendered_lines.extend(
                    [
                        f"## {line}",
                        "",
                    ]
                )

                index += 2
                continue

        if line in subsection_names:
            rendered_lines.extend(
                [
                    f"### {line.rstrip(':')}",
                    "",
                ]
            )

            index += 1
            continue

        if line.startswith("#"):
            rendered_lines.append(
                line
            )

            index += 1
            continue

        stripped_line = line.lstrip()

        if stripped_line.startswith("- "):
            rendered_lines.append(
                stripped_line
            )

            index += 1
            continue

        if line.endswith(":"):
            rendered_lines.extend(
                [
                    f"**{line[:-1]}**",
                    "",
                ]
            )

            index += 1
            continue

        rendered_lines.append(
            f"- {line}"
        )

        index += 1

    cleaned_lines = []

    for line in rendered_lines:
        if (
            line == ""
            and cleaned_lines
            and cleaned_lines[-1] == ""
        ):
            continue

        cleaned_lines.append(
            line
        )

    return (
        "\n".join(cleaned_lines).rstrip()
        + "\n"
    )


def create_site_summary(
    site_layer_path,
    folder_path,
    folder_name,
    summary_settings=None,
):
    """
    Create the initial Markdown report for the analysis site.
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
        (
            "# "
            + report_text(
                "report_site_analysis",
                name=readable_name,
            )
        ),
        "",
        (
            "## "
            + report_text(
                "report_site_summary"
            )
        ),
        "",
        (
            "- **"
            + report_text("report_area")
            + ":** "
            + f"{total_area_ha:.2f} ha"
        ),
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
                "- **"
                + report_text(
                    "report_tariff_zone"
                )
                + ":** "
                + f"{tariff_prefix}{tariff_zone}"
            )

    report_path = os.path.join(
        folder_path,
        "project_report.md",
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
        "project_report.md",
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

    solar_heading = report_text(
        "report_solar_resource"
    )

    lines = [
        "",
        solar_heading,
        "-" * len(solar_heading),
    ]

    for key in parameter_order:

        result = solar_resource_data.get(key)

        if result is None:
            continue

        lines.append("")

        parameter_name = report_text(
            f"report_solar_parameter_{key}"
        )

        lines.append(
            f"{parameter_name}:"
        )

        if result["value"] is None:
            lines.append(
                "  "
                + report_text("report_value")
                + ": "
                + report_text(
                    "report_no_data_available"
                )
            )

            lines.append(
                "  "
                + report_text("report_source")
                + ": "
                + report_text(
                    "report_no_available_source"
                )
            )

            continue

        if result["yearly_value"] is not None:
            lines.append(
                "  "
                + report_text(
                    "report_daily_average"
                )
                + ": "
                + f"{result['value']:.3f} "
                + f"{result['unit']}"
            )

            lines.append(
                "  "
                + report_text(
                    "report_yearly_total"
                )
                + ": "
                + f"{result['yearly_value']:.1f} "
                + f"{result['yearly_unit']}"
            )

        else:
            lines.append(
                "  "
                + report_text("report_value")
                + ": "
                + f"{result['value']:.3f} "
                + f"{result['unit']}"
            )

        lines.append(
            "  "
            + report_text("report_source")
            + ": "
            + str(result["source"])
        )

        if result["status"] == "estimated":
            lines.append(
                "  "
                + report_text("report_status")
                + ": "
                + report_text(
                    "report_estimated_value"
                )
            )

        if "derivation_factor" in result:
            lines.append(
                "  "
                + report_text(
                    "report_derivation"
                )
                + ": GHI × "
                + str(
                    result[
                        "derivation_factor"
                    ]
                )
            )

    with open(
        report_path,
        "a",
        encoding="utf-8",
    ) as report_file:
        report_file.write(
            render_markdown_lines(lines)
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
        "project_report.md",
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

    solar_position_heading = report_text(
        "report_solar_position"
    )

    lines = [
        "",
        solar_position_heading,
        "-" * len(
            solar_position_heading
        ),
    ]

    if average_elevation is None:
        lines.append(
            report_text(
                "report_average_daytime_solar_elevation"
            )
            + ": "
            + report_text(
                "report_no_daylight_samples"
            )
        )

    else:
        lines.append(
            report_text(
                "report_average_daytime_solar_elevation"
            )
            + ": "
            + f"{average_elevation:.2f} "
            + report_text("report_degrees")
        )

        lines.append(
            report_text(
                "report_calculation_period",
                start=(
                    f"{start_date:%Y-%m-%d}"
                ),
                end=(
                    f"{end_date:%Y-%m-%d}"
                ),
            )
        )

        lines.append(
            report_text(
                "report_solar_position_method"
            )
        )

    with open(
        report_path,
        "a",
        encoding="utf-8",
    ) as report_file:
        report_file.write(
            render_markdown_lines(lines)
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

def report_sampling_method(
    sampling_method,
):
    """
    Translate a known meteorological sampling method.
    """

    sampling_method = str(
        sampling_method
    ).strip()

    translation_keys = {
        "polygon raster mean": (
            "report_sampling_polygon_raster_mean"
        ),
        "site centroid raster cell": (
            "report_sampling_site_centroid_raster_cell"
        ),
    }

    translation_key = translation_keys.get(
        sampling_method.casefold()
    )

    if translation_key is None:
        return sampling_method

    return report_text(
        translation_key
    )


def report_month_name(
    month_name,
):
    """
    Translate an English month name used by raster results.
    """

    month_name = str(
        month_name
    ).strip()

    translation_key = (
        "report_month_"
        + month_name.casefold()
    )

    translated_name = report_text(
        translation_key
    )

    if translated_name == translation_key:
        return month_name

    return translated_name



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
        "project_report.md",
    )

    if not os.path.isfile(report_path):
        raise FileNotFoundError(
            f"Site summary does not exist: {report_path}"
        )

    meteorology_heading = report_text(
        "report_meteorological_data"
    )

    lines = [
        "",
        meteorology_heading,
        "-" * len(meteorology_heading),
        "",
    ]

    if wind_speed_result["value"] is None:
        lines.append(
            report_text(
                "report_average_wind_speed"
            )
            + ": "
            + report_text(
                "report_no_data_available"
            )
        )

        if wind_speed_result["source"]:
            lines.append(
                report_text("report_source")
                + ": "
                + str(
                    wind_speed_result["source"]
                )
            )

    else:
        wind_speed_label = report_text(
            "report_average_wind_speed_at_height",
            height=wind_speed_result[
                "height_m"
            ],
        )

        lines.append(
            wind_speed_label
            + ": "
            + f"{wind_speed_result['value']:.2f} "
            + f"{wind_speed_result['unit']}"
        )

        lines.append(
            report_text("report_source")
            + ": "
            + str(
                wind_speed_result["source"]
            )
        )

    if wind_load_result is not None:
        lines.append("")

        wind_load_label = report_text(
            "report_wind_load"
        )

        if not wind_load_result["values"]:
            lines.append(
                wind_load_label
                + ": "
                + report_text(
                    "report_no_data_available"
                )
            )

        else:
            for value in wind_load_result["values"]:
                lines.append(
                    wind_load_label
                    + ": "
                    + f"{value:.2f} "
                    + f"{wind_load_result['unit']}"
                )

            lines.append(
                report_text("report_source")
                + ": "
                + str(
                    wind_load_result["source"]
                )
            )

    if snow_load_result is not None:
        lines.append("")

        snow_load_label = report_text(
            "report_snow_load"
        )

        if not snow_load_result["values"]:
            lines.append(
                snow_load_label
                + ": "
                + report_text(
                    "report_no_data_available"
                )
            )

        else:
            for value in snow_load_result["values"]:
                lines.append(
                    snow_load_label
                    + ": "
                    + f"{value:.2f} "
                    + f"{snow_load_result['unit']}"
                )

            lines.append(
                report_text("report_source")
                + ": "
                + str(
                    snow_load_result["source"]
                )
            )

    raster_results = (
        (
            "report_average_humidity",
            humidity_result,
        ),
        (
            "report_average_air_temperature",
            temperature_result,
        ),
        (
            "report_average_air_pressure",
            air_pressure_result,
        ),
    )

    for label_key, result in raster_results:
        lines.append("")

        label = report_text(
            label_key
        )

        value_text = format_meteorological_value(
            result
        )

        if value_text is None:
            lines.append(
                label
                + ": "
                + report_text(
                    "report_no_data_available"
                )
            )
            continue

        lines.append(
            f"{label}: {value_text}"
        )

        if result.get("source"):
            lines.append(
                report_text("report_source")
                + ": "
                + str(result["source"])
            )

        if result.get("sampling_method"):
            lines.append(
                report_text(
                    "report_sampling_method"
                )
                + ": "
                + report_sampling_method(
                    result["sampling_method"]
                )
            )

    lines.append("")
    lines.append(
        report_text(
            "report_average_monthly_snow_depth"
        )
        + ":"
    )

    if not snow_depth_results:
        lines.append(
            "  "
            + report_text(
                "report_no_data_available"
            )
        )

    else:
        snow_sources = set()

        for month_name, result in (
            snow_depth_results.items()
        ):
            translated_month_name = (
                report_month_name(
                    month_name
                )
            )
            value_text = format_meteorological_value(
                result,
                default_precision=3,
            )

            if value_text is None:
                lines.append(
                    f"  {translated_month_name}: "
                    + report_text(
                        "report_no_data_available"
                    )
                )
                continue

            sampling_method = result.get(
                "sampling_method"
            )

            if sampling_method:
                lines.append(
                    f"  {translated_month_name}: "
                    f"{value_text} "
                    "["
                    + report_sampling_method(
                        sampling_method
                    )
                    + "]"
                )
            else:
                lines.append(
                    f"  {translated_month_name}: "
                    f"{value_text}"
                )

            if result.get("source"):
                snow_sources.add(
                    result["source"]
                )

        for source_name in sorted(snow_sources):
            lines.append(
                report_text("report_source")
                + ": "
                + str(source_name)
            )

    with open(
        report_path,
        "a",
        encoding="utf-8",
    ) as report_file:
        report_file.write(
            render_markdown_lines(lines)
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
        "project_report.md",
    )

    if not os.path.isfile(report_path):
        raise FileNotFoundError(
            f"Site summary does not exist: {report_path}"
        )

    politics_heading = report_text(
        "report_municipality_political_control"
    )

    lines = [
        "",
        politics_heading,
        "-" * len(politics_heading),
    ]

    municipalities = political_result.get(
        "municipalities",
        [],
    )

    if not municipalities:
        lines.append(
            report_text(
                "report_no_political_data"
            )
        )

    else:
        for municipality in municipalities:
            lines.append("")
            lines.append(
                report_text(
                    "report_municipality"
                )
                + ": "
                + str(
                    municipality["name"]
                )
            )

            lines.append(
                report_text(
                    "report_ruling_parties"
                )
                + ":"
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
                        + report_text(
                            "report_of_municipal_seats"
                        )
                    )

    source_path = political_result.get(
        "source"
    )

    if source_path:
        lines.append("")
        lines.append(
            report_text("report_source")
            + ": "
            + os.path.basename(
                source_path
            )
        )

    with open(
        report_path,
        "a",
        encoding="utf-8",
    ) as report_file:
        report_file.write(
            render_markdown_lines(lines)
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
        "project_report.md",
    )

    bos_heading = report_text(
        "report_bos_land_cover"
    )

    lines = [
        "",
        bos_heading,
        "-" * len(bos_heading),
    ]

    if (
        bos_summary is None
        or bos_summary.get("status") != "available"
    ):
        lines.append(
            report_text(
                "report_no_bos_land_cover_data"
            )
        )

    else:
        lines.append(
            report_text(
                "report_analysis_area"
            )
            + ": "
            + f"{bos_summary['analysis_area_ha']:.3f} ha"
        )

        group_order = (
            (
                "Open field",
                "report_land_cover_open_field",
            ),
            (
                "Peat quarry",
                "report_land_cover_peat_quarry",
            ),
            (
                "Forest",
                "report_land_cover_forest",
            ),
            (
                "Wetland",
                "report_land_cover_wetland",
            ),
            (
                "Rocky terrain",
                "report_land_cover_rocky_terrain",
            ),
            (
                "Other land cover",
                "report_land_cover_other",
            ),
            (
                "No land-cover data",
                "report_land_cover_no_data",
            ),
        )

        areas = bos_summary.get(
            "areas_ha",
            {},
        )

        percentages = bos_summary.get(
            "percentages",
            {},
        )

        for (
            group_name,
            translation_key,
        ) in group_order:

            area_ha = areas.get(
                group_name,
                0.0,
            )

            percentage = percentages.get(
                group_name,
                0.0,
            )

            display_name = report_text(
                translation_key
            )

            lines.append(
                f"{display_name}: "
                f"{percentage:.2f}% "
                f"({area_ha:.3f} ha)"
            )

    with open(
        report_path,
        "a",
        encoding="utf-8",
    ) as report_file:
        report_file.write(
            render_markdown_lines(lines)
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
        "project_report.md",
    )

    potential_heading = report_text(
        "report_project_potential"
    )

    assumptions = project_potential[
        "assumptions"
    ]

    lines = [
        "",
        potential_heading,
        "-" * len(potential_heading),
        (
            report_text(
                "report_suitable_solar_area"
            )
            + ": "
            + f"{project_potential['solar_area_ha']:.2f} ha"
        ),
        (
            report_text(
                "report_estimated_solar_capacity"
            )
            + ": "
            + f"{project_potential['solar_capacity_mwp']:.2f} MWp"
        ),
        (
            report_text(
                "report_suitable_wind_area"
            )
            + ": "
            + f"{project_potential['wind_area_ha']:.2f} ha"
        ),
        (
            report_text(
                "report_estimated_wind_turbines"
            )
            + ": "
            + str(
                project_potential[
                    "wind_turbines"
                ]
            )
        ),
        (
            report_text(
                "report_wind_turbine_capacity"
            )
            + ": "
            + f"{project_potential['wind_turbine_capacity_mw']:.2f} "
            + report_text(
                "report_mw_per_turbine"
            )
        ),
        (
            report_text(
                "report_estimated_wind_capacity"
            )
            + ": "
            + f"{project_potential['wind_capacity_mw']:.2f} MW"
        ),
        (
            report_text(
                "report_combined_project_capacity"
            )
            + ": "
            + f"{project_potential['combined_capacity_mw']:.2f} MW"
        ),
        (
            report_text(
                "report_estimated_ac_capacity"
            )
            + ": "
            + f"{project_potential['estimated_ac_capacity_mw']:.2f} MW"
        ),
        (
            report_text(
                "report_estimated_bess_capacity"
            )
            + ": "
            + f"{project_potential['bess_capacity_mw']:.0f} MW"
        ),
        "",
        report_text(
            "report_potential_calculation_assumptions"
        ),
        (
            report_text(
                "report_solar_power_density"
            )
            + ": "
            + f"{assumptions['solar_mwp_per_hectare']:.2f} MWp/ha"
        ),
        (
            report_text(
                "report_wind_area_per_turbine"
            )
            + ": "
            + f"{assumptions['wind_area_per_turbine_ha']:.2f} ha"
        ),
        (
            report_text(
                "report_minimum_wind_turbine_area"
            )
            + ": "
            + f"{assumptions['wind_single_turbine_minimum_ha']:.2f} ha"
        ),
        (
            report_text(
                "report_dc_ac_ratio"
            )
            + ": "
            + f"{assumptions['dc_ac_ratio']:.2f}"
        ),
        (
            report_text(
                "report_bess_share"
            )
            + ": "
            + f"{assumptions['bess_ac_capacity_fraction'] * 100:.1f}%"
        ),
    ]

    with open(
        report_path,
        "a",
        encoding="utf-8",
    ) as report_file:
        report_file.write(
            render_markdown_lines(lines)
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
        "project_report.md",
    )

    grid_heading = report_text(
        "report_grid_information"
    )

    lines = [
        "",
        grid_heading,
        "-" * len(grid_heading),
    ]

    if (
        grid_proximity_result is None
        or grid_proximity_result.get("status")
        == "unavailable"
    ):
        lines.append(
            report_text(
                "report_grid_not_configured"
            )
        )

    elif (
        grid_proximity_result.get("status")
        == "no_features"
    ):
        lines.append(
            report_text(
                "report_no_grid_infrastructure"
            )
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
                distance_text = report_text(
                    "report_grid_crossing"
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
                    report_text("report_voltage")
                    + f" {voltage_kv:.0f} kV"
                )

            primary_voltage_kv = result.get(
                "primary_voltage_kv"
            )

            if primary_voltage_kv is not None:
                details.append(
                    report_text(
                        "report_primary_voltage"
                    )
                    + f" {primary_voltage_kv:.0f} kV"
                )

            secondary_voltage_kv = result.get(
                "secondary_voltage_kv"
            )

            if secondary_voltage_kv is not None:
                details.append(
                    report_text(
                        "report_secondary_voltage"
                    )
                    + f" {secondary_voltage_kv:.0f} kV"
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
                        report_text(
                            "report_grid_threshold"
                        )
                        + ": "
                        + f"{crossing_distance_m:.0f} m"
                    ),
                ]
            )

        lines.append(
            report_text(
                "report_grid_distance_limitation"
            )
        )

    with open(
        report_path,
        "a",
        encoding="utf-8",
    ) as report_file:
        report_file.write(
            render_markdown_lines(lines)
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
        "project_report.md",
    )

    soil_depth_heading = report_text(
        "report_soil_depth_by_type"
    )

    lines = [
        "",
        soil_depth_heading,
        "-" * len(soil_depth_heading),
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
            report_text(
                "report_soil_depth_not_performed"
            )
        )

    elif soil_depth_result.get("status") != "available":
        lines.append(
            report_text(
                "report_no_soil_depth_information"
            )
        )

    else:
        results = soil_depth_result.get(
            "results",
            [],
        )

        if not results:
            lines.append(
                report_text(
                    "report_no_valid_soil_types"
                )
            )

        for result in results:
            soil_type = result.get(
                "soil_type"
            )

            if not soil_type:
                soil_type = report_text(
                    "report_unknown_soil_type"
                )

            if result.get("status") != "available":
                lines.append(
                    f"{soil_type}: "
                    + report_text(
                        "report_no_valid_soil_depth"
                    )
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
                f"{minimum_m_text}\u2013{maximum_m_text} m "
                f"({minimum_cm_text}\u2013{maximum_cm_text} cm)"
            )

        lines.extend(
            [
                "",
                report_text(
                    "report_soil_depth_source_note"
                ),
            ]
        )

    with open(
        report_path,
        "a",
        encoding="utf-8",
    ) as report_file:
        report_file.write(
            render_markdown_lines(lines)
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
        "project_report.md",
    )

    lines = [
        "",
        report_text(
            "report_custom_estates_heading"
        ),
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
                            report_text(
                                "report_overlap"
                            )
                            + ": "
                            + f"{overlap_area_ha:.2f} ha "
                            + f"({analysis_percentage:.2f}% "
                            + report_text(
                                "report_of_analysis_area"
                            )
                            + ")"
                        ),
                        "",
                    ]
                )

        else:
            lines.extend(
                [
                    report_text(
                        "report_no_intersecting_estates"
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
            report_text(
                "report_unmatched_area"
            )
            + ": "
            + f"{unmatched_area_ha:.2f} ha "
            + f"({unmatched_percentage:.2f}%)"
        )

    elif status == "error":
        error_message = (
            custom_estates_result.get(
                "error"
            )
            or report_text(
                "report_unknown_error"
            )
        )

        lines.append(
            report_text(
                "report_estate_identification_failed"
            )
            + ": "
            + str(error_message)
        )

    else:
        lines.append(
            report_text(
                "report_estate_identification_unavailable"
            )
        )

    with open(
        report_path,
        "a",
        encoding="utf-8",
    ) as report_file:
        report_file.write(
            render_markdown_lines(lines)
        )

    print(
        f"Custom-estate summary appended: "
        f"{report_path}"
    )

    return report_path