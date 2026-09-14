from dataclasses import dataclass


@dataclass
class UserSettings:
    crs_mode: str = "auto"
    crs_override: str | None = None
    units: str = "metric"
    language: str = "en"