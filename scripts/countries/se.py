import os

"""
Swedish dataset configuration.

Buffer distances are screening parameters inherited from Anna.
All distances are expressed in metres.

Sources are currently filenames relative to the configured
data directory. They can later be replaced with database sources.

A zero buffer means no additional buffer is applied.
It does not, by itself, determine whether a layer is an exclusion.
"""

COUNTRY_CODE = "SE"
COUNTRY_NAME = "Sweden"


def _layer(
    source,
    name,
    *,
    solar_buffer_m,
    wind_buffer_m,
):
    """
    Create a layer definition with named fields.

    The keyword-only buffer arguments make the two distances
    explicit when adding or editing entries.
    """

    return {
        "source": source,
        "name": name,
        "solar_buffer_m": solar_buffer_m,
        "wind_buffer_m": wind_buffer_m,
    }


LAYERS = [
    # Power infrastructure
    _layer(
        "powerlines-300-500.shp", "300–500 kV ledning",
        solar_buffer_m=55, wind_buffer_m=300,
    ),
    _layer(
        "powerlines-underground.shp", "Nedgrävd ledning",
        solar_buffer_m=15, wind_buffer_m=15,
    ),
    _layer(
        "powerlines-170-220.shp", "170–220 kV ledning",
        solar_buffer_m=55, wind_buffer_m=300,
    ),
    _layer(
        "powerlines-80-170.shp", "80–170 kV ledning",
        solar_buffer_m=55, wind_buffer_m=300,
    ),
    _layer(
        "powerlines-10-80.shp", "10–80 kV ledning",
        solar_buffer_m=55, wind_buffer_m=300,
    ),
    _layer(
        "powerlines-null.shp", "Okänd ledning",
        solar_buffer_m=55, wind_buffer_m=300,
    ),

    # Background data and other features
    _layer(
        "estates.shp", "Fastighetskarta",
        solar_buffer_m=0, wind_buffer_m=0,
    ),
    _layer(
        "soil_types.shp", "Jordtyper",
        solar_buffer_m=0, wind_buffer_m=0,
    ),
    _layer(
        "power_stations_poly.shp", "Transformatorstation",
        solar_buffer_m=15, wind_buffer_m=300,
    ),
    _layer(
        "nature_memory_points_poly.shp", "Naturminne",
        solar_buffer_m=10, wind_buffer_m=10,
    ),
    _layer(
        "misc_poly.shp", "Övrigt",
        solar_buffer_m=0, wind_buffer_m=0,
    ),
    _layer(
        "hiking_trails.shp", "Vandringsled",
        solar_buffer_m=50, wind_buffer_m=300,
    ),
    _layer(
        "peat_extractions_poly.shp", "Torvtäkt",
        solar_buffer_m=0, wind_buffer_m=0,
    ),
    _layer(
        "weather_station_temp_poly.shp", "Väderstation (temperatur)",
        solar_buffer_m=100, wind_buffer_m=100,
    ),
    _layer(
        "weather_station_wind_poly.shp", "Väderstation (vind)",
        solar_buffer_m=100, wind_buffer_m=3000,
    ),

    # Transport
    _layer(
        "railway.shp", "Järnväg",
        solar_buffer_m=15, wind_buffer_m=350,
    ),
    _layer(
        "roads.shp", "Väg",
        solar_buffer_m=8, wind_buffer_m=50,
    ),
    _layer(
        "bike_lane.shp", "Cykelbana",
        solar_buffer_m=0, wind_buffer_m=50,
    ),
    _layer(
        "rest_stop_poly.shp", "Rastplats",
        solar_buffer_m=50, wind_buffer_m=50,
    ),

    # Nature, cultural interests and water
    _layer(
        "swamp_forest.shp", "Sumpskog",
        solar_buffer_m=0, wind_buffer_m=0,
    ),
    _layer(
        "vmi_low.shp", "VMI, klass 3–4",
        solar_buffer_m=0, wind_buffer_m=0,
    ),
    _layer(
        "cultural_reserve.shp", "Kulturmiljövård (MB3, kap. 6)",
        solar_buffer_m=0, wind_buffer_m=0,
    ),
    _layer(
        "outdoor_life_areas.shp",
        "Friluftsliv (rörligt, MB3–4, kap. 1–2, 6)",
        solar_buffer_m=50, wind_buffer_m=50,
    ),
    _layer(
        "protected_water_courses.shp",
        "Skyddsområde (vattendrag, MB4, kap. 6)",
        solar_buffer_m=0, wind_buffer_m=0,
    ),
    _layer(
        "noble_forest.shp", "Ädelskog",
        solar_buffer_m=0, wind_buffer_m=0,
    ),
    _layer(
        "water_flow_poly.shp", "Flödesriktning",
        solar_buffer_m=0, wind_buffer_m=0,
    ),
    _layer(
        "water_courses.shp", "Vattendrag",
        solar_buffer_m=15, wind_buffer_m=50,
    ),
    _layer(
        "water_surfaces.shp", "Sjö/större vattendrag",
        solar_buffer_m=50, wind_buffer_m=50,
    ),
    _layer(
        "ancient_remains_points_poly.shp", "Lämning",
        solar_buffer_m=10, wind_buffer_m=10,
    ),
    _layer(
        "ancient_remains_lines.shp", "Lämning",
        solar_buffer_m=10, wind_buffer_m=10,
    ),
    _layer(
        "ancient_remains_polygons.shp", "Lämning",
        solar_buffer_m=10, wind_buffer_m=10,
    ),
    _layer(
        "landslide_slope-instability.shp", "Rasrisk",
        solar_buffer_m=6, wind_buffer_m=6,
    ),
    _layer(
        "natura2000.shp", "Natura 2000",
        solar_buffer_m=50, wind_buffer_m=550,
    ),
    _layer(
        "inaccessable.shp", "Otillgängligt område",
        solar_buffer_m=6, wind_buffer_m=6,
    ),
    _layer(
        "rich_birdlife.shp", "Rikt fågelliv",
        solar_buffer_m=50, wind_buffer_m=550,
    ),
    _layer(
        "biotopes.shp", "Biotopskyddsområde",
        solar_buffer_m=50, wind_buffer_m=550,
    ),
    _layer(
        "sensitive_wilderness.shp", "Känslig vildmark",
        solar_buffer_m=50, wind_buffer_m=550,
    ),
    _layer(
        "protected_state_forests.shp", "Skyddad skog",
        solar_buffer_m=50, wind_buffer_m=550,
    ),
    _layer(
        "wildlife_preserve.shp", "Vildmarksbevaring",
        solar_buffer_m=50, wind_buffer_m=550,
    ),
    _layer(
        "nature_reserves.shp", "Naturreservat",
        solar_buffer_m=50, wind_buffer_m=550,
    ),
    _layer(
        "nature_conservations.shp", "Naturvård",
        solar_buffer_m=50, wind_buffer_m=550,
    ),
    _layer(
        "nature_memory_polygons.shp", "Naturminne",
        solar_buffer_m=10, wind_buffer_m=10,
    ),
    _layer(
        "vmi_very_high.shp", "VMI, klass 1",
        solar_buffer_m=6, wind_buffer_m=0,
    ),
    _layer(
        "vmi_high.shp", "VMI, klass 2",
        solar_buffer_m=6, wind_buffer_m=0,
    ),
    _layer(
        "wet_soil.shp", "Torv",
        solar_buffer_m=0, wind_buffer_m=10,
    ),

    # Land use
    _layer(
        "military_areas.shp", "Militärt område",
        solar_buffer_m=50, wind_buffer_m=50,
    ),
    _layer(
        "arable_land.shp", "Jordbruk",
        solar_buffer_m=6, wind_buffer_m=6,
    ),
    _layer(
        "grazing_areas.shp", "Betesmark",
        solar_buffer_m=6, wind_buffer_m=6,
    ),
    _layer(
        "reindeer_info.shp", "Rennäring",
        solar_buffer_m=6, wind_buffer_m=6,
    ),

    # Buildings
    _layer(
        "residental_buildings.shp", "Bostadshus",
        solar_buffer_m=50, wind_buffer_m=1500,
    ),
    _layer(
        "accessory_building.shp", "Tillbyggnation",
        solar_buffer_m=50, wind_buffer_m=50,
    ),
    _layer(
        "barn.shp", "Lada",
        solar_buffer_m=50, wind_buffer_m=300,
    ),
    _layer(
        "other_building.shp", "Byggnad (övrig)",
        solar_buffer_m=50, wind_buffer_m=50,
    ),
    _layer(
        "facilities.shp", "Anläggning",
        solar_buffer_m=50, wind_buffer_m=50,
    ),
    _layer(
        "industry.shp", "Industri",
        solar_buffer_m=50, wind_buffer_m=50,
    ),
    _layer(
        "public_function.shp", "Samhällsfunktion",
        solar_buffer_m=50, wind_buffer_m=50,
    ),

    # Aviation
    _layer(
        "air_trafic_areas.shp", "Flygtrafik",
        solar_buffer_m=50, wind_buffer_m=0,
    ),
    _layer(
        "helicopterpads.shp", "Närliggande helikopterplatta",
        solar_buffer_m=0, wind_buffer_m=6,
    ),
    _layer(
        "landing_strips.shp", "Närliggande landningsbana",
        solar_buffer_m=0, wind_buffer_m=6,
    ),
    _layer(
        "minor_airports.shp", "Närliggande mindre flygplats",
        solar_buffer_m=0, wind_buffer_m=6,
    ),
    _layer(
        "major_airports.shp", "Närliggande större flygplats",
        solar_buffer_m=0, wind_buffer_m=6,
    ),

    # Additional context
    _layer(
        "ditches.gpkg", "Diken",
        solar_buffer_m=0, wind_buffer_m=0,
    ),
    _layer(
        "municip_borders.shp", "Kommungräns",
        solar_buffer_m=0, wind_buffer_m=0,
    ),
]

