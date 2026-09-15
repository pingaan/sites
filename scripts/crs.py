import math

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsProject,
    QgsVectorLayer,
)


def resolve_working_crs(settings, site_path):
    """
    Resolve the working CRS using UserSettings.

    An explicit override takes precedence.
    Auto mode selects a WGS 84 / UTM CRS from the
    centre of the site's bounding box.

    Returns
    -------
    QgsCoordinateReferenceSystem
        Working CRS for subsequent processing.
    """

    # ---------------------------------------------------------
    # Explicit CRS from settings
    # ---------------------------------------------------------

    if settings.crs_override is not None:
        override = settings.crs_override.strip()

        working_crs = QgsCoordinateReferenceSystem(override)

        if not working_crs.isValid():
            raise ValueError(
                f"Invalid CRS override: {settings.crs_override!r}"
            )

        if working_crs.isGeographic():
            raise ValueError(
                "Choose a projected CRS for the analysis, "
                "rather than a CRS measured in degrees."
            )

        print(
            f"Working CRS from settings: "
            f"{working_crs.description()}"
        )

        return working_crs

    # ---------------------------------------------------------
    # Automatic CRS selection
    # ---------------------------------------------------------

    if settings.crs_mode != "auto":
        raise ValueError(
            f"Unsupported CRS mode: {settings.crs_mode!r}. "
            "Use 'auto' or supply crs_override."
        )

    site = QgsVectorLayer(
        site_path,
        "Site for CRS selection",
        "ogr",
    )

    if not site.isValid():
        raise ValueError(
            f"Failed to load site: {site_path}"
        )

    if not site.crs().isValid():
        raise ValueError(
            "The site has no valid source CRS."
        )

    if site.featureCount() == 0 or site.extent().isEmpty():
        raise ValueError(
            "The site has no usable extent for CRS selection."
        )

    # Convert the site's centre to longitude/latitude.
    # EPSG:4326 is only used to locate the site here;
    # it is not the working CRS.
    geographic_crs = QgsCoordinateReferenceSystem("EPSG:4326")

    transform = QgsCoordinateTransform(
        site.crs(),
        geographic_crs,
        QgsProject.instance().transformContext(),
    )

    centre = transform.transform(site.extent().center())

    longitude = centre.x()
    latitude = centre.y()

    if (
        not math.isfinite(longitude)
        or not math.isfinite(latitude)
        or not -180 <= longitude <= 180
    ):
        raise ValueError(
            "Could not determine a valid site location."
        )

    if not -80 <= latitude <= 84:
        raise ValueError(
            "The site is outside the UTM latitude range. "
            "Set crs_override to a suitable projected CRS."
        )

    zone = int((longitude + 180) // 6) + 1
    zone = max(1, min(60, zone))

    # WGS 84 / UTM: northern or southern hemisphere.
    epsg_code = (
        32600 + zone
        if latitude >= 0
        else 32700 + zone
    )

    working_crs = QgsCoordinateReferenceSystem(
        f"EPSG:{epsg_code}"
    )

    if not working_crs.isValid():
        raise ValueError(
            f"Failed to initialise automatic CRS: EPSG:{epsg_code}"
        )

    print(
        f"Working CRS selected automatically: "
        f"{working_crs.authid()} — {working_crs.description()}"
    )

    return working_crs