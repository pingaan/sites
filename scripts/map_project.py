import os
from urllib.parse import urlencode

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from scripts.translations import (
    translated_layer_name,
    ui_text,
)
from qgis.core import (
    QgsCategorizedSymbolRenderer,
    QgsFillSymbol,
    QgsLineSymbol,
    QgsMarkerLineSymbolLayer,
    QgsMarkerSymbol,
    QgsProject,
    QgsProperty,
    QgsRasterLayer,
    QgsRendererCategory,
    QgsSimpleFillSymbolLayer,
    QgsSimpleLineSymbolLayer,
    QgsSingleSymbolRenderer,
    QgsSvgMarkerSymbolLayer,
    QgsSymbol,
    QgsSymbolLayer,
    QgsVectorLayer,
    QgsWkbTypes,
)


def prepare_map_project(
    working_crs,
    title,
    language="en",
):
    """
    Prepare the QGIS project and its layer groups.

    This creates project structure only; it does not open
    a window or add basemaps or analysis layers.
    """

    if not working_crs.isValid():
        raise ValueError(
            "The map project requires a valid working CRS."
        )

    project = QgsProject.instance()

    project.setCrs(working_crs)
    project.setTitle(title)

    root = project.layerTreeRoot()

    group_names = {
        "wind": ui_text(
            language,
            "project_group_wind",
        ),
        "solar": ui_text(
            language,
            "project_group_solar",
        ),
        "misc": ui_text(
            language,
            "project_group_other",
        ),
        "slopes": ui_text(
            language,
            "project_group_steep_slopes",
        ),
    }

    groups = {
        "no_folder": root,
    }

    for key, name in group_names.items():
        group = root.findGroup(name)

        if group is None:
            group = root.addGroup(name)

        # Match Anna's initial group visibility.
        group.setItemVisibilityChecked(False)

        groups[key] = group

    print(
        f"Map project prepared: {title} "
        f"({working_crs.authid()})"
    )

    return {
        "project": project,
        "groups": groups,
    }

def add_basemaps(
    map_data,
    basemap_definitions,
    language="en",
):
    """
    Add configured XYZ basemaps beneath the analysis groups.

    Return layer IDs rather than holding extra layer references.
    """

    project = map_data["project"]
    root = project.layerTreeRoot()

    basemap_group = root.addGroup(
        ui_text(
            language,
            "project_group_basemaps",
        )
    )

    layer_ids = {}

    for definition in basemap_definitions:
        uri = urlencode(
            {
                "type": "xyz",
                "zmin": definition["min_zoom"],
                "zmax": definition["max_zoom"],
                "url": definition["url"],
            }
        )

        layer = QgsRasterLayer(
            uri,
            definition["name"],
            "wms",
        )

        if not layer.isValid():
            raise RuntimeError(
                f"Could not initialise basemap: {definition['name']}"
            )

        project.addMapLayer(layer, False)

        node = basemap_group.addLayer(layer)
        node.setItemVisibilityChecked(
            definition.get("visible", True)
        )

        layer_ids[definition["id"]] = layer.id()

        print(
            f"Basemap added to project: {definition['name']}"
        )

    return layer_ids

