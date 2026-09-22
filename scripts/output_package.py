import os
import re
import unicodedata
import json
import sys
import gc
import shutil

from dataclasses import (
    asdict,
    is_dataclass,
)
from datetime import (
    datetime,
    timezone,
)
from qgis.core import (
    Qgis,
    QgsMapLayerStyle,
    QgsProject,
    QgsVectorFileWriter,
    QgsVectorLayer,
)


def create_safe_table_name(
    requested_name,
    used_names,
):
    """
    Create a stable, unique GeoPackage table name.
    """

    normalised = unicodedata.normalize(
        "NFKD",
        requested_name,
    )

    ascii_name = normalised.encode(
        "ascii",
        "ignore",
    ).decode("ascii")

    table_name = re.sub(
        r"[^A-Za-z0-9_]+",
        "_",
        ascii_name,
    )

    table_name = table_name.strip(
        "_"
    ).lower()

    if not table_name:
        table_name = "layer"

    if table_name[0].isdigit():
        table_name = f"layer_{table_name}"

    original_name = table_name
    suffix = 2

    while table_name in used_names:
        table_name = (
            f"{original_name}_{suffix}"
        )
        suffix += 1

    used_names.add(table_name)

    return table_name


def validate_packaged_layer(
    source_layer,
    geopackage_path,
    table_name,
):
    """
    Confirm that a GeoPackage layer is valid and contains
    the same number of features as its source layer.
    """

    geopackage_uri = (
        f"{geopackage_path}"
        f"|layername={table_name}"
    )

    packaged_layer = QgsVectorLayer(
        geopackage_uri,
        table_name,
        "ogr",
    )

    if not packaged_layer.isValid():
        raise RuntimeError(
            f"Packaged layer is invalid: {table_name}"
        )

    source_count = source_layer.featureCount()
    packaged_count = packaged_layer.featureCount()

    if packaged_count != source_count:
        raise RuntimeError(
            f"Feature-count mismatch for {table_name}: "
            f"source={source_count}, "
            f"GeoPackage={packaged_count}"
        )

    if (
        source_layer.crs().isValid()
        and packaged_layer.crs().isValid()
        and source_layer.crs() != packaged_layer.crs()
    ):
        raise RuntimeError(
            f"CRS mismatch for packaged layer: "
            f"{table_name}"
        )

    return {
        "uri": geopackage_uri,
        "feature_count": packaged_count,
    }


