from copy import deepcopy

from scripts.translations import (
    translated_layer_name,
)

from qgis.PyQt.QtCore import (
    QSettings,
)


def layer_settings_prefix(
    country_code,
    layer_definition,
):
    """
    Return the stable settings path for one country layer.
    """

    database = layer_definition[
        "database"
    ]

    return (
        "layers/"
        f"{country_code}/"
        f"{database['schema']}/"
        f"{database['table']}"
    )


def read_float_setting(
    settings,
    key,
    default_value,
):
    """
    Read a numeric QSettings value safely.
    """

    value = settings.value(
        key,
        default_value,
    )

    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default_value)


def apply_layer_settings(
    country_code,
    layer_definitions,
    style_resolver=None,
    language="en",
):
    """
    Copy the country definitions and apply user overrides.

    The imported country module remains unchanged.
    """

    country_code = str(
        country_code
    ).strip().upper()

    settings = QSettings(
        "Sovra",
        "Sovra",
    )

    configured_layers = deepcopy(
        layer_definitions
    )

    hard_count = 0
    indicator_count = 0

    for definition in configured_layers:
        definition["display_name"] = (
            translated_layer_name(
                definition=definition,
                language=language,
            )
        )
                
        prefix = layer_settings_prefix(
            country_code,
            definition,
        )

        definition["solar_buffer_m"] = (
            read_float_setting(
                settings=settings,
                key=(
                    f"{prefix}/"
                    "solar_buffer_m"
                ),
                default_value=definition[
                    "solar_buffer_m"
                ],
            )
        )

        definition["wind_buffer_m"] = (
            read_float_setting(
                settings=settings,
                key=(
                    f"{prefix}/"
                    "wind_buffer_m"
                ),
                default_value=definition[
                    "wind_buffer_m"
                ],
            )
        )

        treatment = str(
            settings.value(
                f"{prefix}/treatment",
                "hard",
            )
        ).strip().lower()

        if treatment not in {
            "hard",
            "indicator",
        }:
            treatment = "hard"

        definition["treatment"] = (
            treatment
        )

        default_style = (
            style_resolver(definition)
            if style_resolver is not None
            else {}
        )

        default_colour = default_style.get(
            "color",
            "#d27800",
        )

        definition["colour"] = str(
            settings.value(
                f"{prefix}/colour",
                default_colour,
            )
        ).strip()

        if treatment == "indicator":
            indicator_count += 1
        else:
            hard_count += 1

    print(
        "Country-layer settings applied: "
        f"{hard_count} hard constraint(s), "
        f"{indicator_count} indicator(s)."
    )

    return configured_layers