def add_analysis_outputs(
    map_data,
    site_layer_path,
    solar_candidate_path,
    wind_candidate_path,
    language="en",
):
    """
    Add the estate boundary and solar/wind candidate layers.

    Use simple initial styles and return the added layer IDs.
    """

    project = map_data["project"]
    groups = map_data["groups"]

    definitions = [
        {
            "id": "estate",
            "path": site_layer_path,
            "name": ui_text(
                language,
                "project_layer_analysis_estate",
            ),
            "group": "no_folder",
            "style": {
                "style": "no",
                "outline_color": "255,255,255,255",
                "outline_width": "0.6",
                "outline_width_unit": "MM",
            },
        },
        {
            "id": "solar",
            "path": solar_candidate_path,
            "name": ui_text(
                language,
                "project_layer_solar_candidate",
            ),
            "group": "solar",
            "style": {
                "color": "255,210,60,140",
                "outline_color": "210,150,0,255",
                "outline_width": "0.3",
                "outline_width_unit": "MM",
            },
        },
        {
            "id": "wind",
            "path": wind_candidate_path,
            "name": ui_text(
                language,
                "project_layer_wind_candidate",
            ),
            "group": "wind",
            "style": {
                "color": "70,170,255,140",
                "outline_color": "20,100,200,255",
                "outline_width": "0.3",
                "outline_width_unit": "MM",
            },
        },
    ]

    layer_ids = {}

    for definition in definitions:
        layer = QgsVectorLayer(
            definition["path"],
            definition["name"],
            "ogr",
        )

        if not layer.isValid():
            raise ValueError(
                f"Failed to load map output: {definition['path']}"
            )

        if layer.featureCount() == 0:
            print(
                f"Map layer omitted because it is empty: "
                f"{definition['name']}"
            )
            continue

        symbol = QgsFillSymbol.createSimple(
            definition["style"]
        )

        layer.renderer().setSymbol(symbol)

        layer.setCustomProperty(
            "sites/analysis_output",
            definition["id"],
        )

        project.addMapLayer(layer, False)

        project.addMapLayer(layer, False)

        group = groups[definition["group"]]

        # Insert above existing layers, including the basemaps.
        node = group.insertLayer(0, layer)
        node.setItemVisibilityChecked(True)

        layer_ids[definition["id"]] = layer.id()

        print(
            f"Analysis output added to map: {definition['name']}"
        )

    return layer_ids

def save_map_project(
    map_data,
    folder_path,
    folder_name,
):
    """
    Save the assembled QGIS project in the analysis output folder.
    """

    project = map_data["project"]

    project_path = os.path.join(
        folder_path,
        f"{folder_name}.qgz",
    )

    if not project.write(project_path):
        raise RuntimeError(
            f"Failed to save QGIS project: {project_path}"
        )

    if not os.path.isfile(project_path):
        raise RuntimeError(
            f"QGIS reported success, but the project file "
            f"was not created: {project_path}"
        )

    print(
        f"QGIS project saved: {project_path}"
    )

    return project_path

def add_supporting_outputs(
    map_data,
    neighbouring_estates_path,
    ineligible_terrain_path,
    contour_lines_path,
    language="en",
):
    """
    Add completed context and terrain outputs to the map project.

    Missing or empty optional outputs are skipped.
    """

    project = map_data["project"]

    other_group = map_data[
        "groups"
    ]["misc"]

    slopes_group = map_data[
        "groups"
    ]["slopes"]

    layer_ids = {}

    def add_vector_layer(
        layer_path,
        layer_name,
        group,
        symbol,
        result_key,
    ):
        if not layer_path or not os.path.isfile(layer_path):
            print(
                f"Map output skipped: {layer_name} — no file."
            )
            layer_ids[result_key] = None
            return

        layer = QgsVectorLayer(
            layer_path,
            layer_name,
            "ogr",
        )

        if not layer.isValid():
            raise ValueError(
                f"Failed to load map output: {layer_path}"
            )

        if layer.featureCount() == 0:
            print(
                f"Map output skipped: {layer_name} — no features."
            )
            layer_ids[result_key] = None
            return

        layer.setRenderer(
            QgsSingleSymbolRenderer(symbol)
        )

        project.addMapLayer(
            layer,
            False,
        )

        node = group.addLayer(layer)
        node.setItemVisibilityChecked(True)

        layer_ids[result_key] = layer.id()

        print(
            f"Supporting output added to map: {layer_name}"
        )

    neighbour_symbol = QgsFillSymbol.createSimple(
        {
            "color": "255,255,255,0",
            "outline_color": "110,110,110,255",
            "outline_width": "0.3",
        }
    )

    terrain_symbol = QgsFillSymbol.createSimple(
        {
            "color": "190,25,25,110",
            "outline_color": "150,0,0,255",
            "outline_width": "0.2",
        }
    )

    contour_symbol = QgsLineSymbol.createSimple(
        {
            "color": "125,85,45,210",
            "width": "0.2",
        }
    )

    add_vector_layer(
        layer_path=neighbouring_estates_path,
        layer_name=ui_text(
            language,
            "package_layer_neighbouring_estates",
        ),
        group=other_group,
        symbol=neighbour_symbol,
        result_key="neighbouring_estates",
    )

    add_vector_layer(
        layer_path=ineligible_terrain_path,
        layer_name=ui_text(
            language,
            "package_layer_ineligible_terrain",
        ),
        group=slopes_group,
        symbol=terrain_symbol,
        result_key="ineligible_terrain",
    )

    add_vector_layer(
        layer_path=contour_lines_path,
        layer_name=ui_text(
            language,
            "package_layer_contour_lines",
        ),
        group=other_group,
        symbol=contour_symbol,
        result_key="contour_lines",
    )

    return layer_ids

