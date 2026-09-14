from qgis.core import QgsApplication, Qgis

from scripts.qgis_setup import initialize_qgis, shutdown_qgis
from scripts.user_settings import UserSettings
from scripts.paths import get_paths
from scripts.site_selection import (
    select_site_source,
    parse_estate,
    sequential_search,
)

estate = ""

custom_polygon = None


def main():

    settings = UserSettings()
    paths = get_paths()

    print("Starting solar site analysis...")

    qgs = initialize_qgis()

    try:

        print(f"QGIS version: {Qgis.QGIS_VERSION}")

        buffer_algorithm = (
            QgsApplication.processingRegistry()
            .algorithmById("native:buffer")
        )

        if buffer_algorithm is None:
            raise RuntimeError(
                "QGIS Processing failed to initialise."
            )

        print("QGIS Processing is ready.")

        site_source = select_site_source(
            estate,
            custom_polygon,
        )

        if site_source["type"] == "estate":

            match = parse_estate(
                site_source["estate"]
            )

            print(
                f"Searching for estate: {match}"
            )

            row_indices = sequential_search(
                paths["csv_file"],
                match,
            )

            if row_indices is None:

                print(
                    "No estate found by that entry."
                )

            else:

                print(
                    f"Estate located at indices: "
                    f"{row_indices}"
                )

        elif site_source["type"] == "custom_polygon":

            print(
                "Custom polygon selected."
            )

    finally:

        shutdown_qgis(qgs)

    print("QGIS shut down cleanly.")


if __name__ == "__main__":
    main()