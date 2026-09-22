from dataclasses import dataclass


@dataclass
class UserSettings:
    crs_mode: str = "auto"
    crs_override: str | None = None
    units: str = "metric"
    language: str = "en"
    min_ineligible_patch_area_m2: float = 150.0
    contour_interval_m: float = 5.0
    country_code: str = "SE"
    fill_solar_holes: bool = True
    solar_inward_buffer_m: float = 10.0
    slope_thresholds: tuple[float, ...] = (
        11, 11.3, 11.8, 12.5, 13.2, 14,
        14.8, 15.7, 16.7, 17.7, 18.8, 20
    )
    solar_reference_year: int = 2024

    solar_start_month: int = 1
    solar_start_day: int = 1

    solar_end_month: int = 12
    solar_end_day: int = 31

    # ---------------------------------------------------------
    # Project-potential assumptions
    # ---------------------------------------------------------

    solar_mwp_per_hectare: float = 0.9

    wind_area_per_turbine_ha: float = 3.0
    wind_single_turbine_minimum_ha: float = 0.5
    wind_turbine_capacity_mw: float = 3.5

    dc_ac_ratio: float = 1.3

    bess_ac_capacity_fraction: float = 0.2