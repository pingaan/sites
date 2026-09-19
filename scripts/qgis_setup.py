import os
import sys

from qgis.core import QgsApplication


def initialize_qgis(gui=False):
    """
    Initialise the QGIS runtime.

    Parameters
    ----------
    gui : bool
        False:
            Run QGIS headlessly for processing/backend work.

        True:
            Enable QGIS GUI components so they can later be embedded
            inside our own application, for example QgsMapCanvas.

    Returns
    -------
    QgsApplication
        The initialised QGIS application instance.
    """

    qgis_prefix = os.environ.get("QGIS_PREFIX_PATH", "/usr")

    QgsApplication.setPrefixPath(qgis_prefix, True)

    qgs = QgsApplication([], gui)
    qgs.initQgis()

    if sys.platform == "win32":
        processing_path = os.path.join(
            qgis_prefix,
            "python",
            "plugins",
        )
    else:
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
    Shut down the QGIS runtime cleanly.
    """

    if qgs is not None:
        qgs.exitQgis()