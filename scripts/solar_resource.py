import csv
import os
import requests
import math
import requests
import pandas as pd

from osgeo import gdal
from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsGeometry,
    QgsProject,
    QgsVectorLayer,
)

gdal.UseExceptions()

SOLARGIS_RESOURCE_DEFINITIONS = {
    "dif": {
        "name": "Diffuse horizontal irradiation",
        "unit": "kWh/m²/day",
        "yearly_unit": "kWh/m²/year",
        "daily_total": True,
    },
    "dni": {
        "name": "Direct normal irradiation",
        "unit": "kWh/m²/day",
        "yearly_unit": "kWh/m²/year",
        "daily_total": True,
    },
    "ghi": {
        "name": "Global horizontal irradiation",
        "unit": "kWh/m²/day",
        "yearly_unit": "kWh/m²/year",
        "daily_total": True,
    },
    "gti": {
        "name": "Global tilted irradiation",
        "unit": "kWh/m²/day",
        "yearly_unit": "kWh/m²/year",
        "daily_total": True,
    },
    "opta": {
        "name": "Optimum tilt angle",
        "unit": "degrees",
        "yearly_unit": None,
        "daily_total": False,
    },
    "pvout": {
        "name": "Specific photovoltaic power output",
        "unit": "kWh/kWp/day",
        "yearly_unit": "kWh/kWp/year",
        "daily_total": True,
    },
    "temperature": {
        "name": "Average air temperature",
        "unit": "°C",
        "yearly_unit": None,
        "daily_total": False,
    },
}

STRANG_PARAMETER_IDS = {
    "ghi": 117,
    "dni": 118,
    "dif": 122,
}

def collect_solargis_resources(
    raster_paths,
    longitude,
    latitude,
):
    """
    Sample all configured Global Solar Atlas rasters.

    Daily energy values are also converted into yearly totals.
    Missing raster coverage is represented by None so another
    provider, such as STRÅNG, can later be attempted.

    Parameters
    ----------
    raster_paths : dict
        SolarGIS raster paths from paths["solargis_rasters"].

    longitude : float
        Site longitude in EPSG:4326.

    latitude : float
        Site latitude in EPSG:4326.

    Returns
    -------
    dict
        Solar-resource results keyed by parameter name.
    """

    results = {}

    print("Reading Global Solar Atlas data...")

    for key, definition in SOLARGIS_RESOURCE_DEFINITIONS.items():

        if key not in raster_paths:
            raise KeyError(
                f"SolarGIS raster path is missing for: {key}"
            )

        raster_path = raster_paths[key]

        value = sample_solargis_raster(
            raster_path=raster_path,
            longitude=longitude,
            latitude=latitude,
        )

        result = {
            "name": definition["name"],
            "value": value,
            "unit": definition["unit"],
            "yearly_value": None,
            "yearly_unit": definition["yearly_unit"],
            "source": None,
            "raster_path": raster_path,
            "status": "missing",
        }

        if value is None:
            print(
                f"{definition['name']}: "
                "no Global Solar Atlas data available."
            )

            results[key] = result
            continue

        result["source"] = "Global Solar Atlas"
        result["status"] = "available"

        print(
            f"{definition['name']}: "
            f"{value:.3f} {definition['unit']}"
        )

        if definition["daily_total"]:
            yearly_value = value * 365

            result["yearly_value"] = yearly_value

            print(
                f"{definition['name']}: "
                f"{yearly_value:.1f} "
                f"{definition['yearly_unit']}"
            )

        results[key] = result

    return results

