import gc
import os

from scripts.run_id import create_run_id
from scripts.output_package import (
    create_output_geopackage,
    repoint_project_layers_to_geopackage,
    create_analysis_manifest,
    cleanup_analysis_outputs,
    remove_cleanup_targets,
)
from scripts.custom_estates import (
    analyse_custom_estates,
)
from scripts.soil_depth import (
    analyse_soil_depth_by_type,
)
from scripts.redlisted_species import (
    download_redlisted_species,
)
from scripts.grid_proximity import (
    analyse_grid_proximity,
)
from scripts.potential import (
    calculate_project_potential,
)
from scripts.bos import (
    prepare_bos_analysis,
    prepare_bos_landcover,
    prepare_bos_override_layers,
    prepare_bos_wetland,
    create_non_overlapping_bos_layers,
    summarise_bos_coverage,
    create_bos_coverage_layer,   
)
from scripts.municipality import (
    analyse_municipality_politics,
)
from scripts.meteorology import (
    calculate_average_wind_speed,
    calculate_site_raster_mean,
    read_site_load_values,
)
from scripts.solar_position import (
    calculate_average_solar_elevation,
)
from scripts.reporting import (
    append_meteorology_summary,
    append_municipality_politics_summary,
    append_solar_position_summary,
    append_solar_resource_summary,
    create_site_summary,
    append_bos_summary,
    append_project_potential_summary,
    append_grid_proximity_summary,
    append_soil_depth_summary,
    append_custom_estates_summary
)
from scripts.solar_resource import (
    apply_strang_fallback,
    collect_solargis_resources,
    get_site_centroid_wgs84,
)
from qgis.core import (QgsApplication, 
    Qgis, 
    QgsProject
)
from scripts.country_config import load_country_config
from scripts.basemap_settings import BASEMAPS
from scripts.map_project import (
    prepare_map_project,
    add_basemaps,
    add_analysis_outputs,
    add_supporting_outputs,
    add_country_outputs,
    save_map_project,
    add_bos_coverage,
    add_redlisted_species,
)
from scripts.constraints import (
    clip_country_layers,
    buffer_country_layers,
    save_country_layer_outputs,
    create_country_layer_centroids,
    subtract_solar_constraints,
    subtract_ineligible_terrain,
    process_solar_holes,
    shrink_solar_candidate_area,
    dissolve_solar_candidate_area,
    save_solar_candidate_parts,
    subtract_wind_constraints,
    dissolve_wind_candidate_area,
    save_wind_candidate_parts,
    calculate_candidate_areas
)
from scripts.terrain import (
    create_terrain_grid,
    extract_grid_dem_tiles,
    calculate_slope_aspect,
    extract_ineligible_terrain,
    buffer_ineligible_points,
    merge_ineligible_polygons_by_cell,
    dissolve_ineligible_polygons,
    buffer_ineligible_polygons,
    merge_ineligible_polygons_by_aspect,
    merge_buffered_ineligible_terrain,
    save_aspect_outputs,
    clean_ineligible_terrain,
    split_cleaned_terrain,
    filter_ineligible_terrain_by_area,
    create_contour_lines
)
from scripts.dem import (
    select_dem_tiles,
    merge_dem_tiles,
    clip_dem_to_site
)
from scripts.qgis_setup import initialize_qgis, shutdown_qgis
from scripts.user_settings import UserSettings
from scripts.paths import get_paths
from scripts.crs import resolve_working_crs
from scripts.site_context import (
    create_site_buffers,
    extract_neighbouring_estates,
    group_neighbouring_estates,
    dissolve_neighbouring_groups,
    split_neighbouring_groups,
    reproject_neighbouring_groups,
    merge_neighbouring_groups,
    subtract_analysis_site,
    save_neighbouring_estates,
    get_layer_extent
)
from scripts.site_selection import (
    select_site_source,
    parse_estate,
    sequential_search,
    extract_estate_features,
    merge_estate_features,
    dissolve_estate_features,
    split_estate_to_singleparts,
    reproject_estate,
    calculate_estate_area,
    prepare_custom_polygon_source,
)


estate = ""

#custom_polygon = None
custom_polygon = (r"C:/Users/tobia/Documents/test.shp")

