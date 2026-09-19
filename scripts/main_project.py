from urllib.parse import urlencode
from qgis.core import (QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsFillSymbol
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