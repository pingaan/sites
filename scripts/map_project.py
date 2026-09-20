import os

from urllib.parse import urlencode
from qgis.core import (
    QgsFillSymbol,
    QgsLineSymbol,
    QgsMarkerSymbol,
    QgsSingleSymbolRenderer,
    QgsVectorLayer,
    QgsWkbTypes,
)


def prepare_map_project(
    working_crs,
    title,
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
        "wind": "Wind",
        "solar": "Solar",
        "misc": "Other",
        "slopes": "Steep slopes",
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
):
    """
    Add configured XYZ basemaps beneath the analysis groups.

    Return layer IDs rather than holding extra layer references.
    """

    project = map_data["project"]
    root = project.layerTreeRoot()

    basemap_group = root.addGroup("Basemaps")

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
            "name": "Analysis estate",
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
            "name": "Solar candidate area",
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
            "name": "Wind candidate area",
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
):
    """
    Add completed context and terrain outputs to the map project.

    Missing or empty optional outputs are skipped.
    """

    project = map_data["project"]
    root = project.layerTreeRoot()

    other_group = root.findGroup("Other")
    slopes_group = root.findGroup("Steep slopes")

    if other_group is None:
        raise RuntimeError(
            "The map project has no 'Other' group."
        )

    if slopes_group is None:
        raise RuntimeError(
            "The map project has no 'Steep slopes' group."
        )

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
        layer_name="Neighbouring estates",
        group=other_group,
        symbol=neighbour_symbol,
        result_key="neighbouring_estates",
    )

    add_vector_layer(
        layer_path=ineligible_terrain_path,
        layer_name="Ineligible terrain",
        group=slopes_group,
        symbol=terrain_symbol,
        result_key="ineligible_terrain",
    )

    add_vector_layer(
        layer_path=contour_lines_path,
        layer_name="Contour lines",
        group=other_group,
        symbol=contour_symbol,
        result_key="contour_lines",
    )

    return layer_ids

def add_country_outputs(
    map_data,
    country_layer_outputs,
    style_resolver=None,
):
    """
    Add locally clipped country constraint layers to the project.

    Styling may be supplied by the active country configuration.
    """

    project = map_data["project"]
    root = project.layerTreeRoot()

    other_group = root.findGroup("Other")

    if other_group is None:
        raise RuntimeError(
            "The map project has no 'Other' group."
        )

    constraints_group = other_group.findGroup(
        "Country constraints"
    )

    if constraints_group is None:
        constraints_group = other_group.addGroup(
            "Country constraints"
        )

    constraints_group.setExpanded(False)

    layer_ids = {}

    for layer_output in country_layer_outputs:

        definition = layer_output["definition"]
        layer_name = definition["name"]
        output_path = layer_output.get("output_path")

        if not output_path or not os.path.isfile(output_path):
            print(
                f"Country map output skipped: "
                f"{layer_name} — no file."
            )
            layer_ids[layer_name] = None
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
            layer_ids[layer_name] = None
            continue

        style = (
            style_resolver(definition)
            if style_resolver is not None
            else {}
        )

        color = style.get(
            "color",
            "#d27800",
        )

        visible = style.get(
            "visible",
            False,
        )

        geometry_type = layer.geometryType()

        if geometry_type == QgsWkbTypes.PolygonGeometry:
            symbol = QgsFillSymbol.createSimple(
                {
                    "color": color,
                    "outline_color": color,
                    "outline_width": "0.25",
                }
            )
            symbol.setOpacity(0.35)

        elif geometry_type == QgsWkbTypes.LineGeometry:
            symbol = QgsLineSymbol.createSimple(
                {
                    "color": color,
                    "width": "0.35",
                }
            )

        elif geometry_type == QgsWkbTypes.PointGeometry:
            symbol = QgsMarkerSymbol.createSimple(
                {
                    "name": "circle",
                    "color": color,
                    "outline_color": color,
                    "size": "2.0",
                }
            )

        else:
            print(
                f"Country map output skipped: "
                f"{layer_name} — unsupported geometry type."
            )
            layer_ids[layer_name] = None
            continue

        layer.setRenderer(
            QgsSingleSymbolRenderer(symbol)
        )

        project.addMapLayer(
            layer,
            False,
        )

        node = constraints_group.addLayer(layer)
        node.setItemVisibilityChecked(visible)

        layer_ids[layer_name] = layer.id()

        print(
            f"Country constraint added to map: {layer_name}"
        )

    return layer_ids