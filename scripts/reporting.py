import os

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