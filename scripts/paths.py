import os
import platform


def get_paths():
    """
    Return the filesystem paths used by the application
    for the current operating system.
    """

    os_name = platform.system()

    if os_name == "Windows":

        base_path = r"D:\Dropbox\GIS-data (sverige)\anna2.0"

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
                r"D:\Dropbox\GIS-data (sverige)\DEM_1m"
            ),
            "pot_path": os.path.join(
                r"D:\Dropbox\GIS-data (sverige)",
                "Potentiella fastigheter",
            ),
            "svg_path": (
                r"C:\Program Files\QGIS 3.28.13"
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

        base_path = "/media/GIS-Data/gis_data/anna2.0"

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
                "/media/GIS-Data/gis_data/DEM_1m/"
            ),
            "pot_path": os.path.join(
                "/media/GIS-Data/gis_data",
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

    return paths