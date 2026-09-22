from datetime import (
    date,
    datetime,
    time,
    timedelta,
    timezone,
)

from astral import Observer
from astral.sun import elevation


def calculate_daylight_elevations(
    latitude,
    longitude,
    current_date,
):
    """
    Calculate solar elevation at every whole UTC hour.

    Only elevations above the horizon are returned.
    """

    observer = Observer(
        latitude=latitude,
        longitude=longitude,
    )

    elevations = []

    for hour in range(24):
        moment = datetime.combine(
            current_date,
            time(
                hour=hour,
                tzinfo=timezone.utc,
            ),
        )

        solar_elevation = elevation(
            observer,
            moment,
        )

        if solar_elevation > 0:
            elevations.append(
                solar_elevation
            )

    return elevations


def calculate_average_solar_elevation(
    latitude,
    longitude,
    reference_year,
    start_month,
    start_day,
    end_month,
    end_day,
):
    """
    Calculate Anna's average daytime solar elevation.

    Solar elevation is sampled at every whole hour between the
    configured start and end dates. Night-time values are excluded.
    """

    if not -90 <= latitude <= 90:
        raise ValueError(
            f"Invalid latitude: {latitude}"
        )

    if not -180 <= longitude <= 180:
        raise ValueError(
            f"Invalid longitude: {longitude}"
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

    if end_date < start_date:
        raise ValueError(
            "Solar-position end date precedes its start date."
        )

    elevations = []

    current_date = start_date

    while current_date <= end_date:
        elevations.extend(
            calculate_daylight_elevations(
                latitude=latitude,
                longitude=longitude,
                current_date=current_date,
            )
        )

        current_date += timedelta(days=1)

    if not elevations:
        return None

    average_elevation = (
        sum(elevations) / len(elevations)
    )

    print(
        "Average daytime solar elevation: "
        f"{average_elevation:.2f} degrees "
        f"({start_date:%d %b}–{end_date:%d %b})"
    )

    return average_elevation