def create_marker_line_symbol(
    color,
    marker_size,
    interval,
):
    """
    Create a line represented by repeated markers.
    """

    marker_symbol = QgsMarkerSymbol.createSimple(
        {
            "name": "circle",
            "color": color,
            "outline_color": color,
            "size": str(marker_size),
        }
    )

    marker_layer = QgsMarkerLineSymbolLayer()
    marker_layer.setInterval(interval)
    marker_layer.setSubSymbol(
        marker_symbol
    )

    line_symbol = QgsLineSymbol()

    line_symbol.changeSymbolLayer(
        0,
        marker_layer,
    )

    return line_symbol

def apply_country_layer_style(
    layer,
    style,
    svg_path=None,
):
    """
    Apply the general and special map styling supplied by
    the active country configuration.
    """

    color = style.get(
        "color",
        "#d27800",
    )

    special = style.get(
        "special",
        "none",
    )

    geometry_type = layer.geometryType()

    # ---------------------------------------------------------
    # Display-name adjustment
    # ---------------------------------------------------------

    if special == "remove_poly_suffix":
        layer.setName(
            layer.name().replace(
                "_poly",
                "",
            )
        )

    # ---------------------------------------------------------
    # Dotted estate boundaries
    # ---------------------------------------------------------

    if (
        special == "dotted"
        and geometry_type == QgsWkbTypes.PolygonGeometry
    ):
        symbol = QgsFillSymbol.createSimple(
            {
                "style": "no",
                "outline_style": "dash",
                "outline_color": "#cccccc",
                "outline_width": "0.1",
            }
        )

        layer.setRenderer(
            QgsSingleSymbolRenderer(symbol)
        )

        return

    # ---------------------------------------------------------
    # Walking-trail marker line
    # ---------------------------------------------------------

    if (
        special == "walking"
        and geometry_type == QgsWkbTypes.LineGeometry
    ):
        walking_symbol = create_marker_line_symbol(
            color=color,
            marker_size=0.8,
            interval=3.0,
        )

        layer.setRenderer(
            QgsSingleSymbolRenderer(
                walking_symbol
            )
        )

        return

    # ---------------------------------------------------------
    # Railway marker line
    # ---------------------------------------------------------

    if (
        special == "rail"
        and geometry_type == QgsWkbTypes.LineGeometry
    ):
        rail_symbol = create_marker_line_symbol(
            color=color,
            marker_size=2.4,
            interval=4.0,
        )

        layer.setRenderer(
            QgsSingleSymbolRenderer(
                rail_symbol
            )
        )

        return

    # ---------------------------------------------------------
    # Cased bicycle-route lines
    # ---------------------------------------------------------

    if (
        special == "bike"
        and geometry_type == QgsWkbTypes.LineGeometry
    ):
        outer_line = QgsSimpleLineSymbolLayer.create(
            {
                "color": "black",
                "width": "2",
                "joinstyle": "round",
                "capstyle": "round",
            }
        )

        inner_line = QgsSimpleLineSymbolLayer.create(
            {
                "color": color,
                "width": "1.46",
                "joinstyle": "round",
                "capstyle": "round",
            }
        )

        bike_symbol = QgsLineSymbol()

        bike_symbol.changeSymbolLayer(
            0,
            outer_line,
        )

        bike_symbol.appendSymbolLayer(
            inner_line
        )

        layer.setRenderer(
            QgsSingleSymbolRenderer(
                bike_symbol
            )
        )

        return

    # ---------------------------------------------------------
    # Directional water-flow arrows
    # ---------------------------------------------------------

    if (
        special == "arrow"
        and geometry_type == QgsWkbTypes.PointGeometry
    ):
        if (
            svg_path is None
            or not os.path.isfile(svg_path)
        ):
            print(
                f"Arrow styling skipped for {layer.name()}: "
                f"SVG file was not found."
            )

        else:
            svg_layer = QgsSvgMarkerSymbolLayer(
                svg_path
            )

            svg_layer.setSize(5)

            if (
                layer.fields().indexFromName(
                    "DIRECTION"
                )
                != -1
            ):
                svg_layer.setDataDefinedProperty(
                    QgsSymbolLayer.PropertyAngle,
                    QgsProperty.fromExpression(
                        '"DIRECTION"'
                    ),
                )

            else:
                print(
                    f"Direction field not found for "
                    f"{layer.name()}; arrows will not "
                    f"be rotated."
                )

            arrow_symbol = QgsMarkerSymbol()

            arrow_symbol.changeSymbolLayer(
                0,
                svg_layer,
            )

            layer.setRenderer(
                QgsSingleSymbolRenderer(
                    arrow_symbol
                )
            )

            layer.setName(
                layer.name().replace(
                    "_poly",
                    "",
                )
            )

            return

    # ---------------------------------------------------------
    # Categorized soil types
    # ---------------------------------------------------------

    if special == "soil":

        field_name = "TYPE"
        field_index = layer.fields().indexFromName(
            field_name
        )

        if field_index == -1:
            print(
                f"Soil styling skipped for {layer.name()}: "
                f"field '{field_name}' was not found."
            )

        else:
            unique_values = sorted(
                layer.dataProvider().uniqueValues(
                    field_index
                ),
                key=str,
            )

            categories = []

            start_color = QColor("#e6a55c")
            end_color = QColor("#5e3506")

            denominator = max(
                len(unique_values) - 1,
                1,
            )

            for index, value in enumerate(
                unique_values
            ):
                fraction = index / denominator

                red = round(
                    start_color.red()
                    + (
                        end_color.red()
                        - start_color.red()
                    )
                    * fraction
                )

                green = round(
                    start_color.green()
                    + (
                        end_color.green()
                        - start_color.green()
                    )
                    * fraction
                )

                blue = round(
                    start_color.blue()
                    + (
                        end_color.blue()
                        - start_color.blue()
                    )
                    * fraction
                )

                category_symbol = (
                    QgsSymbol.defaultSymbol(
                        geometry_type
                    )
                )

                if category_symbol is None:
                    continue

                category_symbol.setColor(
                    QColor(
                        red,
                        green,
                        blue,
                    )
                )

                categories.append(
                    QgsRendererCategory(
                        value,
                        category_symbol,
                        str(value),
                    )
                )

            layer.setRenderer(
                QgsCategorizedSymbolRenderer(
                    field_name,
                    categories,
                )
            )

            return

    # ---------------------------------------------------------
    # Start with the normal symbol for this geometry type
    # ---------------------------------------------------------

    symbol = QgsSymbol.defaultSymbol(
        geometry_type
    )

    if symbol is None:
        print(
            f"No default symbol available for: "
            f"{layer.name()}"
        )
        return

    symbol.setColor(
        QColor(color)
    )

    # ---------------------------------------------------------
    # Wide line
    # ---------------------------------------------------------

    if (
        special == "wide_line"
        and geometry_type == QgsWkbTypes.LineGeometry
    ):
        symbol_layer = symbol.symbolLayer(0)

        if hasattr(symbol_layer, "setWidth"):
            symbol_layer.setWidth(1.1)

    # ---------------------------------------------------------
    # 15% transparency
    # ---------------------------------------------------------

    elif special == "transparent_15":
        symbol.setOpacity(0.85)

    # ---------------------------------------------------------
    # Forward diagonal hatch
    # ---------------------------------------------------------

    elif (
        special == "forward_hatch"
        and geometry_type == QgsWkbTypes.PolygonGeometry
    ):
        fill_layer = QgsSimpleFillSymbolLayer()
        fill_layer.setColor(
            QColor(color)
        )
        fill_layer.setBrushStyle(
            Qt.FDiagPattern
        )

        symbol.changeSymbolLayer(
            0,
            fill_layer,
        )

    # ---------------------------------------------------------
    # Backward diagonal hatch
    # ---------------------------------------------------------

    elif (
        special == "backward_hatch"
        and geometry_type == QgsWkbTypes.PolygonGeometry
    ):
        fill_layer = QgsSimpleFillSymbolLayer()
        fill_layer.setColor(
            QColor(color)
        )
        fill_layer.setBrushStyle(
            Qt.BDiagPattern
        )

        symbol.changeSymbolLayer(
            0,
            fill_layer,
        )

    layer.setRenderer(
        QgsSingleSymbolRenderer(symbol)
    )

