from scripts.translations import (
    translated_layer_name,
)
from qgis.PyQt.QtCore import (
    QSettings,
    Qt,
)
from qgis.PyQt.QtGui import (
    QColor,
)
from qgis.PyQt.QtWidgets import (
    QComboBox,
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)
from scripts.country_config import (
    load_country_config,
)
from scripts.layer_metadata import (
    fetch_layer_metadata,
)

TEXT = {
    "en": {
        "title": "Options",
        "general": "General",
        "layers": "Layer settings",
        "language": "Language:",
        "restart_note": (
            "Language changes take effect after restarting Sovra."
        ),
        "layers_note": (
            "Country-layer buffers and constraint treatment "
            "will be configured here."
        ),
    },
    "sv": {
        "title": "Inställningar",
        "general": "Allmänt",
        "layers": "Lagerinställningar",
        "language": "Språk:",
        "restart_note": (
            "Språkändringar träder i kraft efter att Sovra "
            "har startats om."
        ),
        "layers_note": (
            "Buffertavstånd och hantering av landslager "
            "kommer att konfigureras här."
        ),
    },
    "fi": {
        "title": "Asetukset",
        "general": "Yleiset",
        "layers": "Tasojen asetukset",
        "language": "Kieli:",
        "restart_note": (
            "Kielimuutokset tulevat voimaan, kun Sovra "
            "käynnistetään uudelleen."
        ),
        "layers_note": (
            "Maakohtaisten tasojen puskurit ja käsittely "
            "määritetään täällä."
        ),
    },
}


def option_text(
    language,
    key,
):
    """
    Return translated Options-dialog text.
    """

    language = str(
        language
    ).strip().lower()

    language_text = TEXT.get(
        language,
        TEXT["en"],
    )

    return language_text.get(
        key,
        TEXT["en"].get(key, key),
    )


