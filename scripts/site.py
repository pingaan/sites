import os

from qgis.core import QgsVectorLayer


def load_site(input_path):
    """
    Load the analysis site from a vector file.

    Parameters
    ----------
    input_path : str
        Path to the vector dataset containing the site geometry.

    Returns
    -------
    QgsVectorLayer
        Valid QGIS vector layer containing the site.

    Raises
    ------
    FileNotFoundError
        If the input file does not exist.

    ValueError
        If QGIS cannot load the dataset.
    """

    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Site file does not exist: {input_path}"
        )

    site = QgsVectorLayer(
        input_path,
        "Analysis site",
        "ogr",
    )

    if not site.isValid():
        raise ValueError(
            f"Failed to load site: {input_path}"
        )

    return site