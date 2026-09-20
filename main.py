import gc

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
    calculate_estate_area
)


estate = "kävlinge ålstorp 19:63"

custom_polygon = None


def main():

    settings = UserSettings()
    country_config = load_country_config(
        country_code=settings.country_code,
    )
    paths = get_paths()

    print("Starting solar site analysis...")

    qgs = initialize_qgis()

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

                print(
                    "No estate found by that entry."
                )

            else:

                print(
                    f"Estate located at indices: "
                    f"{row_indices}"
                )
            
            site_data = extract_estate_features(
                match=match,
                row_indices=row_indices,
                estates_layer_path=paths["estates_layer"],
                output_root=paths["pot_path"],
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

            country_layer_outputs = save_country_layer_outputs(
                prepared_country_layers=prepared_country_layers,
                folder_path=site_data["folder_path"],
            )

            country_layer_outputs = create_country_layer_centroids(
                country_layer_outputs=country_layer_outputs,
                folder_path=site_data["folder_path"],
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
            )

            supporting_layer_ids = add_supporting_outputs(
                map_data=map_data,
                neighbouring_estates_path=final_neighbours_path,
                ineligible_terrain_path=filtered_ineligible_terrain_path,
                contour_lines_path=contour_lines_path,
            )

            project_path = save_map_project(
                map_data=map_data,
                folder_path=site_data["folder_path"],
                folder_name=site_data["folder_name"],
            )

            print(
                f"Estate features extracted to: "
                f"{site_data['temp_path']}"
            )

        elif site_source["type"] == "custom_polygon":

            print(
                "Custom polygon selected."
            )

    finally:
        neighbour_groups = None

        # Release references to layer-tree groups before clearing them.
        map_data = None

        QgsProject.instance().clear()

        gc.collect()

        shutdown_qgis(qgs)

    print("QGIS shut down cleanly.")


if __name__ == "__main__":
    main()