def apply_configured_constraint_style(
    layer,
    definition,
):
    """
    Apply the user's hard-constraint or indicator styling.

    Hard constraints use solid, opaque symbols. Indicators use
    hatching, dashes or outlined markers depending on geometry.
    """

    treatment = definition.get(
        "treatment",
        "hard",
    )

    colour = QColor(
        definition.get(
            "colour",
            "#d27800",
        )
    )

    if not colour.isValid():
        colour = QColor(
            "#d27800"
        )

    colour.setAlpha(
        255
    )

    colour_name = colour.name(
        QColor.HexRgb
    )

    outline_colour = colour.darker(
        135
    ).name(
        QColor.HexRgb
    )

    geometry_type = layer.geometryType()

    if geometry_type == QgsWkbTypes.PolygonGeometry:
        if treatment == "indicator":
            symbol = QgsFillSymbol.createSimple(
                {
                    "color": colour_name,
                    "style": "b_diagonal",
                    "outline_color": colour_name,
                    "outline_width": "0.5",
                }
            )

        else:
            symbol = QgsFillSymbol.createSimple(
                {
                    "color": colour_name,
                    "style": "solid",
                    "outline_color": outline_colour,
                    "outline_width": "0.4",
                }
            )

    elif geometry_type == QgsWkbTypes.LineGeometry:
        line_style = (
            "dash"
            if treatment == "indicator"
            else "solid"
        )

        symbol = QgsLineSymbol.createSimple(
            {
                "line_color": colour_name,
                "line_width": "0.8",
                "line_style": line_style,
            }
        )

    elif geometry_type == QgsWkbTypes.PointGeometry:
        if treatment == "indicator":
            symbol = QgsMarkerSymbol.createSimple(
                {
                    "name": "circle",
                    "color": "255,255,255,0",
                    "outline_color": colour_name,
                    "outline_width": "0.8",
                    "size": "3.2",
                }
            )

        else:
            symbol = QgsMarkerSymbol.createSimple(
                {
                    "name": "circle",
                    "color": colour_name,
                    "outline_color": outline_colour,
                    "outline_width": "0.4",
                    "size": "3.2",
                }
            )

    else:
        return

    layer.setRenderer(
        QgsSingleSymbolRenderer(
            symbol
        )
    )

    layer.setCustomProperty(
        "sovra/treatment",
        treatment,
    )

    layer.setCustomProperty(
        "sovra/colour",
        colour_name,
    )

