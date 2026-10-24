import os
import re
import sys

from qgis.PyQt.QtCore import (
    Qt,
    QProcess,
    QProcessEnvironment,
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

    def __init__(self):
        super().__init__()

        self.process = None
        self.cancel_requested = False
        self.progress_output_buffer = ""

        self.setWindowTitle(
            "Sites — Renewable Energy Site Analysis"
        )

        self.resize(
            800,
            340,
        )

        self.create_interface()
        self.connect_signals()
        self.update_source_controls()

    def create_interface(self):
        """
        Create and arrange the user-interface controls.
        """

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(
            central_widget
        )

        # -------------------------------------------------
        # Heading
        # -------------------------------------------------

        heading = QLabel(
            "Sites"
        )

        heading_font = heading.font()
        heading_font.setPointSize(20)
        heading_font.setBold(True)
        heading.setFont(heading_font)

        subtitle = QLabel(
            "Renewable energy site analysis"
        )

        main_layout.addWidget(heading)
        main_layout.addWidget(subtitle)

        # -------------------------------------------------
        # Analysis source
        # -------------------------------------------------

        source_group = QGroupBox(
            "Analysis source"
        )

        source_layout = QFormLayout(
            source_group
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

        source_layout.addRow(
            "Country:",
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
            "Estate identifier"
        )

        self.polygon_radio = QRadioButton(
            "Custom polygon"
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
            "Source type:",
            source_type_widget,
        )

        self.estate_input = QLineEdit()

        self.estate_input.setPlaceholderText(
            "Example: KÄVLINGE ÅLSTORP 19:63"
        )

        source_layout.addRow(
            "Estate:",
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
            "Browse…"
        )

        polygon_layout.addWidget(
            self.polygon_input
        )

        polygon_layout.addWidget(
            self.browse_button
        )

        source_layout.addRow(
            "Polygon file:",
            polygon_widget,
        )

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

        self.cancel_button = QPushButton(
            "Cancel"
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
            "Ready"
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
        self.progress_bar.setFormat("Ready")

        main_layout.addWidget(
            self.progress_bar
        )

        self.details_button = QPushButton(
            "Show more details"
        )

        self.details_button.setCheckable(True)
        self.details_button.setChecked(False)

        main_layout.addWidget(
            self.details_button
        )

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setVisible(False)

        self.log_output.setPlaceholderText(
            "Analysis messages will appear here."
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
            "Select custom polygon",
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
                "Hide details"
            )

            self.resize(
                max(self.width(), 800),
                600,
            )

        else:
            self.details_button.setText(
                "Show more details"
            )

            self.resize(
                max(self.width(), 800),
                340,
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
                "Analysis already running",
                "An analysis is already running.",
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
                    "Missing estate",
                    "Enter an estate identifier.",
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
                    "Missing polygon",
                    "Select a custom polygon file.",
                )

                return

            if not os.path.isfile(source_value):
                QMessageBox.warning(
                    self,
                    "Polygon not found",
                    (
                        "The selected polygon file "
                        "does not exist."
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
                "Launcher missing",
                (
                    "The analysis launcher was not found:\n"
                    f"{launcher_path}"
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
            f"%p% — {message}"
        )

        self.status_label.setText(
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
                18
                + round(
                    current
                    / total
                    * 10
                )
            )

            self.set_progress(
                percentage,
                "Preparing neighbouring estates",
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
                "Downloading local constraint data",
            )

            return

        checkpoints = (
            (
                "Analysis run ID:",
                2,
                "Initialising analysis",
            ),
            (
                "Country configuration loaded:",
                4,
                "Loading country configuration",
            ),
            (
                "QGIS Processing is ready.",
                6,
                "Preparing GIS processing",
            ),
            (
                "Searching for estate:",
                8,
                "Finding estate",
            ),
            (
                "PostGIS returned",
                11,
                "Downloading estate geometry",
            ),
            (
                "Estate saved with area",
                14,
                "Preparing analysis site",
            ),
            (
                "Estate buffer created (5km)",
                17,
                "Creating search area",
            ),
            (
                "Red-listed species observations saved:",
                20,
                "Preparing environmental observations",
            ),
            (
                "Final neighbouring estates saved:",
                28,
                "Neighbouring estates completed",
            ),
            (
                "PostGIS DEM downloaded:",
                32,
                "Downloading terrain data",
            ),
            (
                "DEM clipped",
                35,
                "Clipping terrain data",
            ),
            (
                "Terrain grid created:",
                38,
                "Creating terrain grid",
            ),
            (
                "Total ineligible-terrain point layers:",
                43,
                "Analysing terrain eligibility",
            ),
            (
                "Contour lines saved:",
                46,
                "Terrain analysis completed",
            ),
            (
                "Centroid representation created:",
                70,
                "Preparing local constraint layers",
            ),
            (
                "Site summary saved:",
                74,
                "Creating site summary",
            ),
            (
                "Solar-resource summary appended:",
                79,
                "Solar-resource analysis completed",
            ),
            (
                "Meteorological summary appended:",
                85,
                "Meteorological analysis completed",
            ),
            (
                "Municipality political summary appended:",
                87,
                "Municipality analysis completed",
            ),
            (
                "BoS analysis",
                89,
                "Preparing balance-of-system analysis",
            ),
            (
                "GeoPackage layer written:",
                93,
                "Packaging analysis results",
            ),
            (
                "GeoPackage created:",
                96,
                "GeoPackage completed",
            ),
            (
                "QGIS project saved:",
                97,
                "Saving QGIS project",
            ),
            (
                "Analysis manifest",
                98,
                "Creating analysis manifest",
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
            "Analysis running…"
        )

    def analysis_finished(
        self,
        exit_code,
        exit_status,
    ):
        """
        Restore the interface when analysis ends.
        """

        self.read_process_output()

        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

        self.progress_bar.setRange(
            0,
            100,
        )

        if self.cancel_requested:
            self.status_label.setText(
                "Analysis cancelled"
            )

            self.log_output.append(
                "\nAnalysis was cancelled."
            )

            self.progress_bar.setValue(0)
            self.progress_bar.setFormat(
                "Cancelled"
            )

        elif exit_code == 0:
            self.status_label.setText(
                "Analysis completed successfully"
            )

            self.log_output.append(
                "\nAnalysis completed successfully."
            )

            self.progress_bar.setValue(100)
            self.progress_bar.setFormat(
                "Completed"
            )

        else:
            self.status_label.setText(
                "Analysis failed"
            )

            self.log_output.append(
                "\nAnalysis stopped with "
                f"exit code {exit_code}."
            )

            self.progress_bar.setValue(0)
            self.progress_bar.setFormat(
                "Failed"
            )

            self.details_button.setChecked(
                True
            )

        self.process = None

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
            "Process error"
        )

        self.details_button.setChecked(
            True
        )

        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

        self.status_label.setText(
            "Process error"
        )

        self.log_output.append(
            "\nProcess error: "
            f"{process_error}"
        )

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
            "Cancel analysis",
            (
                "Stop the running analysis?\n\n"
                "The current output folder may remain "
                "in an incomplete state."
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
            "Cancelling analysis…"
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
        "Sites"
    )

    window = SitesWindow()
    window.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(
        main()
    )