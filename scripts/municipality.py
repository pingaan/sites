import os

import pandas as pd

from qgis.core import QgsVectorLayer


def normalize_municipality_name(value):
    """
    Normalise municipality names for case-insensitive matching.
    """

    if value is None:
        return None

    return str(value).strip().casefold()


def analyse_municipality_politics(
    site_layer_path,
    data_path,
    political_settings,
):
    """
    Match the analysis site to the configured political CSV.

    Returns the ruling parties and their municipal-seat shares.
    """

    result = {
        "status": "missing",
        "municipalities": [],
        "source": None,
    }

    if not political_settings:
        print(
            "Municipality politics unavailable: "
            "no country source configured."
        )
        return result

    csv_path = os.path.join(
        data_path,
        political_settings["source"],
    )

    result["source"] = csv_path

    if not os.path.isfile(csv_path):
        raise FileNotFoundError(
            f"Configured political CSV does not exist: "
            f"{csv_path}"
        )

    site = QgsVectorLayer(
        site_layer_path,
        "Political municipality lookup",
        "ogr",
    )

    if not site.isValid():
        raise ValueError(
            f"Failed to load analysis site: "
            f"{site_layer_path}"
        )

    site_field = political_settings[
        "site_municipality_field"
    ]

    site_field_names = {
        field.name()
        for field in site.fields()
    }

    if site_field not in site_field_names:
        print(
            "Municipality politics unavailable: "
            f"site field '{site_field}' does not exist."
        )
        return result

    municipality_names = set()

    for feature in site.getFeatures():
        municipality_name = normalize_municipality_name(
            feature[site_field]
        )

        if municipality_name:
            municipality_names.add(
                municipality_name
            )

    if not municipality_names:
        print(
            "Municipality politics unavailable: "
            "the site contains no municipality name."
        )
        return result

    table = pd.read_csv(
        csv_path,
        encoding="utf-8",
    )

    municipality_field = political_settings[
        "csv_municipality_field"
    ]

    control_field = political_settings[
        "control_field"
    ]

    total_seats_field = political_settings[
        "total_seats_field"
    ]

    required_fields = {
        municipality_field,
        control_field,
        total_seats_field,
    }

    missing_fields = (
        required_fields
        - set(table.columns)
    )

    if missing_fields:
        raise ValueError(
            "Political CSV is missing columns: "
            + ", ".join(
                sorted(missing_fields)
            )
        )

    table["_normalised_municipality"] = (
        table[municipality_field]
        .apply(normalize_municipality_name)
    )

    matches = table[
        table["_normalised_municipality"].isin(
            municipality_names
        )
    ]

    if matches.empty:
        print(
            "Municipality politics unavailable: "
            "no CSV municipality matched the site."
        )
        return result

    party_names = political_settings[
        "party_names"
    ]

    municipalities = []

    for _, row in matches.iterrows():
        control_value = str(
            row[control_field]
        )

        ruling_party_codes = [
            party.strip()
            for party in control_value.split("+")
            if party.strip()
        ]

        try:
            total_seats = float(
                row[total_seats_field]
            )
        except (TypeError, ValueError):
            total_seats = 0

        ruling_parties = []

        for party_code in ruling_party_codes:
            party_name = party_names.get(
                party_code,
                f"Minor local party ({party_code})",
            )

            influence = None

            if (
                party_code in party_names
                and party_code in table.columns
                and total_seats > 0
            ):
                try:
                    party_seats = float(
                        row[party_code]
                    )

                    influence = round(
                        party_seats
                        / total_seats
                        * 100,
                        1,
                    )

                except (TypeError, ValueError):
                    influence = None

            ruling_parties.append(
                {
                    "code": party_code,
                    "name": party_name,
                    "influence_percent": influence,
                }
            )

        municipality_result = {
            "name": str(
                row[municipality_field]
            ),
            "ruling_parties": ruling_parties,
        }

        municipalities.append(
            municipality_result
        )

        print(
            f"Municipality political data found: "
            f"{municipality_result['name']}"
        )

        for party in ruling_parties:
            if party["influence_percent"] is None:
                print(
                    f"  {party['name']}"
                )
            else:
                print(
                    f"  {party['name']}: "
                    f"{party['influence_percent']:.1f}%"
                )

    result["status"] = "available"
    result["municipalities"] = municipalities

    return result