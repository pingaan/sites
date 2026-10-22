import os
import re
import sys
import shutil
import time

from scripts.translations import (
    ui_text,
)
from datetime import datetime
from pathlib import Path
from qgis.PyQt.QtPrintSupport import (
    QPrinter,
    QPrintDialog,
)
from qgis.PyQt.QtCore import (
    Qt,
    QTimer,
    QPointF,
    QSizeF,
    pyqtSignal,
    QPointF,
    QSizeF,
    QUrl,
    QSettings,
)
from qgis.PyQt.QtGui import (
    QColor,
    QIcon,
    QColor,
    QCursor,
    QTextDocument,
    QPixmap,
    QCursor,
    QPainter,
    QDesktopServices,
)
from qgis.PyQt.QtWidgets import (
    QAction,
    QActionGroup,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStyle,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QTextBrowser,
    QAbstractItemView,
    QInputDialog,
    QSplashScreen,
    QInputDialog,
    QMenu,
)

from qgis.gui import (
    QgsLayerTreeView,
    QgsMapCanvas,
    QgsMapCanvasAnnotationItem,
    QgsMapToolIdentifyFeature,
    QgsMapToolPan,
    QgsVertexMarker,
    QgsMapTool,
    QgsRubberBand,
)
from qgis.core import (
    QgsApplication,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsGeometry,
    QgsLayerTreeModel,
    QgsMapLayerType,
    QgsProject,
    QgsRasterLayer,
    QgsRectangle,
    QgsVectorLayer,
    QgsWkbTypes,
    Qgis,
    QgsFillSymbol,
    QgsProviderRegistry,
    QgsSingleSymbolRenderer,
    QgsFeature,
    QgsVectorFileWriter,
    QgsDistanceArea,
    QgsPointXY,
    QgsTextAnnotation,
    QgsLayoutExporter,
)

from gui import SitesWindow as AnalysisWindow
from scripts.options_dialog import OptionsDialog


BASEMAPS = {
    "OpenStreetMap": (
        "type=xyz&"
        "url=https://tile.openstreetmap.org/"
        "{z}/{x}/{y}.png&"
        "zmin=0&zmax=19"
    ),
    "Google Maps": (
        "type=xyz&"
        "url=https://mt1.google.com/vt/"
        "lyrs%3Dm%26x%3D{x}%26y%3D{y}%26z%3D{z}&"
        "zmin=0&zmax=22"
    ),
    "Google Roads": (
        "type=xyz&"
        "url=https://mt1.google.com/vt/"
        "lyrs%3Dr%26x%3D{x}%26y%3D{y}%26z%3D{z}&"
        "zmin=0&zmax=22"
    ),
    "Google Satellite": (
        "type=xyz&"
        "url=https://mt1.google.com/vt/"
        "lyrs%3Ds%26x%3D{x}%26y%3D{y}%26z%3D{z}&"
        "zmin=0&zmax=22"
    ),
    "Google Hybrid": (
        "type=xyz&"
        "url=https://mt1.google.com/vt/"
        "lyrs%3Dy%26x%3D{x}%26y%3D{y}%26z%3D{z}&"
        "zmin=0&zmax=22"
    ),
}

COUNTRY_MAP_SETTINGS = {
    "SE": {
        "admin_name": "Sweden",
        "crs": "EPSG:3006",
    },
    "FI": {
        "admin_name": "Finland",
        "crs": "EPSG:3067",
    },
}

class DrawPolygonMapTool(QgsMapTool):
    polygonCompleted = pyqtSignal(object)
    polygonUpdated = pyqtSignal(object)
    drawingCancelled = pyqtSignal()

    def __init__(self, canvas):
        super().__init__(canvas)

        self.application_settings = QSettings(
            "Sovra",
            "Sovra",
        )

        self.language_code = str(
            self.application_settings.value(
                "language",
                "en",
            )
        ).strip().lower()

        if self.language_code not in {
            "en",
            "sv",
            "fi",
        }:
            self.language_code = "en"

        self.canvas = canvas
        self.points = []

        self.rubber_band = QgsRubberBand(
            canvas,
            QgsWkbTypes.PolygonGeometry,
        )

        self.rubber_band.setStrokeColor(
            QColor(255, 110, 0, 255)
        )

        self.rubber_band.setFillColor(
            QColor(255, 196, 0, 70)
        )

        self.rubber_band.setWidth(2)

        self.setCursor(
            QCursor(Qt.CrossCursor)
        )

    def start_drawing(self):
        self.reset()

    def canvasPressEvent(self, event):
        point = event.mapPoint()

        if event.button() == Qt.LeftButton:
            self.points.append(
                point
            )

            self.update_rubber_band()

            geometry = self.build_geometry()

            if geometry is not None:
                self.polygonUpdated.emit(
                    geometry
                )

            return

        if event.button() != Qt.RightButton:
            return

        geometry = self.build_geometry()

        if geometry is None:
            return

        self.reset()

        self.polygonCompleted.emit(
            geometry
        )

    def canvasMoveEvent(self, event):
        """
        Preview the polygon and its area while the cursor moves.
        """

        if not self.points:
            return

        preview_point = event.mapPoint()

        self.update_rubber_band(
            preview_point=preview_point
        )

        geometry = self.build_geometry(
            preview_point=preview_point
        )

        if geometry is not None:
            self.polygonUpdated.emit(
                geometry
            )

    def build_geometry(
        self,
        preview_point=None,
    ):
        """
        Build a temporary polygon from the fixed points and,
        while moving the mouse, the current cursor position.
        """

        ring = list(
            self.points
        )

        if preview_point is not None:
            ring.append(
                preview_point
            )

        if len(ring) < 3:
            return None

        ring.append(
            ring[0]
        )

        geometry = QgsGeometry.fromPolygonXY(
            [
                ring,
            ]
        )

        if geometry.isEmpty():
            return None

        return geometry

    def update_rubber_band(
        self,
        preview_point=None,
    ):
        """
        Redraw the orange polygon preview.
        """

        display_points = list(
            self.points
        )

        if preview_point is not None:
            display_points.append(
                preview_point
            )

        self.rubber_band.reset(
            QgsWkbTypes.PolygonGeometry
        )

        for index, point in enumerate(
            display_points
        ):
            self.rubber_band.addPoint(
                point,
                index == len(display_points) - 1,
            )

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reset()

            self.drawingCancelled.emit()

            return

        super().keyPressEvent(event)

    def reset(self):
        self.points = []

        self.rubber_band.reset(
            QgsWkbTypes.PolygonGeometry
        )

class MeasurementMapTool(QgsMapTool):
    """
    Interactive distance or area measurement tool.

    Left-click adds vertices.
    Right-click finishes the measurement.
    Backspace removes the latest vertex.
    Escape clears the measurement.
    """

    def __init__(
        self,
        canvas,
        measurement_type,
        message_callback,
    ):
        super().__init__(
            canvas
        )

        if measurement_type not in {
            "distance",
            "area",
        }:
            raise ValueError(
                "Measurement type must be "
                "'distance' or 'area'."
            )

        self.canvas = canvas
        self.measurement_type = measurement_type
        self.message_callback = message_callback
        self.points = []
        self.finished = False

        if measurement_type == "distance":
            self.geometry_type = (
                Qgis.GeometryType.Line
            )
        else:
            self.geometry_type = (
                Qgis.GeometryType.Polygon
            )

        self.rubber_band = QgsRubberBand(
            self.canvas,
            self.geometry_type,
        )

        self.rubber_band.setStrokeColor(
            QColor(
                220,
                45,
                45,
                230,
            )
        )

        self.rubber_band.setFillColor(
            QColor(
                220,
                45,
                45,
                45,
            )
        )

        self.rubber_band.setWidth(
            2
        )

        # -------------------------------------------------
        # Floating measurement label
        # -------------------------------------------------

        self.measurement_annotation = (
            QgsTextAnnotation()
        )

        self.measurement_annotation.setFillSymbol(
            QgsFillSymbol.createSimple(
                {
                    "color": "255,255,255,235",
                    "outline_color": "220,45,45,255",
                    "outline_width": "0.5",
                }
            )
        )

        self.measurement_annotation_item = (
            QgsMapCanvasAnnotationItem(
                self.measurement_annotation,
                self.canvas,
            )
        )

        self.measurement_annotation_item.hide()

        self.setCursor(
            QCursor(
                Qt.CrossCursor
            )
        )

    def activate(self):
        super().activate()

        if self.measurement_type == "distance":
            message = (
                "Measure distance: left-click to add "
                "points; right-click to finish."
            )
        else:
            message = (
                "Measure area: left-click to add "
                "corners; right-click to finish."
            )

        self.message_callback(
            message
        )

    def deactivate(self):
        self.clear_measurement(
            show_instruction=False
        )

        super().deactivate()

    def canvasPressEvent(
        self,
        event,
    ):
        if event.button() == Qt.LeftButton:
            if self.finished:
                self.clear_measurement(
                    show_instruction=False
                )

            self.points.append(
                QgsPointXY(
                    event.mapPoint()
                )
            )

            self.update_measurement()

            return

        if event.button() == Qt.RightButton:
            minimum_points = (
                2
                if self.measurement_type
                == "distance"
                else 3
            )

            if len(self.points) < minimum_points:
                return

            self.finished = True

            self.update_measurement(
                final=True
            )

    def canvasMoveEvent(
        self,
        event,
    ):
        if (
            not self.points
            or self.finished
        ):
            return

        cursor_point = QgsPointXY(
            event.mapPoint()
        )

        self.update_measurement(
            cursor_point=cursor_point,
        )

    def keyPressEvent(
        self,
        event,
    ):
        if event.key() == Qt.Key_Escape:
            self.clear_measurement()

            event.accept()
            return

        if (
            event.key() == Qt.Key_Backspace
            and self.points
        ):
            self.points.pop()
            self.finished = False
            self.update_measurement()

            event.accept()
            return

        super().keyPressEvent(
            event
        )

    def create_distance_calculator(self):
        calculator = QgsDistanceArea()

        calculator.setSourceCrs(
            self.canvas
            .mapSettings()
            .destinationCrs(),
            QgsProject
            .instance()
            .transformContext(),
        )

        project_ellipsoid = (
            QgsProject
            .instance()
            .ellipsoid()
        )

        if (
            not project_ellipsoid
            or project_ellipsoid == "NONE"
        ):
            project_ellipsoid = "WGS84"

        calculator.setEllipsoid(
            project_ellipsoid
        )

        return calculator

    def update_measurement_label(
        self,
        map_position,
        measurement_text,
    ):
        """
        Display a compact measurement label beside a map point.
        """

        if (
            map_position is None
            or not measurement_text
        ):
            self.measurement_annotation_item.hide()
            return

        map_crs = (
            self.canvas
            .mapSettings()
            .destinationCrs()
        )

        self.measurement_annotation.setMapPositionCrs(
            map_crs
        )

        self.measurement_annotation.setMapPosition(
            map_position
        )

        document = (
            self.measurement_annotation.document()
        )

        document.setHtml(
            (
                "<div style=\""
                "font-family: 'Segoe UI';"
                "font-size: 9pt;"
                "font-weight: 600;"
                "color: #17324d;"
                "white-space: nowrap;"
                "\">"
                f"{measurement_text}"
                "</div>"
            )
        )

        document.adjustSize()

        document_size = document.size()

        frame_width = (
            document_size.width() + 16
        )

        frame_height = (
            document_size.height() + 10
        )

        self.measurement_annotation.setFrameSize(
            QSizeF(
                frame_width,
                frame_height,
            )
        )

        self.measurement_annotation.setFrameOffsetFromReferencePoint(
            QPointF(
                12,
                -frame_height - 12,
            )
        )

        self.measurement_annotation_item.show()
        self.measurement_annotation_item.updatePosition()

    def update_measurement(
        self,
        cursor_point=None,
        final=False,
    ):
        display_points = list(
            self.points
        )

        if cursor_point is not None:
            display_points.append(
                cursor_point
            )

        self.rubber_band.reset(
            self.geometry_type
        )

        for index, point in enumerate(
            display_points
        ):
            is_last_point = (
                index
                == len(display_points) - 1
            )

            self.rubber_band.addPoint(
                point,
                is_last_point,
            )

        if (
            self.measurement_type == "area"
            and len(display_points) >= 3
        ):
            self.rubber_band.closePoints(
                True
            )

        calculator = (
            self.create_distance_calculator()
        )

        prefix = (
            "Final"
            if final
            else "Current"
        )

        if (
            self.measurement_type == "distance"
            and len(display_points) >= 2
        ):
            measured_length = (
                calculator.measureLine(
                    display_points
                )
            )

            metres = (
                calculator
                .convertLengthMeasurement(
                    measured_length,
                    Qgis.DistanceUnit.Meters,
                )
            )

            if metres >= 1000:
                measurement_text = (
                    f"{metres / 1000:.3f} km"
                )
            else:
                measurement_text = (
                    f"{metres:.2f} m"
                )

            self.message_callback(
                f"{prefix} distance: "
                f"{measurement_text}"
            )

            self.update_measurement_label(
                map_position=display_points[-1],
                measurement_text=measurement_text,
            )

        elif (
            self.measurement_type == "area"
            and len(display_points) >= 3
        ):
            measured_area = (
                calculator.measurePolygon(
                    display_points
                )
            )

            square_metres = (
                calculator
                .convertAreaMeasurement(
                    measured_area,
                    Qgis.AreaUnit.SquareMeters,
                )
            )

            hectares = (
                square_metres / 10000
            )

            if hectares >= 0.01:
                measurement_text = (
                    f"{hectares:.3f} ha "
                    f"({square_metres:,.1f} m²)"
                )
            else:
                measurement_text = (
                    f"{square_metres:.2f} m²"
                )

            self.message_callback(
                f"{prefix} area: "
                f"{measurement_text}"
            )

            self.update_measurement_label(
                map_position=display_points[-1],
                measurement_text=measurement_text,
            )

        self.canvas.refresh()

    def clear_measurement(
        self,
        show_instruction=True,
    ):
        self.points = []
        self.finished = False

        self.rubber_band.reset(
            self.geometry_type
        )

        self.measurement_annotation_item.hide()

        self.canvas.refresh()

        if not show_instruction:
            return

        if self.measurement_type == "distance":
            self.message_callback(
                "Measure distance: left-click to begin."
            )
        else:
            self.message_callback(
                "Measure area: left-click to begin."
            )

