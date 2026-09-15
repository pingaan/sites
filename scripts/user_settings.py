from dataclasses import dataclass


@dataclass
class UserSettings:
    crs_mode: str = "auto"
    crs_override: str | None = None
    units: str = "metric"
    language: str = "en"
    slope_thresholds: tuple[float, ...] = (
        11, 11.3, 11.8, 12.5, 13.2, 14,
        14.8, 15.7, 16.7, 17.7, 18.8, 20,
    )