def add_country_outputs(
    map_data,
    country_layer_outputs,
    style_resolver=None,
    svg_path=None,
    language="en",
):
    """
    Add locally clipped country constraint layers to the project.

    Styling may be supplied by the active country configuration.
    """

    project = map_data["project"]

    other_group = map_data[
        "groups"
    ]["misc"]

    constraints_group_name = ui_text(
        language,
        "project_group_country_constraints",
    )

    constraints_group = other_group.findGroup(
        constraints_group_name
    )

    if constraints_group is None:
        constraints_group = other_group.addGroup(
            constraints_group_name
        )

    constraints_group.setExpanded(False)

    layer_ids = {}

    for layer_output in country_layer_outputs:

        definition = layer_output["definition"]

        internal_layer_name = (
            definition["name"]
        )

        layer_name = translated_layer_name(
            definition=definition,
            language=language,
        )
        output_path = layer_output.get(
            "output_path"
        )

        if (
            not output_path
            or not os.path.isfile(output_path)
        ):
            print(
                f"Country map output skipped: "
                f"{layer_name} — no file."
            )

            layer_ids[internal_layer_name] = None
            continue

        layer = QgsVectorLayer(
            output_path,
            layer_name,
            "ogr",
        )

        if not layer.isValid():
            raise ValueError(
                f"Failed to load country map output: "
                f"{output_path}"
            )

        if layer.featureCount() == 0:
            print(
                f"Country map output skipped: "
                f"{layer_name} — no features."
            )

            layer_ids[internal_layer_name] = None
            continue

        style = (
            style_resolver(definition)
            if style_resolver is not None
            else {}
        )

        visible = style.get(
            "visible",
            False,
        )

        apply_country_layer_style(
            layer=layer,
            style=style,
            svg_path=svg_path,
        )

        apply_configured_constraint_style(
            layer=layer,
            definition=definition,
        )

        project.addMapLayer(
            layer,
            False,
        )

        node = constraints_group.addLayer(
            layer
        )

        node.setItemVisibilityChecked(
            visible
        )

        layer_ids[internal_layer_name] = layer.id()

        print(
            f"Country constraint added to map: "
            f"{layer_name}"
        )

    return layer_ids

