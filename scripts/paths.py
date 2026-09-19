import os
import platform


def get_paths():
    """
    Return the filesystem paths used by the application
    for the current operating system.
    """

    os_name = platform.system()

    if os_name == "Windows":

        gis_root = r"H:\gis_data"
        base_path = os.path.join(gis_root, "anna2.0")

        paths = {
            "data_path": base_path,
            "csv_file": os.path.join(
                base_path,
                "estates.csv",
            ),
            "estates_layer": os.path.join(
                base_path,
                "estates.shp",
            ),
            "path_dem": os.path.join(
                gis_root,
                "DEM_1m",
            ),
            "pot_path": os.path.join(
                gis_root,
                "Potentiella fastigheter",
            ),
            "svg_path": (
                r"C:\Program Files\QGIS 3.44.14"
                r"\apps\qgis-ltr\svg\arrows\Arrow_05.svg"
            ),
            "empty_shapefile_path": os.path.join(
                base_path,
                "artportal_red_empty.shp",
            ),
        }

    elif os_name == "Darwin":

        base_path = (
            "/Users/pingaan/Dropbox/Documents/"
            "GIS-data (sverige)/anna2.0"
        )

        paths = {
            "data_path": base_path,
            "csv_file": os.path.join(
                base_path,
                "estates.csv",
            ),
            "estates_layer": os.path.join(
                base_path,
                "estates.shp",
            ),
            "path_dem": os.path.normpath(
                "/Users/pingaan/Dropbox/Documents/"
                "GIS-data (sverige)/DEM_1m/"
            ),
            "pot_path": os.path.join(
                "/Users/pingaan/Dropbox/Documents/"
                "GIS-data (sverige)",
                "Potentiella fastigheter",
            ),
            "svg_path": (
                "/Applications/QGIS.app/Contents/"
                "Resources/svg/arrows/Arrow_05.svg"
            ),
            "empty_shapefile_path": os.path.join(
                base_path,
                "artportal_red_empty.shp",
            ),
        }

    elif os_name == "Linux":

        base_path = "/run/media/pingaan/GIS Data/gis_data/anna2.0"

        paths = {
            "data_path": base_path,
            "csv_file": os.path.join(
                base_path,
                "estates.csv",
            ),
            "estates_layer": os.path.join(
                base_path,
                "estates.shp",
            ),
            "path_dem": os.path.normpath(
                "/run/media/pingaan/GIS Data/gis_data//DEM_1m/"
            ),
            "pot_path": os.path.join(
                "/run/media/pingaan/GIS Data/gis_data/",
                "Potentiella fastigheter",
            ),
            "svg_path": (
                "/usr/share/qgis/svg/arrows/Arrow_05.svg"
            ),
            "empty_shapefile_path": os.path.join(
                base_path,
                "artportal_red_empty.shp",
            ),
        }

    else:
        raise OSError(
            f"Unsupported operating system: {os_name}"
        )

    paths["dem_index_crs"] = "EPSG:3006"

    return paths