def create_output_geopackage(
    layer_definitions,
    folder_path,
    folder_name,
):
    """
    Package final vector outputs into one validated GPKG.

    Parameters
    ----------
    layer_definitions : list[dict]
        Each dictionary must contain:

        key:
            Stable internal identifier.

        name:
            Preferred GeoPackage table name.

        path:
            Existing vector-layer path.

        Empty valid vector layers are retained because an
        empty result is still a meaningful analysis result.

    folder_path : str
        Main output folder.

    folder_name : str
        Analysis name used for the GeoPackage filename.
    """

    final_path = os.path.join(
        folder_path,
        f"{folder_name}.gpkg",
    )

    staging_path = os.path.join(
        folder_path,
        f"{folder_name}.building.gpkg",
    )

    if os.path.isfile(staging_path):
        os.remove(staging_path)

    used_names = set()
    packaged_layers = []
    first_layer = True

    for definition in layer_definitions:
        key = definition["key"]
        requested_name = definition["name"]
        source_path = definition.get("path")

        if not source_path:
            print(
                f"GeoPackage layer skipped: "
                f"{requested_name} — no path."
            )
            continue

        source_file = source_path.split(
            "|",
            1,
        )[0]

        if not os.path.isfile(source_file):
            print(
                f"GeoPackage layer skipped: "
                f"{requested_name} — file missing."
            )
            continue

        source_layer = QgsVectorLayer(
            source_path,
            requested_name,
            "ogr",
        )

        if not source_layer.isValid():
            raise ValueError(
                f"Failed to load final output layer: "
                f"{source_path}"
            )

        table_name = create_safe_table_name(
            requested_name=requested_name,
            used_names=used_names,
        )

        options = (
            QgsVectorFileWriter.SaveVectorOptions()
        )

        options.driverName = "GPKG"
        options.layerName = table_name
        options.fileEncoding = "UTF-8"

        if first_layer:
            options.actionOnExistingFile = (
                QgsVectorFileWriter
                .CreateOrOverwriteFile
            )
        else:
            options.actionOnExistingFile = (
                QgsVectorFileWriter
                .CreateOrOverwriteLayer
            )

        writer_result = (
            QgsVectorFileWriter
            .writeAsVectorFormatV3(
                source_layer,
                staging_path,
                QgsProject.instance().transformContext(),
                options,
            )
        )

        error_code = writer_result[0]
        error_message = writer_result[1]

        if (
            error_code
            != QgsVectorFileWriter.NoError
        ):
            raise RuntimeError(
                f"Failed to package {requested_name}: "
                f"{error_message}"
            )

        validation = validate_packaged_layer(
            source_layer=source_layer,
            geopackage_path=staging_path,
            table_name=table_name,
        )

        packaged_layers.append(
            {
                "key": key,
                "display_name": requested_name,
                "table_name": table_name,
                "source_path": source_path,
                "gpkg_uri": validation["uri"],
                "feature_count": validation[
                    "feature_count"
                ],
            }
        )

        print(
            f"GeoPackage layer written: "
            f"{table_name} "
            f"({validation['feature_count']} features)"
        )

        first_layer = False

    if not packaged_layers:
        raise RuntimeError(
            "No valid vector layers were supplied for "
            "GeoPackage creation."
        )

    # Release the staging datasource before renaming it.
    source_layer = None

    if os.path.isfile(final_path):
        os.replace(
            staging_path,
            final_path,
        )

    else:
        os.rename(
            staging_path,
            final_path,
        )

    # Update URIs because validation used the staging filename.
    for packaged_layer in packaged_layers:
        packaged_layer["gpkg_uri"] = (
            f"{final_path}"
            f"|layername="
            f"{packaged_layer['table_name']}"
        )

    print(
        f"Validated output GeoPackage created: "
        f"{final_path}"
    )

    return {
        "status": "complete",
        "gpkg_path": final_path,
        "layers": packaged_layers,
        "layer_count": len(packaged_layers),
    }

def normalise_layer_source(source):
    """
    Return a comparable filesystem path from a QGIS
    datasource string.
    """

    if not source:
        return None

    source_path = source.split(
        "|",
        1,
    )[0]

    return os.path.normcase(
        os.path.abspath(
            os.path.normpath(
                source_path
            )
        )
    )


def repoint_project_layers_to_geopackage(
    output_package,
):
    """
    Repoint existing QGIS project vector layers to their
    corresponding GeoPackage tables.

    Existing layer styles and layer-tree objects are retained.
    """

    project = QgsProject.instance()

    packaged_by_source = {}

    for packaged_layer in output_package["layers"]:
        normalised_source = normalise_layer_source(
            packaged_layer["source_path"]
        )

        if normalised_source:
            packaged_by_source[
                normalised_source
            ] = packaged_layer

    repointed_layers = []

    for layer in project.mapLayers().values():

        if not isinstance(
            layer,
            QgsVectorLayer,
        ):
            continue

        current_source = normalise_layer_source(
            layer.source()
        )

        packaged_layer = packaged_by_source.get(
            current_source
        )

        if packaged_layer is None:
            continue

        # Capture the complete current project style before
        # changing the datasource.
        saved_style = QgsMapLayerStyle()
        saved_style.readFromLayer(
            layer
        )

        existing_name = layer.name()
        geopackage_uri = packaged_layer[
            "gpkg_uri"
        ]

        layer.setDataSource(
            geopackage_uri,
            existing_name,
            "ogr",
        )

        if not layer.isValid():
            raise RuntimeError(
                f"Project layer became invalid after "
                f"repointing: {existing_name}"
            )

        # Restore renderer, labels and other layer styling.
        saved_style.writeToLayer(
            layer
        )

        layer.triggerRepaint()

        repointed_layers.append(
            {
                "layer_name": existing_name,
                "gpkg_uri": geopackage_uri,
            }
        )

        print(
            f"Project layer repointed to GeoPackage: "
            f"{existing_name}"
        )

    if not repointed_layers:
        raise RuntimeError(
            "No QGIS project layers were repointed to "
            "the output GeoPackage."
        )

    print(
        f"Project layers repointed to GeoPackage: "
        f"{len(repointed_layers)}"
    )

    return repointed_layers