MAP_COLORS = {
    "powerlines-300-500.shp": "#ff0004",
    "powerlines-underground.shp": "#ff2bb8",
    "powerlines-170-220.shp": "#cb00c8",
    "powerlines-80-170.shp": "#0000ff",
    "powerlines-10-80.shp": "#00ff88",
    "powerlines-null.shp": "#e18e00",
    "estates.shp": "#000000",
    "soil_types.shp": "#000000",
    "power_stations_poly.shp": "#37ff00",
    "nature_memory_points_poly.shp": "#ff73b9",
    "misc_poly.shp": "#8c8c8c",
    "hiking_trails.shp": "#ff2693",
    "peat_extractions_poly.shp": "#b7484b",
    "weather_station_temp_poly.shp": "#00b7cf",
    "weather_station_wind_poly.shp": "#00a1b3",
    "railway.shp": "#474747",
    "roads.shp": "#999999",
    "bike_lane.shp": "#e9f0e4",
    "rest_stop_poly.shp": "#00cf98",
    "swamp_forest.shp": "#f67fff",
    "vmi_low.shp": "#f673ff",
    "cultural_reserve.shp": "#0004ff",
    "outdoor_life_areas.shp": "#a200f3",
    "protected_water_courses.shp": "#006eff",
    "noble_forest.shp": "#19b800",
    "water_flow_poly.shp": "#006eff",
    "water_courses.shp": "#006eff",
    "water_surfaces.shp": "#006eff",
    "ancient_remains_points_poly.shp": "#fff761",
    "ancient_remains_lines.shp": "#fff761",
    "ancient_remains_polygons.shp": "#fff761",
    "landslide_slope-instability.shp": "#ff0004",
    "natura2000.shp": "#ffb2d7",
    "inaccessable.shp": "#ffa6d1",
    "rich_birdlife.shp": "#ff99ca",
    "biotopes.shp": "#ff8cc4",
    "sensitive_wilderness.shp": "#ff66b3",
    "protected_state_forests.shp": "#ff59ac",
    "wildlife_preserve.shp": "#ff4ca6",
    "nature_reserves.shp": "#ff40a0",
    "nature_conservations.shp": "#ff3399",
    "nature_memory_polygons.shp": "#ff73b9",
    "vmi_very_high.shp": "#f64cff",
    "vmi_high.shp": "#f459ff",
    "wet_soil.shp": "#f58cff",
    "military_areas.shp": "#00e8bd",
    "arable_land.shp": "#b97b3e",
    "grazing_areas.shp": "#b6ad00",
    "reindeer_info.shp": "#8e8571",
    "residental_buildings.shp": "#b2b2b2",
    "accessory_building.shp": "#a6a6a6",
    "barn.shp": "#a6a6a6",
    "other_building.shp": "#999999",
    "facilities.shp": "#8c8c8c",
    "industry.shp": "#808080",
    "public_function.shp": "#737373",
    "air_trafic_areas.shp": "#1ca600",
    "helicopterpads.shp": "#1ca600",
    "landing_strips.shp": "#179900",
    "minor_airports.shp": "#138c00",
    "major_airports.shp": "#118000",
    "ditches.gpkg": "#006eff",
    "municip_borders.shp": "#00e8bd",
}

