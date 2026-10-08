import os
import re
import sys

from datetime import datetime
from pathlib import Path
from qgis.PyQt.QtCore import (
    Qt,
    QTimer,
)

from qgis.PyQt.QtGui import (
    QColor,
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
)

from qgis.core import (
    QgsApplication,
    QgsLayerTreeModel,
    QgsMapLayerType,
    QgsProject,
    QgsRasterLayer,
    QgsWkbTypes,
)

from qgis.gui import (
    QgsLayerTreeView,
    QgsMapCanvas,
    QgsMapToolPan,
)

from gui import SitesWindow as AnalysisWindow


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


class SitesDesktop(QMainWindow):
    """
    Main GIS workspace for Sites.
    """

    def __init__(self):
        super().__init__()

        self.project = QgsProject.instance()
        self.analysis_window = None
        self.custom_polygon_path = None
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

        self.setWindowTitle(
            "Sites — Renewable Energy Site Analysis"
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

    # ---------------------------------------------------------
    # Main map
    # ---------------------------------------------------------

    def create_map_canvases(self):
        self.map_canvas = QgsMapCanvas()

        self.map_canvas.setCanvasColor(
            QColor("#e8edf2")
        )

        self.map_canvas.enableAntiAliasing(
            True
        )

        self.setCentralWidget(
            self.map_canvas
        )

        self.overview_canvas = QgsMapCanvas()

        self.overview_canvas.setCanvasColor(
            QColor("#dde5eb")
        )

        self.overview_canvas.enableAntiAliasing(
            True
        )

        self.pan_tool = QgsMapToolPan(
            self.map_canvas
        )

    # ---------------------------------------------------------
    # Local projects panel
    # ---------------------------------------------------------

    def create_projects_panel(self):
        self.projects_dock = QDockWidget(
            "Projects",
            self,
        )

        self.projects_dock.setObjectName(
            "projects_dock"
        )

        self.projects_tree = QTreeWidget()

        self.projects_tree.setHeaderLabels(
            [
                "Project",
                "Updated",
            ]
        )

        self.projects_tree.setAlternatingRowColors(
            True
        )

        self.projects_tree.setColumnWidth(
            0,
            190,
        )

        self.projects_dock.setWidget(
            self.projects_tree
        )

        self.addDockWidget(
            Qt.LeftDockWidgetArea,
            self.projects_dock,
        )

        self.refresh_project_list()

    def refresh_project_list(self):
        self.projects_tree.clear()

        if not self.projects_root.is_dir():
            placeholder = QTreeWidgetItem(
                [
                    "No local projects found",
                    "",
                ]
            )

            self.projects_tree.addTopLevelItem(
                placeholder
            )

            return

        project_files = list(
            self.projects_root.rglob("*.qgz")
        )

        grouped_projects = {}

        for project_path in project_files:
            try:
                relative_path = (
                    project_path.relative_to(
                        self.projects_root
                    )
                )
            except ValueError:
                continue

            relative_parts = relative_path.parts

            if len(relative_parts) >= 2:
                project_name = relative_parts[0]
            else:
                project_name = project_path.stem

            grouped_projects.setdefault(
                project_name,
                [],
            ).append(project_path)

        sorted_groups = sorted(
            grouped_projects.items(),
            key=lambda entry: max(
                path.stat().st_mtime
                for path in entry[1]
            ),
            reverse=True,
        )

        for project_name, paths in sorted_groups:
            project_item = QTreeWidgetItem(
                [
                    project_name,
                    "",
                ]
            )

            self.projects_tree.addTopLevelItem(
                project_item
            )

            sorted_paths = sorted(
                paths,
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )

            for project_path in sorted_paths:
                modified_time = datetime.fromtimestamp(
                    project_path.stat().st_mtime
                ).strftime(
                    "%Y-%m-%d %H:%M"
                )

                run_name = project_path.parent.name

                run_item = QTreeWidgetItem(
                    [
                        run_name,
                        modified_time,
                    ]
                )

                run_item.setData(
                    0,
                    Qt.UserRole,
                    str(project_path),
                )

                run_item.setToolTip(
                    0,
                    str(project_path),
                )

                project_item.addChild(
                    run_item
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
            item.setExpanded(
                not item.isExpanded()
            )

            return

        if not os.path.isfile(project_path):
            QMessageBox.warning(
                self,
                "Project unavailable",
                (
                    "The project file no longer exists:\n\n"
                    f"{project_path}"
                ),
            )

            self.refresh_project_list()

            return

        current_project = (
            self.project.fileName()
        )

        if (
            current_project
            and os.path.normcase(current_project)
            == os.path.normcase(project_path)
        ):
            return

        self.load_project(
            project_path
        )

    # ---------------------------------------------------------
    # Layer panel
    # ---------------------------------------------------------

    def create_layer_panel(self):
        self.layer_dock = QDockWidget(
            "Layers",
            self,
        )

        self.layer_dock.setObjectName(
            "layers_dock"
        )

        self.layer_tree = QgsLayerTreeView()

        self.layer_tree_model = QgsLayerTreeModel(
            self.project.layerTreeRoot()
        )

        self.layer_tree.setModel(
            self.layer_tree_model
        )

        self.layer_dock.setWidget(
            self.layer_tree
        )

        self.addDockWidget(
            Qt.LeftDockWidgetArea,
            self.layer_dock,
        )

    # ---------------------------------------------------------
    # Information panel
    # ---------------------------------------------------------

    def create_information_panel(self):
        self.information_dock = QDockWidget(
            "Information",
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
                "Field",
                "Value",
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
                "Property",
                "Value",
            ]
        )

        self.layer_table.horizontalHeader().setStretchLastSection(
            True
        )

        self.information_tabs.addTab(
            self.feature_table,
            "Feature information",
        )

        self.information_tabs.addTab(
            self.layer_table,
            "Layer information",
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
            "Country overview",
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
        self.open_project_action = QAction(
            QgsApplication.getThemeIcon(
                "/mActionFileOpen.svg"
            ),
            "Open project…",
            self,
        )

        self.open_project_action.setShortcut(
            "Ctrl+O"
        )

        self.save_project_action = QAction(
            QgsApplication.getThemeIcon(
                "/mActionFileSave.svg"
            ),
            "Save project",
            self,
        )

        self.save_project_action.setShortcut(
            "Ctrl+S"
        )

        self.exit_action = QAction(
            "Exit",
            self,
        )

        self.full_extent_action = QAction(
            QgsApplication.getThemeIcon(
                "/mActionZoomFullExtent.svg"
            ),
            "Full extent",
            self,
        )

        self.open_project_action.setToolTip(
            "Open a QGIS project"
        )

        self.save_project_action.setToolTip(
            "Save the current QGIS project"
        )

        self.full_extent_action.setToolTip(
            "Zoom to the full extent of project data"
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
            "About Sites",
            self,
        )

    # ---------------------------------------------------------
    # Menus
    # ---------------------------------------------------------

    def create_menus(self):
        file_menu = self.menuBar().addMenu(
            "&File"
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
            "&Edit"
        )

        view_menu = self.menuBar().addMenu(
            "&View"
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
            "Basemap"
        )

        for action in self.basemap_actions.values():
            self.basemap_menu.addAction(
                action
            )

        analysis_menu = self.menuBar().addMenu(
            "&Analysis"
        )

        self.start_analysis_action = QAction(
            "Start analysis",
            self,
        )

        self.start_analysis_action.setShortcut(
            "Ctrl+Return"
        )

        analysis_menu.addAction(
            self.start_analysis_action
        )

        help_menu = self.menuBar().addMenu(
            "&Help"
        )

        help_menu.addAction(
            self.about_action
        )

    # ---------------------------------------------------------
    # Toolbars
    # ---------------------------------------------------------

    def create_toolbars(self):
        map_toolbar = self.addToolBar(
            "Map navigation"
        )

        map_toolbar.setObjectName(
            "map_toolbar"
        )

        map_toolbar.addAction(
            self.open_project_action
        )

        map_toolbar.addAction(
            self.save_project_action
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

        self.basemap_button.setText(
            "OpenStreetMap"
        )

        self.basemap_button.setToolTip(
            "Select background map"
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
            "Analysis"
        )

        analysis_toolbar.setObjectName(
            "analysis_toolbar"
        )

        analysis_toolbar.addWidget(
            QLabel("Country:")
        )

        self.country_combo = QComboBox()

        self.country_combo.addItem(
            "Sweden",
            "SE",
        )

        self.country_combo.addItem(
            "Finland",
            "FI",
        )

        analysis_toolbar.addWidget(
            self.country_combo
        )

        analysis_toolbar.addSeparator()

        self.source_combo = QComboBox()

        self.source_combo.addItem(
            "Estate",
            "estate",
        )

        self.source_combo.addItem(
            "Custom polygon",
            "custom_polygon",
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
            "Browse…"
        )

        self.browse_button.setEnabled(
            False
        )

        analysis_toolbar.addWidget(
            self.browse_button
        )

        analysis_toolbar.addSeparator()

        self.run_button = QPushButton(
            "Start analysis"
        )

        analysis_toolbar.addWidget(
            self.run_button
        )

    # ---------------------------------------------------------
    # Status bar
    # ---------------------------------------------------------

    def create_status_bar(self):
        self.status_message = QLabel(
            "Ready"
        )

        self.coordinate_label = QLabel(
            "X: —  Y: —"
        )

        self.scale_label = QLabel(
            "Scale: —"
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

        self.source_combo.currentIndexChanged.connect(
            self.update_source_type
        )

        self.browse_button.clicked.connect(
            self.select_custom_polygon
        )

        self.projects_tree.itemClicked.connect(
            self.load_local_project
        )

        self.layer_tree.currentLayerChanged.connect(
            self.update_layer_information
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

    def activate_pan_tool(self):
        self.map_canvas.setMapTool(
            self.pan_tool
        )

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
                "Basemap unavailable",
                (
                    "The selected background map could "
                    "not be loaded:\n"
                    f"{basemap_name}"
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
            f"Basemap: {basemap_name}"
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

    def refresh_map_layers(self):
        project_layers = self.visible_project_layers()

        canvas_layers = list(
            project_layers
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

        polygon_selected = (
            source_type == "custom_polygon"
        )

        self.browse_button.setEnabled(
            polygon_selected
        )

        self.source_input.setReadOnly(
            polygon_selected
        )

        if polygon_selected:
            self.source_input.setPlaceholderText(
                "Select a polygon file…"
            )

            if self.custom_polygon_path:
                self.source_input.setText(
                    self.custom_polygon_path
                )
        else:
            self.source_input.clear()
            self.update_source_placeholder()

    def select_custom_polygon(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select custom polygon",
            os.path.expanduser("~"),
            (
                "Vector data "
                "(*.gpkg *.shp *.geojson);;"
                "All files (*.*)"
            ),
        )

        if file_path:
            self.custom_polygon_path = file_path

            self.source_input.setText(
                file_path
            )

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
                "Missing analysis source",
                (
                    "Enter an estate identifier or "
                    "select a custom polygon."
                ),
            )

            return

        if (
            source_type == "custom_polygon"
            and not os.path.isfile(source_value)
        ):
            QMessageBox.warning(
                self,
                "Polygon not found",
                "The selected polygon file does not exist.",
            )

            return

        if (
            self.analysis_window is not None
            and self.analysis_window.isVisible()
        ):
            self.analysis_window.raise_()
            self.analysis_window.activateWindow()

            return

        self.analysis_window = AnalysisWindow()

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
            "Analysis running…"
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
                "Analysis failed"
            )

            if "No estate was found for" in output:
                estate_name = (
                    self.source_input
                    .text()
                    .strip()
                )

                QMessageBox.warning(
                    self,
                    "Estate not found",
                    (
                        "No estate was found matching:\n\n"
                        f"{estate_name}\n\n"
                        "Check the spelling and the order "
                        "of the municipality, sector and "
                        "estate identifier."
                    ),
                )
            else:
                QMessageBox.critical(
                    self,
                    "Analysis failed",
                    (
                        "The analysis could not be completed.\n\n"
                        "Open the progress window details "
                        "for the complete error message."
                    ),
                )

            return

        self.status_message.setText(
            "Analysis completed"
        )

    # ---------------------------------------------------------
    # Project handling
    # ---------------------------------------------------------

    def open_project(self):
        project_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open QGIS project",
            os.path.expanduser("~"),
            "QGIS projects (*.qgz *.qgs)",
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
                "Project error",
                (
                    "Failed to open the QGIS project:\n"
                    f"{project_path}"
                ),
            )

            return

        self.remove_embedded_basemaps()
        self.refresh_map_layers()
        self.zoom_full_extent()

        self.status_message.setText(
            f"Project loaded: {os.path.basename(project_path)}"
        )

    def save_project(self):
        project_path = (
            self.project.fileName()
        )

        if not project_path:
            project_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save QGIS project",
                os.path.expanduser("~"),
                "QGIS project (*.qgz)",
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
                "Save error",
                "The project could not be saved.",
            )

            return

        self.status_message.setText(
            "Project saved"
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

    def refresh_overview(self, *args):
        project_layers = self.visible_project_layers()
        layers = list(project_layers)

        if (
            self.basemap_layer is not None
            and self.basemap_layer.isValid()
        ):
            layers.append(
                self.basemap_layer
            )

        self.overview_canvas.setLayers(
            layers
        )

        if project_layers:
            self.overview_canvas.setLayers(
                project_layers
            )

            self.overview_canvas.zoomToFullExtent()

            extent = self.overview_canvas.extent()

            self.overview_canvas.setLayers(
                layers
            )

            self.overview_canvas.setExtent(
                extent
            )

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
            f"Scale: 1:{scale:,.0f}"
        )

    def show_about(self):
        QMessageBox.about(
            self,
            "About Sites",
            (
                "Sites\n\n"
                "Renewable energy site analysis "
                "and GIS workspace."
            ),
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

    app.setApplicationName(
        "Sites"
    )

    app.initQgis()

    window = SitesDesktop()
    window.showMaximized()

    exit_code = app.exec_()

    app.exitQgis()

    return exit_code


if __name__ == "__main__":
    sys.exit(
        main()
    )