def fetch_strang_parameter(
    parameter_id,
    longitude,
    latitude,
    output_folder,
    start_date="2010-01-01",
    end_date="2023-12-31",
):
    """
    Download and summarise one SMHI STRÅNG parameter.

    STRÅNG values are converted into average daily and yearly
    irradiation totals to match the SolarGIS result structure.

    Returns
    -------
    dict | None
        Daily and yearly values, or None when STRÅNG data could
        not be retrieved.
    """

    url = (
        "https://opendata-download-metanalys.smhi.se/"
        "api/category/strang1g/version/1/"
        "geotype/point/"
        f"lon/{longitude:.4f}/"
        f"lat/{latitude:.4f}/"
        f"parameter/{parameter_id}/"
        "data.json"
    )

    try:
        response = requests.get(
            url,
            params={
                "from": start_date,
                "to": end_date,
            },
            timeout=120,
        )

        response.raise_for_status()

        data = response.json()

    except (
        requests.RequestException,
        ValueError,
    ) as error:
        print(
            f"STRÅNG parameter {parameter_id} failed: "
            f"{error}"
        )
        return None

    if not isinstance(data, list) or not data:
        print(
            f"STRÅNG parameter {parameter_id}: "
            "no data returned."
        )
        return None

    table = pd.DataFrame(data)

    required_columns = {
        "date_time",
        "value",
    }

    if not required_columns.issubset(table.columns):
        print(
            f"STRÅNG parameter {parameter_id}: "
            "unexpected response structure."
        )
        return None

    table["date_time"] = pd.to_datetime(
        table["date_time"],
        errors="coerce",
    )

    table["value"] = pd.to_numeric(
        table["value"],
        errors="coerce",
    )

    table = table.dropna(
        subset=[
            "date_time",
            "value",
        ]
    )

    table = table[
        table["value"] > 0
    ]

    if table.empty:
        print(
            f"STRÅNG parameter {parameter_id}: "
            "no usable values returned."
        )
        return None

    csv_path = os.path.join(
        output_folder,
        f"STRÅNG_param_{parameter_id}.csv",
    )

    table.to_csv(
        csv_path,
        index=False,
        encoding="utf-8",
    )

    table = table.set_index(
        "date_time"
    )

    daily_totals_wh = (
        table["value"]
        .resample("D")
        .sum()
    )

    daily_totals_wh = daily_totals_wh[
        daily_totals_wh > 0
    ]

    if daily_totals_wh.empty:
        print(
            f"STRÅNG parameter {parameter_id}: "
            "no complete daily values available."
        )
        return None

    average_daily_kwh = (
        daily_totals_wh.mean() / 1000
    )

    average_yearly_kwh = (
        average_daily_kwh * 365
    )

    return {
        "daily_value": average_daily_kwh,
        "yearly_value": average_yearly_kwh,
        "csv_path": csv_path,
    }


def apply_strang_fallback(
    solar_resource_data,
    longitude,
    latitude,
    output_folder,
):
    """
    Replace missing SolarGIS irradiation values with STRÅNG.

    SolarGIS remains the primary source. STRÅNG is contacted only
    for missing DIF, DNI, or GHI values.
    """

    resolved_data = {
        key: value.copy()
        for key, value in solar_resource_data.items()
    }

    fallback_required = False

    for key, parameter_id in STRANG_PARAMETER_IDS.items():

        result = resolved_data.get(key)

        if result is None:
            continue

        if result["value"] is not None:
            continue

        fallback_required = True

        print(
            f"{result['name']}: attempting STRÅNG fallback..."
        )

        strang_result = fetch_strang_parameter(
            parameter_id=parameter_id,
            longitude=longitude,
            latitude=latitude,
            output_folder=output_folder,
        )

        if strang_result is None:
            print(
                f"{result['name']}: no data available "
                "from SolarGIS or STRÅNG."
            )
            continue

        result["value"] = strang_result["daily_value"]
        result["yearly_value"] = strang_result["yearly_value"]
        result["source"] = "SMHI STRÅNG"
        result["status"] = "available"
        result["strang_parameter"] = parameter_id
        result["strang_csv_path"] = strang_result["csv_path"]

        print(
            f"{result['name']} — SMHI STRÅNG: "
            f"{result['value']:.3f} {result['unit']}"
        )

        print(
            f"{result['name']} — SMHI STRÅNG: "
            f"{result['yearly_value']:.1f} "
            f"{result['yearly_unit']}"
        )
        
    # ---------------------------------------------------------
    # Derive PVOUT from STRÅNG GHI using Anna's original factor
    # ---------------------------------------------------------

    ghi_result = resolved_data.get("ghi")
    pvout_result = resolved_data.get("pvout")

    if (
        pvout_result is not None
        and pvout_result["value"] is None
        and ghi_result is not None
        and ghi_result["yearly_value"] is not None
        and ghi_result["source"] == "SMHI STRÅNG"
    ):
        pvout_yearly = (
            ghi_result["yearly_value"] * 1.053
        )

        pvout_daily = (
            pvout_yearly / 365
        )

        pvout_result["value"] = pvout_daily
        pvout_result["yearly_value"] = pvout_yearly
        pvout_result["source"] = (
            "Derived from SMHI STRÅNG GHI"
        )
        pvout_result["status"] = "estimated"
        pvout_result["derived_from"] = "ghi"
        pvout_result["derivation_factor"] = 1.053

        print(
            "Specific photovoltaic power output — "
            "derived from SMHI STRÅNG GHI: "
            f"{pvout_daily:.3f} "
            f"{pvout_result['unit']}"
        )

        print(
            "Specific photovoltaic power output — "
            "derived from SMHI STRÅNG GHI: "
            f"{pvout_yearly:.1f} "
            f"{pvout_result['yearly_unit']}"
        )
    if not fallback_required:
        print(
            "STRÅNG fallback not required: "
            "SolarGIS irradiation data is available."
        )

    # Explicitly report parameters which STRÅNG cannot replace.
    for key, result in resolved_data.items():

        if result["value"] is not None:
            continue

        if key in STRANG_PARAMETER_IDS:
            continue

        print(
            f"{result['name']}: no data available. "
            "No STRÅNG equivalent exists."
        )

    return resolved_data

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

