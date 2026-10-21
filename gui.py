import os
import re
import sys
import shutil

from scripts.translations import (
    normalise_language,
    ui_text,
)
from pathlib import Path
from qgis.PyQt.QtCore import (
    QProcess,
    QProcessEnvironment,
    Qt,
    QTimer,
)
from qgis.PyQt.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QProgressBar,
)


class SitesWindow(QMainWindow):
    """
    Main application window for Sites.
    """

    def __init__(
        self,
        language="en",
        parent=None,
    ):
        super().__init__(
            parent
        )

        self.language_code = (
            normalise_language(
                language
            )
        )

        self.process = None
        self.cancel_requested = False
        self.progress_output_buffer = ""
        self.analysis_run_id = None
        self.large_area_warning_shown = False

        self.setWindowTitle(
            self.text(
                "analysis_progress_title"
            )
        )

        self.resize(
            560,
            170,
        )

        self.create_interface()
        self.connect_signals()
        self.update_source_controls()

    def text(
        self,
        key,
        **values,
    ):
        """
        Return text in the selected global language.
        """

        return ui_text(
            self.language_code,
            key,
            **values,
        )

    def create_interface(self):
        """
        Create and arrange the user-interface controls.
        """

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(
            central_widget
        )

        main_layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )

        main_layout.setSpacing(12)

        # -------------------------------------------------
        # Heading
        # -------------------------------------------------

        heading = QLabel(
            "Sovra"
        )

        heading_font = heading.font()
        heading_font.setPointSize(20)
        heading_font.setBold(True)
        heading.setFont(heading_font)

        subtitle = QLabel(
            self.text(
                "renewable_energy_site_analysis"
            )
        )

        heading.setVisible(False)
        subtitle.setVisible(False)

        # -------------------------------------------------
        # Analysis source
        # -------------------------------------------------

        source_group = QGroupBox(
            self.text("analysis_source")
        )

        source_layout = QFormLayout(
            source_group
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

        source_layout.addRow(
            self.text("country_label"),
            self.country_combo,
        )

        source_type_widget = QWidget()

        source_type_layout = QHBoxLayout(
            source_type_widget
        )

        source_type_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.estate_radio = QRadioButton(
            self.text("estate_identifier")
        )

        self.polygon_radio = QRadioButton(
            self.text("custom_polygon")
        )

        self.estate_radio.setChecked(True)

        source_type_layout.addWidget(
            self.estate_radio
        )

        source_type_layout.addWidget(
            self.polygon_radio
        )

        source_type_layout.addStretch()

        source_layout.addRow(
            self.text("source_type_label"),
            source_type_widget,
        )

        self.estate_input = QLineEdit()

        self.estate_input.setPlaceholderText(
            "Example: KÄVLINGE ÅLSTORP 19:63"
        )

        source_layout.addRow(
            self.text("estate_label"),
            self.estate_input,
        )

        polygon_widget = QWidget()

        polygon_layout = QHBoxLayout(
            polygon_widget
        )

        polygon_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.polygon_input = QLineEdit()
        self.polygon_input.setReadOnly(True)

        self.browse_button = QPushButton(
            self.text("browse")
        )

        polygon_layout.addWidget(
            self.polygon_input
        )

        polygon_layout.addWidget(
            self.browse_button
        )

        source_layout.addRow(
            self.text("polygon_file_label"),
            polygon_widget,
        )

        source_group.setVisible(False)

        main_layout.addWidget(
            source_group
        )

        # -------------------------------------------------
        # Start button
        # -------------------------------------------------

        button_widget = QWidget()

        button_layout = QHBoxLayout(
            button_widget
        )

        button_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.start_button = QPushButton(
            "Start analysis"
        )

        self.start_button.setMinimumHeight(
            42
        )

        self.start_button.setVisible(False)

        self.cancel_button = QPushButton(
            self.text(
                "cancel"
            )
        )

        self.cancel_button.setMinimumHeight(
            42
        )

        self.cancel_button.setEnabled(False)

        button_layout.addWidget(
            self.start_button,
            1,
        )

        button_layout.addWidget(
            self.cancel_button,
        )

        main_layout.addWidget(
            button_widget
        )

        # -------------------------------------------------
        # Status and log
        # -------------------------------------------------

        self.status_label = QLabel(
            self.text("preparing_analysis")
        )

        self.status_label.setAlignment(
            Qt.AlignLeft
        )

        main_layout.addWidget(
            self.status_label
        )

        self.progress_bar = QProgressBar()

        self.progress_bar.setRange(
            0,
            100,
        )

        self.progress_bar.setValue(0)

        self.progress_bar.setFormat(
            "%p%"
        )

        main_layout.addWidget(
            self.progress_bar
        )

        self.progress_step_label = QLabel(
            self.text("preparing_analysis")
        )

        self.progress_step_label.setWordWrap(
            True
        )

        main_layout.addWidget(
            self.progress_step_label
        )

        main_layout.addWidget(
            self.progress_bar
        )

        self.details_button = QPushButton(
            self.text(
                "show_details"
            )
        )

        self.details_button.setCheckable(True)
        self.details_button.setChecked(False)

        button_layout.insertWidget(
            0,
            self.details_button,
            1,
        )

        main_layout.addWidget(
            button_widget
        )

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setVisible(False)

        self.log_output.setPlaceholderText(
            self.text(
                "analysis_messages_placeholder"
            )
        )

        main_layout.addWidget(
            self.log_output,
            1,
        )

    def connect_signals(self):
        """
        Connect interface controls to their actions.
        """

        self.details_button.toggled.connect(
            self.toggle_details
        )

        self.country_combo.currentIndexChanged.connect(
            self.update_country
        )

        self.estate_radio.toggled.connect(
            self.update_source_controls
        )

        self.browse_button.clicked.connect(
            self.select_polygon
        )

        self.start_button.clicked.connect(
            self.start_analysis
        )

        self.cancel_button.clicked.connect(
            self.cancel_analysis
        )

    def update_country(self):
        """
        Update the estate example when the country changes.
        """

        country_code = (
            self.country_combo.currentData()
        )

        if country_code == "FI":
            self.estate_input.setPlaceholderText(
                "Example: 434-415-1-226"
            )

        else:
            self.estate_input.setPlaceholderText(
                "Example: KÄVLINGE ÅLSTORP 19:63"
            )

    def update_source_controls(self):
        """
        Enable controls belonging to the selected source.
        """

        estate_selected = (
            self.estate_radio.isChecked()
        )

        self.estate_input.setEnabled(
            estate_selected
        )

        self.polygon_input.setEnabled(
            not estate_selected
        )

        self.browse_button.setEnabled(
            not estate_selected
        )

    def select_polygon(self):
        """
        Let the user select a local polygon dataset.
        """

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.text("select_custom_polygon"),
            os.path.expanduser("~"),
            (
                "Vector data "
                "(*.gpkg *.shp *.geojson);;"
                "All files (*.*)"
            ),
        )

        if file_path:
            self.polygon_input.setText(
                file_path
            )

    def toggle_details(
        self,
        visible,
    ):
        """
        Show or hide the detailed backend output.
        """

        self.log_output.setVisible(
            visible
        )

        if visible:
            self.details_button.setText(
                self.text(
                    "hide_details"
                )
            )

            self.resize(
                720,
                500,
            )

        else:
            self.details_button.setText(
                self.text(
                    "show_details"
                )
            )

            self.resize(
                560,
                170,
            )

    def start_analysis(self):
        """
        Validate the selected configuration and launch the
        existing analysis through run_qgis.bat.
        """

        if (
            self.process is not None
            and self.process.state()
            != QProcess.NotRunning
        ):
            QMessageBox.information(
                self,
                self.text(
                    "analysis_already_running"
                ),
                self.text(
                    "analysis_already_running_message"
                ),
            )

            return

        country_code = (
            self.country_combo.currentData()
        )

        if self.estate_radio.isChecked():
            source_type = "estate"

            source_value = (
                self.estate_input.text().strip()
            )

            if not source_value:
                QMessageBox.warning(
                    self,
                    self.text("missing_polygon"),
                    self.text(
                        "select_custom_polygon_file"
                    ),
                )

                return

        else:
            source_type = "custom_polygon"

            source_value = (
                self.polygon_input.text().strip()
            )

            if not source_value:
                QMessageBox.warning(
                    self,
                    self.text("missing_polygon"),
                    self.text(
                        "select_custom_polygon_file"
                    ),
                )

                return

            polygon_file = source_value.split(
                "|",
                1,
            )[0]

            if not os.path.isfile(polygon_file):
                QMessageBox.warning(
                    self,
                    self.text("polygon_not_found"),
                    self.text(
                        "polygon_not_found_message",
                        path=polygon_file,
                    ),
                )

                return

        project_root = os.path.dirname(
            os.path.abspath(__file__)
        )

        launcher_path = os.path.join(
            project_root,
            "run_qgis.bat",
        )

        if not os.path.isfile(launcher_path):
            QMessageBox.critical(
                self,
                self.text("launcher_missing"),
                self.text(
                    "launcher_missing_message",
                    path=launcher_path,
                ),
            )

            return

        self.cancel_requested = False
        self.log_output.clear()

        self.log_output.append(
            "Starting Sites analysis..."
        )

        self.log_output.append(
            f"Country: {country_code}"
        )

        self.log_output.append(
            f"Source type: {source_type}"
        )

        self.log_output.append(
            f"Source: {source_value}"
        )

        self.log_output.append("")
        self.status_label.setText(
            "Starting analysis…"
        )

        self.progress_output_buffer = ""

        self.progress_bar.setRange(
            0,
            100,
        )

        self.progress_bar.setValue(1)

        self.progress_bar.setFormat(
            "%p% — Starting analysis"
        )

        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

        environment = (
            QProcessEnvironment.systemEnvironment()
        )

        environment.insert(
            "SITES_COUNTRY_CODE",
            country_code,
        )

        environment.insert(
            "SITES_LANGUAGE",
            self.language_code,
        )

        if source_type == "estate":
            environment.insert(
                "SITES_ESTATE",
                source_value,
            )

            environment.insert(
                "SITES_CUSTOM_POLYGON",
                "",
            )

        else:
            environment.insert(
                "SITES_ESTATE",
                "",
            )

            environment.insert(
                "SITES_CUSTOM_POLYGON",
                source_value,
            )

        environment.insert(
            "PYTHONIOENCODING",
            "utf-8",
        )

        environment.insert(
            "PYTHONUTF8",
            "1",
        )

        self.process = QProcess(
            self
        )

        self.process.setWorkingDirectory(
            project_root
        )

        self.process.setProcessEnvironment(
            environment
        )

        self.process.setProcessChannelMode(
            QProcess.MergedChannels
        )

        self.process.readyReadStandardOutput.connect(
            self.read_process_output
        )

        self.process.started.connect(
            self.analysis_started
        )

        self.process.finished.connect(
            self.analysis_finished
        )

        self.process.errorOccurred.connect(
            self.analysis_error
        )

        self.process.start(
            "cmd.exe",
            [
                "/d",
                "/c",
                launcher_path,
            ],
        )

    def read_process_output(self):
        """
        Copy newly available analysis output into the log box.
        """

        if self.process is None:
            return

        raw_output = (
            self.process.readAllStandardOutput()
        )

        output = bytes(
            raw_output
        ).decode(
            "utf-8",
            errors="replace",
        )

        if not output:
            return

        self.update_progress_from_output(
            output
        )

        self.log_output.insertPlainText(
            output
        )

        scroll_bar = (
            self.log_output.verticalScrollBar()
        )

        scroll_bar.setValue(
            scroll_bar.maximum()
        )

    def set_progress(
        self,
        percentage,
        message,
    ):
        """
        Advance the progress bar without allowing it to move
        backwards.
        """

        percentage = max(
            0,
            min(
                100,
                int(percentage),
            ),
        )

        if percentage > self.progress_bar.value():
            self.progress_bar.setValue(
                percentage
            )

        self.progress_bar.setFormat(
            "%p%"
        )

        self.progress_step_label.setText(
            message
        )

    def update_progress_from_output(
        self,
        output,
    ):
        """
        Convert existing backend messages into progress stages.

        Output can arrive in incomplete pieces, so unfinished lines
        are retained until the next piece arrives.
        """

        self.progress_output_buffer += (
            output.replace(
                "\r",
                "\n",
            )
        )

        lines = (
            self.progress_output_buffer
            .split("\n")
        )

        self.progress_output_buffer = (
            lines.pop()
        )

        for line in lines:
            self.update_progress_from_line(
                line.strip()
            )

    def update_progress_from_line(
        self,
        line,
    ):
        """
        Update progress from one complete backend output line.
        """

        if not line:
            return

        run_id_match = re.match(
            r"Analysis run ID:\s*(\S+)",
            line,
        )

        if run_id_match:
            self.analysis_run_id = (
                run_id_match.group(1)
            )

        large_area_match = re.match(
            r"LARGE_ANALYSIS_AREA_WARNING:"
            r"(\d+(?:\.\d+)?)",
            line,
        )

        if (
            large_area_match
            and not self.large_area_warning_shown
        ):
            self.large_area_warning_shown = True

            area_ha = float(
                large_area_match.group(1)
            )

            self.progress_step_label.setText(
                "Preparing a large analysis area"
            )

            QTimer.singleShot(
                0,
                lambda area=area_ha: (
                    QMessageBox.warning(
                        self,
                        self.text(
                            "large_analysis_area"
                        ),
                        self.text(
                            "large_analysis_area_message",
                            area=f"{area:,.2f}",
                        ),
                    )
                ),
            )

            return

        neighbour_match = re.search(
            r"Neighbouring estate reprojected "
            r"\((\d+)/(\d+)\)",
            line,
        )

        if neighbour_match:
            current = int(
                neighbour_match.group(1)
            )

            total = int(
                neighbour_match.group(2)
            )

            percentage = (
                22
                + round(
                    current
                    / total
                    * 8
                )
            )

            self.set_progress(
                percentage,
                (
                    "Preparing neighbouring estates "
                    f"({current} of {total})"
                ),
            )

            return

        country_layer_match = re.search(
            r"Downloading country layer "
            r"(\d+)/(\d+)",
            line,
        )

        if country_layer_match:
            current = int(
                country_layer_match.group(1)
            )

            total = int(
                country_layer_match.group(2)
            )

            percentage = (
                47
                + round(
                    current
                    / total
                    * 21
                )
            )

            self.set_progress(
                percentage,
                (
                    "Downloading local constraint data "
                    f"({current} of {total})"
                ),
            )

            return

        checkpoints = (
            (
                "Analysis run ID:",
                2,
                "Creating analysis workspace",
            ),
            (
                "Country configuration loaded:",
                4,
                "Loading country-specific settings",
            ),
            (
                "Starting solar site analysis...",
                5,
                "Starting the GIS analysis engine",
            ),
            (
                "QGIS Processing is ready.",
                6,
                "GIS processing tools are ready",
            ),
            (
                "Searching for estate:",
                8,
                "Searching the cadastral database",
            ),
            (
                "PostGIS returned",
                10,
                "Estate geometry found",
            ),
            (
                "Estate downloaded from PostGIS:",
                12,
                "Downloading estate geometry",
            ),
            (
                "Estate features merged:",
                13,
                "Merging estate parts",
            ),
            (
                "Estate features dissolved:",
                14,
                "Dissolving estate boundaries",
            ),
            (
                "Estate converted to singleparts:",
                15,
                "Separating estate polygons",
            ),
            (
                "Working CRS selected automatically:",
                16,
                "Selecting the local coordinate system",
            ),
            (
                "Estate reprojected to",
                17,
                "Reprojecting the analysis site",
            ),
            (
                "Estate saved with area",
                18,
                "Calculating the analysis-site area",
            ),
            (
                "Estate buffer created (100m)",
                19,
                "Creating the local site buffer",
            ),
            (
                "Estate buffer created (5km)",
                20,
                "Creating the surrounding context area",
            ),
            (
                "Red-listed species search context:",
                20,
                "Preparing the species-observation search",
            ),
            (
                "Downloading red-listed observations",
                21,
                "Downloading red-listed species observations",
            ),
            (
                "Red-listed species observations saved:",
                22,
                "Saving nearby species observations",
            ),
            (
                "Final neighbouring estates saved:",
                30,
                "Neighbouring-estate processing completed",
            ),
            (
                "Requesting indexed DEM tiles",
                31,
                "Finding elevation tiles",
            ),
            (
                "PostGIS DEM downloaded:",
                33,
                "Downloading elevation data",
            ),
            (
                "DEM clipped",
                35,
                "Clipping elevation data to the site",
            ),
            (
                "Terrain grid created:",
                37,
                "Creating the terrain-processing grid",
            ),
            (
                "DEM clipped to grid feature",
                39,
                "Dividing elevation data into terrain cells",
            ),
            (
                "Slope and aspect calculated",
                42,
                "Calculating terrain slope and direction",
            ),
            (
                "Total ineligible-terrain point layers:",
                44,
                "Identifying unsuitable terrain",
            ),
            (
                "Contour lines saved:",
                46,
                "Creating elevation contour lines",
            ),
            (
                "Centroid representation created:",
                70,
                "Preparing local constraint representations",
            ),
            (
                "Site summary saved:",
                73,
                "Writing the site summary",
            ),
            (
                "Soil-depth summary appended:",
                75,
                "Adding soil-depth results",
            ),
            (
                "Project-potential summary appended:",
                77,
                "Calculating renewable-energy potential",
            ),
            (
                "Grid-proximity summary appended:",
                78,
                "Calculating electrical-grid proximity",
            ),
            (
                "Reading Global Solar Atlas data from PostGIS",
                79,
                "Reading solar-resource data",
            ),
            (
                "Solar-resource summary appended:",
                81,
                "Adding solar-resource results",
            ),
            (
                "Solar-position summary appended:",
                82,
                "Calculating solar position",
            ),
            (
                "Average wind speed at",
                83,
                "Calculating average wind speed",
            ),
            (
                "Meteorological summary appended:",
                86,
                "Adding meteorological results",
            ),
            (
                "Municipality political summary appended:",
                88,
                "Adding municipality information",
            ),
            (
                "BoS analysis enabled",
                89,
                "Starting balance-of-system analysis",
            ),
            (
                "PostGIS BoS land-cover raster downloaded:",
                90,
                "Downloading land-cover data",
            ),
            (
                "BoS base land-cover prepared:",
                91,
                "Classifying land-cover areas",
            ),
            (
                "BoS wetland coverage prepared:",
                92,
                "Calculating wetland coverage",
            ),
            (
                "GeoPackage layer written:",
                93,
                "Packaging analysis layers",
            ),
            (
                "GeoPackage created:",
                96,
                "Analysis package completed",
            ),
            (
                "QGIS project saved:",
                97,
                "Saving the QGIS project",
            ),
            (
                "Analysis manifest",
                98,
                "Creating the analysis manifest",
            ),
        )

        for (
            marker,
            percentage,
            message,
        ) in checkpoints:
            if marker in line:
                self.set_progress(
                    percentage,
                    message,
                )

                return

    def analysis_started(self):
        """
        Update the interface after the process starts.
        """

        self.status_label.setText(
            self.text(
                "analysis_running"
            )
        )

    def analysis_finished(
        self,
        exit_code,
        exit_status,
    ):
        """
        Finalise the progress window when analysis ends.
        """

        self.read_process_output()

        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

        self.progress_bar.setRange(
            0,
            100,
        )

        self.process = None

        if self.cancel_requested:
            self.status_label.setText(
                self.text(
                    "analysis_cancelled"
                )
            )

            self.progress_step_label.setText(
                self.text(
                    "removing_incomplete_files"
                )
            )

            self.log_output.append(
                "\nAnalysis was cancelled."
            )

            self.progress_bar.setValue(0)
            self.progress_bar.setFormat(
                "%p%"
            )

            QTimer.singleShot(
                500,
                self.remove_cancelled_analysis,
            )

            return

        if exit_code == 0:
            self.status_label.setText(
                self.text(
                    "analysis_completed"
                )
            )

            self.progress_step_label.setText(
                self.text(
                    "opening_completed_project"
                )
            )

            self.log_output.append(
                "\nAnalysis completed successfully."
            )

            self.progress_bar.setValue(100)
            self.progress_bar.setFormat(
                "%p%"
            )

            QTimer.singleShot(
                250,
                self.close,
            )

            return

        self.status_label.setText(
            self.text(
                "analysis_failed"
            )
        )

        self.progress_step_label.setText(
            self.text(
                "analysis_stopped_exit_code",
                exit_code=exit_code,
            )
        )

        self.log_output.append(
            "\nAnalysis stopped with "
            f"exit code {exit_code}."
        )

        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(
            "%p%"
        )

        self.details_button.setChecked(
            True
        )

    def analysis_error(
        self,
        process_error,
    ):
        """
        Report a failure to launch or control the process.
        """

        self.progress_bar.setRange(
            0,
            100,
        )

        self.progress_bar.setValue(0)

        self.progress_bar.setFormat(
            self.text("process_error")
        )

        self.details_button.setChecked(
            True
        )

        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

        self.status_label.setText(
            self.text("process_error")
        )

        self.log_output.append(
            "\n"
            + self.text(
                "process_error_message",
                error=process_error,
            )
        )

    def remove_cancelled_analysis(
        self,
        attempts_remaining=6,
    ):
        """
        Remove only the incomplete output folder belonging to
        the analysis that was just cancelled.
        """

        if not self.analysis_run_id:
            self.close()
            return

        local_app_data = os.environ.get(
            "LOCALAPPDATA"
        )

        if not local_app_data:
            self.close()
            return

        projects_root = (
            Path(local_app_data)
            / "Sites"
            / "Projects"
        )

        if not projects_root.is_dir():
            self.close()
            return

        run_folder = None

        for project_folder in projects_root.iterdir():
            if not project_folder.is_dir():
                continue

            candidate = (
                project_folder
                / self.analysis_run_id
            )

            if candidate.is_dir():
                run_folder = candidate
                break

        if run_folder is None:
            self.close()
            return

        try:
            shutil.rmtree(
                run_folder
            )

            project_folder = run_folder.parent

            if (
                project_folder != projects_root
                and project_folder.is_dir()
                and not any(project_folder.iterdir())
            ):
                project_folder.rmdir()

        except OSError as error:
            if attempts_remaining > 1:
                QTimer.singleShot(
                    500,
                    lambda: (
                        self.remove_cancelled_analysis(
                            attempts_remaining - 1
                        )
                    ),
                )

                return

            QMessageBox.warning(
                self,
                self.text("cleanup_incomplete"),
                self.text(
                    "cleanup_incomplete_message",
                    path=run_folder,
                    error=error,
                ),
            )

        self.close()

    def cancel_analysis(self):
        """
        Stop the running analysis and its child processes.
        """

        if (
            self.process is None
            or self.process.state()
            == QProcess.NotRunning
        ):
            return

        answer = QMessageBox.question(
            self,
            self.text("cancel_analysis"),
            self.text(
                "cancel_analysis_message"
            ),
            QMessageBox.Yes
            | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        self.cancel_requested = True

        process_id = int(
            self.process.processId()
        )

        self.status_label.setText(
            self.text(
                "cancelling_analysis"
            )
        )

        self.progress_step_label.setText(
            self.text(
                "stopping_analysis_processes"
            )
        )

        QProcess.startDetached(
            "taskkill.exe",
            [
                "/PID",
                str(process_id),
                "/T",
                "/F",
            ],
        )


def main():
    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "Sovra"
    )

    window = SitesWindow()
    window.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(
        main()
    )