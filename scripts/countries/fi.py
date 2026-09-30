import re


COUNTRY_CODE = "FI"
COUNTRY_NAME = "Finland"


ESTATE_CONFIG = {
    "schema": "fi",
    "table": "estates",
    "geometry_column": "geom",
    "key_column": "ogc_fid",
    "srid": 3067,
    "group_fields": (
        "kiinteisto",
    ),
}


def parse_estate_reference(value):
    """
    Interpret a Finnish cadastral identifier.

    Accepted formats:
        434-415-1-226
        43441500010226
    """

    supplied_value = value.strip()

    formatted_match = re.fullmatch(
        r"(\d{1,3})\s*-\s*"
        r"(\d{1,3})\s*-\s*"
        r"(\d{1,4})\s*-\s*"
        r"(\d{1,4})",
        supplied_value,
    )

    if formatted_match:
        municipality, village, estate, unit = (
            formatted_match.groups()
        )

        municipality = municipality.zfill(3)
        village = village.zfill(3)
        estate = estate.zfill(4)
        unit = unit.zfill(4)

        normalized = (
            municipality
            + village
            + estate
            + unit
        )

    else:
        normalized = re.sub(
            r"\s+",
            "",
            supplied_value,
        )

        if not re.fullmatch(
            r"\d{14}",
            normalized,
        ):
            raise ValueError(
                "A Finnish estate identifier must use "
                "either 434-415-1-226 or the normalized "
                "14-digit form 43441500010226."
            )

        municipality = normalized[0:3]
        village = normalized[3:6]
        estate = normalized[6:10]
        unit = normalized[10:14]

    display_name = (
        f"{municipality}-"
        f"{village}-"
        f"{int(estate)}-"
        f"{int(unit)}"
    )

    return {
        "display_name": display_name,
        "folder_name": display_name,
        "filter_groups": [
            {
                "kiinteisto": normalized,
            }
        ],
    }