def sample_solargis_raster(
    raster_path,
    longitude,
    latitude,
):
    """
    Sample one SolarGIS raster cell at a WGS 84 coordinate.

    Parameters
    ----------
    raster_path : str
        Path to a SolarGIS GeoTIFF.

    longitude : float
        Longitude in EPSG:4326.

    latitude : float
        Latitude in EPSG:4326.

    Returns
    -------
    float | None
        The raster value, or None when the coordinate is outside
        the raster coverage or the selected cell contains NoData.
    """

    if not os.path.isfile(raster_path):
        raise FileNotFoundError(
            f"SolarGIS raster does not exist: {raster_path}"
        )

    dataset = None

    try:
        dataset = gdal.Open(
            raster_path,
            gdal.GA_ReadOnly,
        )

        if dataset is None:
            raise RuntimeError(
                f"Failed to open SolarGIS raster: {raster_path}"
            )

        geo_transform = dataset.GetGeoTransform()

        inverse_transform = gdal.InvGeoTransform(
            geo_transform
        )

        if inverse_transform is None:
            raise RuntimeError(
                f"Could not invert raster transformation: "
                f"{raster_path}"
            )

        pixel_x_float, pixel_y_float = (
            gdal.ApplyGeoTransform(
                inverse_transform,
                longitude,
                latitude,
            )
        )

        pixel_x = math.floor(pixel_x_float)
        pixel_y = math.floor(pixel_y_float)

        # The coordinate is outside SolarGIS coverage.
        if (
            pixel_x < 0
            or pixel_y < 0
            or pixel_x >= dataset.RasterXSize
            or pixel_y >= dataset.RasterYSize
        ):
            return None

        band = dataset.GetRasterBand(1)

        if band is None:
            raise RuntimeError(
                f"SolarGIS raster has no first band: "
                f"{raster_path}"
            )

        sample = band.ReadAsArray(
            pixel_x,
            pixel_y,
            1,
            1,
        )

        if sample is None or sample.size == 0:
            return None

        value = float(sample[0, 0])

        # SolarGIS primarily represents missing coverage using NaN.
        if not math.isfinite(value):
            return None

        no_data_value = band.GetNoDataValue()

        if (
            no_data_value is not None
            and math.isfinite(no_data_value)
            and math.isclose(
                value,
                no_data_value,
                rel_tol=0.0,
                abs_tol=1e-12,
            )
        ):
            return None

        return value

    finally:
        dataset = None

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