class SitesDesktop(QMainWindow):

    def __init__(self):
        super().__init__()

        self.application_settings = QSettings(
            "Sovra",
            "Sovra",
        )

        self.language_code = str(
            self.application_settings.value(
                "language",
                "en",
            )
        ).strip().lower()

        if self.language_code not in {
            "en",
            "sv",
            "fi",
        }:
            self.language_code = "en"

        self.project = QgsProject.instance()
        self.analysis_window = None
        self.analysis_project_snapshot = {}
        self.custom_polygon_path = None
        self.custom_polygon_layer = None
        self.drawn_polygon_path = None
        self.drawn_polygon_layer = None
        self.drawn_polygon_area_annotation = None
        self.drawn_polygon_area_item = None
        local_app_data = os.environ.get(
            "LOCALAPPDATA",
            os.path.expanduser("~"),
        )

        self.projects_root = (
            Path(local_app_data)
            / "Sites"
            / "Projects"
        )
        self.basemap_layer = None
        self.current_basemap_name = None
        self.world_countries_layer = None
        self.overview_satellite_layer = None
        self.overview_project_marker = None
        self.default_map_crs = (
            QgsCoordinateReferenceSystem(
                "EPSG:3857"
            )
        )

        self.setWindowTitle(
            self.text(
                "application_title"
            )
        )

        self.resize(
            1500,
            900,
        )

        self.create_map_canvases()
        self.create_layer_panel()
        self.create_projects_panel()
        self.create_information_panel()
        self.create_overview_panel()
        self.create_actions()
        self.create_menus()
        self.create_toolbars()
        self.create_status_bar()
        self.connect_signals()
        self.arrange_panels()
        self.activate_pan_tool()
        self.set_basemap("OpenStreetMap")
        self.focus_selected_country()
        QTimer.singleShot(
            750,
            self.check_for_stale_projects,
        )

    def text(
        self,
        key,
        **values,
    ):
        """
        Return interface text in the global language.
        """

        return ui_text(
            self.language_code,
            key,
            **values,
        )

    # ---------------------------------------------------------
    # Main map
    # ---------------------------------------------------------

    def create_map_canvases(self):
        # -------------------------------------------------
        # Main interactive map
        # -------------------------------------------------

        self.map_canvas = QgsMapCanvas()

        self.map_canvas.setCanvasColor(
            QColor("#e8edf2")
        )

        self.map_canvas.enableAntiAliasing(
            True
        )
        self.map_canvas.setDestinationCrs(
            self.default_map_crs
        )

        # -------------------------------------------------
        # Project report viewer
        # -------------------------------------------------

        self.project_report_view = QTextBrowser()

        self.project_report_view.setOpenExternalLinks(
            True
        )

        self.project_report_view.setMarkdown(
            "# Project information\n\n"
            "Load a local project to view its report."
        )

        # -------------------------------------------------
        # Central Map and Info tabs
        # -------------------------------------------------

        self.central_tabs = QTabWidget()

        self.central_tabs.setDocumentMode(
            True
        )

        self.central_tabs.addTab(
            self.map_canvas,
            self.text(
                "map"
            ),
        )

        self.central_tabs.addTab(
            self.project_report_view,
            self.text(
                "info"
            ),
        )

        self.setCentralWidget(
            self.central_tabs
        )

        # -------------------------------------------------
        # Small country-overview map
        # -------------------------------------------------

        self.overview_canvas = QgsMapCanvas()

        self.overview_canvas.setCanvasColor(
            QColor("#dde5eb")
        )

        self.overview_canvas.enableAntiAliasing(
            True
        )

        self.overview_canvas.setDestinationCrs(
            self.default_map_crs
        )

        # -------------------------------------------------
        # Default mouse navigation
        # -------------------------------------------------

        self.pan_tool = QgsMapToolPan(
            self.map_canvas
        )

        self.identify_tool = QgsMapToolIdentifyFeature(
            self.map_canvas
        )

        self.map_canvas.setMapTool(
            self.pan_tool
        )

        # -------------------------------------------------
        # Draw polygon
        # -------------------------------------------------

        self.draw_polygon_tool = (
            DrawPolygonMapTool(
                self.map_canvas
            )
        )

    # ---------------------------------------------------------
    # Layer panel
    # ---------------------------------------------------------

    def create_layer_panel(self):
        self.layer_dock = QDockWidget(
            self.text(
                "layers"
            ),
            self,
        )

        self.layer_dock.setObjectName(
            "layers_dock"
        )

        self.layer_tree = QgsLayerTreeView()

        self.layer_tree_model = QgsLayerTreeModel(
            self.project.layerTreeRoot()
        )

        self.layer_tree_model.setFlag(
            QgsLayerTreeModel.AllowNodeChangeVisibility,
            True,
        )

        self.layer_tree_model.setFlag(
            QgsLayerTreeModel.AllowLegendChangeState,
            True,
        )

        self.layer_tree.setModel(
            self.layer_tree_model
        )

        self.project.layerTreeRoot().visibilityChanged.connect(
            self.refresh_map_layers
        )

        self.layer_dock.setWidget(
            self.layer_tree
        )

        self.addDockWidget(
            Qt.LeftDockWidgetArea,
            self.layer_dock,
        )

    # ---------------------------------------------------------
    # Local projects panel
    # ---------------------------------------------------------

    def create_projects_panel(self):
        self.projects_dock = QDockWidget(
            self.text(
                "projects"
            ),
            self,
        )

        self.projects_dock.setObjectName(
            "projects_dock"
        )

        self.projects_tree = QTreeWidget()

        self.projects_tree.setHeaderLabels(
            [
                self.text("local_projects"),
            ]
        )

        self.projects_tree.setAlternatingRowColors(
            True
        )

        self.projects_tree.setSelectionMode(
            QAbstractItemView.ExtendedSelection
        )

        self.projects_tree.itemDoubleClicked.connect(
            self.load_local_project
        )

        self.open_local_project_action = QAction(
            self.text(
                "open"
            ),
            self.projects_tree,
        )

        self.open_local_project_action.triggered.connect(
            self.open_selected_local_project
        )

        self.projects_tree.addAction(
            self.open_local_project_action
        )

        self.open_project_location_action = QAction(
            self.text(
                "open_location"
            ),
            self.projects_tree,
        )

        self.open_project_location_action.triggered.connect(
            self.open_selected_project_location
        )

        self.projects_tree.addAction(
            self.open_project_location_action
        )

        self.projects_tree.addAction(
            QAction(
                self.projects_tree
            )
        )

        separator_action = (
            self.projects_tree.actions()[-1]
        )

        separator_action.setSeparator(True)

        self.rename_project_action = QAction(
            self.text(
                "rename_project_or_folder"
            ),
            self.projects_tree,
        )

        self.rename_project_action.setShortcut(
            "F2"
        )

        self.rename_project_action.triggered.connect(
            self.rename_selected_project
        )

        self.projects_tree.addAction(
            self.rename_project_action
        )

        self.delete_projects_action = QAction(
            self.text(
                "delete_local_projects"
            ),
            self.projects_tree,
        )

        self.delete_projects_action.setShortcut(
            "Delete"
        )

        self.delete_projects_action.triggered.connect(
            self.delete_selected_projects
        )

        self.projects_tree.addAction(
            self.delete_projects_action
        )

        self.projects_tree.setContextMenuPolicy(
            Qt.ActionsContextMenu
        )

        self.projects_dock.setWidget(
            self.projects_tree
        )

        self.addDockWidget(
            Qt.LeftDockWidgetArea,
            self.projects_dock,
        )

        self.splitDockWidget(
            self.projects_dock,
            self.layer_dock,
            Qt.Vertical,
        )

        self.refresh_project_list()

    def remove_empty_project_folders(self):
        """
        Remove empty directories underneath the local Projects
        folder, working from the deepest directories upward.
        """

        if not self.projects_root.is_dir():
            return

        directories = sorted(
            (
                path
                for path in self.projects_root.rglob("*")
                if path.is_dir()
            ),
            key=lambda path: len(path.parts),
            reverse=True,
        )

        for directory in directories:
            try:
                if not any(directory.iterdir()):
                    directory.rmdir()
            except OSError:
                continue

    def check_for_stale_projects(self):
        """
        Find analysis-run folders whose newest QGIS project
        file has not been modified during the last 30 days.

        Nothing is removed without user confirmation.
        """

        if not self.projects_root.is_dir():
            return

        stale_before = (
            time.time()
            - 30 * 24 * 60 * 60
        )

        project_files = list(
            self.projects_root.rglob(
                "*.qgz"
            )
        )

        project_files.extend(
            self.projects_root.rglob(
                "*.qgs"
            )
        )

        run_projects = {}

        for project_path in project_files:
            try:
                modified_time = (
                    project_path.stat().st_mtime
                )
            except OSError:
                continue

            run_directory = (
                project_path.parent.resolve()
            )

            previous_modified_time = (
                run_projects.get(
                    run_directory
                )
            )

            if (
                previous_modified_time is None
                or modified_time
                > previous_modified_time
            ):
                run_projects[
                    run_directory
                ] = modified_time

        current_project_path = None

        if self.project.fileName():
            try:
                current_project_path = Path(
                    self.project.fileName()
                ).resolve()
            except OSError:
                current_project_path = None

        stale_directories = []

        for (
            run_directory,
            modified_time,
        ) in run_projects.items():
            if modified_time >= stale_before:
                continue

            if (
                current_project_path is not None
                and current_project_path.parent
                == run_directory
            ):
                continue

            stale_directories.append(
                (
                    run_directory,
                    modified_time,
                )
            )

        stale_directories.sort(
            key=lambda item: item[1]
        )

        if not stale_directories:
            return

        preview_lines = []

        for run_directory, modified_time in (
            stale_directories[:12]
        ):
            try:
                relative_path = (
                    run_directory.relative_to(
                        self.projects_root
                    )
                )
            except ValueError:
                relative_path = run_directory

            modified_text = time.strftime(
                "%Y-%m-%d",
                time.localtime(
                    modified_time
                ),
            )

            preview_lines.append(
                f"• {relative_path} "
                f"({modified_text})"
            )

        if len(stale_directories) > 12:
            remaining_count = (
                len(stale_directories) - 12
            )

            preview_lines.append(
                self.text(
                    "old_projects_more",
                    count=remaining_count,
                )
            )

        project_list = "\n".join(
            preview_lines
        )

        answer = QMessageBox.question(
            self,
            self.text(
                "old_projects_found"
            ),
            self.text(
                "old_projects_message",
                projects=project_list,
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.Yes,
        )

        if answer != QMessageBox.Yes:
            return

        removed_count = 0
        removal_errors = []

        projects_root = (
            self.projects_root.resolve()
        )

        for run_directory, _ in stale_directories:
            try:
                run_directory = (
                    run_directory.resolve()
                )

                try:
                    run_directory.relative_to(
                        projects_root
                    )
                except ValueError:
                    raise RuntimeError(
                        "Folder is outside the local "
                        "Projects directory."
                    )

                if run_directory == projects_root:
                    raise RuntimeError(
                        "Refusing to remove the Projects "
                        "root directory."
                    )

                if run_directory.is_dir():
                    shutil.rmtree(
                        run_directory
                    )

                    removed_count += 1

            except Exception as error:
                removal_errors.append(
                    f"{run_directory}: {error}"
                )

        self.refresh_project_list()

        if removal_errors:
            error_preview = "\n".join(
                removal_errors[:8]
            )

            QMessageBox.warning(
                self,
                self.text(
                    "project_cleanup_incomplete"
                ),
                self.text(
                    "project_cleanup_incomplete_message",
                    count=removed_count,
                    errors=error_preview,
                ),
            )

            return

        QMessageBox.information(
            self,
            self.text(
                "project_cleanup_completed"
            ),
            self.text(
                "project_cleanup_completed_message",
                count=removed_count,
            ),
        )

    def refresh_project_list(self):
        self.projects_tree.clear()

        if not self.projects_root.is_dir():
            unavailable_item = QTreeWidgetItem(
                [
                    self.text(
                        "no_local_projects_found"
                    ),
                ]
            )

            self.projects_tree.addTopLevelItem(
                unavailable_item
            )

            return

        self.remove_empty_project_folders()

        project_directories = sorted(
            (
                path
                for path in self.projects_root.iterdir()
                if path.is_dir()
            ),
            key=lambda path: path.name.casefold(),
        )

        for project_directory in project_directories:
            project_item = QTreeWidgetItem(
                [
                    project_directory.name,
                ]
            )

            project_item.setData(
                0,
                Qt.UserRole + 1,
                str(project_directory),
            )

            self.projects_tree.addTopLevelItem(
                project_item
            )

            project_files = list(
                project_directory.rglob(
                    "*.qgz"
                )
            )

            project_files.extend(
                project_directory.rglob(
                    "*.qgs"
                )
            )

            project_files.sort(
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )

            for project_path in project_files:
                run_name = project_path.parent.name

                run_item = QTreeWidgetItem(
                    [
                        run_name,
                    ]
                )

                run_item.setToolTip(
                    0,
                    str(project_path),
                )

                run_item.setData(
                    0,
                    Qt.UserRole,
                    str(project_path),
                )

                run_item.setData(
                    0,
                    Qt.UserRole + 1,
                    str(project_path.parent),
                )

                project_item.addChild(
                    run_item
                )

        if self.projects_tree.topLevelItemCount() == 0:
            unavailable_item = QTreeWidgetItem(
                [
                    self.text(
                        "no_local_projects_found"
                    ),
                ]
            )

            self.projects_tree.addTopLevelItem(
                unavailable_item
            )

    def open_selected_local_project(self):
        """
        Open the selected local project.

        When a project folder is selected, open its newest
        analysis run.
        """

        selected_items = (
            self.projects_tree.selectedItems()
        )

        if len(selected_items) != 1:
            QMessageBox.information(
                self,
                self.text(
                    "open_location_title"
                ),
                self.text(
                    "select_one_project_or_folder"
                ),
            )

            return

        selected_item = selected_items[0]

        project_path = selected_item.data(
            0,
            Qt.UserRole,
        )

        if (
            not project_path
            and selected_item.childCount() > 0
        ):
            newest_run_item = (
                selected_item.child(0)
            )

            project_path = newest_run_item.data(
                0,
                Qt.UserRole,
            )

        if not project_path:
            QMessageBox.information(
                self,
                self.text(
                    "open_project_title"
                ),
                self.text(
                    "folder_has_no_qgis_project"
                ),
            )

            return

        if not Path(project_path).is_file():
            QMessageBox.warning(
                self,
                self.text(
                    "project_missing"
                ),
                self.text(
                    "project_missing_message",
                    path=project_path,
                ),
            )

            self.refresh_project_list()

            return

        self.load_project(
            project_path
        )

    def open_selected_project_location(self):
        """
        Open the selected project or run directory in the
        operating system's file manager.
        """

        selected_items = (
            self.projects_tree.selectedItems()
        )

        if len(selected_items) != 1:
            QMessageBox.information(
                self,
                self.text("open_location_title"),
                self.text(
                    "select_one_project_or_folder"
                ),
            )

            return

        selected_item = selected_items[0]

        directory_path = selected_item.data(
            0,
            Qt.UserRole + 1,
        )

        if not directory_path:
            QMessageBox.information(
                self,
                self.text(
                    "open_location_title"
                ),
                self.text(
                    "no_local_folder_associated"
                ),
            )

            return

        directory = Path(
            directory_path
        ).resolve()

        if not directory.is_dir():
            QMessageBox.warning(
                self,
                self.text(
                    "folder_missing"
                ),
                self.text(
                    "folder_missing_message",
                    path=directory,
                ),
            )

            self.refresh_project_list()

            return

        opened = QDesktopServices.openUrl(
            QUrl.fromLocalFile(
                str(directory)
            )
        )

        if not opened:
            QMessageBox.warning(
                self,
                self.text(
                    "open_location_title"
                ),
                self.text(
                    "open_location_failed_message",
                    path=directory,
                ),
            )

    def load_local_project(
        self,
        item,
        column,
    ):
        project_path = item.data(
            0,
            Qt.UserRole,
        )

        if not project_path:
            return

        self.load_project(
            project_path
        )

    def rename_selected_project(self):
        """
        Rename one selected project folder or analysis-run folder.
        """

        selected_items = (
            self.projects_tree.selectedItems()
        )

        if len(selected_items) != 1:
            QMessageBox.information(
                self,
                self.text(
                    "select_one_item"
                ),
                self.text(
                    "select_one_item_to_rename"
                ),
            )
            return

        selected_item = selected_items[0]

        stored_path = selected_item.data(
            0,
            Qt.UserRole + 1,
        )

        if not stored_path:
            return

        source_path = Path(
            stored_path
        ).resolve()

        projects_root = (
            self.projects_root.resolve()
        )

        if (
            source_path == projects_root
            or projects_root not in source_path.parents
            or not source_path.is_dir()
        ):
            QMessageBox.critical(
                self,
                self.text("rename_prevented_title"),
                self.text("rename_prevented_message"),
            )
            return

        new_name, accepted = QInputDialog.getText(
            self,
            self.text("rename_project_title"),
            self.text("new_name_label"),
            text=source_path.name,
        )

        if not accepted:
            return

        new_name = new_name.strip()

        if not new_name:
            QMessageBox.warning(
                self,
                self.text("invalid_name_title"),
                self.text("name_cannot_be_empty"),
            )
            return

        invalid_characters = set(
            '<>:"/\\|?*'
        )

        reserved_names = {
            "CON",
            "PRN",
            "AUX",
            "NUL",
            *{
                f"COM{number}"
                for number in range(1, 10)
            },
            *{
                f"LPT{number}"
                for number in range(1, 10)
            },
        }

        if (
            any(
                character in invalid_characters
                for character in new_name
            )
            or new_name.endswith((" ", "."))
            or new_name.upper() in reserved_names
        ):
            QMessageBox.warning(
                self,
                self.text("invalid_name_title"),
                self.text(
                    "invalid_folder_name_message"
                ),
            )
            return

        target_path = (
            source_path.parent
            / new_name
        )

        if target_path == source_path:
            return

        if target_path.exists():
            QMessageBox.warning(
                self,
                self.text(
                    "name_already_exists_title"
                ),
                self.text(
                    "name_already_exists_message"
                ),
            )
            return

        loaded_project_path = None
        loaded_relative_path = None

        if self.project.fileName():
            loaded_project_path = Path(
                self.project.fileName()
            ).resolve()

            try:
                loaded_relative_path = (
                    loaded_project_path.relative_to(
                        source_path
                    )
                )
            except ValueError:
                loaded_relative_path = None

        try:
            source_path.rename(
                target_path
            )
        except OSError as error:
            QMessageBox.critical(
                self,
                self.text("rename_failed_title"),
                self.text(
                    "rename_failed_message",
                    error=error,
                ),
            )
            return

        self.refresh_project_list()

        if loaded_relative_path is not None:
            renamed_project_path = (
                target_path
                / loaded_relative_path
            )

            if renamed_project_path.is_file():
                self.load_project(
                    str(renamed_project_path)
                )

        self.status_message.setText(
            self.text(
                "renamed_to",
                name=new_name,
            )
        )

    def delete_selected_projects(self):
        selected_items = (
            self.projects_tree.selectedItems()
        )

        deletion_paths = []

        for item in selected_items:
            stored_path = item.data(
                0,
                Qt.UserRole + 1,
            )

            if not stored_path:
                continue

            deletion_paths.append(
                Path(stored_path).resolve()
            )

        deletion_paths = sorted(
            set(deletion_paths),
            key=lambda path: len(path.parts),
        )

        filtered_paths = []

        for candidate in deletion_paths:
            if any(
                parent == candidate
                or parent in candidate.parents
                for parent in filtered_paths
            ):
                continue

            filtered_paths.append(
                candidate
            )

        if not filtered_paths:
            QMessageBox.information(
                self,
                self.text(
                    "no_projects_selected"
                ),
                self.text(
                    "select_projects_before_deletion"
                ),
            )
            return

        projects_root = (
            self.projects_root.resolve()
        )

        safe_paths = []

        for deletion_path in filtered_paths:
            if (
                deletion_path == projects_root
                or projects_root
                not in deletion_path.parents
            ):
                QMessageBox.critical(
                    self,
                    self.text(
                        "unsafe_deletion_prevented"
                    ),
                    self.text(
                        "unsafe_deletion_message",
                        path=deletion_path,
                    ),
                )
                return

            safe_paths.append(
                deletion_path
            )

        names = "\n".join(
            f"- {path.name}"
            for path in safe_paths
        )

        answer = QMessageBox.warning(
            self,
            self.text(
                "delete_local_projects_title"
            ),
            self.text(
                "delete_local_projects_message",
                names=names,
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        deletion_errors = []

        for deletion_path in safe_paths:
            try:
                shutil.rmtree(
                    deletion_path
                )
            except OSError as error:
                deletion_errors.append(
                    f"{deletion_path}\n{error}"
                )

        self.refresh_project_list()

        if deletion_errors:
            QMessageBox.critical(
                self,
                self.text(
                    "deletion_incomplete"
                ),
                self.text(
                    "deletion_incomplete_message",
                    errors="\n\n".join(
                        deletion_errors
                    ),
                ),
            )
            return

        self.status_message.setText(
            self.text(
                "selected_local_projects_deleted"
            )
        )

    # ---------------------------------------------------------
    # Information panel
    # ---------------------------------------------------------

    def create_information_panel(self):

        self.information_dock = QDockWidget(
            self.text(
                "information"
            ),
            self,
        )

        self.information_dock.setObjectName(
            "information_dock"
        )

        self.information_tabs = QTabWidget()

        self.feature_table = QTableWidget(
            0,
            2,
        )

        self.feature_table.setHorizontalHeaderLabels(
            [
                self.text("field"),
                self.text("value"),
            ]
        )

        self.feature_table.horizontalHeader().setStretchLastSection(
            True
        )

        self.layer_table = QTableWidget(
            0,
            2,
        )

        self.layer_table.setHorizontalHeaderLabels(
            [
                self.text("property"),
                self.text("value"),
            ]
        )

        self.layer_table.horizontalHeader().setStretchLastSection(
            True
        )

        self.information_tabs.addTab(
            self.feature_table,
            self.text(
                "feature_information"
            ),
        )

        self.information_tabs.addTab(
            self.layer_table,
            self.text(
                "layer_information"
            ),
        )

        self.information_dock.setWidget(
            self.information_tabs
        )

        self.addDockWidget(
            Qt.RightDockWidgetArea,
            self.information_dock,
        )

    # ---------------------------------------------------------
    # Country overview
    # ---------------------------------------------------------

    def create_overview_panel(self):
        self.overview_dock = QDockWidget(
            self.text(
                "country_overview"
            ),
            self,
        )

        self.overview_dock.setObjectName(
            "overview_dock"
        )

        self.overview_dock.setWidget(
            self.overview_canvas
        )

        self.addDockWidget(
            Qt.RightDockWidgetArea,
            self.overview_dock,
        )

    # ---------------------------------------------------------
    # Actions
    # ---------------------------------------------------------

    def create_actions(self):

        self.options_action = QAction(
            QgsApplication.getThemeIcon(
                "/mActionOptions.svg"
            ),
            self.text(
                "options"
            ),
            self,
        )

        self.options_action.setToolTip(
            self.text(
                "configure_sovra"
            )
        )

        self.options_action.triggered.connect(
            self.open_options
        )

        self.open_project_action = QAction(
            QgsApplication.getThemeIcon(
                "/mActionFileOpen.svg"
            ),
            self.text(
                "open_project"
            ),
            self,
        )

        self.open_project_action.setShortcut(
            "Ctrl+O"
        )

        self.save_project_action = QAction(
            QgsApplication.getThemeIcon(
                "/mActionFileSave.svg"
            ),
            self.text(
                "save_project"
            ),
            self,
        )

        self.save_project_action.setShortcut(
            "Ctrl+S"
        )

        self.print_project_action = QAction(
            QgsApplication.getThemeIcon(
                "/mActionFilePrint.svg"
            ),
            self.text(
                "print_project"
            ),
            self,
        )

        self.print_project_action.setShortcut(
            "Ctrl+P"
        )

        self.print_project_action.setToolTip(
            self.text(
                "print_project_tooltip"
            )
        )

        self.print_project_action.triggered.connect(
            self.print_project
        )

        export_icon = QgsApplication.getThemeIcon(
            "/mActionSaveAs.svg"
        )

        if export_icon.isNull():
            export_icon = self.style().standardIcon(
                QStyle.SP_DialogSaveButton
            )

        self.export_solar_action = QAction(
            export_icon,
            self.text(
                "export_solar_area"
            ),
            self,
        )

        self.export_solar_action.setToolTip(
            self.text(
                "export_solar_area_tooltip"
            )
        )

        self.export_solar_action.triggered.connect(
            lambda checked=False: (
                self.export_analysis_area("solar")
            )
        )

        self.export_wind_action = QAction(
            export_icon,
            self.text(
                "export_wind_area"
            ),
            self,
        )

        self.export_wind_action.setToolTip(
            self.text(
                "export_wind_area_tooltip"
            )
        )

        self.export_wind_action.triggered.connect(
            lambda checked=False: (
                self.export_analysis_area("wind")
            )
        )

        self.exit_action = QAction(
            self.text(
                "exit"
            ),
            self,
        )

        self.full_extent_action = QAction(
            QgsApplication.getThemeIcon(
                "/mActionZoomFullExtent.svg"
            ),
            self.text(
                "full_extent"
            ),
            self,
        )

        self.open_project_action.setToolTip(
            self.text(
                "open_qgis_project_tooltip"
            )
        )

        self.save_project_action.setToolTip(
            self.text(
                "save_project_tooltip"
            )
        )

        self.full_extent_action.setToolTip(
            self.text(
                "full_extent_tooltip"
            )
        )

        self.basemap_action_group = QActionGroup(
            self
        )

        self.basemap_action_group.setExclusive(
            True
        )

        self.basemap_actions = {}

        for basemap_name in BASEMAPS:
            action = QAction(
                basemap_name,
                self,
            )

            action.setCheckable(True)

            action.triggered.connect(
                lambda checked=False,
                name=basemap_name: self.set_basemap(
                    name
                )
            )

            self.basemap_action_group.addAction(
                action
            )

            self.basemap_actions[
                basemap_name
            ] = action

        self.basemap_actions[
            "OpenStreetMap"
        ].setChecked(True)

        self.about_action = QAction(
            self.text(
                "about_sovra"
            ),
            self,
        )

        # -------------------------------------------------
        # Interactive map tools
        # -------------------------------------------------

        self.map_tool_action_group = QActionGroup(
            self
        )

        self.map_tool_action_group.setExclusive(
            True
        )

        self.pan_action = QAction(
            QgsApplication.getThemeIcon(
                "/mActionPan.svg"
            ),
            self.text(
                "pan_map"
            ),
            self,
        )

        self.pan_action.setCheckable(
            True
        )

        self.pan_action.setToolTip(
            self.text(
                "pan_map_tooltip"
            )
        )

        self.identify_feature_action = QAction(
            QgsApplication.getThemeIcon(
                "/mActionIdentify.svg"
            ),
            self.text(
                "identify_feature"
            ),
            self,
        )

        self.identify_feature_action.setCheckable(
            True
        )

        self.identify_feature_action.setToolTip(
            self.text(
                "identify_feature_tooltip"
            )
        )

        self.identify_feature_action.setEnabled(
            False
        )

        self.measure_distance_action = QAction(
            QgsApplication.getThemeIcon(
                "/mActionMeasure.svg"
            ),
            self.text(
                "measure_distance"
            ),
            self,
        )

        self.measure_distance_action.setCheckable(
            True
        )

        self.measure_distance_action.setToolTip(
            self.text(
                "measure_distance_tooltip"
            )
        )

        self.measure_distance_action.triggered.connect(
            self.activate_measure_distance_tool
        )

        self.measure_area_action = QAction(
            QgsApplication.getThemeIcon(
                "/mActionMeasureArea.svg"
            ),
            self.text(
                "measure_area"
            ),
            self,
        )

        self.measure_area_action.setCheckable(
            True
        )

        self.measure_area_action.setToolTip(
            self.text(
                "measure_area_tooltip"
            )
        )

        self.measure_area_action.triggered.connect(
            self.activate_measure_area_tool
        )

        self.map_tool_action_group.addAction(
            self.pan_action
        )

        self.map_tool_action_group.addAction(
            self.identify_feature_action
        )

        self.map_tool_action_group.addAction(
            self.measure_distance_action
        )

        self.map_tool_action_group.addAction(
            self.measure_area_action
        )

        self.pan_action.setChecked(
            True
        )

    # ---------------------------------------------------------
    # Menus
    # ---------------------------------------------------------

    def create_language_actions(self):
        """
        Create the global application-language actions.

        Application language is independent of the country
        selected for analysis.
        """

        self.language_action_group = QActionGroup(
            self
        )

        self.language_action_group.setExclusive(
            True
        )

        self.language_actions = {}

        language_definitions = (
            (
                "English",
                "en",
            ),
            (
                "Svenska",
                "sv",
            ),
            (
                "Suomi",
                "fi",
            ),
        )

        for language_name, language_code in (
            language_definitions
        ):
            action = QAction(
                language_name,
                self,
            )

            action.setCheckable(
                True
            )

            action.setData(
                language_code
            )

            action.setChecked(
                language_code
                == self.language_code
            )

            action.triggered.connect(
                lambda checked=False,
                code=language_code:
                self.set_application_language(
                    code
                )
            )

            self.language_action_group.addAction(
                action
            )

            self.language_actions[
                language_code
            ] = action

    def set_application_language(
        self,
        language_code,
    ):
        """
        Store the global application language.

        This setting does not change the selected analysis
        country, country CRS or country datasets.
        """

        language_code = str(
            language_code
        ).strip().lower()

        if language_code not in {
            "en",
            "sv",
            "fi",
        }:
            return

        self.language_code = language_code

        self.application_settings.setValue(
            "language",
            language_code,
        )

        self.application_settings.sync()

        language_names = {
            "en": "English",
            "sv": "Svenska",
            "fi": "Suomi",
        }

        self.status_message.setText(
            self.text(
                "application_language_selected",
                language=language_names[
                    language_code
                ],
            )
        )

    def open_options(self):
        """
        Open the global Sovra options.
        """

        dialog = OptionsDialog(
            current_language=self.language_code,
            current_country=(
                self.country_combo.currentData()
            ),
            parent=self,
        )

        if not dialog.exec_():
            return

        selected_language = (
            dialog.selected_language()
        )

        if (
            selected_language
            == self.language_code
        ):
            return

        self.set_application_language(
            selected_language
        )

        answer = QMessageBox.question(
            self,
            ui_text(
                selected_language,
                "restart_required",
            ),
            ui_text(
                selected_language,
                "restart_required_message",
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.Yes,
        )

        if answer == QMessageBox.Yes:
            self.close()

    def create_menus(self):
        file_menu = self.menuBar().addMenu(
            self.text(
                "menu_file"
            )
        )

        file_menu.addAction(
            self.open_project_action
        )

        file_menu.addAction(
            self.save_project_action
        )

        file_menu.addSeparator()

        file_menu.addAction(
            self.exit_action
        )

        self.menuBar().addMenu(
            self.text(
                "menu_edit"
            )
        )

        view_menu = self.menuBar().addMenu(
            self.text(
                "menu_view"
            )
        )

        view_menu.addAction(
            self.layer_dock.toggleViewAction()
        )

        view_menu.addAction(
            self.information_dock.toggleViewAction()
        )

        view_menu.addAction(
            self.overview_dock.toggleViewAction()
        )

        view_menu.addSeparator()

        self.basemap_menu = view_menu.addMenu(
            self.text(
                "basemap"
            )
        )

        for action in self.basemap_actions.values():
            self.basemap_menu.addAction(
                action
            )

        settings_menu = self.menuBar().addMenu(
            self.text(
                "menu_settings"
            )
        )

        settings_menu.addAction(
            self.options_action
        )

        analysis_menu = self.menuBar().addMenu(
            self.text(
                "menu_analysis"
            )
        )

        self.start_analysis_action = QAction(
            self.text(
                "start_analysis"
            ),
            self,
        )

        self.start_analysis_action.setShortcut(
            "Ctrl+Return"
        )

        analysis_menu.addAction(
            self.start_analysis_action
        )

        help_menu = self.menuBar().addMenu(
            self.text(
                "menu_help"
            )
        )

        help_menu.addAction(
            self.about_action
        )

    # ---------------------------------------------------------
    # Toolbars
    # ---------------------------------------------------------

    def find_analysis_output_layer(
        self,
        output_id,
    ):
        """
        Find a solar or wind result layer using its stable
        project property.

        The name/source fallback supports older projects created
        before the custom property was introduced.
        """

        vector_layers = []

        for layer in self.project.mapLayers().values():
            if (
                layer.type()
                != QgsMapLayerType.VectorLayer
            ):
                continue

            vector_layers.append(
                layer
            )

            stored_id = str(
                layer.customProperty(
                    "sites/analysis_output",
                    "",
                )
            )

            if stored_id == output_id:
                return layer

        # Compatibility with projects created before the stable
        # analysis-output property was introduced.
        for layer in vector_layers:
            searchable_text = (
                f"{layer.name()} {layer.source()}"
                .casefold()
            )

            if (
                output_id in searchable_text
                and (
                    "candidate" in searchable_text
                    or "potential" in searchable_text
                )
            ):
                return layer

        return None

    def export_analysis_area(
        self,
        output_id,
    ):
        """
        Export one complete eligible-area result to a standalone
        GeoPackage.
        """

        definitions = {
            "solar": {
                "title": self.text(
                    "eligible_solar_area_name"
                ),
                "filename": "eligible_solar_area.gpkg",
                "layer_name": "eligible_solar_area",
            },
            "wind": {
                "title": self.text(
                    "eligible_wind_area_name"
                ),
                "filename": "eligible_wind_area.gpkg",
                "layer_name": "eligible_wind_area",
            },
        }

        definition = definitions.get(
            output_id
        )

        if definition is None:
            return

        layer = self.find_analysis_output_layer(
            output_id
        )

        if layer is None or not layer.isValid():
            QMessageBox.warning(
                self,
                self.text(
                    "analysis_area_unavailable"
                ),
                self.text(
                    "analysis_area_not_found",
                    area=definition["title"],
                ),
            )
            return

        project_path = self.project.fileName()

        if project_path:
            default_directory = os.path.dirname(
                project_path
            )
        else:
            default_directory = os.path.expanduser(
                "~"
            )

        suggested_path = os.path.join(
            default_directory,
            definition["filename"],
        )

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            self.text(
                "export_area_dialog",
                area=definition["title"],
            ),
            suggested_path,
            "GeoPackage (*.gpkg)",
        )

        if not output_path:
            return

        if not output_path.lower().endswith(
            ".gpkg"
        ):
            output_path += ".gpkg"

        options = (
            QgsVectorFileWriter.SaveVectorOptions()
        )

        options.driverName = "GPKG"
        options.layerName = definition[
            "layer_name"
        ]

        options.actionOnExistingFile = (
            QgsVectorFileWriter
            .CreateOrOverwriteFile
        )

        # GeoPackage reserves the name 'fid' for its primary key.
        # Excluding an existing attribute with that name prevents
        # the OGR "Wrong field type for fid" error.
        options.attributes = [
            field_index
            for field_index, field in enumerate(
                layer.fields()
            )
            if field.name().casefold() != "fid"
        ]

        writer_result = (
            QgsVectorFileWriter
            .writeAsVectorFormatV3(
                layer,
                output_path,
                self.project.transformContext(),
                options,
            )
        )

        if (
            writer_result[0]
            != QgsVectorFileWriter.NoError
        ):
            QMessageBox.critical(
                self,
                self.text(
                    "export_failed"
                ),
                self.text(
                    "area_export_failed",
                    area=definition["title"],
                    error=writer_result[1],
                ),
            )
            return

        QMessageBox.information(
            self,
            self.text(
                "export_completed"
            ),
            self.text(
                "area_export_completed",
                area=definition["title"],
                path=output_path,
            ),
        )

    def create_toolbars(self):
        map_toolbar = self.addToolBar(
            self.text(
                "map_navigation"
            )
        )

        map_toolbar.setObjectName(
            "map_toolbar"
        )

        map_toolbar.addAction(
            self.open_project_action
        )

        map_toolbar.addSeparator()

        map_toolbar.addAction(
            self.measure_distance_action
        )

        map_toolbar.addAction(
            self.measure_area_action
        )

        map_toolbar.addSeparator()

        map_toolbar.addAction(
            self.pan_action
        )

        map_toolbar.addAction(
            self.identify_feature_action
        )

        map_toolbar.addAction(
            self.save_project_action
        )

        map_toolbar.addAction(
            self.print_project_action
        )

        self.export_area_menu = QMenu(
            self
        )

        self.export_area_menu.addAction(
            self.export_solar_action
        )

        self.export_area_menu.addAction(
            self.export_wind_action
        )

        self.export_area_button = QToolButton(
            self
        )

        self.export_area_button.setIcon(
            self.export_solar_action.icon()
        )

        self.export_area_button.setText(
            self.text(
                "export_area"
            )
        )

        self.export_area_button.setToolTip(
            self.text(
                "export_area_tooltip"
            )
        )

        self.export_area_button.setToolButtonStyle(
            Qt.ToolButtonTextBesideIcon
        )

        self.export_area_button.setPopupMode(
            QToolButton.InstantPopup
        )

        self.export_area_button.setMenu(
            self.export_area_menu
        )

        map_toolbar.addWidget(
            self.export_area_button
        )

        map_toolbar.addSeparator()

        map_toolbar.addAction(
            self.full_extent_action
        )

        map_toolbar.addSeparator()

        self.basemap_button = QToolButton(
            self
        )

        basemap_icon = QgsApplication.getThemeIcon(
            "/mActionAddXyzLayer.svg"
        )

        if basemap_icon.isNull():
            basemap_icon = self.style().standardIcon(
                QStyle.SP_DriveNetIcon
            )

        self.basemap_button.setIcon(
            basemap_icon
        )

        self.basemap_button.setToolTip(
            self.text(
                "select_background_map"
            )
        )

        self.basemap_button.setToolTip(
            self.text("select_background_map")
        )

        self.basemap_button.setToolButtonStyle(
            Qt.ToolButtonTextBesideIcon
        )

        self.basemap_button.setPopupMode(
            QToolButton.InstantPopup
        )

        self.basemap_button.setMenu(
            self.basemap_menu
        )

        map_toolbar.addWidget(
            self.basemap_button
        )

        analysis_toolbar = self.addToolBar(
            self.text(
                "analysis"
            )
        )

        analysis_toolbar.setObjectName(
            "analysis_toolbar"
        )

        analysis_toolbar.addWidget(
            QLabel(
                self.text(
                    "country_label"
                )
            )
        )

        self.country_combo = QComboBox()

        self.country_combo.addItem(
            self.text("country_sweden"),
            "SE",
        )

        self.country_combo.addItem(
            self.text("country_finland"),
            "FI",
        )

        analysis_toolbar.addWidget(
            self.country_combo
        )

        analysis_toolbar.addSeparator()

        self.source_combo = QComboBox()

        self.source_combo.addItem(
            self.text("source_estate"),
            "estate",
        )

        self.source_combo.addItem(
            self.text("source_predefined_area"),
            "custom_polygon",
        )

        self.source_combo.addItem(
            self.text("source_draw_area"),
            "draw_polygon",
        )

        analysis_toolbar.addWidget(
            self.source_combo
        )

        self.source_input = QLineEdit()

        self.source_input.setMinimumWidth(
            280
        )

        self.source_input.setPlaceholderText(
            "KÄVLINGE ÅLSTORP 19:63"
        )

        analysis_toolbar.addWidget(
            self.source_input
        )

        self.browse_button = QPushButton(
            self.text("browse")
        )

        self.browse_button.setEnabled(
            False
        )

        analysis_toolbar.addWidget(
            self.browse_button
        )

        analysis_toolbar.addSeparator()

        self.run_button = QPushButton(
            self.text(
                "start_analysis"
            )
        )

        analysis_toolbar.addWidget(
            self.run_button
        )

    # ---------------------------------------------------------
    # Status bar
    # ---------------------------------------------------------

    def create_status_bar(self):
        self.status_message = QLabel(
            self.text("ready")
        )

        self.coordinate_label = QLabel(
            "X: —  Y: —"
        )

        self.scale_label = QLabel(
            self.text("scale_unavailable")
        )

        self.statusBar().addWidget(
            self.status_message,
            1,
        )

        self.statusBar().addPermanentWidget(
            self.coordinate_label
        )

        self.statusBar().addPermanentWidget(
            self.scale_label
        )

    # ---------------------------------------------------------
    # Connections
    # ---------------------------------------------------------

    def connect_signals(self):
        self.open_project_action.triggered.connect(
            self.open_project
        )

        self.source_input.returnPressed.connect(
            self.start_analysis
        )

        self.save_project_action.triggered.connect(
            self.save_project
        )

        self.exit_action.triggered.connect(
            self.close
        )

        self.full_extent_action.triggered.connect(
            self.zoom_full_extent
        )

        self.about_action.triggered.connect(
            self.show_about
        )

        self.start_analysis_action.triggered.connect(
            self.start_analysis
        )

        self.run_button.clicked.connect(
            self.start_analysis
        )

        self.country_combo.currentIndexChanged.connect(
            self.update_source_placeholder
        )

        self.country_combo.currentIndexChanged.connect(
            self.focus_selected_country
        )

        self.source_combo.currentIndexChanged.connect(
            self.update_source_type
        )

        self.browse_button.clicked.connect(
            self.select_custom_polygon
        )

        self.draw_polygon_tool.polygonCompleted.connect(
            self.finish_drawn_polygon
        )

        self.draw_polygon_tool.polygonUpdated.connect(
            self.update_drawn_polygon_area_preview
        )

        self.draw_polygon_tool.drawingCancelled.connect(
            self.cancel_polygon_drawing
        )

        self.layer_tree.currentLayerChanged.connect(
            self.update_layer_information
        )

        self.layer_tree.currentLayerChanged.connect(
            self.update_identify_layer
        )

        self.pan_action.triggered.connect(
            self.activate_pan_tool
        )

        self.identify_feature_action.triggered.connect(
            self.activate_identify_tool
        )

        self.identify_tool.featureIdentified.connect(
            self.handle_identified_feature
        )

        self.map_canvas.xyCoordinates.connect(
            self.update_coordinates
        )

        self.map_canvas.scaleChanged.connect(
            self.update_scale
        )

        self.project.layersAdded.connect(
            self.schedule_canvas_refresh
        )

        self.project.layersRemoved.connect(
            self.schedule_canvas_refresh
        )

        self.project.layerTreeRoot().visibilityChanged.connect(
            self.schedule_canvas_refresh
        )

    def arrange_panels(self):
        self.splitDockWidget(
            self.projects_dock,
            self.layer_dock,
            Qt.Vertical,
        )
        self.splitDockWidget(
            self.information_dock,
            self.overview_dock,
            Qt.Vertical,
        )

        self.resizeDocks(
            [
                self.layer_dock,
                self.information_dock,
            ],
            [
                280,
                350,
            ],
            Qt.Horizontal,
        )

        self.resizeDocks(
            [
                self.information_dock,
                self.overview_dock,
            ],
            [
                500,
                300,
            ],
            Qt.Vertical,
        )

        self.resizeDocks(
            [
                self.projects_dock,
                self.layer_dock,
            ],
            [
                300,
                500,
            ],
            Qt.Vertical,
        )

    # ---------------------------------------------------------
    # Map navigation
    # ---------------------------------------------------------

    def activate_pan_tool(self, *args):
        self.map_canvas.setMapTool(
            self.pan_tool
        )

        self.pan_action.setChecked(
            True
        )

    def update_identify_layer(
        self,
        layer,
    ):
        """
        Point the identify tool at the layer currently highlighted
        in the Layers pane.
        """

        vector_layer_selected = (
            layer is not None
            and layer.isValid()
            and layer.type()
            == QgsMapLayerType.VectorLayer
        )

        self.identify_feature_action.setEnabled(
            vector_layer_selected
        )

        if vector_layer_selected:
            self.identify_tool.setLayer(
                layer
            )

            return

        if (
            self.map_canvas.mapTool()
            == self.identify_tool
        ):
            self.activate_pan_tool()

    def activate_identify_tool(self, *args):
        """
        Activate feature identification for the layer highlighted
        in the Layers pane.
        """

        layer = self.layer_tree.currentLayer()

        if (
            layer is None
            or not layer.isValid()
            or layer.type()
            != QgsMapLayerType.VectorLayer
        ):
            QMessageBox.information(
                self,
                self.text(
                    "select_vector_layer"
                ),
                self.text(
                    "select_vector_layer_before_identify"
                ),
            )

            self.activate_pan_tool()
            return

        self.identify_tool.setLayer(
            layer
        )

        self.map_canvas.setMapTool(
            self.identify_tool
        )

        self.identify_feature_action.setChecked(
            True
        )

    def activate_measure_distance_tool(
        self,
        *args,
    ):
        if not hasattr(
            self,
            "measure_distance_tool",
        ):
            self.measure_distance_tool = (
                MeasurementMapTool(
                    canvas=self.map_canvas,
                    measurement_type="distance",
                    message_callback=(
                        self.status_message.setText
                    ),
                )
            )

        self.map_canvas.setMapTool(
            self.measure_distance_tool
        )

        self.measure_distance_action.setChecked(
            True
        )

    def activate_measure_area_tool(
        self,
        *args,
    ):
        if not hasattr(
            self,
            "measure_area_tool",
        ):
            self.measure_area_tool = (
                MeasurementMapTool(
                    canvas=self.map_canvas,
                    measurement_type="area",
                    message_callback=(
                        self.status_message.setText
                    ),
                )
            )

        self.map_canvas.setMapTool(
            self.measure_area_tool
        )

        self.measure_area_action.setChecked(
            True
        )

    def handle_identified_feature(
        self,
        feature,
    ):
        """
        Select an identified feature and display its attributes.
        """

        layer = self.layer_tree.currentLayer()

        if (
            layer is None
            or not layer.isValid()
            or layer.type()
            != QgsMapLayerType.VectorLayer
        ):
            return

        layer.selectByIds(
            [
                feature.id(),
            ]
        )

        self.update_layer_information(
            layer
        )

        feature_tab_index = (
            self.information_tabs.indexOf(
                self.feature_table
            )
        )

        if feature_tab_index >= 0:
            self.information_tabs.setCurrentIndex(
                feature_tab_index
            )

        self.map_canvas.refresh()

    def zoom_full_extent(self):
        project_layers = self.visible_project_layers()

        if not project_layers:
            self.map_canvas.zoomToFullExtent()
            return

        self.map_canvas.setLayers(
            project_layers
        )

        self.map_canvas.zoomToFullExtent()

        extent = self.map_canvas.extent()

        self.refresh_map_layers()

        self.map_canvas.setExtent(
            extent
        )

        self.map_canvas.refresh()

    # ---------------------------------------------------------
    # Basemaps and canvas layer order
    # ---------------------------------------------------------

    def set_basemap(
        self,
        basemap_name,
    ):
        uri = BASEMAPS.get(
            basemap_name
        )

        if uri is None:
            return

        candidate = QgsRasterLayer(
            uri,
            basemap_name,
            "wms",
        )

        if not candidate.isValid():
            QMessageBox.warning(
                self,
                self.text("basemap_unavailable"),
                self.text(
                    "basemap_unavailable_message",
                    name=basemap_name,
                ),
            )

            return

        self.basemap_layer = candidate
        self.current_basemap_name = basemap_name

        action = self.basemap_actions.get(
            basemap_name
        )

        if action is not None:
            action.setChecked(True)

        if hasattr(self, "basemap_button"):
            self.basemap_button.setText(
                basemap_name
            )

        self.refresh_map_layers()

        self.status_message.setText(
            self.text(
                "basemap_selected",
                name=basemap_name,
            )
        )

    def visible_project_layers(self):
        return [
            layer
            for layer in (
                self.project
                .layerTreeRoot()
                .checkedLayers()
            )
            if layer is not self.basemap_layer
        ]

    def schedule_canvas_refresh(
        self,
        *args,
    ):
        QTimer.singleShot(
            0,
            self.refresh_map_layers,
        )

    def refresh_map_layers(self, *args):
        project_layers = self.visible_project_layers()

        canvas_layers = list(
            project_layers
        )

        preview_layer = None

        source_type = (
            self.source_combo.currentData()
        )

        if self.drawn_polygon_area_annotation is not None:
            self.drawn_polygon_area_annotation.setVisible(
                source_type == "draw_polygon"
            )

        if self.drawn_polygon_area_item is not None:
            self.drawn_polygon_area_item.setVisible(
                source_type == "draw_polygon"
            )

        if source_type == "custom_polygon":
            preview_layer = (
                self.custom_polygon_layer
            )

        elif source_type == "draw_polygon":
            preview_layer = (
                self.drawn_polygon_layer
            )

        if (
            preview_layer is not None
            and preview_layer.isValid()
        ):
            canvas_layers.insert(
                0,
                preview_layer,
            )

        if (
            self.basemap_layer is not None
            and self.basemap_layer.isValid()
        ):
            canvas_layers.append(
                self.basemap_layer
            )

        self.map_canvas.setLayers(
            canvas_layers
        )

        self.refresh_overview()

    def remove_embedded_basemaps(self):
        basemap_layer_ids = []

        for layer in self.project.mapLayers().values():
            if layer.type() != QgsMapLayerType.RasterLayer:
                continue

            source = layer.source().lower()

            if (
                "type=xyz" in source
                or "tile.openstreetmap.org" in source
                or "google.com/vt" in source
            ):
                basemap_layer_ids.append(
                    layer.id()
                )

        if basemap_layer_ids:
            self.project.removeMapLayers(
                basemap_layer_ids
            )

    # ---------------------------------------------------------
    # Analysis toolbar
    # ---------------------------------------------------------

    def update_source_placeholder(self):
        country_code = (
            self.country_combo.currentData()
        )

        if country_code == "FI":
            self.source_input.setPlaceholderText(
                "434-415-1-226"
            )
        else:
            self.source_input.setPlaceholderText(
                "KÄVLINGE ÅLSTORP 19:63"
            )

    def update_source_type(self):
        source_type = (
            self.source_combo.currentData()
        )

        polygon_file_selected = (
            source_type == "custom_polygon"
        )

        draw_selected = (
            source_type == "draw_polygon"
        )

        self.browse_button.setEnabled(
            polygon_file_selected
        )

        self.source_input.setReadOnly(
            polygon_file_selected
            or draw_selected
        )

        if polygon_file_selected:
            self.activate_pan_tool()

            self.source_input.setPlaceholderText(
                self.text(
                    "select_polygon_file_placeholder"
                )
            )

            if self.custom_polygon_path:
                self.source_input.setText(
                    self.custom_polygon_path
                )
            else:
                self.source_input.clear()

        elif draw_selected:
            if self.drawn_polygon_path:
                self.source_input.setText(
                    self.drawn_polygon_path
                )
            else:
                self.source_input.clear()

            self.begin_polygon_drawing()

        else:
            self.activate_pan_tool()
            self.source_input.clear()
            self.update_source_placeholder()

        self.refresh_map_layers()

    def update_drawn_polygon_area_preview(
        self,
        geometry,
    ):
        """
        Update the hectare indicator during polygon drawing.
        """

        map_crs = (
            self.map_canvas
            .mapSettings()
            .destinationCrs()
        )

        if (
            geometry is None
            or geometry.isEmpty()
            or not map_crs.isValid()
        ):
            return

        self.show_drawn_polygon_area_indicator(
            geometry=geometry,
            geometry_crs=map_crs,
        )

    def remove_drawn_polygon_area_indicator(self):
        """
        Remove the hectare indicator from the map canvas.
        """

        if self.drawn_polygon_area_annotation is not None:
            self.drawn_polygon_area_annotation.setVisible(
                False
            )

        if self.drawn_polygon_area_item is not None:
            self.drawn_polygon_area_item.setVisible(
                False
            )

            self.map_canvas.scene().removeItem(
                self.drawn_polygon_area_item
            )

        self.drawn_polygon_area_item = None
        self.drawn_polygon_area_annotation = None

    def show_drawn_polygon_area_indicator(
        self,
        geometry,
        geometry_crs,
    ):
        """
        Create or update the polygon hectare indicator.
        """

        if geometry is None or geometry.isEmpty():
            return

        # ---------------------------------------------
        # Calculate the area
        # ---------------------------------------------

        area_calculator = QgsDistanceArea()

        area_calculator.setSourceCrs(
            geometry_crs,
            QgsProject.instance().transformContext(),
        )

        area_calculator.setEllipsoid(
            "WGS84"
        )

        area_square_metres = (
            area_calculator.measureArea(
                geometry
            )
        )

        area_hectares = (
            area_square_metres / 10000.0
        )

        label_text = (
            f"{area_hectares:.2f} ha"
        )

        # ---------------------------------------------
        # Find the upper-right polygon vertex
        # ---------------------------------------------

        bounds = geometry.boundingBox()

        target_corner = QgsPointXY(
            bounds.xMaximum(),
            bounds.yMaximum(),
        )

        vertices = [
            QgsPointXY(
                vertex.x(),
                vertex.y(),
            )
            for vertex in geometry.vertices()
        ]

        if not vertices:
            return

        anchor_point = min(
            vertices,
            key=lambda vertex: (
                (
                    vertex.x()
                    - target_corner.x()
                )
                ** 2
                + (
                    vertex.y()
                    - target_corner.y()
                )
                ** 2
            ),
        )

        # ---------------------------------------------
        # Prepare the text
        # ---------------------------------------------

        document = QTextDocument()

        document.setDocumentMargin(
            2.0
        )

        document.setHtml(
            (
                "<div style=\""
                "font-family: Segoe UI, sans-serif;"
                "font-size: 9pt;"
                "font-weight: 600;"
                "color: #172033;"
                "white-space: nowrap;"
                "\">"
                f"{label_text}"
                "</div>"
            )
        )

        document.adjustSize()

        # QTextDocument reports pixel dimensions.
        # Convert these into the millimetres used by
        # QgsTextAnnotation.
        horizontal_dpi = max(
            self.map_canvas.logicalDpiX(),
            1,
        )

        vertical_dpi = max(
            self.map_canvas.logicalDpiY(),
            1,
        )

        frame_width_mm = (
            document.idealWidth()
            * 25.4
            / horizontal_dpi
            + 1.5
        )

        frame_height_mm = (
            document.size().height()
            * 25.4
            / vertical_dpi
            + 1.0
        )

        # ---------------------------------------------
        # Create or update the annotation
        # ---------------------------------------------

        annotation = (
            self.drawn_polygon_area_annotation
        )

        if annotation is None:
            annotation = QgsTextAnnotation()

            frame_symbol = (
                QgsFillSymbol.createSimple(
                    {
                        "color": "255,255,255,235",
                        "outline_color": (
                            "255,110,0,255"
                        ),
                        "outline_width": "0.4",
                    }
                )
            )

            annotation.setFillSymbol(
                frame_symbol
            )

            self.drawn_polygon_area_annotation = (
                annotation
            )

        annotation.setDocument(
            document
        )

        annotation.setMapPosition(
            anchor_point
        )

        annotation.setMapPositionCrs(
            geometry_crs
        )

        annotation.setHasFixedMapPosition(
            True
        )

        annotation.setFrameSizeMm(
            QSizeF(
                frame_width_mm,
                frame_height_mm,
            )
        )

        annotation.setFrameOffsetFromReferencePointMm(
            QPointF(
                3.0,
                -frame_height_mm - 3.0,
            )
        )

        annotation.setVisible(
            True
        )

        # Only create the canvas item once. During drawing,
        # the existing item is simply updated.
        if self.drawn_polygon_area_item is None:
            self.drawn_polygon_area_item = (
                QgsMapCanvasAnnotationItem(
                    annotation,
                    self.map_canvas,
                )
            )

        self.drawn_polygon_area_item.setVisible(
            True
        )

        self.drawn_polygon_area_item.update()
        self.map_canvas.refresh()

    def begin_polygon_drawing(self):
        self.remove_drawn_polygon_area_indicator()

        self.central_tabs.setCurrentIndex(0)

        self.draw_polygon_tool.start_drawing()

        self.map_canvas.setMapTool(
            self.draw_polygon_tool
        )

        self.status_message.setText(
            self.text(
                "draw_polygon_instructions"
            )
        )

    def cancel_polygon_drawing(self):
        self.remove_drawn_polygon_area_indicator()

        self.activate_pan_tool()

        self.status_message.setText(
            self.text(
                "polygon_drawing_cancelled"
            )
        )

    def finish_drawn_polygon(self, geometry):
        if geometry is None or geometry.isEmpty():
            QMessageBox.warning(
                self,
                self.text(
                    "invalid_polygon"
                ),
                self.text(
                    "drawn_polygon_has_no_geometry"
                ),
            )
            return

        if not geometry.isGeosValid():
            QMessageBox.warning(
                self,
                self.text(
                    "invalid_polygon"
                ),
                self.text(
                    "drawn_polygon_invalid"
                ),
            )

            self.begin_polygon_drawing()
            return

        map_crs = (
            self.map_canvas
            .mapSettings()
            .destinationCrs()
        )

        if not map_crs.isValid():
            QMessageBox.warning(
                self,
                self.text(
                    "invalid_map_crs"
                ),
                self.text(
                    "invalid_map_crs_message"
                ),
            )
            return

        memory_layer = QgsVectorLayer(
            (
                "Polygon?crs="
                f"{map_crs.authid()}"
            ),
            self.text(
                "drawn_analysis_polygon"
            ),
            "memory",
        )

        feature = QgsFeature()
        feature.setGeometry(geometry)

        provider = memory_layer.dataProvider()

        if not provider.addFeature(feature):
            QMessageBox.critical(
                self,
                self.text(
                    "polygon_error"
                ),
                self.text(
                    "polygon_temporary_layer_error"
                ),
            )
            return

        memory_layer.updateExtents()

        temporary_root = (
            Path(
                os.environ.get(
                    "LOCALAPPDATA",
                    str(Path.home()),
                )
            )
            / "Sites"
            / "Temporary"
        )

        temporary_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        timestamp = datetime.now().strftime(
            "%Y%m%d-%H%M%S-%f"
        )

        output_path = (
            temporary_root
            / (
                "drawn_analysis_polygon_"
                f"{timestamp}.gpkg"
            )
        )

        options = (
            QgsVectorFileWriter
            .SaveVectorOptions()
        )

        options.driverName = "GPKG"
        options.layerName = "analysis_polygon"

        options.actionOnExistingFile = (
            QgsVectorFileWriter
            .CreateOrOverwriteFile
        )

        writer_result = (
            QgsVectorFileWriter
            .writeAsVectorFormatV3(
                memory_layer,
                str(output_path),
                (
                    QgsProject.instance()
                    .transformContext()
                ),
                options,
            )
        )

        if (
            writer_result[0]
            != QgsVectorFileWriter.NoError
        ):
            QMessageBox.critical(
                self,
                self.text(
                    "polygon_save_error"
                ),
                self.text(
                    "polygon_save_error_message",
                    error=writer_result[1],
                ),
            )
            return

        polygon_uri = (
            f"{output_path}"
            "|layername=analysis_polygon"
        )

        preview_layer = QgsVectorLayer(
            polygon_uri,
            self.text(
                "drawn_analysis_polygon"
            ),
            "ogr",
        )

        if not preview_layer.isValid():
            QMessageBox.critical(
                self,
                self.text(
                    "polygon_preview_error"
                ),
                self.text(
                    "polygon_preview_error_message"
                ),
            )
            return

        preview_symbol = QgsFillSymbol.createSimple(
            {
                "color": "255,196,0,70",
                "outline_color": "255,110,0,255",
                "outline_width": "1.2",
            }
        )

        preview_layer.setRenderer(
            QgsSingleSymbolRenderer(
                preview_symbol
            )
        )

        self.drawn_polygon_path = polygon_uri
        self.drawn_polygon_layer = preview_layer

        self.show_drawn_polygon_area_indicator(
            geometry=geometry,
            geometry_crs=map_crs,
        )

        self.source_input.setText(
            polygon_uri
        )

        self.source_input.setToolTip(
            polygon_uri
        )

        self.activate_pan_tool()
        self.refresh_map_layers()

        preview_extent = self.project_layer_extent(
            preview_layer,
            (
                self.map_canvas
                .mapSettings()
                .destinationCrs()
            ),
        )

        if (
            preview_extent is not None
            and not preview_extent.isEmpty()
        ):
            preview_extent.scale(1.25)

            self.map_canvas.setExtent(
                preview_extent
            )

        self.map_canvas.refresh()

        self.status_message.setText(
            self.text(
                "drawn_polygon_ready"
            )
        )

    def select_custom_polygon(self):
        registry = QgsProviderRegistry.instance()

        file_filters = registry.fileVectorFilters()

        if "All files" not in file_filters:
            file_filters += ";;All files (*.*)"

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.text(
                "select_analysis_polygon"
            ),
            os.path.expanduser("~"),
            file_filters,
        )
        if not file_path:
            return

        polygon_candidates = []

        try:
            sublayers = registry.querySublayers(
                file_path
            )
        except Exception as error:
            QMessageBox.warning(
                self,
                self.text(
                    "unable_to_inspect_data_source"
                ),
                self.text(
                    "unable_to_inspect_data_source_message",
                    path=file_path,
                    error=error,
                ),
            )
            return

        for details in sublayers:
            if details.type() != Qgis.LayerType.Vector:
                continue

            candidate = QgsVectorLayer(
                details.uri(),
                details.name(),
                details.providerKey(),
            )

            if not candidate.isValid():
                continue

            if (
                candidate.geometryType()
                != QgsWkbTypes.PolygonGeometry
            ):
                continue

            polygon_candidates.append(
                {
                    "details": details,
                    "layer": candidate,
                }
            )

        # Some simple formats may not report sublayers.
        if not polygon_candidates:
            candidate = QgsVectorLayer(
                file_path,
                Path(file_path).stem,
                "ogr",
            )

            if (
                candidate.isValid()
                and candidate.geometryType()
                == QgsWkbTypes.PolygonGeometry
            ):
                polygon_candidates.append(
                    {
                        "details": None,
                        "layer": candidate,
                    }
                )

        if not polygon_candidates:
            QMessageBox.warning(
                self,
                self.text(
                    "polygon_layer_required"
                ),
                self.text(
                    "polygon_layer_required_message"
                ),
            )
            return

        selected_candidate = polygon_candidates[0]

        if len(polygon_candidates) > 1:
            candidate_names = [
                candidate["layer"].name()
                for candidate in polygon_candidates
            ]

            selected_name, accepted = (
                QInputDialog.getItem(
                    self,
                    self.text(
                        "select_polygon_layer"
                    ),
                    self.text(
                        "multiple_polygon_layers"
                    ),
                    candidate_names,
                    0,
                    False,
                )
            )

            if not accepted:
                return

            selected_index = (
                candidate_names.index(
                    selected_name
                )
            )

            selected_candidate = (
                polygon_candidates[selected_index]
            )

        preview_layer = selected_candidate["layer"]
        details = selected_candidate["details"]

        if details is None:
            polygon_uri = file_path
        else:
            polygon_uri = details.uri()

        preview_layer.setName(
            self.text(
                "analysis_polygon_preview"
            )
        )

        preview_symbol = QgsFillSymbol.createSimple(
            {
                "color": "255,196,0,70",
                "outline_color": "255,110,0,255",
                "outline_width": "1.2",
            }
        )

        preview_layer.setRenderer(
            QgsSingleSymbolRenderer(
                preview_symbol
            )
        )

        self.custom_polygon_path = polygon_uri
        self.custom_polygon_layer = preview_layer

        self.source_input.setText(
            polygon_uri
        )

        self.source_input.setToolTip(
            polygon_uri
        )

        self.refresh_map_layers()

        preview_extent = self.project_layer_extent(
            preview_layer,
            self.map_canvas.mapSettings()
            .destinationCrs(),
        )

        if (
            preview_extent is not None
            and not preview_extent.isEmpty()
        ):
            preview_extent.scale(1.25)

            self.map_canvas.setExtent(
                preview_extent
            )

            self.map_canvas.refresh()

        self.status_message.setText(
            self.text(
                "analysis_polygon_loaded"
            )
        )

    def local_project_files(self):
        if not self.projects_root.is_dir():
            return []

        return [
            path
            for path in self.projects_root.rglob("*")
            if (
                path.is_file()
                and path.suffix.lower()
                in {".qgz", ".qgs"}
            )
        ]

    def create_local_project_snapshot(self):
        snapshot = {}

        for project_path in self.local_project_files():
            try:
                snapshot[str(project_path.resolve())] = (
                    project_path.stat().st_mtime_ns
                )
            except OSError:
                continue

        return snapshot

    def find_completed_analysis_project(self):
        changed_projects = []

        for project_path in self.local_project_files():
            try:
                resolved_path = str(
                    project_path.resolve()
                )

                modified_time = (
                    project_path.stat().st_mtime_ns
                )
            except OSError:
                continue

            previous_modified_time = (
                self.analysis_project_snapshot.get(
                    resolved_path
                )
            )

            if (
                previous_modified_time is None
                or modified_time
                > previous_modified_time
            ):
                changed_projects.append(
                    project_path
                )

        if not changed_projects:
            return None

        return max(
            changed_projects,
            key=lambda path: (
                path.stat().st_mtime_ns
            ),
        )

    def clear_drawn_polygon_preview(self):
        self.remove_drawn_polygon_area_indicator()
        self.draw_polygon_tool.reset()

        self.drawn_polygon_layer = None
        self.drawn_polygon_path = None

        if (
            self.source_combo.currentData()
            == "draw_polygon"
        ):
            self.source_input.clear()
            self.source_input.setToolTip("")

        self.activate_pan_tool()
        self.refresh_map_layers()

    def start_analysis(self):
        country_code = (
            self.country_combo.currentData()
        )

        source_type = (
            self.source_combo.currentData()
        )

        source_value = (
            self.source_input.text().strip()
        )

        if not source_value:
            QMessageBox.warning(
                self,
                self.text("missing_analysis_source"),
                self.text(
                    "missing_analysis_source_message"
                ),
            )

            return

        if source_type in {
            "custom_polygon",
            "draw_polygon",
        }:
            source_file = source_value.split(
                "|",
                1,
            )[0]

            if not os.path.isfile(source_file):
                QMessageBox.warning(
                    self,
                    self.text("polygon_not_found"),
                    self.text(
                        "polygon_not_found_message",
                        path=source_file,
                    ),
                )

                return

        if (
            self.analysis_window is not None
            and self.analysis_window.isVisible()
        ):
            self.analysis_window.raise_()
            self.analysis_window.activateWindow()

            return

        self.analysis_project_snapshot = (
            self.create_local_project_snapshot()
        )

        self.analysis_window = AnalysisWindow(
            language=self.language_code,
            parent=self,
        )

        country_index = (
            self.analysis_window
            .country_combo
            .findData(country_code)
        )

        self.analysis_window.country_combo.setCurrentIndex(
            country_index
        )

        if source_type == "estate":
            self.analysis_window.estate_radio.setChecked(
                True
            )

            self.analysis_window.estate_input.setText(
                source_value
            )
        else:
            self.analysis_window.polygon_radio.setChecked(
                True
            )

            self.analysis_window.polygon_input.setText(
                source_value
            )

        self.analysis_window.show()
        self.analysis_window.raise_()

        QTimer.singleShot(
            0,
            self.launch_analysis_process,
        )

    def launch_analysis_process(self):
        if self.analysis_window is None:
            return

        self.analysis_window.start_analysis()

        if self.analysis_window.process is not None:
            self.analysis_window.process.finished.connect(
                self.analysis_process_finished
            )

        self.status_message.setText(
            self.text("analysis_running")
        )

    def analysis_process_finished(
        self,
        exit_code,
        exit_status,
    ):
        output = (
            self.analysis_window
            .log_output
            .toPlainText()
        )

        if exit_code != 0:
            self.status_message.setText(
                self.text("analysis_failed")
            )

            if "No estate was found for" in output:
                estate_name = (
                    self.source_input
                    .text()
                    .strip()
                )

                QMessageBox.warning(
                    self,
                    self.text("estate_not_found"),
                    self.text(
                        "estate_not_found_message",
                        estate=estate_name,
                    ),
                )
            else:
                QMessageBox.critical(
                    self,
                    self.text("analysis_failed"),
                    self.text(
                        "analysis_failed_message"
                    ),
                )

            return

        completed_project = (
            self.find_completed_analysis_project()
        )

        self.clear_drawn_polygon_preview()
        self.refresh_project_list()

        if completed_project is None:
            self.status_message.setText(
                self.text(
                    "analysis_project_not_found"
                )
            )

            return

        self.load_project(
            str(completed_project)
        )

        if self.analysis_window is not None:
            self.analysis_window.hide()

        self.show()
        self.raise_()
        self.activateWindow()

        self.status_message.setText(
            self.text(
                "analysis_completed_project_loaded"
            )
        )

    # ---------------------------------------------------------
    # Project handling
    # ---------------------------------------------------------

    def load_project_report(
        self,
        project_path,
    ):
        project_directory = (
            Path(project_path)
            .resolve()
            .parent
        )

        markdown_path = (
            project_directory
            / "project_report.md"
        )

        if markdown_path.is_file():
            try:
                report_text = (
                    markdown_path.read_text(
                        encoding="utf-8-sig"
                    )
                )
            except OSError as error:
                self.project_report_view.setMarkdown(
                    "# Project information\n\n"
                    "The project report could not "
                    "be read.\n\n"
                    f"`{error}`"
                )
                return

            self.project_report_view.setMarkdown(
                report_text
            )

            self.project_report_view.setToolTip(
                str(markdown_path)
            )

            return

        # Older projects used text reports.
        legacy_reports = sorted(
            project_directory.glob(
                "prints (*.txt)"
            ),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

        if legacy_reports:
            legacy_path = legacy_reports[0]

            try:
                report_text = (
                    legacy_path.read_text(
                        encoding="utf-8-sig"
                    )
                )
            except OSError as error:
                self.project_report_view.setMarkdown(
                    "# Project information\n\n"
                    "The legacy project report could "
                    "not be read.\n\n"
                    f"`{error}`"
                )
                return

            self.project_report_view.setPlainText(
                report_text
            )

            self.project_report_view.setToolTip(
                str(legacy_path)
            )

            return

        self.project_report_view.setMarkdown(
            "# Project information\n\n"
            "No project report was found in:\n\n"
            f"`{project_directory}`"
        )

        self.project_report_view.setToolTip(
            str(project_directory)
        )

    def open_project(self):
        project_path, _ = QFileDialog.getOpenFileName(
            self,
            self.text("open_qgis_project"),
            os.path.expanduser("~"),
            self.text("qgis_project_files"),
        )

        if project_path:
            self.load_project(
                project_path
            )

    def load_project(
        self,
        project_path,
    ):
        self.project.clear()

        if not self.project.read(project_path):
            QMessageBox.critical(
                self,
                self.text("project_error"),
                self.text(
                    "project_open_failed_message",
                    path=project_path,
                ),
            )

            return

        project_crs = self.project.crs()

        if not project_crs.isValid():
            QMessageBox.critical(
                self,
                self.text("project_crs_error"),
                self.text(
                    "project_crs_error_message"
                ),
            )
            return

        self.map_canvas.setDestinationCrs(
            project_crs
        )

        self.overview_canvas.setDestinationCrs(
            project_crs
        )

        self.remove_embedded_basemaps()
        self.refresh_map_layers()
        self.zoom_full_extent()

        self.load_project_report(
            project_path
        )

        self.status_message.setText(
            self.text(
                "project_loaded",
                name=os.path.basename(
                    project_path
                ),
            )
        )

    def print_project(self):
        """
        Print one layout from the currently loaded QGIS project.
        """

        if not self.project.fileName():
            QMessageBox.information(
                self,
                self.text("no_project_loaded"),
                self.text(
                    "load_project_before_printing"
                ),
            )
            return

        layouts = (
            self.project
            .layoutManager()
            .printLayouts()
        )

        if not layouts:
            QMessageBox.information(
                self,
                self.text(
                    "no_print_layout"
                ),
                self.text(
                    "no_print_layout_message"
                ),
            )
            return

        if len(layouts) == 1:
            selected_layout = layouts[0]

        else:
            layout_names = [
                layout.name()
                for layout in layouts
            ]

            selected_name, accepted = (
                QInputDialog.getItem(
                    self,
                    "Select print layout",
                    "Layout:",
                    layout_names,
                    0,
                    False,
                )
            )

            if not accepted:
                return

            selected_layout = next(
                layout
                for layout in layouts
                if layout.name() == selected_name
            )

        printer = QPrinter(
            QPrinter.HighResolution
        )

        printer.setDocName(
            selected_layout.name()
        )

        printer.setFullPage(
            True
        )

        print_dialog = QPrintDialog(
            printer,
            self,
        )

        print_dialog.setWindowTitle(
            self.text("print_sovra_project")
        )

        if not print_dialog.exec_():
            return

        painter = QPainter()

        if not painter.begin(printer):
            QMessageBox.critical(
                self,
                self.text("printing_failed_title"),
                self.text(
                    "printer_open_failed_message"
                ),
            )
            return

        exporter = QgsLayoutExporter(
            selected_layout
        )

        page_count = (
            selected_layout
            .pageCollection()
            .pageCount()
        )

        try:
            for page_number in range(page_count):
                if (
                    page_number > 0
                    and not printer.newPage()
                ):
                    raise RuntimeError(
                        "The printer could not create "
                        "another page."
                    )

                exporter.renderPage(
                    painter,
                    page_number,
                )

        except Exception as error:
            QMessageBox.critical(
                self,
                self.text("printing_failed_title"),
                str(error),
            )

        finally:
            painter.end()

    def save_project(self):
        project_path = (
            self.project.fileName()
        )

        if not project_path:
            project_path, _ = QFileDialog.getSaveFileName(
                self,
                self.text("save_qgis_project"),
                os.path.expanduser("~"),
                self.text("qgis_project_file"),
            )

            if not project_path:
                return

            if not project_path.lower().endswith(
                ".qgz"
            ):
                project_path += ".qgz"

        if not self.project.write(
            project_path
        ):
            QMessageBox.critical(
                self,
                self.text("save_error_title"),
                self.text(
                    "project_save_failed_message"
                ),
            )
            return

        self.status_message.setText(
            self.text("project_saved")
        )

    # ---------------------------------------------------------
    # Layer and overview information
    # ---------------------------------------------------------

    def update_layer_information(
        self,
        layer,
    ):
        self.layer_table.setRowCount(0)
        self.feature_table.setRowCount(0)

        if layer is None:
            return

        properties = [
            (
                "Name",
                layer.name(),
            ),
            (
                "Source",
                layer.source(),
            ),
            (
                "CRS",
                layer.crs().authid(),
            ),
        ]

        if layer.type() == QgsMapLayerType.VectorLayer:
            properties.extend(
                [
                    (
                        "Geometry",
                        QgsWkbTypes.displayString(
                            layer.wkbType()
                        ),
                    ),
                    (
                        "Features",
                        str(
                            layer.featureCount()
                        ),
                    ),
                ]
            )

        for property_name, value in properties:
            row = self.layer_table.rowCount()
            self.layer_table.insertRow(row)

            self.layer_table.setItem(
                row,
                0,
                QTableWidgetItem(
                    str(property_name)
                ),
            )

            self.layer_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    str(value)
                ),
            )

        if (
            layer.type()
            != QgsMapLayerType.VectorLayer
        ):
            return

        selected_features = (
            layer.selectedFeatures()
        )

        if not selected_features:
            return

        feature = selected_features[0]

        for field in layer.fields():
            row = self.feature_table.rowCount()
            self.feature_table.insertRow(row)

            self.feature_table.setItem(
                row,
                0,
                QTableWidgetItem(
                    field.name()
                ),
            )

            self.feature_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    str(
                        feature[field.name()]
                    )
                ),
            )

    def selected_country_feature(self):
        """
        Return the world-country feature selected in the toolbar.
        """

        if not self.initialize_overview_layers():
            return None

        country_code = (
            self.country_combo.currentData()
        )

        country_settings = (
            COUNTRY_MAP_SETTINGS.get(
                country_code
            )
        )

        if country_settings is None:
            return None

        country_name = country_settings[
            "admin_name"
        ]

        admin_field_index = (
            self.world_countries_layer
            .fields()
            .indexFromName("ADMIN")
        )

        if admin_field_index == -1:
            self.status_message.setText(
                self.text(
                    "overview_admin_field_missing"
                )
            )

            return None

        for feature in (
            self.world_countries_layer.getFeatures()
        ):
            admin_name = str(
                feature["ADMIN"]
            ).strip()

            if (
                admin_name.casefold()
                == country_name.casefold()
            ):
                return feature

        self.status_message.setText(
            self.text(
                "overview_country_not_found",
                country=country_name,
            )
        )

        return None

    def country_extent_for_crs(
        self,
        country_feature,
        target_crs,
    ):
        """
        Transform a country's bounding box into a target CRS.
        """

        geometry = country_feature.geometry()

        if (
            geometry is None
            or geometry.isEmpty()
        ):
            return None

        source_crs = (
            self.world_countries_layer.crs()
        )

        source_extent = geometry.boundingBox()

        if source_crs == target_crs:
            country_extent = QgsRectangle(
                source_extent
            )
        else:
            coordinate_transform = (
                QgsCoordinateTransform(
                    source_crs,
                    target_crs,
                    self.project,
                )
            )

            try:
                country_extent = (
                    coordinate_transform
                    .transformBoundingBox(
                        source_extent
                    )
                )
            except Exception as error:
                print(
                    "Could not transform the selected "
                    f"country extent: {error}"
                )

                return None

        country_extent.scale(
            1.10
        )

        return country_extent

    def focus_selected_country(
        self,
        *args,
        update_main_map=True,
    ):
        """
        Display the toolbar-selected country in the map canvases.
        """

        country_feature = (
            self.selected_country_feature()
        )

        if country_feature is None:
            return

        country_code = (
            self.country_combo.currentData()
        )

        country_settings = (
            COUNTRY_MAP_SETTINGS.get(
                country_code
            )
        )

        if country_settings is None:
            return

        target_crs = QgsCoordinateReferenceSystem(
            country_settings["crs"]
        )

        if not target_crs.isValid():
            self.status_message.setText(
                self.text(
                    "country_map_invalid_crs",
                    crs=country_settings["crs"],
                )
            )

            return

        self.map_canvas.setDestinationCrs(
            target_crs
        )

        self.overview_canvas.setDestinationCrs(
            target_crs
        )

        country_extent = (
            self.country_extent_for_crs(
                country_feature=country_feature,
                target_crs=target_crs,
            )
        )

        if (
            country_extent is None
            or country_extent.isEmpty()
        ):
            return

        country_name = (
            self.country_combo.currentText()
        )

        self.overview_canvas.setDestinationCrs(
            target_crs
        )

        self.overview_canvas.setLayers(
            [
                self.overview_satellite_layer,
            ]
        )

        self.overview_canvas.setExtent(
            country_extent
        )

        if self.overview_project_marker is not None:
            self.overview_project_marker.hide()

        self.overview_canvas.refresh()

        if update_main_map:
            self.refresh_map_layers()

            print(
                "Main canvas CRS:",
                self.map_canvas
                .mapSettings()
                .destinationCrs()
                .authid(),
            )

            print(
                "Main canvas layers:",
                [
                    (
                        layer.name(),
                        layer.isValid(),
                        layer.crs().authid(),
                    )
                    for layer in (
                        self.map_canvas.layers()
                    )
                ],
            )

        if update_main_map:
            self.map_canvas.setExtent(
                country_extent
            )

            self.map_canvas.refresh()

        self.overview_dock.setWindowTitle(
            self.text(
                "country_overview_named",
                country=country_name,
            )
        )

        self.status_message.setText(
            self.text(
                "country_selected",
                country=country_name,
            )
        )

    def initialize_overview_layers(self):
        """
        Create the private layers used by the country overview.

        These layers are deliberately not added to QgsProject, so
        they never appear in the Layers panel.
        """

        if self.world_countries_layer is None:
            countries_path = (
                Path(__file__).resolve().parent
                / "assets"
                / "world_countries.gpkg"
            )

            countries_uri = (
                f"{countries_path}"
                "|layername=world_countries"
            )

            self.world_countries_layer = QgsVectorLayer(
                countries_uri,
                "World countries",
                "ogr",
            )

            if not self.world_countries_layer.isValid():
                self.world_countries_layer = None

                self.status_message.setText(
                    self.text(
                        "overview_dataset_unavailable"
                    )
                )

                return False

        if self.overview_satellite_layer is None:
            self.overview_satellite_layer = QgsRasterLayer(
                BASEMAPS["Google Satellite"],
                "Country overview satellite",
                "wms",
            )

            if not self.overview_satellite_layer.isValid():
                self.overview_satellite_layer = None

                self.status_message.setText(
                    self.text(
                        "overview_satellite_unavailable"
                    )
                )

                return False

        if self.overview_project_marker is None:
            self.overview_project_marker = QgsVertexMarker(
                self.overview_canvas
            )

            self.overview_project_marker.setColor(
                QColor("#e31b23")
            )

            self.overview_project_marker.setFillColor(
                QColor("#e31b23")
            )

            self.overview_project_marker.setIconType(
                QgsVertexMarker.ICON_CIRCLE
            )

            self.overview_project_marker.setIconSize(12)
            self.overview_project_marker.setPenWidth(3)
            self.overview_project_marker.hide()

        return True

    def project_layer_extent(
        self,
        layer,
        project_crs,
    ):
        """
        Return a layer extent transformed into the project CRS.
        """

        if (
            layer is None
            or not layer.isValid()
            or not layer.crs().isValid()
        ):
            return None

        layer_extent = layer.extent()

        if layer_extent.isEmpty():
            return None

        if layer.crs() == project_crs:
            return QgsRectangle(
                layer_extent
            )

        coordinate_transform = QgsCoordinateTransform(
            layer.crs(),
            project_crs,
            self.project,
        )

        try:
            return coordinate_transform.transformBoundingBox(
                layer_extent
            )
        except Exception as error:
            print(
                "Could not transform overview extent for "
                f"{layer.name()}: {error}"
            )

            return None

    def overview_project_extent(
        self,
        project_layers,
        project_crs,
    ):
        """
        Find the analysis-site extent, falling back to the combined
        extent of all visible project layers.
        """

        preferred_names = (
            "fastigheten",
            "analysis site",
            "project area",
        )

        for layer in project_layers:
            layer_name = layer.name().strip().casefold()

            if any(
                preferred_name in layer_name
                for preferred_name in preferred_names
            ):
                layer_extent = self.project_layer_extent(
                    layer,
                    project_crs,
                )

                if layer_extent is not None:
                    return layer_extent

        combined_extent = None

        for layer in project_layers:
            layer_extent = self.project_layer_extent(
                layer,
                project_crs,
            )

            if layer_extent is None:
                continue

            if combined_extent is None:
                combined_extent = QgsRectangle(
                    layer_extent
                )
            else:
                combined_extent.combineExtentWith(
                    layer_extent
                )

        return combined_extent

    def refresh_overview(self, *args):
        project_layers = self.visible_project_layers()

        if not project_layers:
            self.focus_selected_country(
                update_main_map=False
            )

            return 

        if not self.initialize_overview_layers():
            return

        project_crs = self.project.crs()

        if not project_crs.isValid():
            return

        project_extent = self.overview_project_extent(
            project_layers=project_layers,
            project_crs=project_crs,
        )

        if (
            project_extent is None
            or project_extent.isEmpty()
        ):
            self.overview_project_marker.hide()
            return

        project_center = project_extent.center()

        to_country_crs = QgsCoordinateTransform(
            project_crs,
            self.world_countries_layer.crs(),
            self.project,
        )

        try:
            country_point = to_country_crs.transform(
                project_center
            )
        except Exception as error:
            print(
                "Could not transform the project location "
                f"for the country overview: {error}"
            )

            self.overview_project_marker.hide()
            return

        point_geometry = QgsGeometry.fromPointXY(
            country_point
        )

        selected_country = None

        for feature in (
            self.world_countries_layer.getFeatures()
        ):
            geometry = feature.geometry()

            if (
                geometry is None
                or geometry.isEmpty()
            ):
                continue

            if geometry.intersects(point_geometry):
                selected_country = feature
                break

        if selected_country is None:
            self.status_message.setText(
                self.text(
                    "project_country_not_found"
                )
            )

            self.overview_project_marker.hide()
            return

        country_name = str(
            selected_country["ADMIN"]
        )

        to_project_crs = QgsCoordinateTransform(
            self.world_countries_layer.crs(),
            project_crs,
            self.project,
        )

        try:
            country_extent = (
                to_project_crs.transformBoundingBox(
                    selected_country.geometry().boundingBox()
                )
            )
        except Exception as error:
            print(
                "Could not transform the country extent "
                f"for {country_name}: {error}"
            )

            self.overview_project_marker.hide()
            return

        country_extent.scale(
            1.10
        )

        self.overview_canvas.setDestinationCrs(
            project_crs
        )

        self.overview_canvas.setLayers(
            [
                self.overview_satellite_layer,
            ]
        )

        self.overview_canvas.setExtent(
            country_extent
        )

        self.overview_project_marker.setCenter(
            project_center
        )

        self.overview_project_marker.show()

        self.overview_canvas.refresh()

    # ---------------------------------------------------------
    # Status information
    # ---------------------------------------------------------

    def update_coordinates(
        self,
        point,
    ):
        self.coordinate_label.setText(
            f"X: {point.x():.2f}  "
            f"Y: {point.y():.2f}"
        )

    def update_scale(
        self,
        scale,
    ):
        self.scale_label.setText(
            self.text(
                "scale_value",
                scale=f"{scale:,.0f}",
            )
        )

    def show_about(self):
        application_root = (
            Path(__file__).resolve().parent
        )

        branding_directory = (
            application_root
            / "assets"
            / "branding"
        )

        technologies = [
            (
                "QGIS",
                branding_directory
                / "qgis-logo.png",
            ),
            (
                "Qt",
                branding_directory
                / "qt-logo.png",
            ),
            (
                "Python",
                branding_directory
                / "python-powered.png",
            ),
        ]

        technology_rows = []

        for technology_name, logo_path in technologies:
            if logo_path.is_file():
                technology_rows.append(
                    "<td style='padding: 8px 14px;'>"
                    f"<img src='{logo_path.as_uri()}' "
                    "height='36'>"
                    "</td>"
                )
            else:
                technology_rows.append(
                    "<td style='padding: 8px 14px;'>"
                    f"<b>{technology_name}</b>"
                    "</td>"
                )

        technology_html = "".join(
            technology_rows
        )

        about_box = QMessageBox(
            self
        )

        about_box.setWindowTitle(
            self.text("about_sovra")
        )

        about_box.setTextFormat(
            Qt.RichText
        )

        about_box.setText(
            self.text(
                "about_content",
                technology_html=technology_html,
            )
        )

        about_box.setStandardButtons(
            QMessageBox.Ok
        )

        about_box.exec_()