def make_json_safe(value):
    """
    Convert settings and other values into JSON-safe data.
    """

    if is_dataclass(value):
        return make_json_safe(
            asdict(value)
        )

    if isinstance(value, dict):
        return {
            str(key): make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            make_json_safe(item)
            for item in value
        ]

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ) or value is None:
        return value

    return str(value)


def create_analysis_manifest(
    folder_path,
    folder_name,
    run_id,
    output_package,
    project_path,
    site_source,
    settings,
    country_config,
    working_crs,
):
    """
    Create a machine-readable description of the completed
    analysis package.
    """

    manifest_path = os.path.join(
        folder_path,
        "analysis_manifest.json",
    )

    temporary_path = os.path.join(
        folder_path,
        "analysis_manifest.building.json",
    )

    manifest = {
        "run_id": run_id,
        "manifest_version": 1,
        "created_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "analysis_name": folder_name,
        "country": {
            "code": getattr(
                country_config,
                "COUNTRY_CODE",
                None,
            ),
            "name": getattr(
                country_config,
                "COUNTRY_NAME",
                None,
            ),
        },
        "working_crs": {
            "authid": working_crs.authid(),
            "description": (
                working_crs.description()
            ),
        },
        "software": {
            "qgis": Qgis.QGIS_VERSION,
            "python": sys.version,
        },
        "site_source": make_json_safe(
            site_source
        ),
        "settings": make_json_safe(
            settings
        ),
        "outputs": {
            "project": os.path.basename(
                project_path
            ),
            "geopackage": os.path.basename(
                output_package["gpkg_path"]
            ),
            "report": (
                f"prints ({folder_name}).txt"
            ),
        },
        "geopackage_layers": [
            {
                "key": layer["key"],
                "display_name": layer[
                    "display_name"
                ],
                "table_name": layer[
                    "table_name"
                ],
                "feature_count": layer[
                    "feature_count"
                ],
            }
            for layer in output_package["layers"]
        ],
    }

    with open(
        temporary_path,
        "w",
        encoding="utf-8",
    ) as manifest_file:
        json.dump(
            manifest,
            manifest_file,
            ensure_ascii=False,
            indent=4,
        )

    os.replace(
        temporary_path,
        manifest_path,
    )

    print(
        f"Analysis manifest saved: "
        f"{manifest_path}"
    )

    return manifest_path

