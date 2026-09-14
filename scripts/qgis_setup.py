import os
import sys

from qgis.core import QgsApplication


def initialize_qgis():
    """
    Start the QGIS engine in headless mode and initialise
    the QGIS Processing framework.
    """

    qgis_prefix = os.environ.get("QGIS_PREFIX_PATH", "/usr")

    QgsApplication.setPrefixPath(qgis_prefix, True)

    qgs = QgsApplication([], False)
    qgs.initQgis()

    processing_path = os.path.join(
        qgis_prefix,
        "share",
        "qgis",
        "python",
        "plugins",
    )

    if processing_path not in sys.path:
        sys.path.append(processing_path)

    from processing.core.Processing import Processing
    Processing.initialize()

    return qgs


def shutdown_qgis(qgs):
    """
    Shut down the QGIS engine cleanly.
    """

    if qgs is not None:
        qgs.exitQgis()