MAP_SPECIALS = {
    "powerlines-300-500.shp": "wide_line",
    "powerlines-underground.shp": "wide_line",
    "powerlines-170-220.shp": "wide_line",
    "powerlines-80-170.shp": "wide_line",
    "powerlines-10-80.shp": "wide_line",
    "powerlines-null.shp": "wide_line",

    "estates.shp": "dotted",
    "soil_types.shp": "soil",

    "power_stations_poly.shp": "remove_poly_suffix",
    "nature_memory_points_poly.shp": "remove_poly_suffix",
    "misc_poly.shp": "remove_poly_suffix",
    "peat_extractions_poly.shp": "remove_poly_suffix",
    "weather_station_temp_poly.shp": "remove_poly_suffix",
    "weather_station_wind_poly.shp": "remove_poly_suffix",
    "rest_stop_poly.shp": "remove_poly_suffix",
    "ancient_remains_points_poly.shp": "remove_poly_suffix",

    "hiking_trails.shp": "walking",
    "railway.shp": "rail",
    "bike_lane.shp": "bike",

    "swamp_forest.shp": "forward_hatch",
    "noble_forest.shp": "forward_hatch",
    "municip_borders.shp": "forward_hatch",

    "vmi_low.shp": "backward_hatch",
    "cultural_reserve.shp": "backward_hatch",
    "outdoor_life_areas.shp": "backward_hatch",
    "protected_water_courses.shp": "backward_hatch",
    "minor_airports.shp": "backward_hatch",
    "major_airports.shp": "backward_hatch",

    "water_flow_poly.shp": "arrow",
    "water_courses.shp": "wide_line",

    "water_surfaces.shp": "transparent_15",
    "ancient_remains_polygons.shp": "transparent_15",
    "landslide_slope-instability.shp": "transparent_15",
    "natura2000.shp": "transparent_15",
    "inaccessable.shp": "transparent_15",
    "rich_birdlife.shp": "transparent_15",
    "biotopes.shp": "transparent_15",
    "sensitive_wilderness.shp": "transparent_15",
    "protected_state_forests.shp": "transparent_15",
    "wildlife_preserve.shp": "transparent_15",
    "nature_reserves.shp": "transparent_15",
    "nature_conservations.shp": "transparent_15",
    "nature_memory_polygons.shp": "transparent_15",
    "vmi_very_high.shp": "transparent_15",
    "vmi_high.shp": "transparent_15",
    "wet_soil.shp": "transparent_15",
    "military_areas.shp": "transparent_15",
    "arable_land.shp": "transparent_15",
    "grazing_areas.shp": "transparent_15",
    "reindeer_info.shp": "transparent_15",
    "helicopterpads.shp": "transparent_15",
    "landing_strips.shp": "transparent_15",
}