def cleanup_analysis_outputs(
    folder_path,
    project_path,
    geopackage_path,
    report_path,
    manifest_path,
    dry_run=True,
):
    """
    Remove intermediate analysis outputs while preserving
    the final project package.

    When dry_run is True, only print what would be removed.
    """

    required_files = {
        os.path.normcase(
            os.path.abspath(path)
        )
        for path in (
            project_path,
            geopackage_path,
            report_path,
            manifest_path,
        )
    }

    for required_path in required_files:
        if not os.path.isfile(required_path):
            raise FileNotFoundError(
                f"Required final output is missing: "
                f"{required_path}"
            )

        if os.path.getsize(required_path) == 0:
            raise RuntimeError(
                f"Required final output is empty: "
                f"{required_path}"
            )

    folder_absolute = os.path.normcase(
        os.path.abspath(folder_path)
    )

    geopackage_absolute = os.path.normcase(
        os.path.abspath(geopackage_path)
    )

    # Refuse cleanup if a project layer still references a
    # loose local file inside the analysis folder.
    unsafe_sources = []

    for layer in QgsProject.instance().mapLayers().values():
        source_path = normalise_layer_source(
            layer.source()
        )

        if not source_path:
            continue

        try:
            source_inside_folder = (
                os.path.commonpath(
                    [
                        folder_absolute,
                        source_path,
                    ]
                )
                == folder_absolute
            )

        except ValueError:
            source_inside_folder = False

        if (
            source_inside_folder
            and source_path
            != geopackage_absolute
        ):
            unsafe_sources.append(
                {
                    "layer": layer.name(),
                    "source": source_path,
                }
            )

    if unsafe_sources:
        details = "\n".join(
            (
                f"  {item['layer']}: "
                f"{item['source']}"
            )
            for item in unsafe_sources
        )

        raise RuntimeError(
            "Cleanup refused because project layers still "
            "reference loose files:\n"
            f"{details}"
        )

    removal_targets = []

    for entry_name in os.listdir(folder_path):
        entry_path = os.path.join(
            folder_path,
            entry_name,
        )

        entry_absolute = os.path.normcase(
            os.path.abspath(entry_path)
        )

        if entry_absolute in required_files:
            continue

        removal_targets.append(
            entry_path
        )

    if dry_run:
        print(
            "Cleanup preview — the following outputs "
            "would be removed:"
        )

        for target in removal_targets:
            print(
                f"  {target}"
            )

        print(
            "Cleanup preview complete. No files removed."
        )

        return {
            "status": "preview",
            "targets": removal_targets,
            "removed_count": 0,
        }

    # The QGZ has already been saved. Clear the in-memory
    # project to release Windows file handles before deletion.
    QgsProject.instance().clear()
    gc.collect()

    removed_count = 0

    for target in removal_targets:
        if os.path.isdir(target):
            shutil.rmtree(
                target
            )

        elif os.path.isfile(target):
            os.remove(
                target
            )

        removed_count += 1

        print(
            f"Removed intermediate output: "
            f"{target}"
        )

    print(
        f"Analysis output cleanup complete: "
        f"{removed_count} entries removed."
    )

    return {
        "status": "complete",
        "targets": removal_targets,
        "removed_count": removed_count,
    }

def remove_cleanup_targets(
    folder_path,
    removal_targets,
):
    """
    Delete a previously validated cleanup plan after QGIS
    has shut down and released its file handles.
    """

    folder_absolute = os.path.normcase(
        os.path.abspath(folder_path)
    )

    removed_count = 0
    failures = []

    for target in removal_targets:
        target_absolute = os.path.normcase(
            os.path.abspath(target)
        )

        try:
            target_inside_folder = (
                os.path.commonpath(
                    [
                        folder_absolute,
                        target_absolute,
                    ]
                )
                == folder_absolute
            )

        except ValueError:
            target_inside_folder = False

        if (
            not target_inside_folder
            or target_absolute == folder_absolute
        ):
            raise RuntimeError(
                f"Unsafe cleanup target refused: "
                f"{target}"
            )

        # Some targets may already be absent following an
        # earlier partially completed cleanup.
        if not os.path.exists(target):
            continue

        try:
            if os.path.isdir(target):
                shutil.rmtree(
                    target
                )

            else:
                os.remove(
                    target
                )

            removed_count += 1

            print(
                f"Removed intermediate output: "
                f"{target}"
            )

        except OSError as error:
            failures.append(
                {
                    "target": target,
                    "error": str(error),
                }
            )

    if failures:
        failure_text = "\n".join(
            (
                f"  {failure['target']}: "
                f"{failure['error']}"
            )
            for failure in failures
        )

        raise RuntimeError(
            "Some intermediate outputs could not be "
            "removed:\n"
            f"{failure_text}"
        )

    print(
        f"Analysis output cleanup complete: "
        f"{removed_count} entries removed."
    )

    return {
        "status": "complete",
        "removed_count": removed_count,
    }