def add_bos_coverage(
    map_data,
    bos_coverage_path,
    language="en",
):
    """
    Add the final classified BoS coverage layer to the
    QGIS project.
    """

    if (
        bos_coverage_path is None
        or not os.path.isfile(bos_coverage_path)
    ):
        print(
            "BoS map output skipped: no coverage file."
        )
        return None

    project = map_data["project"]

    layer = QgsVectorLayer(
        bos_coverage_path,
        ui_text(
            language,
            "project_layer_bos_coverage",
        ),
        "ogr",
    )

    if not layer.isValid():
        raise ValueError(
            f"Failed to load BoS coverage layer: "
            f"{bos_coverage_path}"
        )

    if layer.featureCount() == 0:
        print(
            "BoS map output skipped: coverage layer is empty."
        )
        return None

    if layer.fields().indexOf("BOS_GROUP") == -1:
        raise ValueError(
            "BoS coverage layer has no BOS_GROUP field."
        )

    category_styles = {
        "Open field": {
            "label_key": "project_bos_open_field",
            "color": "#e5d76f",
            "outline": "#9c8d32",
        },
        "Peat quarry": {
            "label_key": "project_bos_peat_quarry",
            "color": "#795548",
            "outline": "#4e342e",
        },
        "Forest": {
            "label_key": "project_bos_forest",
            "color": "#4f8a4c",
            "outline": "#285a2b",
        },
        "Wetland": {
            "label_key": "project_bos_wetland",
            "color": "#55a6cf",
            "outline": "#276987",
        },
        "Rocky terrain": {
            "label_key": "project_bos_rocky_terrain",
            "color": "#9e9e9e",
            "outline": "#616161",
        },
        "Other land cover": {
            "label_key": (
                "project_bos_other_land_cover"
            ),
            "color": "#c8a6d8",
            "outline": "#79558a",
        },
        "No land-cover data": {
            "label_key": (
                "project_bos_no_land_cover"
            ),
            "color": "#eeeeee",
            "outline": "#777777",
        },
    }

    categories = []

    for group_name, style in category_styles.items():

        symbol = QgsFillSymbol.createSimple(
            {
                "color": style["color"],
                "outline_color": style["outline"],
                "outline_width": "0.30",
            }
        )

        if group_name == "No land-cover data":
            symbol.setOpacity(0.30)

        else:
            symbol.setOpacity(0.65)

        category = QgsRendererCategory(
            group_name,
            symbol,
            ui_text(
                language,
                style["label_key"],
            ),
        )

        categories.append(category)

    renderer = QgsCategorizedSymbolRenderer(
        "BOS_GROUP",
        categories,
    )

    layer.setRenderer(renderer)

    project.addMapLayer(
        layer,
        False,
    )

    root = project.layerTreeRoot()

    bos_group_name = ui_text(
        language,
        "project_group_bos_analysis",
    )

    bos_group = root.findGroup(
        bos_group_name
    )

    if bos_group is None:
        bos_group = root.addGroup(
            bos_group_name
        )

    node = bos_group.addLayer(layer)

    # Leave BoS visible when the project is first opened.
    node.setItemVisibilityChecked(True)

    print(
        f"BoS coverage added to map: "
        f"{layer.featureCount()} categories."
    )

    return layer.id()