HIDDEN_MAP_LAYERS = {
    "soil_types.shp",
    "roads.shp",
}


def get_map_style(layer_definition):
    """
    Return Sweden-specific display settings for a country layer.
    """

    source_name = os.path.basename(
        layer_definition["source"]
    )

    return {
        "color": MAP_COLORS.get(
            source_name,
            "#d27800",
        ),
        "visible": source_name not in HIDDEN_MAP_LAYERS,
        "special": MAP_SPECIALS.get(
            source_name,
            "none",
        ),
    }

# These datasets represent points stored as polygons in Anna's data.
# Values specify the exported centroid filenames.
CENTROID_OUTPUTS = {
    "power_stations_poly.shp": "power_stations.shp",
    "nature_memory_points_poly.shp": "nature_memory_points.shp",
    "misc_poly.shp": "misc.shp",
    "peat_extractions_poly.shp": "peat_extractions.shp",
    "weather_station_temp_poly.shp": "weather_station_temp.shp",
    "weather_station_wind_poly.shp": "weather_station_wind.shp",
    "rest_stop_poly.shp": "rest_stop.shp",
    "water_flow_poly.shp": "water_flow.shp",
    "ancient_remains_points_poly.shp": "ancient_remains_points.shp",
}

for definition in LAYERS:
    definition["centroid_output"] = CENTROID_OUTPUTS.get(
        definition["source"]
    )