def load_application_stylesheet(
    application,
):
    application_root = (
        Path(__file__).resolve().parent
    )

    styles_directory = (
        application_root
        / "styles"
    )

    style_paths = [
        styles_directory
        / "sites_base.qss"
    ]

    if sys.platform.startswith("win"):
        platform_style = (
            styles_directory
            / "sites_windows.qss"
        )

    elif sys.platform == "darwin":
        platform_style = (
            styles_directory
            / "sites_macos.qss"
        )

    else:
        platform_style = (
            styles_directory
            / "sites_linux.qss"
        )

    style_paths.append(
        platform_style
    )

    stylesheet_parts = []

    for style_path in style_paths:
        if not style_path.is_file():
            raise FileNotFoundError(
                "Application stylesheet is missing: "
                f"{style_path}"
            )

        stylesheet_parts.append(
            style_path.read_text(
                encoding="utf-8-sig"
            )
        )

    application.setStyleSheet(
        "\n\n".join(
            stylesheet_parts
        )
    )

    print(
        "Application design loaded: "
        f"{platform_style.name}"
    )


def create_splash_pixmap(
    image_path,
    width=550,
    height=150,
):
    """
    Load and crop the splash artwork to the requested size
    without stretching it.
    """

    pixmap = QPixmap(
        str(image_path)
    )

    if pixmap.isNull():
        return pixmap

    source_width = pixmap.width()
    source_height = pixmap.height()

    target_ratio = width / height
    source_ratio = source_width / source_height

    if source_ratio > target_ratio:
        crop_width = round(
            source_height * target_ratio
        )

        crop_x = round(
            (source_width - crop_width) / 2
        )

        cropped = pixmap.copy(
            crop_x,
            0,
            crop_width,
            source_height,
        )

    else:
        crop_height = round(
            source_width / target_ratio
        )

        crop_y = round(
            (source_height - crop_height) / 2
        )

        cropped = pixmap.copy(
            0,
            crop_y,
            source_width,
            crop_height,
        )

    return cropped.scaled(
        width,
        height,
        Qt.IgnoreAspectRatio,
        Qt.SmoothTransformation,
    )

