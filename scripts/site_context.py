import os
import processing

from collections import defaultdict
from qgis.core import (
    Qgis,
    QgsUnitTypes,
    QgsVectorLayer,
    QgsWkbTypes
)


def create_site_buffers(
    site_layer_path,
    temp_path,
):
    """
    Create dissolved 100 m and 5 km buffers around the estate.

    Buffer distances are converted from metres to the
    working CRS's units.
    """

    site = QgsVectorLayer(
        site_layer_path,
        "Analysis site",
        "ogr",
    )

    if not site.isValid():
        raise ValueError(
            f"Failed to load site: {site_layer_path}"
        )

    crs = site.crs()

    if not crs.isValid() or crs.isGeographic():
        raise ValueError(
            "Buffer creation requires a valid projected CRS."
        )

    map_units = crs.mapUnits()

    if map_units == Qgis.DistanceUnit.Unknown:
        raise ValueError(
            "The site CRS has unknown measurement units."
        )

    units_per_metre = QgsUnitTypes.fromUnitToUnitFactor(
        Qgis.DistanceUnit.Meters,
        map_units,
    )

    buffer_paths = {}

    for label, distance_metres, segments in (
        ("100m", 100, 5),
        ("5km", 5000, 25),
    ): 
        output_path = os.path.join(
            temp_path,
            f"Fastigheten_buffer_{label}.shp",
        )

        processing.run(
            "native:buffer",
            {
                "INPUT": site,
                "DISTANCE": distance_metres * units_per_metre,
                "SEGMENTS": segments,
                "END_CAP_STYLE": 0,
                "JOIN_STYLE": 0,
                "MITER_LIMIT": 2,
                "DISSOLVE": False,
                "OUTPUT": output_path,
            },
        )

        processing.run(
            "native:createspatialindex",
            {
                "INPUT": output_path,
            },
        )

        buffer_paths[label] = output_path

        print(
            f"Estate buffer created ({label}): {output_path}"
        )

    return buffer_paths

def extract_neighbouring_estates(
    estates_layer_path,
    hundred_m_buffer_path,
    folder_path,
):
    """
    Extract whole estate features intersecting the 100 m buffer.

    The analysis estate remains included at this stage,
    matching Anna's original sequence.
    """

    estates = QgsVectorLayer(
        estates_layer_path,
        "Estates",
        "ogr",
    )

    if not estates.isValid():
        raise ValueError(
            f"Failed to load estates: {estates_layer_path}"
        )

    buffer_layer = QgsVectorLayer(
        hundred_m_buffer_path,
        "100 m buffer",
        "ogr",
    )

    if not buffer_layer.isValid():
        raise ValueError(
            f"Failed to load buffer: {hundred_m_buffer_path}"
        )

    if not estates.crs().isValid() or not buffer_layer.crs().isValid():
        raise ValueError(
            "Both estates and buffer must have valid source CRSs."
        )

    output_path = os.path.join(
        folder_path,
        "neighbouring_estates.shp",
    )

    processing.run(
        "native:extractbylocation",
        {
            "INPUT": estates,
            "PREDICATE": [0],  # Intersects
            "INTERSECT": buffer_layer,
            "OUTPUT": output_path,
        },
    )

    processing.run(
        "native:createspatialindex",
        {
            "INPUT": output_path,
        },
    )

    print(
        f"Neighbouring estate features extracted: {output_path}"
    )

    return output_path

def group_neighbouring_estates(neighbouring_estates_path):
    """
    Group extracted estate features by BOROUGH, SECTOR and SEGMENT.

    Return the source layer and grouped features for the
    following processing step.
    """

    neighbours = QgsVectorLayer(
        neighbouring_estates_path,
        "Neighbouring estates",
        "ogr",
    )

    if not neighbours.isValid():
        raise ValueError(
            f"Failed to load neighbouring estates: "
            f"{neighbouring_estates_path}"
        )

    required_fields = (
        "BOROUGH",
        "SECTOR",
        "SEGMENT",
    )

    missing_fields = [
        name
        for name in required_fields
        if neighbours.fields().indexFromName(name) == -1
    ]

    if missing_fields:
        raise ValueError(
            f"Missing estate fields: {', '.join(missing_fields)}"
        )

    feature_groups = defaultdict(list)

    for feature in neighbours.getFeatures():
        key = (
            feature["BOROUGH"],
            feature["SECTOR"],
            feature["SEGMENT"],
        )

        feature_groups[key].append(feature)

    print(
        f"Neighbouring features grouped into "
        f"{len(feature_groups)} estates."
    )

    return {
        "layer": neighbours,
        "groups": dict(feature_groups),
    }

