import csv
import os
import requests

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsGeometry,
    QgsProject,
    QgsVectorLayer,
)


def get_site_centroid_wgs84(
    site_layer_path,
):
    """
    Calculate the analysis site's combined centroid and
    transform it to WGS 84 for external solar-data services.

    The analysis layer may use any valid working CRS.
    """

    site_layer = QgsVectorLayer(
        site_layer_path,
        "Solar-resource site",
        "ogr",
    )

    if not site_layer.isValid():
        raise ValueError(
            f"Failed to load analysis site: "
            f"{site_layer_path}"
        )

    source_crs = site_layer.crs()

    if not source_crs.isValid():
        raise ValueError(
            "The analysis site has no valid CRS."
        )

    geometries = []

    for feature in site_layer.getFeatures():
        geometry = feature.geometry()

        if geometry is None or geometry.isEmpty():
            continue

        geometries.append(
            QgsGeometry(geometry)
        )

    if not geometries:
        raise ValueError(
            "The analysis site contains no usable geometry."
        )

    combined_geometry = QgsGeometry.unaryUnion(
        geometries
    )

    if (
        combined_geometry is None
        or combined_geometry.isEmpty()
    ):
        raise RuntimeError(
            "Failed to combine the analysis-site geometry."
        )

    centroid_geometry = (
        combined_geometry.centroid()
    )

    if centroid_geometry.isEmpty():
        raise RuntimeError(
            "Failed to calculate the analysis-site centroid."
        )

    centroid_point = centroid_geometry.asPoint()

    target_crs = QgsCoordinateReferenceSystem(
        "EPSG:4326"
    )

    coordinate_transform = QgsCoordinateTransform(
        source_crs,
        target_crs,
        QgsProject.instance().transformContext(),
    )

    centroid_wgs84 = coordinate_transform.transform(
        centroid_point
    )

    longitude = centroid_wgs84.x()
    latitude = centroid_wgs84.y()

    print(
        f"Site centroid for solar-resource data: "
        f"{latitude:.4f}, {longitude:.4f}"
    )

    return {
        "latitude": latitude,
        "longitude": longitude,
    }

def download_strang_data(
    site_layer_path,
    folder_path,
    settings,
):
    """
    Download SMHI STRÅNG irradiance data for the analysis
    site's centroid.

    Failed parameters are reported and skipped without
    stopping the complete site analysis.
    """

    if not settings:
        print(
            "No STRÅNG settings are available for "
            "the selected country."
        )
        return {}

    centroid = get_site_centroid_wgs84(
        site_layer_path
    )

    latitude = centroid["latitude"]
    longitude = centroid["longitude"]

    base_url = settings["base_url"].rstrip(
        "/"
    )

    from_date = settings["from_date"]
    to_date = settings["to_date"]
    parameters = settings["parameters"]

    downloaded_files = {}

    for parameter, description in parameters.items():

        url = (
            f"{base_url}/geotype/point"
            f"/lon/{longitude:.4f}"
            f"/lat/{latitude:.4f}"
            f"/parameter/{parameter}"
            f"/data.json"
        )

        print(
            f"Downloading STRÅNG parameter "
            f"{parameter}: {description}..."
        )

        try:
            response = requests.get(
                url,
                params={
                    "from": from_date,
                    "to": to_date,
                },
                timeout=60,
            )

            response.raise_for_status()
            data = response.json()

        except (
            requests.RequestException,
            ValueError,
        ) as error:
            print(
                f"STRÅNG parameter {parameter} "
                f"could not be downloaded: {error}"
            )

            downloaded_files[parameter] = None
            continue

        if (
            not isinstance(data, list)
            or not data
            or not isinstance(data[0], dict)
        ):
            print(
                f"STRÅNG parameter {parameter} returned "
                f"no usable records."
            )

            downloaded_files[parameter] = None
            continue

        output_path = os.path.join(
            folder_path,
            f"STRÅNG_param_{parameter}.csv",
        )

        field_names = list(
            data[0].keys()
        )

        with open(
            output_path,
            "w",
            newline="",
            encoding="utf-8",
        ) as output_file:
            writer = csv.DictWriter(
                output_file,
                fieldnames=field_names,
                extrasaction="ignore",
            )

            writer.writeheader()
            writer.writerows(data)

        downloaded_files[parameter] = (
            output_path
        )

        print(
            f"STRÅNG parameter {parameter} saved: "
            f"{output_path}"
        )

    return downloaded_files