import os
import psycopg2

import pandas as pd

from psycopg2 import sql
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

    database_config = political_settings.get(
        "database"
    )

    if database_config is None:
        raise ValueError(
            "Political settings have no PostGIS "
            "database configuration."
        )

    result["source"] = (
        f"{database_config['schema']}."
        f"{database_config['table']}"
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

    configured_site_field = political_settings[
        "site_municipality_field"
    ]

    site_field = next(
        (
            field.name()
            for field in site.fields()
            if field.name().casefold()
            == configured_site_field.casefold()
        ),
        None,
    )

    if site_field is None:
        print(
            "Municipality politics unavailable: "
            f"site field '{configured_site_field}' "
            "does not exist."
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

    municipality_field = political_settings[
        "csv_municipality_field"
    ]

    control_field = political_settings[
        "control_field"
    ]

    total_seats_field = political_settings[
        "total_seats_field"
    ]

    password = os.environ.get(
        "SITES_DB_PASSWORD"
    )

    if not password:
        raise RuntimeError(
            "SITES_DB_PASSWORD has not been set."
        )

    connection = psycopg2.connect(
        host=os.environ.get(
            "SITES_DB_HOST",
            "127.0.0.1",
        ),
        port=int(
            os.environ.get(
                "SITES_DB_PORT",
                "5433",
            )
        ),
        dbname=os.environ.get(
            "SITES_DB_NAME",
            "sites",
        ),
        user=os.environ.get(
            "SITES_DB_USER",
            "sites_app",
        ),
        password=password,
        connect_timeout=15,
        application_name=(
            "Sites municipality politics"
        ),
    )

    party_columns = []

    for party_code in political_settings[
        "party_names"
    ]:
        party_columns.append(
            sql.SQL("{} AS {}").format(
                sql.Identifier(
                    party_code.lower()
                ),
                sql.Identifier(party_code),
            )
        )

    selected_columns = [
        sql.SQL("{} AS {}").format(
            sql.Identifier("municipality"),
            sql.Identifier(
                municipality_field
            ),
        ),
        sql.SQL("{} AS {}").format(
            sql.Identifier(
                "political_control"
            ),
            sql.Identifier(control_field),
        ),
        sql.SQL("{} AS {}").format(
            sql.Identifier("total_seats"),
            sql.Identifier(
                total_seats_field
            ),
        ),
        *party_columns,
    ]

    query = sql.SQL(
        """
        SELECT {columns}
        FROM {schema}.{table}
        WHERE
            lower(btrim(municipality))
            = ANY(%s)
        ORDER BY municipality
        """
    ).format(
        columns=sql.SQL(", ").join(
            selected_columns
        ),
        schema=sql.Identifier(
            database_config["schema"]
        ),
        table=sql.Identifier(
            database_config["table"]
        ),
    )

    try:
        table = pd.read_sql_query(
            query.as_string(connection),
            connection,
            params=(
                sorted(municipality_names),
            ),
        )

    finally:
        connection.close()

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