def add_redlisted_species(
    map_data,
    redlisted_species_result,
    language="en",
):
    """
    Add offline red-listed species observations to the QGIS
    project and categorize them by red-list status.
    """

    if (
        not redlisted_species_result
        or redlisted_species_result.get("status")
        != "available"
    ):
        print(
            "Red-listed species map layer skipped: "
            "no offline observations available."
        )
        return None

    output_path = redlisted_species_result.get(
        "output_path"
    )

    if (
        not output_path
        or not os.path.isfile(output_path)
    ):
        print(
            "Red-listed species map layer skipped: "
            "output file is missing."
        )
        return None

    layer = QgsVectorLayer(
        output_path,
        ui_text(
            language,
            "project_layer_redlisted_species",
        ),
        "ogr",
    )

    if not layer.isValid():
        raise ValueError(
            f"Failed to load red-listed species layer: "
            f"{output_path}"
        )

    if layer.featureCount() == 0:
        print(
            "Red-listed species map layer skipped: "
            "the layer is empty."
        )
        return None

    if layer.fields().indexOf("REDLIST") == -1:
        raise ValueError(
            "The red-listed species layer has no "
            "REDLIST field."
        )

    category_styles = {
        "CR": {
            "label_key": (
                "project_species_critically_endangered"
            ),
            "color": "#7f0000",
            "size": "3.5",
        },
        "EN": {
            "label_key": (
                "project_species_endangered"
            ),
            "color": "#d7301f",
            "size": "3.2",
        },
        "VU": {
            "label_key": (
                "project_species_vulnerable"
            ),
            "color": "#fc8d59",
            "size": "3.0",
        },
        "NT": {
            "label_key": (
                "project_species_near_threatened"
            ),
            "color": "#fdbb30",
            "size": "2.8",
        },
    }

    categories = []

    for category_value, style in (
        category_styles.items()
    ):

        symbol = QgsMarkerSymbol.createSimple(
            {
                "name": "circle",
                "color": style["color"],
                "outline_color": "#202020",
                "outline_width": "0.25",
                "size": style["size"],
            }
        )

        categories.append(
            QgsRendererCategory(
                category_value,
                symbol,
                ui_text(
                    language,
                    style["label_key"],
                ),
            )
        )

    renderer = QgsCategorizedSymbolRenderer(
        "REDLIST",
        categories,
    )

    layer.setRenderer(renderer)

    # Show the complete species name in identify results,
    # layer previews and map tips.
    unknown_species = ui_text(
        language,
        "project_unknown_species",
    ).replace(
        "'",
        "''",
    )

    layer.setDisplayExpression(
        f"""
        CASE
            WHEN "SPECIES" IS NOT NULL
                 AND "SPECIES" != ''
            THEN "SPECIES"
            WHEN "SCI_NAME" IS NOT NULL
                 AND "SCI_NAME" != ''
            THEN "SCI_NAME"
            ELSE '{unknown_species}'
        END
        """
    )

    project = map_data["project"]

    project.addMapLayer(
        layer,
        False,
    )

    root = project.layerTreeRoot()

    species_group_name = ui_text(
        language,
        "project_group_species_observations",
    )

    species_group = root.findGroup(
        species_group_name
    )

    if species_group is None:
        species_group = root.addGroup(
            species_group_name
        )

    node = species_group.addLayer(layer)
    node.setItemVisibilityChecked(True)

    print(
        f"Red-listed species added to map: "
        f"{layer.featureCount()} observations."
    )

    return layer.id()