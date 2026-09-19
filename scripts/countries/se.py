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