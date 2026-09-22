import math
import os

from qgis.core import (
    QgsUnitTypes,
    QgsVectorLayer,
)


def calculate_candidate_area_hectares(
    candidate_path,
    technology,
):
    """
    Calculate the total polygon area of an energy candidate
    layer in hectares.

    Empty candidate layers correctly return zero.
    """

    if not os.path.isfile(candidate_path):
        raise FileNotFoundError(
            f"{technology.capitalize()} candidate layer "
            f"does not exist: {candidate_path}"
        )

    layer = QgsVectorLayer(
        candidate_path,
        f"{technology.capitalize()} candidate area",
        "ogr",
    )

    if not layer.isValid():
        raise ValueError(
            f"Failed to load {technology} candidate layer: "
            f"{candidate_path}"
        )

    if not layer.crs().isValid():
        raise ValueError(
            f"The {technology} candidate layer has no valid CRS."
        )

    if layer.crs().isGeographic():
        raise ValueError(
            f"The {technology} candidate layer must use a "
            f"projected CRS for area calculations."
        )

    square_metre_factor = QgsUnitTypes.fromUnitToUnitFactor(
        layer.crs().mapUnits(),
        QgsUnitTypes.DistanceMeters,
    ) ** 2

    total_square_metres = 0.0

    for feature in layer.getFeatures():

        geometry = feature.geometry()

        if geometry is None or geometry.isEmpty():
            continue

        total_square_metres += (
            geometry.area()
            * square_metre_factor
        )

    return total_square_metres / 10000.0


def calculate_project_potential(
    solar_candidate_path,
    wind_candidate_path,
    settings,
):
    """
    Estimate solar, wind, grid and BESS potential using the
    current user-configurable assumptions.

    This preserves Anna's original calculation logic without
    depending on layers being loaded into QgsProject.
    """

    solar_density = settings.solar_mwp_per_hectare

    wind_area_per_turbine = (
        settings.wind_area_per_turbine_ha
    )

    wind_minimum_area = (
        settings.wind_single_turbine_minimum_ha
    )

    turbine_capacity = (
        settings.wind_turbine_capacity_mw
    )

    dc_ac_ratio = settings.dc_ac_ratio

    bess_fraction = (
        settings.bess_ac_capacity_fraction
    )

    if solar_density < 0:
        raise ValueError(
            "Solar MWp per hectare cannot be negative."
        )

    if wind_area_per_turbine <= 0:
        raise ValueError(
            "Wind area per turbine must be greater than zero."
        )

    if wind_minimum_area < 0:
        raise ValueError(
            "The minimum wind area cannot be negative."
        )

    if turbine_capacity < 0:
        raise ValueError(
            "Wind turbine capacity cannot be negative."
        )

    if dc_ac_ratio <= 0:
        raise ValueError(
            "The DC/AC ratio must be greater than zero."
        )

    if bess_fraction < 0:
        raise ValueError(
            "The BESS capacity fraction cannot be negative."
        )

    solar_area_ha = calculate_candidate_area_hectares(
        candidate_path=solar_candidate_path,
        technology="solar",
    )

    wind_area_ha = calculate_candidate_area_hectares(
        candidate_path=wind_candidate_path,
        technology="wind",
    )

    # ---------------------------------------------------------
    # Solar potential
    # ---------------------------------------------------------

    solar_capacity_mwp = (
        solar_area_ha
        * solar_density
    )

    # ---------------------------------------------------------
    # Wind potential
    #
    # Preserve Anna's special rule:
    #   > minimum and < normal spacing = one turbine
    #   >= normal spacing             = whole turbines by area
    # ---------------------------------------------------------

    if (
        wind_area_ha > wind_minimum_area
        and wind_area_ha < wind_area_per_turbine
    ):
        wind_turbines = 1

    elif wind_area_ha >= wind_area_per_turbine:
        wind_turbines = math.floor(
            wind_area_ha
            / wind_area_per_turbine
        )

    else:
        wind_turbines = 0

    wind_capacity_mw = (
        wind_turbines
        * turbine_capacity
    )

    # ---------------------------------------------------------
    # Combined project estimate
    #
    # Anna treated solar MWp and wind MW together as the
    # project's combined nameplate/DC-side capacity.
    # ---------------------------------------------------------

    combined_capacity_mw = (
        solar_capacity_mwp
        + wind_capacity_mw
    )

    estimated_ac_capacity_mw = (
        combined_capacity_mw
        / dc_ac_ratio
    )

    bess_capacity_mw = round(
        estimated_ac_capacity_mw
        * bess_fraction
    )

    result = {
        "solar_area_ha": solar_area_ha,
        "solar_capacity_mwp": solar_capacity_mwp,
        "wind_area_ha": wind_area_ha,
        "wind_turbines": wind_turbines,
        "wind_turbine_capacity_mw": turbine_capacity,
        "wind_capacity_mw": wind_capacity_mw,
        "combined_capacity_mw": combined_capacity_mw,
        "estimated_ac_capacity_mw": (
            estimated_ac_capacity_mw
        ),
        "bess_capacity_mw": bess_capacity_mw,
        "assumptions": {
            "solar_mwp_per_hectare": solar_density,
            "wind_area_per_turbine_ha": (
                wind_area_per_turbine
            ),
            "wind_single_turbine_minimum_ha": (
                wind_minimum_area
            ),
            "wind_turbine_capacity_mw": (
                turbine_capacity
            ),
            "dc_ac_ratio": dc_ac_ratio,
            "bess_ac_capacity_fraction": (
                bess_fraction
            ),
        },
    }

    print(
        f"Solar potential: "
        f"{solar_area_ha:.2f} ha — "
        f"{solar_capacity_mwp:.2f} MWp."
    )

    print(
        f"Wind potential: "
        f"{wind_area_ha:.2f} ha — "
        f"{wind_turbines} turbine(s), "
        f"{wind_capacity_mw:.2f} MW."
    )

    print(
        f"Combined project capacity: "
        f"{combined_capacity_mw:.2f} MW."
    )

    print(
        f"Estimated AC capacity: "
        f"{estimated_ac_capacity_mw:.2f} MW."
    )

    print(
        f"Estimated BESS capacity: "
        f"{bess_capacity_mw} MW."
    )

    return result