def main():
    prefix_path = os.environ.get(
        "QGIS_PREFIX_PATH"
    )

    if prefix_path:
        QgsApplication.setPrefixPath(
            prefix_path,
            True,
        )

    app = QgsApplication(
        [],
        True,
    )

    application_root = Path(
        __file__
    ).resolve().parent

    icon_path = (
        application_root
        / "assets"
        / "sovra_icon.png"
    )

    if icon_path.is_file():
        app.setWindowIcon(
            QIcon(str(icon_path))
        )

    app.setApplicationName(
        "Sovra"
    )

    application_root = (
        Path(__file__).resolve().parent
    )

    splash_path = (
        application_root
        / "assets"
        / "splash.png"
    )

    splash_pixmap = create_splash_pixmap(
        image_path=splash_path,
        width=550,
        height=150,
    )

    splash = None

    if not splash_pixmap.isNull():
        splash = QSplashScreen(
            splash_pixmap,
            Qt.WindowStaysOnTopHint,
        )

        splash.show()
        splash.raise_()

        app.processEvents()

    else:
        print(
            f"Splash image could not be loaded: "
            f"{splash_path}"
        )

    app.initQgis()

    window = SitesDesktop()


    def reveal_main_window():
        window.show()
        window.raise_()
        window.activateWindow()

        if splash is not None:
            splash.finish(window)


    if splash is not None:
        splash.raise_()

        QTimer.singleShot(
            2000,
            reveal_main_window,
        )

    else:
        reveal_main_window()

    exit_code = app.exec_()

    app.exitQgis()

    return exit_code


if __name__ == "__main__":
    sys.exit(
        main()
    )