SITE_SUMMARY = {
    "tariff_zone_field": "TARIFFZONE",
    "tariff_zone_prefix": "SE",
}

STRANG_SETTINGS = {
    "base_url": (
        "https://opendata-download-metanalys.smhi.se/"
        "api/category/strang1g/version/1"
    ),
    "from_date": "2010-01-01",
    "to_date": "2023-12-31",
    "parameters": {
        117: "Global Horizontal Irradiation",
        118: "Direct Normal Irradiation",
        122: "Diffuse Horizontal Irradiation",
    },
}

SNOW_DEPTH_MONTHS = {
    "January": "jan",
    "February": "feb",
    "March": "mar",
    "April": "apr",
    "May": "may",
    "June": "jun",
    "July": "jul",
    "August": "aug",
    "September": "sep",
    "October": "oct",
    "November": "nov",
    "December": "dec",
}

METEOROLOGY_SETTINGS = {
    "wind_speed": {
        "source": "wind_map.shp",
        "value_field": "Z",
        "measurement_height_m": 140,
        "source_name": "Swedish wind map",
    },

    "wind_load_field": "WINDLOAD",
    "snow_load_field": "SNOWLOAD",

    "raster_data": {
        "humidity": {
            "source": "humidity_data.tif",
            "name": "Average humidity",
            "unit": "%",
            "source_name": "Swedish meteorological raster",
        },

        "temperature_fallback": {
            "source": "temp_data.tif",
            "name": "Average air temperature",
            "unit": "°C",
            "source_name": "Swedish meteorological raster",
        },

        "air_pressure": {
            "source": "air_pressure_data.tif",
            "name": "Average air pressure",
            "unit": "hPa",
            "source_name": "Swedish meteorological raster",
        },

        "snow_depth": {
            month_name: {
                "source": f"snow_depth_{month_code}.tif",
                "name": f"Average snow depth — {month_name}",
                "unit": "m",
                "source_name": "Swedish meteorological raster",
                "precision": 3,
                "secondary_unit": "cm",
                "secondary_multiplier": 100,
                "secondary_precision": 2,
            }
            for month_name, month_code
            in SNOW_DEPTH_MONTHS.items()
        },
    },
}