def main():

    settings = UserSettings()

    run_id = create_run_id()

    print(
        f"Analysis run ID: {run_id}"
    )

    country_config = load_country_config(
        country_code=settings.country_code,
    )
    paths = get_paths()

    print("Starting solar site analysis...")

    qgs = initialize_qgis()

    cleanup_targets = []
    cleanup_folder_path = None

    try:

        print(f"QGIS version: {Qgis.QGIS_VERSION}")

        buffer_algorithm = (
            QgsApplication.processingRegistry()
            .algorithmById("native:buffer")
        )

        if buffer_algorithm is None:
            raise RuntimeError(
                "QGIS Processing failed to initialise."
            )

        print("QGIS Processing is ready.")

        site_source = select_site_source(
            estate,
            custom_polygon,
        )

        if site_source["type"] == "estate":

            match = parse_estate(
                site_source["estate"]
            )

            print(
                f"Searching for estate: {match}"
            )

            row_indices = sequential_search(
                paths["csv_file"],
                match,
            )

            if row_indices is None:
                raise ValueError(
                    f"No estate found for: "
                    f"{site_source['estate']}"
                )

            print(
                f"Estate located at indices: "
                f"{row_indices}"
            )

            site_data = extract_estate_features(
                match=match,
                row_indices=row_indices,
                estates_layer_path=paths[
                    "estates_layer"
                ],
                output_root=paths["pot_path"],
                run_id=run_id,
            )

            site_data["source_type"] = "estate"
            site_data["match"] = match

        elif site_source["type"] == "custom_polygon":

            site_data = prepare_custom_polygon_source(
                custom_polygon_path=site_source[
                    "polygon"
                ],
                output_root=paths["pot_path"],
                run_id=run_id,
            )

            print(
                f"Custom polygon selected: "
                f"{site_data['source_path']}"
            )

        else:
            raise ValueError(
                f"Unsupported site-source type: "
                f"{site_source['type']}"
            )

        merged_layer_path = merge_estate_features(
            extracted_layers=site_data["extracted_layers"],
            temp_path=site_data["temp_path"],
        )

        dissolved_layer_path = dissolve_estate_features(
            merged_layer_path=merged_layer_path,
            temp_path=site_data["temp_path"],
        )

        singleparts_layer_path = split_estate_to_singleparts(
            dissolved_layer_path=dissolved_layer_path,
            temp_path=site_data["temp_path"],
        )

        working_crs = resolve_working_crs(
            settings=settings,
            site_path=singleparts_layer_path,
        )

        reprojected_layer_path = reproject_estate(
            singleparts_layer_path=singleparts_layer_path,
            temp_path=site_data["temp_path"],
            target_crs=working_crs,
        )

        site_layer_path = calculate_estate_area(
            reprojected_layer_path=reprojected_layer_path,
            folder_path=site_data["folder_path"],
        )

        buffer_paths = create_site_buffers(
            site_layer_path=site_layer_path,
            temp_path=site_data["temp_path"],
        )

        custom_estates_result = None

        if site_source["type"] == "custom_polygon":

            if (
                paths.get("estates_layer")
                and paths.get("csv_file")
            ):
                try:
                    custom_estates_result = (
                        analyse_custom_estates(
                            analysis_layer_path=(
                                site_layer_path
                            ),
                            estates_layer_path=paths[
                                "estates_layer"
                            ],
                            csv_file=paths[
                                "csv_file"
                            ],
                        )
                    )

                except (
                    ValueError,
                    RuntimeError,
                ) as error:
                    print(
                        "Custom-estate analysis failed, "
                        "but processing will continue: "
                        f"{error}"
                    )

                    custom_estates_result = {
                        "status": "error",
                        "estates": [],
                        "error": str(error),
                    }

            else:
                print(
                    "Custom-estate analysis unavailable: "
                    "no estate source is configured."
                )

                custom_estates_result = {
                    "status": "unavailable",
                    "estates": [],
                }

        # -------------------------------------------------
        # Red-listed species observations
        # -------------------------------------------------

        redlisted_species_settings = getattr(
            country_config,
            "REDLISTED_SPECIES_SETTINGS",
            None,
        )

        redlisted_species_result = None

        if redlisted_species_settings:

            try:
                redlisted_species_result = (
                    download_redlisted_species(
                        context_polygon_path=(
                            site_layer_path
                        ),
                        folder_path=site_data[
                            "folder_path"
                        ],
                        temp_path=site_data[
                            "temp_path"
                        ],
                        settings=(
                            redlisted_species_settings
                        ),
                    )
                )

            except RuntimeError as error:
                print(
                    "Red-listed species download failed, "
                    "but the analysis will continue: "
                    f"{error}"
                )

                redlisted_species_result = {
                    "status": "error",
                    "output_path": None,
                    "feature_count": 0,
                    "error": str(error),
                }

        else:
            print(
                "Red-listed species download skipped: "
                "not configured for this country."
            )

            redlisted_species_result = {
                "status": "unavailable",
                "output_path": None,
                "feature_count": 0,
            }

        neighbouring_estates_path = extract_neighbouring_estates(
            estates_layer_path=paths["estates_layer"],
            hundred_m_buffer_path=buffer_paths["100m"],
            folder_path=site_data["folder_path"],
        )

        neighbour_groups = group_neighbouring_estates(
            neighbouring_estates_path=neighbouring_estates_path,
        )

        dissolved_neighbour_paths = dissolve_neighbouring_groups(
            neighbour_groups=neighbour_groups,
            temp_path=site_data["temp_path"],
        )

        singlepart_neighbour_paths = split_neighbouring_groups(
            dissolved_neighbour_paths=dissolved_neighbour_paths,
            temp_path=site_data["temp_path"],
        )

        reprojected_neighbour_paths = reproject_neighbouring_groups(
            singlepart_neighbour_paths=singlepart_neighbour_paths,
            temp_path=site_data["temp_path"],
            target_crs=working_crs,
        )

        merged_neighbours_path = merge_neighbouring_groups(
            reprojected_neighbour_paths=reprojected_neighbour_paths,
            temp_path=site_data["temp_path"],
            target_crs=working_crs,
        )

        neighbours_difference_path = subtract_analysis_site(
            merged_neighbours_path=merged_neighbours_path,
            site_layer_path=site_layer_path,
            temp_path=site_data["temp_path"],
        )

        final_neighbours_path = save_neighbouring_estates(
            neighbours_difference_path=neighbours_difference_path,
            folder_path=site_data["folder_path"],
        )

        dem_search_extent = get_layer_extent(
            layer_path=site_layer_path,
        )

        dem_tile_paths = select_dem_tiles(
            site_extent=dem_search_extent,
            data_path=paths["data_path"],
            dem_path=paths["path_dem"],
            temp_path=site_data["temp_path"],
            dem_index_crs=paths["dem_index_crs"],
        )

        merged_dem_path = merge_dem_tiles(
            dem_tile_paths=dem_tile_paths,
            temp_path=site_data["temp_path"],
        )

        clipped_dem_path = clip_dem_to_site(
            merged_dem_path=merged_dem_path,
            site_layer_path=site_layer_path,
            folder_path=site_data["folder_path"],
            target_crs=working_crs,
        )

        terrain_grid_path = create_terrain_grid(
            site_layer_path=site_layer_path,
            temp_path=site_data["temp_path"],
        )

        terrain_dem_paths = extract_grid_dem_tiles(
            terrain_grid_path=terrain_grid_path,
            clipped_dem_path=clipped_dem_path,
            temp_path=site_data["temp_path"],
        )

        terrain_results = calculate_slope_aspect(
            terrain_dem_paths=terrain_dem_paths,
            temp_path=site_data["temp_path"],
        )

        ineligible_point_paths = extract_ineligible_terrain(
            terrain_results=terrain_results,
            temp_path=site_data["temp_path"],
            slope_thresholds=settings.slope_thresholds,
        )

        ineligible_polygon_paths = buffer_ineligible_points(
            ineligible_point_paths=ineligible_point_paths,
            temp_path=site_data["temp_path"],
        )

        merged_ineligible_paths = merge_ineligible_polygons_by_cell(
            ineligible_polygon_paths=ineligible_polygon_paths,
            temp_path=site_data["temp_path"],
            target_crs=working_crs,
        )

        dissolved_ineligible_paths = dissolve_ineligible_polygons(
            merged_ineligible_paths=merged_ineligible_paths,
            temp_path=site_data["temp_path"],
        )

        buffered_ineligible_paths = buffer_ineligible_polygons(
            dissolved_ineligible_paths=dissolved_ineligible_paths,
            temp_path=site_data["temp_path"],
        )

        aspect_polygon_paths = merge_ineligible_polygons_by_aspect(
            ineligible_polygon_paths=ineligible_polygon_paths,
            temp_path=site_data["temp_path"],
            target_crs=working_crs,
        )

        merged_ineligible_terrain_path = merge_buffered_ineligible_terrain(
            buffered_ineligible_paths=buffered_ineligible_paths,
            temp_path=site_data["temp_path"],
            target_crs=working_crs,
        )

        final_aspect_paths = save_aspect_outputs(
            aspect_polygon_paths=aspect_polygon_paths,
            folder_path=site_data["folder_path"],
        )

        cleaned_ineligible_terrain_path = clean_ineligible_terrain(
            merged_ineligible_terrain_path=merged_ineligible_terrain_path,
            temp_path=site_data["temp_path"],
        )

        singlepart_ineligible_terrain_path = split_cleaned_terrain(
            cleaned_ineligible_terrain_path=cleaned_ineligible_terrain_path,
            temp_path=site_data["temp_path"],
        )

        filtered_ineligible_terrain_path = filter_ineligible_terrain_by_area(
            singlepart_ineligible_terrain_path=singlepart_ineligible_terrain_path,
            temp_path=site_data["temp_path"],
            folder_path=site_data["folder_path"],
            min_area_m2=settings.min_ineligible_patch_area_m2,
        )

        contour_lines_path = create_contour_lines(
            merged_dem_path=merged_dem_path,
            temp_path=site_data["temp_path"],
            folder_path=site_data["folder_path"],
            target_crs=working_crs,
            interval_m=settings.contour_interval_m,
        )

        clipped_country_layers = clip_country_layers(
            layer_definitions=country_config.LAYERS,
            data_path=paths["data_path"],
            context_polygon_path=buffer_paths["5km"],
            temp_path=site_data["temp_path"],
            target_crs=working_crs,
        )

        prepared_country_layers = buffer_country_layers(
            clipped_country_layers=clipped_country_layers,
            temp_path=site_data["temp_path"],
        )

        grid_proximity_result = None

        country_layer_outputs = save_country_layer_outputs(
            prepared_country_layers=prepared_country_layers,
            folder_path=site_data["folder_path"],
        )

        country_layer_outputs = create_country_layer_centroids(
            country_layer_outputs=country_layer_outputs,
            folder_path=site_data["folder_path"],
        )

        soil_depth_result = analyse_soil_depth_by_type(
            analysis_layer_path=site_layer_path,
            country_layer_outputs=country_layer_outputs,
            data_path=paths["data_path"],
            temp_path=site_data["temp_path"],
            settings=getattr(
                country_config,
                "SOIL_DEPTH_SETTINGS",
                None,
            ),
        )

        solar_remaining_path = subtract_solar_constraints(
            site_layer_path=site_layer_path,
            country_layer_outputs=country_layer_outputs,
            temp_path=site_data["temp_path"],
        )

        solar_terrain_remaining_path = subtract_ineligible_terrain(
            solar_remaining_path=solar_remaining_path,
            filtered_ineligible_terrain_path=filtered_ineligible_terrain_path,
            temp_path=site_data["temp_path"],
        )

        solar_holes_processed_path = process_solar_holes(
            solar_terrain_remaining_path=solar_terrain_remaining_path,
            temp_path=site_data["temp_path"],
            fill_holes=settings.fill_solar_holes,
        )

        solar_shrunk_path = shrink_solar_candidate_area(
            solar_holes_processed_path=solar_holes_processed_path,
            temp_path=site_data["temp_path"],
            inward_distance_m=settings.solar_inward_buffer_m,
        )

        solar_terrain_rechecked_path = subtract_ineligible_terrain(
            solar_remaining_path=solar_shrunk_path,
            filtered_ineligible_terrain_path=filtered_ineligible_terrain_path,
            temp_path=site_data["temp_path"],
            output_filename="almost_done_solar_igen.shp",
        )

        solar_dissolved_path = dissolve_solar_candidate_area(
            solar_terrain_rechecked_path=solar_terrain_rechecked_path,
            temp_path=site_data["temp_path"],
        )

        solar_candidate_path = save_solar_candidate_parts(
            solar_dissolved_path=solar_dissolved_path,
            folder_path=site_data["folder_path"],
        )

        solar_summary = calculate_candidate_areas(
            candidate_path=solar_candidate_path,
            technology="solar",
        )

        wind_remaining_path = subtract_wind_constraints(
            site_layer_path=site_layer_path,
            country_layer_outputs=country_layer_outputs,
            temp_path=site_data["temp_path"],
        )

        wind_dissolved_path = dissolve_wind_candidate_area(
            wind_remaining_path=wind_remaining_path,
            temp_path=site_data["temp_path"],
        )

        wind_candidate_path = save_wind_candidate_parts(
            wind_dissolved_path=wind_dissolved_path,
            folder_path=site_data["folder_path"],
        )

        wind_summary = calculate_candidate_areas(
            candidate_path=wind_candidate_path,
            technology="wind",
        )

        project_potential = calculate_project_potential(
            solar_candidate_path=solar_candidate_path,
            wind_candidate_path=wind_candidate_path,
            settings=settings,
        )

        map_data = prepare_map_project(
            working_crs=working_crs,
            title=site_data["folder_name"],
        )

        basemap_layer_ids = add_basemaps(
            map_data=map_data,
            basemap_definitions=BASEMAPS,
        )

        analysis_layer_ids = add_analysis_outputs(
            map_data=map_data,
            site_layer_path=site_layer_path,
            solar_candidate_path=solar_candidate_path,
            wind_candidate_path=wind_candidate_path,
        )

        country_map_layer_ids = add_country_outputs(
            map_data=map_data,
            country_layer_outputs=country_layer_outputs,
            style_resolver=getattr(
                country_config,
                "get_map_style",
                None,
            ),
            svg_path=paths["svg_path"],
        )

        grid_proximity_result = analyse_grid_proximity(
            analysis_layer_path=site_layer_path,
            country_layer_outputs=country_layer_outputs,
            grid_settings=getattr(
                country_config,
                "GRID_PROXIMITY_SETTINGS",
                None,
            ),
        )

        supporting_layer_ids = add_supporting_outputs(
            map_data=map_data,
            neighbouring_estates_path=final_neighbours_path,
            ineligible_terrain_path=filtered_ineligible_terrain_path,
            contour_lines_path=contour_lines_path,
        )

        redlisted_species_layer_id = (
            add_redlisted_species(
                map_data=map_data,
                redlisted_species_result=(
                    redlisted_species_result
                ),
            )
        )

        site_summary = create_site_summary(
            site_layer_path=site_layer_path,
            folder_path=site_data["folder_path"],
            folder_name=site_data["folder_name"],
            summary_settings=getattr(
                country_config,
                "SITE_SUMMARY",
                None,
            ),
        )

        if site_source["type"] == "custom_polygon":
            custom_estates_report_path = (
                append_custom_estates_summary(
                    folder_path=site_data[
                        "folder_path"
                    ],
                    folder_name=site_data[
                        "folder_name"
                    ],
                    custom_estates_result=(
                        custom_estates_result
                    ),
                )
            )

        soil_depth_report_path = append_soil_depth_summary(
            folder_path=site_data["folder_path"],
            folder_name=site_data["folder_name"],
            soil_depth_result=soil_depth_result,
            settings=getattr(
                country_config,
                "SOIL_DEPTH_SETTINGS",
                None,
            ),
        )

        potential_report_path = (
            append_project_potential_summary(
                folder_path=site_data["folder_path"],
                folder_name=site_data["folder_name"],
                project_potential=project_potential,
            )
        )

        grid_report_path = (
            append_grid_proximity_summary(
                folder_path=site_data["folder_path"],
                folder_name=site_data["folder_name"],
                grid_proximity_result=(
                    grid_proximity_result
                ),
            )
        )

        # -------------------------------------------------
        # Global Solar Atlas resource data
        # -------------------------------------------------

        site_centroid = get_site_centroid_wgs84(
            site_layer_path=site_layer_path,
        )

        solar_resource_data = collect_solargis_resources(
            raster_paths=paths["solargis_rasters"],
            longitude=site_centroid["longitude"],
            latitude=site_centroid["latitude"],
        )

        solar_resource_data = apply_strang_fallback(
            solar_resource_data=solar_resource_data,
            longitude=site_centroid["longitude"],
            latitude=site_centroid["latitude"],
            output_folder=site_data["folder_path"],
        )

        solar_report_path = append_solar_resource_summary(
            folder_path=site_data["folder_path"],
            folder_name=site_data["folder_name"],
            solar_resource_data=solar_resource_data,
        )

        average_solar_elevation = (
            calculate_average_solar_elevation(
                latitude=site_centroid["latitude"],
                longitude=site_centroid["longitude"],
                reference_year=settings.solar_reference_year,
                start_month=settings.solar_start_month,
                start_day=settings.solar_start_day,
                end_month=settings.solar_end_month,
                end_day=settings.solar_end_day,
            )
        )

        solar_position_report_path = (
            append_solar_position_summary(
                folder_path=site_data["folder_path"],
                folder_name=site_data["folder_name"],
                average_elevation=average_solar_elevation,
                reference_year=settings.solar_reference_year,
                start_month=settings.solar_start_month,
                start_day=settings.solar_start_day,
                end_month=settings.solar_end_month,
                end_day=settings.solar_end_day,
            )
        )

        # -------------------------------------------------
        # Meteorological data: average wind speed
        # -------------------------------------------------

        meteorology_settings = getattr(
            country_config,
            "METEOROLOGY_SETTINGS",
            {},
        )

        average_wind_speed = (
            calculate_average_wind_speed(
                site_layer_path=site_layer_path,
                data_path=paths["data_path"],
                temp_path=site_data["temp_path"],
                wind_settings=meteorology_settings.get(
                    "wind_speed"
                ),
            )
        )

        wind_load_result = read_site_load_values(
            site_layer_path=site_layer_path,
            field_name=meteorology_settings.get(
                "wind_load_field"
            ),
            result_name="Wind load",
            unit="m/s",
            source_name="Boverket",
        )

        snow_load_result = read_site_load_values(
            site_layer_path=site_layer_path,
            field_name=meteorology_settings.get(
                "snow_load_field"
            ),
            result_name="Snow load",
            unit="kN/m²",
            source_name="Boverket",
        )

        # -------------------------------------------------
        # Meteorological raster data
        # -------------------------------------------------

        raster_data_settings = meteorology_settings.get(
            "raster_data",
            {},
        )

        humidity_result = calculate_site_raster_mean(
            site_layer_path=site_layer_path,
            data_path=paths["data_path"],
            temp_path=site_data["temp_path"],
            raster_settings=raster_data_settings.get(
                "humidity"
            ),
            output_name="meteorology_humidity.tif",
        )

        air_pressure_result = calculate_site_raster_mean(
            site_layer_path=site_layer_path,
            data_path=paths["data_path"],
            temp_path=site_data["temp_path"],
            raster_settings=raster_data_settings.get(
                "air_pressure"
            ),
            output_name="meteorology_air_pressure.tif",
        )

        # -------------------------------------------------
        # Temperature provider selection
        # -------------------------------------------------

        solargis_temperature = solar_resource_data.get(
            "temperature",
            {},
        )

        if solargis_temperature.get("value") is not None:
            temperature_result = {
                "name": "Average air temperature",
                "value": solargis_temperature["value"],
                "unit": solargis_temperature["unit"],
                "source": solargis_temperature["source"],
                "status": solargis_temperature["status"],
                "output_path": solargis_temperature.get(
                    "raster_path"
                ),
            }

            print(
                "Meteorological temperature supplied by "
                f"{temperature_result['source']}: "
                f"{temperature_result['value']:.2f} "
                f"{temperature_result['unit']}"
            )

        else:
            print(
                "SolarGIS temperature unavailable. "
                "Trying the country-specific fallback..."
            )

            temperature_result = (
                calculate_site_raster_mean(
                    site_layer_path=site_layer_path,
                    data_path=paths["data_path"],
                    temp_path=site_data["temp_path"],
                    raster_settings=raster_data_settings.get(
                        "temperature_fallback"
                    ),
                    output_name=(
                        "meteorology_temperature.tif"
                    ),
                )
            )

        # -------------------------------------------------
        # Monthly snow depth
        # -------------------------------------------------

        snow_depth_results = {}

        snow_depth_settings = raster_data_settings.get(
            "snow_depth",
            {},
        )

        for month_name, month_settings in (
            snow_depth_settings.items()
        ):
            output_name = (
                "meteorology_snow_depth_"
                f"{month_name.lower()}.tif"
            )

            snow_depth_results[month_name] = (
                calculate_site_raster_mean(
                    site_layer_path=site_layer_path,
                    data_path=paths["data_path"],
                    temp_path=site_data["temp_path"],
                    raster_settings=month_settings,
                    output_name=output_name,
                )
            )

        meteorology_report_path = (
            append_meteorology_summary(
                folder_path=site_data["folder_path"],
                folder_name=site_data["folder_name"],
                wind_speed_result=average_wind_speed,
                wind_load_result=wind_load_result,
                snow_load_result=snow_load_result,
                humidity_result=humidity_result,
                temperature_result=temperature_result,
                air_pressure_result=air_pressure_result,
                snow_depth_results=snow_depth_results,
            )
        )

        # -------------------------------------------------
        # Municipality political control
        # -------------------------------------------------

        political_result = (
            analyse_municipality_politics(
                site_layer_path=site_layer_path,
                data_path=paths["data_path"],
                political_settings=getattr(
                    country_config,
                    "POLITICAL_SETTINGS",
                    None,
                ),
            )
        )

        political_report_path = (
            append_municipality_politics_summary(
                folder_path=site_data["folder_path"],
                folder_name=site_data["folder_name"],
                political_result=political_result,
            )
        )

        # -------------------------------------------------
        # BoS land-cover analysis
        # -------------------------------------------------

        bos_settings = getattr(
            country_config,
            "BOS_SETTINGS",
            None,
        )

        bos_result = prepare_bos_analysis(
            analysis_layer_path=site_layer_path,
            bos_settings=bos_settings,
        )

        soil_depth_result = None
        bos_landcover_result = None
        bos_wetland_result = None
        bos_override_results = None
        bos_priority_result = None
        bos_summary = None
        bos_coverage_path = None

        if bos_result["status"] == "ready":
            bos_landcover_result = (
                prepare_bos_landcover(
                    analysis_layer_path=site_layer_path,
                    data_path=paths["data_path"],
                    temp_path=site_data["temp_path"],
                    bos_settings=bos_settings,
                )
            )

            bos_wetland_result = (
                prepare_bos_wetland(
                    analysis_layer_path=site_layer_path,
                    landcover_layer_path=(
                        bos_landcover_result[
                            "landcover_path"
                        ]
                    ),
                    data_path=paths["data_path"],
                    temp_path=site_data["temp_path"],
                    bos_settings=bos_settings,
                )
            )

            bos_override_results = (
                prepare_bos_override_layers(
                    analysis_layer_path=site_layer_path,
                    data_path=paths["data_path"],
                    temp_path=site_data["temp_path"],
                    bos_settings=bos_settings,
                )
            )

            bos_priority_result = (
                create_non_overlapping_bos_layers(
                    landcover_path=(
                        bos_landcover_result[
                            "landcover_path"
                        ]
                    ),
                    wetland_path=(
                        bos_wetland_result[
                            "output_path"
                        ]
                    ),
                    rocky_terrain_path=(
                        bos_override_results[
                            "rocky_terrain"
                        ]["output_path"]
                    ),
                    peat_quarry_path=(
                        bos_override_results[
                            "peat_quarry"
                        ]["output_path"]
                    ),
                    temp_path=site_data["temp_path"],
                )
            )

            bos_summary = summarise_bos_coverage(
                analysis_layer_path=site_layer_path,
                bos_priority_result=bos_priority_result,
                bos_settings=bos_settings,
            )

            bos_summary = summarise_bos_coverage(
                analysis_layer_path=site_layer_path,
                bos_priority_result=bos_priority_result,
                bos_settings=bos_settings,
            )

            bos_coverage_path = create_bos_coverage_layer(
                analysis_layer_path=site_layer_path,
                bos_priority_result=bos_priority_result,
                bos_settings=bos_settings,
                folder_path=site_data["folder_path"],
                temp_path=site_data["temp_path"],
            )

        bos_report_path = append_bos_summary(
            folder_path=site_data["folder_path"],
            folder_name=site_data["folder_name"],
            bos_summary=bos_summary,
        )

        bos_map_layer_id = add_bos_coverage(
            map_data=map_data,
            bos_coverage_path=bos_coverage_path,
        )

        # -------------------------------------------------
        # Package permanent vector outputs
        # -------------------------------------------------

        final_layer_definitions = [
            {
                "key": "analysis_site",
                "name": "Analysis site",
                "path": site_layer_path,
            },
            {
                "key": "solar_candidate",
                "name": "Solar candidate area",
                "path": solar_candidate_path,
            },
            {
                "key": "wind_candidate",
                "name": "Wind candidate area",
                "path": wind_candidate_path,
            },
            {
                "key": "neighbouring_estates",
                "name": "Neighbouring estates",
                "path": final_neighbours_path,
            },
            {
                "key": "ineligible_terrain",
                "name": "Ineligible terrain",
                "path": filtered_ineligible_terrain_path,
            },
            {
                "key": "contour_lines",
                "name": "Contour lines",
                "path": contour_lines_path,
            },
            {
                "key": "bos_coverage",
                "name": "BoS coverage",
                "path": bos_coverage_path,
            },
        ]

        # Add every configured country output.
        for number, layer_output in enumerate(
            country_layer_outputs,
            start=1,
        ):
            definition = layer_output[
                "definition"
            ]

            final_layer_definitions.append(
                {
                    "key": (
                        f"country_{number:03d}"
                    ),
                    "name": definition["name"],
                    "path": layer_output.get(
                        "output_path"
                    ),
                }
            )

        # Add the downloaded red-listed observations when
        # the service returned a valid output.
        redlisted_output_path = None

        if redlisted_species_result:
            redlisted_output_path = (
                redlisted_species_result.get(
                    "output_path"
                )
            )

        final_layer_definitions.append(
            {
                "key": "redlisted_species",
                "name": (
                    "Red-listed species observations"
                ),
                "path": redlisted_output_path,
            }
        )

        output_package = create_output_geopackage(
            layer_definitions=final_layer_definitions,
            folder_path=site_data["folder_path"],
            folder_name=site_data["folder_name"],
        )

        repointed_project_layers = (
            repoint_project_layers_to_geopackage(
                output_package=output_package,
            )
        )

        project_path = save_map_project(
            map_data=map_data,
            folder_path=site_data["folder_path"],
            folder_name=site_data["folder_name"],
        )

        manifest_path = create_analysis_manifest(
            folder_path=site_data["folder_path"],
            folder_name=site_data["folder_name"],
            run_id=run_id,
            output_package=output_package,
            project_path=project_path,
            site_source=site_source,
            settings=settings,
            country_config=country_config,
            working_crs=working_crs,
        )

        report_path = os.path.join(
            site_data["folder_path"],
            f"prints ({site_data['folder_name']}).txt",
        )

        cleanup_plan = cleanup_analysis_outputs(
            folder_path=site_data["folder_path"],
            project_path=project_path,
            geopackage_path=output_package[
                "gpkg_path"
            ],
            report_path=report_path,
            manifest_path=manifest_path,
            dry_run=True,
        )

        cleanup_targets = cleanup_plan[
            "targets"
        ]

        cleanup_folder_path = site_data[
            "folder_path"
        ]

        print(
            f"Final analysis package prepared: "
            f"{site_data['folder_path']}"
        )

    finally:
        neighbour_groups = None

        # Release references to layer-tree groups before
        # clearing them.
        map_data = None

        QgsProject.instance().clear()

        gc.collect()

        shutdown_qgis(qgs)

    print("QGIS shut down cleanly.")

    if (
        cleanup_targets
        and cleanup_folder_path
    ):
        remove_cleanup_targets(
            folder_path=cleanup_folder_path,
            removal_targets=cleanup_targets,
        )


if __name__ == "__main__":
    main()