class OptionsDialog(QDialog):
    """
    Global Sovra application settings.
    """

    def __init__(
        self,
        current_language="en",
        current_country="SE",
        parent=None,
    ):
        super().__init__(
            parent
        )

        self.current_language = (
            str(current_language)
            .strip()
            .lower()
        )

        if self.current_language not in {
            "en",
            "sv",
            "fi",
        }:
            self.current_language = "en"

        self.current_country = (
            str(current_country)
            .strip()
            .upper()
        )

        if self.current_country not in {
            "SE",
            "FI",
        }:
            self.current_country = "SE"

        self.layer_country_code = (
            self.current_country
        )

        self.settings = QSettings(
            "Sovra",
            "Sovra",
        )

        self.layer_rows = {}

        self.setWindowTitle(
            option_text(
                self.current_language,
                "title",
            )
        )

        self.setMinimumSize(
            620,
            420,
        )

        self.create_interface()

    def create_interface(self):
        main_layout = QVBoxLayout(
            self
        )

        self.tabs = QTabWidget()

        # -------------------------------------------------
        # General settings
        # -------------------------------------------------

        general_tab = QWidget()

        general_layout = QFormLayout(
            general_tab
        )

        self.language_combo = QComboBox()

        self.language_combo.addItem(
            "English",
            "en",
        )

        self.language_combo.addItem(
            "Svenska",
            "sv",
        )

        self.language_combo.addItem(
            "Suomi",
            "fi",
        )

        current_index = (
            self.language_combo.findData(
                self.current_language
            )
        )

        self.language_combo.setCurrentIndex(
            current_index
        )

        general_layout.addRow(
            option_text(
                self.current_language,
                "language",
            ),
            self.language_combo,
        )

        restart_note = QLabel(
            option_text(
                self.current_language,
                "restart_note",
            )
        )

        restart_note.setWordWrap(
            True
        )

        general_layout.addRow(
            restart_note
        )

        self.tabs.addTab(
            general_tab,
            option_text(
                self.current_language,
                "general",
            ),
        )

        # -------------------------------------------------
        # Country-layer settings
        # -------------------------------------------------

        layer_tab = QWidget()

        layer_layout = QVBoxLayout(
            layer_tab
        )

        layer_note = QLabel(
            option_text(
                self.current_language,
                "layers_note",
            )
        )

        layer_note.setWordWrap(
            True
        )

        layer_layout.addWidget(
            layer_note
        )

        self.layer_country_combo = QComboBox()

        self.layer_country_combo.addItem(
            "Sweden",
            "SE",
        )

        self.layer_country_combo.addItem(
            "Finland",
            "FI",
        )

        country_index = (
            self.layer_country_combo.findData(
                self.current_country
            )
        )

        self.layer_country_combo.setCurrentIndex(
            country_index
        )

        layer_layout.addWidget(
            self.layer_country_combo
        )

        self.layer_table = QTableWidget()

        self.layer_table.setColumnCount(
            6
        )

        self.layer_table.setHorizontalHeaderLabels(
            [
                "ⓘ",
                "Layer",
                "Solar distance",
                "Wind distance",
                "Colour",
                "Treatment",
            ]
        )

        self.layer_table.verticalHeader().setVisible(
            False
        )

        self.layer_table.setAlternatingRowColors(
            True
        )

        self.layer_table.setColumnWidth(
            0,
            38,
        )

        self.layer_table.setColumnWidth(
            2,
            125,
        )

        self.layer_table.setColumnWidth(
            3,
            125,
        )

        self.layer_table.setColumnWidth(
            4,
            90,
        )

        self.layer_table.setColumnWidth(
            5,
            145,
        )

        self.layer_table.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.Stretch,
        )

        layer_layout.addWidget(
            self.layer_table,
            1,
        )

        self.tabs.addTab(
            layer_tab,
            option_text(
                self.current_language,
                "layers",
            ),
        )

        self.layer_country_combo.currentIndexChanged.connect(
            self.change_layer_country
        )

        self.populate_layer_table()

        main_layout.addWidget(
            self.tabs
        )

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok
            | QDialogButtonBox.Cancel
        )

        self.button_box.accepted.connect(
            self.accept
        )

        self.button_box.rejected.connect(
            self.reject
        )

        main_layout.addWidget(
            self.button_box
        )

    def layer_settings_prefix(
        self,
        country_code,
        layer_definition,
    ):
        """
        Return the stable QSettings path for one layer.

        Display names are deliberately excluded because they
        may change when the application language changes.
        """

        database = layer_definition[
            "database"
        ]

        return (
            "layers/"
            f"{country_code}/"
            f"{database['schema']}/"
            f"{database['table']}"
        )

    def stored_number(
        self,
        key,
        default_value,
    ):
        """
        Safely read a numeric value from QSettings.
        """

        value = self.settings.value(
            key,
            default_value,
        )

        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default_value)

    def create_distance_control(
        self,
        value,
    ):
        """
        Create one distance input measured in metres.
        """

        control = QDoubleSpinBox()

        control.setRange(
            0,
            1000000,
        )

        control.setDecimals(
            1
        )

        control.setSingleStep(
            5
        )

        control.setSuffix(
            " m"
        )

        control.setValue(
            float(value)
        )

        return control

    def set_colour_button(
        self,
        button,
        colour,
    ):
        """
        Store and display the selected layer colour.
        """

        normalised_colour = QColor(
            colour
        )

        if not normalised_colour.isValid():
            normalised_colour = QColor(
                "#d64545"
            )

        button.setProperty(
            "layer_colour",
            normalised_colour.name(),
        )

        button.setText(
            normalised_colour.name().upper()
        )

        button.setStyleSheet(
            "QPushButton {"
            f"background-color: {normalised_colour.name()};"
            "color: white;"
            "font-weight: bold;"
            "}"
        )

    def choose_layer_colour(
        self,
        button,
    ):
        """
        Open the colour picker for one layer row.
        """

        current_colour = QColor(
            button.property(
                "layer_colour"
            )
            or "#d64545"
        )

        selected_colour = QColorDialog.getColor(
            current_colour,
            self,
            "Select layer colour",
        )

        if not selected_colour.isValid():
            return

        self.set_colour_button(
            button,
            selected_colour,
        )

    def display_metadata_date(
        self,
        value,
    ):
        """
        Format a catalogue timestamp for a tooltip.
        """

        if value is None:
            return "Not recorded"

        try:
            return value.astimezone().strftime(
                "%Y-%m-%d %H:%M"
            )
        except (AttributeError, ValueError):
            return str(value)

    def layer_information_tooltip(
        self,
        layer_definition,
        metadata=None,
        metadata_error=None,
    ):
        """
        Build the information tooltip for one country layer.
        """

        database = layer_definition[
            "database"
        ]

        display_name = translated_layer_name(
            definition=layer_definition,
            language=self.current_language,
        )

        lines = [
            display_name,
            "",
            (
                "Source file: "
                f"{layer_definition['source']}"
            ),
            (
                "Database layer: "
                f"{database['schema']}."
                f"{database['table']}"
            ),
            (
                "Geometry column: "
                f"{database['geometry_column']}"
            ),
            (
                "CRS: "
                f"EPSG:{database['srid']}"
            ),
        ]

        if metadata is None:
            lines.extend(
                [
                    "",
                    (
                        metadata_error
                        or (
                            "No catalogue entry was found "
                            "for this layer."
                        )
                    ),
                ]
            )

            return "\n".join(lines)

        lines.extend(
            [
                "",
                (
                    "Dataset: "
                    f"{metadata.get('dataset_name') or 'Not recorded'}"
                ),
                (
                    "Provider: "
                    f"{metadata.get('provider') or 'Not recorded'}"
                ),
                (
                    "Source updated: "
                    f"{self.display_metadata_date(metadata.get('source_updated_at'))}"
                ),
                (
                    "Migrated to Sovra: "
                    f"{self.display_metadata_date(metadata.get('migrated_at'))}"
                ),
                (
                    "Records: "
                    f"{metadata.get('record_count') if metadata.get('record_count') is not None else 'Not recorded'}"
                ),
                (
                    "Geometry: "
                    f"{metadata.get('geometry_type') or 'Not recorded'}"
                ),
                (
                    "Migration status: "
                    f"{metadata.get('migration_status') or 'Not recorded'}"
                ),
            ]
        )

        source_url = metadata.get(
            "source_url"
        )

        if source_url:
            lines.extend(
                [
                    "",
                    f"Source URL: {source_url}",
                ]
            )

        return "\n".join(lines)

    def populate_layer_table(self):
        """
        Populate the table using the selected country's
        configured layers.
        """

        country_code = (
            self.layer_country_combo.currentData()
        )

        country_config = load_country_config(
            country_code
        )

        layer_definitions = (
            country_config.LAYERS
        )

        style_resolver = getattr(
            country_config,
            "get_map_style",
            None,
        )

        (
            metadata_by_layer,
            metadata_error,
        ) = fetch_layer_metadata(
            country_code
        )

        self.layer_country_code = (
            country_code
        )

        self.layer_rows = {}

        self.layer_table.setRowCount(
            len(layer_definitions)
        )

        for row, layer_definition in enumerate(
            layer_definitions
        ):
            display_name = translated_layer_name(
                definition=layer_definition,
                language=self.current_language,
            )

            prefix = self.layer_settings_prefix(
                country_code,
                layer_definition,
            )

            info_label = QLabel(
                "ⓘ"
            )

            info_label.setAlignment(
                Qt.AlignCenter
            )

            database = layer_definition[
                "database"
            ]

            layer_metadata = (
                metadata_by_layer.get(
                    (
                        database["schema"],
                        database["table"],
                    )
                )
            )

            info_label.setToolTip(
                self.layer_information_tooltip(
                    layer_definition=layer_definition,
                    metadata=layer_metadata,
                    metadata_error=metadata_error,
                )
            )

            info_label.setCursor(
                Qt.WhatsThisCursor
            )

            self.layer_table.setCellWidget(
                row,
                0,
                info_label,
            )

            name_label = QLabel(
                display_name
            )

            self.layer_table.setCellWidget(
                row,
                1,
                name_label,
            )

            solar_control = (
                self.create_distance_control(
                    self.stored_number(
                        (
                            f"{prefix}/"
                            "solar_buffer_m"
                        ),
                        layer_definition[
                            "solar_buffer_m"
                        ],
                    )
                )
            )

            self.layer_table.setCellWidget(
                row,
                2,
                solar_control,
            )

            wind_control = (
                self.create_distance_control(
                    self.stored_number(
                        (
                            f"{prefix}/"
                            "wind_buffer_m"
                        ),
                        layer_definition[
                            "wind_buffer_m"
                        ],
                    )
                )
            )

            self.layer_table.setCellWidget(
                row,
                3,
                wind_control,
            )

            colour_button = QPushButton()

            default_style = (
                style_resolver(layer_definition)
                if style_resolver is not None
                else {}
            )

            default_colour = default_style.get(
                "color",
                "#d27800",
            )

            stored_colour = self.settings.value(
                f"{prefix}/colour",
                default_colour,
            )

            self.set_colour_button(
                colour_button,
                stored_colour,
            )

            colour_button.clicked.connect(
                lambda checked=False,
                button=colour_button: (
                    self.choose_layer_colour(
                        button
                    )
                )
            )

            self.layer_table.setCellWidget(
                row,
                4,
                colour_button,
            )

            treatment_combo = QComboBox()

            treatment_combo.addItem(
                "Hard constraint",
                "hard",
            )

            treatment_combo.addItem(
                "Indicator",
                "indicator",
            )

            stored_treatment = (
                self.settings.value(
                    f"{prefix}/treatment",
                    "hard",
                )
            )

            treatment_index = (
                treatment_combo.findData(
                    stored_treatment
                )
            )

            if treatment_index < 0:
                treatment_index = 0

            treatment_combo.setCurrentIndex(
                treatment_index
            )

            self.layer_table.setCellWidget(
                row,
                5,
                treatment_combo,
            )

            self.layer_rows[
                prefix
            ] = {
                "definition": layer_definition,
                "solar": solar_control,
                "wind": wind_control,
                "colour": colour_button,
                "treatment": treatment_combo,
            }

    def save_visible_layer_settings(self):
        """
        Save all rows currently displayed in the table.
        """

        for prefix, controls in (
            self.layer_rows.items()
        ):
            self.settings.setValue(
                f"{prefix}/solar_buffer_m",
                controls["solar"].value(),
            )

            self.settings.setValue(
                f"{prefix}/wind_buffer_m",
                controls["wind"].value(),
            )

            self.settings.setValue(
                f"{prefix}/colour",
                controls["colour"].property(
                    "layer_colour"
                ),
            )

            self.settings.setValue(
                f"{prefix}/treatment",
                controls["treatment"].currentData(),
            )

        self.settings.sync()

    def change_layer_country(self):
        """
        Preserve the visible country before loading another.
        """

        self.save_visible_layer_settings()
        self.populate_layer_table()

    def accept(self):
        """
        Save Options values before closing the dialog.
        """

        self.save_visible_layer_settings()

        super().accept()

    def selected_language(self):
        """
        Return the chosen ISO language code.
        """

        return self.language_combo.currentData()