POLITICAL_SETTINGS = {
    "source": "parties.csv",
    "site_municipality_field": "BOROUGH",
    "csv_municipality_field": "Kommun",
    "control_field": "Kommunal Politiskt styre",
    "total_seats_field": "TOT",

    "party_names": {
        "M": "Moderaterna",
        "SD": "Sverigedemokraterna",
        "KD": "Kristdemokraterna",
        "L": "Liberalerna",
        "S": "Socialdemokraterna",
        "C": "Centerpartiet",
        "MP": "Miljöpartiet",
        "V": "Vänsterpartiet",
    },
}

BOS_SETTINGS = {
    "landcover_raster": "landcover.tif",
    "wet_soil_layer": "wet_soil.shp",
    "rocky_terrain_layer": "rocky_terrain.shp",
    "peat_quarry_layer": "peat_quarry.shp",

    "class_groups": {
        "Open field": [
            3,
            41,
            42,
            115,
            117,
        ],
        "Forest": [
            111,
            112,
            113,
            114,
            116,
            118,
            121,
            122,
            123,
            124,
            126,
            128,
        ],
        "Wetland": [
            2,
            125,
            127,
        ],
        "Rocky terrain": [
            200,
        ],
        "Peat quarry": [
            201,
        ],
    },

    "rocky_terrain_value": 200,
    "peat_quarry_value": 201,
}

GRID_PROXIMITY_SETTINGS = {
    # Anna treated anything closer than 70 metres as
    # crossing the project area.
    "crossing_distance_m": 70.0,

    "layers": [
        {
            "name": "300–500 kV ledning",
            "type": "power_line",
            "voltage_field": "max_voltag",
            "voltage_divisor": 1000.0,
        },
        {
            "name": "Nedgrävd ledning",
            "type": "underground_power_line",
            "voltage_field": "max_voltag",
            "voltage_divisor": 1000.0,
        },
        {
            "name": "170–220 kV ledning",
            "type": "power_line",
            "voltage_field": "max_voltag",
            "voltage_divisor": 1000.0,
        },
        {
            "name": "80–170 kV ledning",
            "type": "power_line",
            "voltage_field": "max_voltag",
            "voltage_divisor": 1000.0,
        },
        {
            "name": "10–80 kV ledning",
            "type": "power_line",
            "voltage_field": "max_voltag",
            "voltage_divisor": 1000.0,
        },
        {
            "name": "Okänd ledning",
            "type": "power_line",
            "voltage_field": "max_voltag",
            "voltage_divisor": 1000.0,
        },
        {
            "name": "Transformatorstation",
            "type": "transformer_station",
            "primary_voltage_field": "v_primary",
            "secondary_voltage_field": "v_secondar",
            "voltage_divisor": 1000.0,
        },
    ],
}

REDLISTED_SPECIES_SETTINGS = {
    "service_url": (
        "https://sosgeo.artdata.slu.se/"
        "geoserver/SOS/ows"
    ),

    "wfs_version": "2.0.0",

    "type_name": (
        "SOS:SpeciesObservationsRedlisted"
    ),

    "source_crs": "EPSG:4326",

    "context_distance_m": 1000.0,

    "page_size": 5000,

    "output_filename": (
        "redlisted_species.shp"
    ),

    "map_layer_name": (
        "Red-listed species observations"
    ),
}

SOIL_DEPTH_SETTINGS = {
    "raster_source": "soil_depth.tif",

    # Name of the already processed country layer.
    "soil_layer_name": "Jordtyper",

    "soil_type_field": "TYPE",

    "band": 1,

    # SGU Jorddjupsmodell values are whole metres
    # representing estimated depth to bedrock.
    "source_unit": "m",

    "metre_multiplier": 1.0,

    "nodata_value": 0.0,

    "metre_precision": 0,
    "centimetre_precision": 0,
}