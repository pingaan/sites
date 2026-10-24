from datetime import datetime
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
            "select_layer_colour": "Select layer colour",
        "source_file": "Source file",
        "database_layer": "Database layer",
        "geometry_column": "Geometry column",
        "crs": "CRS",
        "dataset": "Dataset",
        "provider": "Provider",
        "source_updated": "Source updated",
        "migrated_to_sovra": "Migrated to Sovra",
        "last_accessed": "Last accessed",
        "metadata_updated": "Metadata updated",
        "records": "Records",
        "geometry": "Geometry",
        "migration_status": "Migration status",
        "source_url": "Source URL",
        "not_recorded": "Not recorded",
        "no_catalogue_entry": (
            "No catalogue entry was found for this layer."
        ),
        "metadata_unavailable": (
            "Layer metadata is currently unavailable."
        ),
        "migration_unknown": "Unknown",
        "migration_running": "Running",
        "migration_success": "Successful",
        "migration_failed": "Failed",
        "country_sweden": "Sweden",
        "country_finland": "Finland",
        "layer": "Layer",
        "solar_distance": "Solar distance",
        "wind_distance": "Wind distance",
        "colour": "Colour",
        "treatment": "Treatment",
        "hard_constraint": "Hard constraint",
        "indicator": "Indicator",
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
        "select_layer_colour": "Välj lagerfärg",
        "source_file": "Källfil",
        "database_layer": "Databaslager",
        "geometry_column": "Geometrikolumn",
        "crs": "Koordinatsystem",
        "dataset": "Datamängd",
        "provider": "Dataleverantör",
        "source_updated": "Källan uppdaterad",
        "migrated_to_sovra": "Migrerad till Sovra",
        "last_accessed": "Senast använd",
        "metadata_updated": "Metadata uppdaterad",
        "records": "Poster",
        "geometry": "Geometri",
        "migration_status": "Migreringsstatus",
        "source_url": "Källans URL",
        "not_recorded": "Inte registrerat",
        "no_catalogue_entry": (
            "Ingen katalogpost hittades för detta lager."
        ),
        "metadata_unavailable": (
            "Lagermetadata är inte tillgänglig just nu."
        ),
        "migration_unknown": "Okänd",
        "migration_running": "Pågår",
        "migration_success": "Lyckades",
        "migration_failed": "Misslyckades",
        "country_sweden": "Sverige",
        "country_finland": "Finland",        
        "layer": "Lager",
        "solar_distance": "Solavstånd",
        "wind_distance": "Vindavstånd",
        "colour": "Färg",
        "treatment": "Hantering",
        "hard_constraint": "Hård begränsning",
        "indicator": "Indikator",
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
        "select_layer_colour": "Valitse tason väri",
        "source_file": "Lähdetiedosto",
        "database_layer": "Tietokantataso",
        "geometry_column": "Geometriasarake",
        "crs": "Koordinaattijärjestelmä",
        "dataset": "Aineisto",
        "provider": "Tietojen tarjoaja",
        "source_updated": "Lähde päivitetty",
        "migrated_to_sovra": "Siirretty Sovraan",
        "last_accessed": "Viimeksi käytetty",
        "metadata_updated": "Metatiedot päivitetty",
        "records": "Tietueet",
        "geometry": "Geometria",
        "migration_status": "Siirron tila",
        "source_url": "Lähteen URL",
        "not_recorded": "Ei tallennettu",
        "no_catalogue_entry": (
            "Tälle tasolle ei löytynyt luettelomerkintää."
        ),
        "metadata_unavailable": (
            "Tason metatiedot eivät ole tällä hetkellä "
            "saatavilla."
        ),
        "migration_unknown": "Tuntematon",
        "migration_running": "Käynnissä",
        "migration_success": "Onnistui",
        "migration_failed": "Epäonnistui",
        "country_sweden": "Ruotsi",
        "country_finland": "Suomi",
        "layer": "Taso",
        "solar_distance": "Aurinkoetäisyys",
        "wind_distance": "Tuulietäisyys",
        "colour": "Väri",
        "treatment": "Käsittely",
        "hard_constraint": "Ehdoton rajoite",
        "indicator": "Indikaattori",
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
            option_text(
                self.current_language,
                "country_sweden",
            ),
            "SE",
        )

        self.layer_country_combo.addItem(
            option_text(
                self.current_language,
                "country_finland",
            ),
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
                option_text(
                    self.current_language,
                    "layer",
                ),
                option_text(
                    self.current_language,
                    "solar_distance",
                ),
                option_text(
                    self.current_language,
                    "wind_distance",
                ),
                option_text(
                    self.current_language,
                    "colour",
                ),
                option_text(
                    self.current_language,
                    "treatment",
                ),
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
            option_text(
                self.current_language,
                "select_layer_colour",
            ),
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

        if not value:
            return option_text(
                self.current_language,
                "not_recorded",
            )

        try:
            if isinstance(value, str):
                value = datetime.fromisoformat(
                    value.replace(
                        "Z",
                        "+00:00",
                    )
                )

            return value.astimezone().strftime(
                "%Y-%m-%d %H:%M"
            )

        except (
            AttributeError,
            TypeError,
            ValueError,
        ):
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

        not_recorded = option_text(
            self.current_language,
            "not_recorded",
        )

        lines = [
            display_name,
            "",
            (
                option_text(
                    self.current_language,
                    "source_file",
                )
                + ": "
                + str(
                    layer_definition["source"]
                )
            ),
            (
                option_text(
                    self.current_language,
                    "database_layer",
                )
                + ": "
                + f"{database['schema']}."
                + f"{database['table']}"
            ),
            (
                option_text(
                    self.current_language,
                    "geometry_column",
                )
                + ": "
                + str(
                    database["geometry_column"]
                )
            ),
            (
                option_text(
                    self.current_language,
                    "crs",
                )
                + ": "
                + f"EPSG:{database['srid']}"
            ),
        ]

        if metadata is None:
            if metadata_error:
                unavailable_text = option_text(
                    self.current_language,
                    "metadata_unavailable",
                )
            else:
                unavailable_text = option_text(
                    self.current_language,
                    "no_catalogue_entry",
                )

            lines.extend(
                [
                    "",
                    unavailable_text,
                ]
            )

            return "\n".join(lines)

        migration_status = str(
            metadata.get(
                "migration_status"
            )
            or "unknown"
        ).strip().lower()

        migration_status_text = option_text(
            self.current_language,
            {
                "unknown": "migration_unknown",
                "running": "migration_running",
                "success": "migration_success",
                "failed": "migration_failed",
            }.get(
                migration_status,
                "migration_unknown",
            ),
        )

        record_count = metadata.get(
            "record_count"
        )

        if record_count is None:
            record_count = not_recorded

        lines.extend(
            [
                "",
                (
                    option_text(
                        self.current_language,
                        "dataset",
                    )
                    + ": "
                    + str(
                        metadata.get(
                            "dataset_name"
                        )
                        or not_recorded
                    )
                ),
                (
                    option_text(
                        self.current_language,
                        "provider",
                    )
                    + ": "
                    + str(
                        metadata.get(
                            "provider"
                        )
                        or not_recorded
                    )
                ),
                (
                    option_text(
                        self.current_language,
                        "source_updated",
                    )
                    + ": "
                    + self.display_metadata_date(
                        metadata.get(
                            "source_updated_at"
                        )
                    )
                ),
                (
                    option_text(
                        self.current_language,
                        "migrated_to_sovra",
                    )
                    + ": "
                    + self.display_metadata_date(
                        metadata.get(
                            "migrated_at"
                        )
                    )
                ),
                (
                    option_text(
                        self.current_language,
                        "last_accessed",
                    )
                    + ": "
                    + self.display_metadata_date(
                        metadata.get(
                            "last_accessed_at"
                        )
                    )
                ),
                (
                    option_text(
                        self.current_language,
                        "metadata_updated",
                    )
                    + ": "
                    + self.display_metadata_date(
                        metadata.get(
                            "metadata_updated_at"
                        )
                    )
                ),
                (
                    option_text(
                        self.current_language,
                        "records",
                    )
                    + ": "
                    + str(record_count)
                ),
                (
                    option_text(
                        self.current_language,
                        "geometry",
                    )
                    + ": "
                    + str(
                        metadata.get(
                            "geometry_type"
                        )
                        or not_recorded
                    )
                ),
                (
                    option_text(
                        self.current_language,
                        "migration_status",
                    )
                    + ": "
                    + migration_status_text
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
                    (
                        option_text(
                            self.current_language,
                            "source_url",
                        )
                        + ": "
                        + str(source_url)
                    ),
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
                option_text(
                    self.current_language,
                    "hard_constraint",
                ),
                "hard",
            )

            treatment_combo.addItem(
                option_text(
                    self.current_language,
                    "indicator",
                ),
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