def dissolve_neighbouring_groups(
    neighbour_groups,
    temp_path,
):
    """
    Save and dissolve each estate group separately.

    Preserve the source geometry type, fields and CRS.
    Return the paths to the dissolved group shapefiles.
    """

    source_layer = neighbour_groups["layer"]
    groups = neighbour_groups["groups"]

    if not source_layer.isValid():
        raise ValueError(
            "The neighbouring-estates source layer is invalid."
        )

    if not source_layer.crs().isValid():
        raise ValueError(
            "The neighbouring-estates source CRS is invalid."
        )

    os.makedirs(temp_path, exist_ok=True)

    geometry_type = QgsWkbTypes.displayString(
        source_layer.wkbType()
    )

    dissolved_paths = []

    for index, (estate_key, features) in enumerate(groups.items()):

        group_layer = QgsVectorLayer(
            geometry_type,
            f"group_{index}",
            "memory",
        )

        if not group_layer.isValid():
            raise RuntimeError(
                f"Failed to create layer for estate: {estate_key}"
            )

        group_layer.setCrs(source_layer.crs())

        provider = group_layer.dataProvider()

        if not provider.addAttributes(list(source_layer.fields())):
            raise RuntimeError(
                f"Failed to copy fields for estate: {estate_key}"
            )

        group_layer.updateFields()

        success, added_features = provider.addFeatures(features)

        if not success or len(added_features) != len(features):
            raise RuntimeError(
                f"Failed to copy all features for estate: {estate_key}"
            )

        group_layer.updateExtents()

        # Save the estate group.
        group_path = os.path.join(
            temp_path,
            f"temp_group_{index}.shp",
        )

        processing.run(
            "native:savefeatures",
            {
                "INPUT": group_layer,
                "OUTPUT": group_path,
            },
        )

        processing.run(
            "native:createspatialindex",
            {
                "INPUT": group_path,
            },
        )

        # Dissolve the pieces belonging to this estate.
        dissolved_path = os.path.join(
            temp_path,
            f"dissolved_group_{index}.shp",
        )

        processing.run(
            "native:dissolve",
            {
                "INPUT": group_path,
                "OUTPUT": dissolved_path,
            },
        )

        processing.run(
            "native:createspatialindex",
            {
                "INPUT": dissolved_path,
            },
        )

        dissolved_paths.append(dissolved_path)

        estate_name = " ".join(str(value) for value in estate_key)

        print(
            f"Neighbouring estate dissolved "
            f"({index + 1}/{len(groups)}): {estate_name}"
        )

    return dissolved_paths

def split_neighbouring_groups(
    dissolved_neighbour_paths,
    temp_path,
):
    """
    Convert each dissolved estate group to singlepart features.

    Preserve the CRS and return the output paths.
    """

    singlepart_paths = []

    for index, dissolved_path in enumerate(dissolved_neighbour_paths):

        singlepart_path = os.path.join(
            temp_path,
            f"singlepart_group_{index}.shp",
        )

        processing.run(
            "native:multiparttosingleparts",
            {
                "INPUT": dissolved_path,
                "OUTPUT": singlepart_path,
            },
        )

        processing.run(
            "native:createspatialindex",
            {
                "INPUT": singlepart_path,
            },
        )

        singlepart_paths.append(singlepart_path)

        print(
            f"Neighbouring estate converted to singleparts "
            f"({index + 1}/{len(dissolved_neighbour_paths)}): "
            f"{singlepart_path}"
        )

    return singlepart_paths

def reproject_neighbouring_groups(
    singlepart_neighbour_paths,
    temp_path,
    target_crs,
):
    """
    Reproject each neighbouring estate group to the
    working CRS already resolved for this analysis.
    """

    reprojected_paths = []

    for index, singlepart_path in enumerate(singlepart_neighbour_paths):

        reprojected_path = os.path.join(
            temp_path,
            f"reprojected_group_{index}.shp",
        )

        processing.run(
            "native:reprojectlayer",
            {
                "INPUT": singlepart_path,
                "TARGET_CRS": target_crs,
                "OUTPUT": reprojected_path,
            },
        )

        processing.run(
            "native:createspatialindex",
            {
                "INPUT": reprojected_path,
            },
        )

        reprojected_paths.append(reprojected_path)

        print(
            f"Neighbouring estate reprojected "
            f"({index + 1}/{len(singlepart_neighbour_paths)}): "
            f"{reprojected_path}"
        )

    return reprojected_paths

def merge_neighbouring_groups(
    reprojected_neighbour_paths,
    temp_path,
    target_crs,
):
    """
    Merge the reprojected neighbouring estate groups
    into one layer using the analysis working CRS.
    """

    if not reprojected_neighbour_paths:
        raise ValueError(
            "No neighbouring estate groups are available to merge."
        )

    merged_path = os.path.join(
        temp_path,
        "merged_final_layer.shp",
    )

    processing.run(
        "native:mergevectorlayers",
        {
            "LAYERS": reprojected_neighbour_paths,
            "CRS": target_crs,
            "OUTPUT": merged_path,
        },
    )

    processing.run(
        "native:createspatialindex",
        {
            "INPUT": merged_path,
        },
    )

    print(
        f"Neighbouring estate groups merged: {merged_path}"
    )

    return merged_path

def subtract_analysis_site(
    merged_neighbours_path,
    site_layer_path,
    temp_path,
):
    """
    Remove the analysis site's geometry from the merged
    neighbouring estates and save Grannar.shp.
    """

    neighbours_path = os.path.join(
        temp_path,
        "Grannar.shp",
    )

    processing.run(
        "native:difference",
        {
            "INPUT": merged_neighbours_path,
            "OVERLAY": site_layer_path,
            "OUTPUT": neighbours_path,
        },
    )

    processing.run(
        "native:createspatialindex",
        {
            "INPUT": neighbours_path,
        },
    )

    print(
        f"Analysis site subtracted from neighbours: "
        f"{neighbours_path}"
    )

    return neighbours_path

def save_neighbouring_estates(
    neighbours_difference_path,
    folder_path,
):
    """
    Save the processed neighbouring estates as the final output.

    Preserve the working CRS and the removal of the analysis site.
    """

    output_path = os.path.join(
        folder_path,
        "neighbouring_estates_reprojected.shp",
    )

    processing.run(
        "native:savefeatures",
        {
            "INPUT": neighbours_difference_path,
            "OUTPUT": output_path,
        },
    )

    processing.run(
        "native:createspatialindex",
        {
            "INPUT": output_path,
        },
    )

    print(
        f"Final neighbouring estates saved: {output_path}"
    )

    return output_path

def get_layer_extent(layer_path):
    """
    Return a polygon layer's bounding coordinates and CRS.
    """

    layer = QgsVectorLayer(
        layer_path,
        "Extent source",
        "ogr",
    )

    if not layer.isValid():
        raise ValueError(
            f"Failed to load extent source: {layer_path}"
        )

    if not layer.crs().isValid():
        raise ValueError(
            f"Extent source has no valid CRS: {layer_path}"
        )

    extent = layer.extent()

    if layer.featureCount() == 0 or extent.isEmpty():
        raise ValueError(
            f"Extent source has no usable extent: {layer_path}"
        )

    extent_data = {
        "x_min": extent.xMinimum(),
        "y_min": extent.yMinimum(),
        "x_max": extent.xMaximum(),
        "y_max": extent.yMaximum(),
        "crs": layer.crs(),
    }

    print(
        f"Extent of {os.path.basename(layer_path)} "
        f"({extent_data['crs'].authid()}): "
        f"x={extent_data['x_min']:.2f}"
        f" to {extent_data['x_max']:.2f}, "
        f"y={extent_data['y_min']:.2f}"
        f" to {extent_data['y_max']:.2f}"
    )

    return extent_data