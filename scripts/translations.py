"""
Application translations that are independent of analysis country.

Internal configuration names must remain stable. These translations
are used only when text is presented to the user.
"""


SUPPORTED_LANGUAGES = {
    "en",
    "sv",
    "fi",
}


LAYER_NAMES = {
    "powerlines_300_500": {
        "en": "300–500 kV power line",
        "sv": "300–500 kV ledning",
        "fi": "300–500 kV voimajohto",
    },
    "powerlines_220_300": {
        "en": "220–300 kV power line",
        "sv": "220–300 kV ledning",
        "fi": "220–300 kV voimajohto",
    },
    "powerlines_170_220": {
        "en": "170–220 kV power line",
        "sv": "170–220 kV ledning",
        "fi": "170–220 kV voimajohto",
    },
    "powerlines_80_170": {
        "en": "80–170 kV power line",
        "sv": "80–170 kV ledning",
        "fi": "80–170 kV voimajohto",
    },
    "powerlines_10_80": {
        "en": "10–80 kV power line",
        "sv": "10–80 kV ledning",
        "fi": "10–80 kV voimajohto",
    },
    "powerlines_underground": {
        "en": "Underground power line",
        "sv": "Nedgrävd ledning",
        "fi": "Maakaapeli",
    },
    "powerlines_unknown": {
        "en": "Unknown power line",
        "sv": "Okänd ledning",
        "fi": "Tuntematon voimajohto",
    },
    "power_stations": {
        "en": "Substation",
        "sv": "Transformatorstation",
        "fi": "Sähköasema",
    },
    "estates": {
        "en": "Cadastral map",
        "sv": "Fastighetskarta",
        "fi": "Kiinteistökartta",
    },
    "railway": {
        "en": "Railway",
        "sv": "Järnväg",
        "fi": "Rautatie",
    },
    "roads": {
        "en": "Road",
        "sv": "Väg",
        "fi": "Tie",
    },
    "minor_roads": {
        "en": "Minor road",
        "sv": "Mindre väg",
        "fi": "Pientie",
    },
    "bike_lane": {
        "en": "Cycleway",
        "sv": "Cykelbana",
        "fi": "Pyörätie",
    },
    "hiking_trails": {
        "en": "Hiking trail",
        "sv": "Vandringsled",
        "fi": "Retkeilyreitti",
    },
    "ditches": {
        "en": "Ditches",
        "sv": "Diken",
        "fi": "Ojat",
    },
    "military_areas": {
        "en": "Military area",
        "sv": "Militärt område",
        "fi": "Sotilasalue",
    },
    "arable_land": {
        "en": "Arable land",
        "sv": "Jordbruk",
        "fi": "Viljelysmaa",
    },
    "residential_buildings": {
        "en": "Residential building",
        "sv": "Bostadshus",
        "fi": "Asuinrakennus",
    },
}

LAYER_NAMES.update(
    {
        "accessory_buildings": {
            "en": "Accessory building",
            "sv": "Tillbyggnation",
            "fi": "Lisärakennus",
        },
        "air_traffic_areas": {
            "en": "Air traffic area",
            "sv": "Flygtrafik",
            "fi": "Lentoliikennealue",
        },
        "ancient_remains_lines": {
            "en": "Ancient remain",
            "sv": "Lämning",
            "fi": "Muinaisjäännös",
        },
        "ancient_remains_points": {
            "en": "Ancient remain",
            "sv": "Lämning",
            "fi": "Muinaisjäännös",
        },
        "ancient_remains_polygons": {
            "en": "Ancient remain",
            "sv": "Lämning",
            "fi": "Muinaisjäännös",
        },
        "barns": {
            "en": "Barn",
            "sv": "Lada",
            "fi": "Lato",
        },
        "biotopes": {
            "en": "Biotope protection area",
            "sv": "Biotopskyddsområde",
            "fi": "Luontotyyppien suojelualue",
        },
        "building_heritage": {
            "en": "Listed building",
            "sv": "Byggnadsminne",
            "fi": "Suojeltu rakennus",
        },
        "buildings": {
            "en": "Building (other)",
            "sv": "Byggnad (övrig)",
            "fi": "Rakennus (muu)",
        },
        "cultural_reserve": {
            "en": "Cultural environment",
            "sv": "Kulturmiljö",
            "fi": "Kulttuuriympäristö",
        },
        "facilities": {
            "en": "Facility",
            "sv": "Anläggning",
            "fi": "Laitos",
        },
        "grazing_areas": {
            "en": "Pasture",
            "sv": "Betesmark",
            "fi": "Laidunmaa",
        },
        "helicopterpads": {
            "en": "Nearby helipad",
            "sv": "Närliggande helikopterplatta",
            "fi": "Läheinen helikopterikenttä",
        },
        "inaccessible": {
            "en": "Inaccessible area",
            "sv": "Otillgängligt område",
            "fi": "Saavuttamaton alue",
        },
        "industry": {
            "en": "Industrial area",
            "sv": "Industri",
            "fi": "Teollisuusalue",
        },
        "landing_strips": {
            "en": "Nearby runway",
            "sv": "Närliggande landningsbana",
            "fi": "Läheinen kiitotie",
        },
        "landslide_slope_instability": {
            "en": "Landslide susceptibility",
            "sv": "Rasrisk",
            "fi": "Maanvyörymäriski",
        },
        "major_airports": {
            "en": "Nearby major airport",
            "sv": "Närliggande större flygplats",
            "fi": "Läheinen suuri lentoasema",
        },
        "minor_airports": {
            "en": "Nearby minor airport",
            "sv": "Närliggande mindre flygplats",
            "fi": "Läheinen pieni lentoasema",
        },
        "miscellaneous": {
            "en": "Other",
            "sv": "Övrigt",
            "fi": "Muut kohteet",
        },
        "municipality_borders": {
            "en": "Municipal boundary",
            "sv": "Kommungräns",
            "fi": "Kuntaraja",
        },
        "national_parks": {
            "en": "National park",
            "sv": "Nationalpark",
            "fi": "Kansallispuisto",
        },
        "natura2000": {
            "en": "Natura 2000",
            "sv": "Natura 2000",
            "fi": "Natura 2000",
        },
        "nature_conservations": {
            "en": "Nature conservation",
            "sv": "Naturvård",
            "fi": "Luonnonsuojelukohde",
        },
        "nature_memory_points": {
            "en": "Natural monument",
            "sv": "Naturminne",
            "fi": "Luonnonmuistomerkki",
        },
        "nature_memory_polygons": {
            "en": "Natural monument",
            "sv": "Naturminne",
            "fi": "Luonnonmuistomerkki",
        },
        "nature_reserves": {
            "en": "Nature reserve",
            "sv": "Naturreservat",
            "fi": "Luonnonsuojelualue",
        },
        "noble_forest": {
            "en": "Broadleaved woodland",
            "sv": "Ädelskog",
            "fi": "Jalopuumetsä",
        },
        "other_buildings": {
            "en": "Building (other)",
            "sv": "Byggnad (övrig)",
            "fi": "Rakennus (muu)",
        },
        "outdoor_life_areas": {
            "en": "Outdoor recreation area",
            "sv": "Friluftsliv",
            "fi": "Ulkoilualue",
        },
        "peat_extractions": {
            "en": "Peat extraction",
            "sv": "Torvtäkt",
            "fi": "Turpeenottoalue",
        },
        "protected_state_forests": {
            "en": "Protected forest",
            "sv": "Skyddad skog",
            "fi": "Suojeltu metsä",
        },
        "protected_water_areas": {
            "en": "Protected water area",
            "sv": "Skyddsområde (vatten)",
            "fi": "Suojeltu vesialue",
        },
        "protected_water_courses": {
            "en": "Protected watercourse",
            "sv": "Skyddsområde (vattendrag)",
            "fi": "Suojeltu vesiuoma",
        },
        "public_functions": {
            "en": "Public service",
            "sv": "Samhällsfunktion",
            "fi": "Julkinen palvelu",
        },
        "reindeer_info": {
            "en": "Reindeer husbandry",
            "sv": "Rennäring",
            "fi": "Poronhoito",
        },
        "rest_stops": {
            "en": "Rest area",
            "sv": "Rastplats",
            "fi": "Levähdyspaikka",
        },
        "rich_birdlife": {
            "en": "Valuable bird area",
            "sv": "Rikt fågelliv",
            "fi": "Arvokas lintualue",
        },
        "rivers": {
            "en": "River",
            "sv": "Vattendrag",
            "fi": "Joki",
        },
        "sensitive_wilderness": {
            "en": "Sensitive wilderness",
            "sv": "Känslig vildmark",
            "fi": "Herkkä erämaa",
        },
        "soil_types": {
            "en": "Soil type",
            "sv": "Jordtyper",
            "fi": "Maalajit",
        },
        "swamp_forest": {
            "en": "Swamp forest",
            "sv": "Sumpskog",
            "fi": "Suometsä",
        },
        "vmi_high": {
            "en": "Wetland inventory, class 2",
            "sv": "VMI, klass 2",
            "fi": "Kosteikköinventointi, luokka 2",
        },
        "vmi_low": {
            "en": "Wetland inventory, class 3–4",
            "sv": "VMI, klass 3–4",
            "fi": "Kosteikköinventointi, luokka 3–4",
        },
        "vmi_very_high": {
            "en": "Wetland inventory, class 1",
            "sv": "VMI, klass 1",
            "fi": "Kosteikköinventointi, luokka 1",
        },
        "water_courses": {
            "en": "Watercourse",
            "sv": "Vattendrag",
            "fi": "Vesiuoma",
        },
        "water_flow": {
            "en": "Flow direction",
            "sv": "Flödesriktning",
            "fi": "Virtaussuunta",
        },
        "water_surfaces": {
            "en": "Lake or major watercourse",
            "sv": "Sjö/större vattendrag",
            "fi": "Järvi tai suuri vesistö",
        },
        "weather_station_temperature": {
            "en": "Weather station (temperature)",
            "sv": "Väderstation (temperatur)",
            "fi": "Sääasema (lämpötila)",
        },
        "weather_station_wind": {
            "en": "Weather station (wind)",
            "sv": "Väderstation (vind)",
            "fi": "Sääasema (tuuli)",
        },
        "wet_soil": {
            "en": "Peat",
            "sv": "Torv",
            "fi": "Turve",
        },
        "wildlife_preserve": {
            "en": "Wilderness conservation",
            "sv": "Vildmarksbevaring",
            "fi": "Erämaiden suojelu",
        },
    }
)

def normalise_language(language):
    """
    Return a supported language code, defaulting to English.
    """

    language = str(
        language or ""
    ).strip().lower()

    if language not in SUPPORTED_LANGUAGES:
        return "en"

    return language


def translated_layer_name(
    definition,
    language,
):
    """
    Return a translated display name for a country layer.

    Database table names act as stable language-independent keys.
    The existing definition name remains the fallback.
    """

    language = normalise_language(
        language
    )

    database = definition.get(
        "database",
        {},
    )

    table_name = database.get(
        "table"
    )

    translations = LAYER_NAMES.get(
        table_name,
        {},
    )

    return translations.get(
        language,
        translations.get(
            "en",
            definition.get(
                "name",
                table_name or "Unnamed layer",
            ),
        ),
    )

UI_TEXT = {
    "renamed_to": {
        "en": "Renamed to: {name}",
        "sv": "Namn ändrat till: {name}",
        "fi": "Uusi nimi: {name}",
    },
    "basemap_selected": {
        "en": "Basemap: {name}",
        "sv": "Bakgrundskarta: {name}",
        "fi": "Taustakartta: {name}",
    },
    "project_loaded": {
        "en": "Project loaded: {name}",
        "sv": "Projekt inläst: {name}",
        "fi": "Projekti ladattu: {name}",
    },
    "scale_value": {
        "en": "Scale: 1:{scale}",
        "sv": "Skala: 1:{scale}",
        "fi": "Mittakaava: 1:{scale}",
    },
    "application_language_selected": {
        "en": "Application language selected: {language}",
        "sv": "Applikationsspråk valt: {language}",
        "fi": "Sovelluksen kieli valittu: {language}",
    },
    "starting_analysis": {
        "en": "Starting analysis…",
        "sv": "Startar analys…",
        "fi": "Käynnistetään analyysiä…",
    },
    "preparing_large_analysis_area": {
        "en": "Preparing a large analysis area",
        "sv": "Förbereder ett stort analysområde",
        "fi": "Valmistellaan suurta analyysialuetta",
    },
    "local_projects": {
        "en": "Local projects",
        "sv": "Lokala projekt",
        "fi": "Paikalliset projektit",
    },
    "field": {
        "en": "Field",
        "sv": "Fält",
        "fi": "Kenttä",
    },
    "value": {
        "en": "Value",
        "sv": "Värde",
        "fi": "Arvo",
    },
    "property": {
        "en": "Property",
        "sv": "Egenskap",
        "fi": "Ominaisuus",
    },
    "select_background_map": {
        "en": "Select background map",
        "sv": "Välj bakgrundskarta",
        "fi": "Valitse taustakartta",
    },
    "ready": {
        "en": "Ready",
        "sv": "Klar",
        "fi": "Valmis",
    },
    "scale_unavailable": {
        "en": "Scale: —",
        "sv": "Skala: —",
        "fi": "Mittakaava: —",
    },
    "select_polygon_file_placeholder": {
        "en": "Select a polygon file…",
        "sv": "Välj en polygonfil…",
        "fi": "Valitse polygonitiedosto…",
    },
    "analysis_project_not_found": {
        "en": (
            "Analysis completed, but the new QGIS project "
            "could not be located."
        ),
        "sv": (
            "Analysen slutfördes, men det nya QGIS-projektet "
            "kunde inte hittas."
        ),
        "fi": (
            "Analyysi valmistui, mutta uutta QGIS-projektia "
            "ei löytynyt."
        ),
    },
    "analysis_completed_project_loaded": {
        "en": "Analysis completed and project loaded",
        "sv": "Analysen slutfördes och projektet lästes in",
        "fi": "Analyysi valmistui ja projekti ladattiin",
    },
    "print_sovra_project": {
        "en": "Print Sovra project",
        "sv": "Skriv ut Sovra-projekt",
        "fi": "Tulosta Sovra-projekti",
    },
    "overview_admin_field_missing": {
        "en": (
            "Country overview unavailable: the ADMIN field "
            "was not found."
        ),
        "sv": (
            "Landsöversikten är inte tillgänglig: fältet "
            "ADMIN hittades inte."
        ),
        "fi": (
            "Maan yleiskartta ei ole käytettävissä: "
            "ADMIN-kenttää ei löytynyt."
        ),
    },
    "overview_country_not_found": {
        "en": (
            "Country overview unavailable: {country} "
            "was not found."
        ),
        "sv": (
            "Landsöversikten är inte tillgänglig: {country} "
            "hittades inte."
        ),
        "fi": (
            "Maan yleiskartta ei ole käytettävissä: maata "
            "{country} ei löytynyt."
        ),
    },
    "country_map_invalid_crs": {
        "en": "Country map unavailable: invalid CRS {crs}.",
        "sv": (
            "Landskartan är inte tillgänglig: ogiltigt "
            "koordinatsystem {crs}."
        ),
        "fi": (
            "Maakartta ei ole käytettävissä: virheellinen "
            "koordinaattijärjestelmä {crs}."
        ),
    },
    "overview_dataset_unavailable": {
        "en": (
            "Country overview unavailable: "
            "world_countries.gpkg could not be loaded."
        ),
        "sv": (
            "Landsöversikten är inte tillgänglig: "
            "world_countries.gpkg kunde inte läsas in."
        ),
        "fi": (
            "Maan yleiskartta ei ole käytettävissä: tiedostoa "
            "world_countries.gpkg ei voitu ladata."
        ),
    },
    "overview_satellite_unavailable": {
        "en": (
            "Country overview unavailable: satellite imagery "
            "could not be loaded."
        ),
        "sv": (
            "Landsöversikten är inte tillgänglig: "
            "satellitbilderna kunde inte läsas in."
        ),
        "fi": (
            "Maan yleiskartta ei ole käytettävissä: "
            "satelliittikuvia ei voitu ladata."
        ),
    },
    "project_country_not_found": {
        "en": (
            "Country overview unavailable: the project "
            "location did not match a country."
        ),
        "sv": (
            "Landsöversikten är inte tillgänglig: projektets "
            "läge kunde inte kopplas till ett land."
        ),
        "fi": (
            "Maan yleiskartta ei ole käytettävissä: projektin "
            "sijainti ei vastannut mitään maata."
        ),
    },
    "rename_prevented_title": {
        "en": "Rename prevented",
        "sv": "Namnändring förhindrad",
        "fi": "Nimeäminen estettiin",
    },
    "rename_prevented_message": {
        "en": (
            "Sovra refused to rename a path outside the local "
            "Projects folder."
        ),
        "sv": (
            "Sovra vägrade att byta namn på en sökväg utanför "
            "den lokala projektmappen."
        ),
        "fi": (
            "Sovra esti projektikansion ulkopuolella olevan "
            "polun nimeämisen uudelleen."
        ),
    },
    "rename_project_title": {
        "en": "Rename project",
        "sv": "Byt namn på projekt",
        "fi": "Nimeä projekti uudelleen",
    },
    "new_name_label": {
        "en": "New name:",
        "sv": "Nytt namn:",
        "fi": "Uusi nimi:",
    },
    "invalid_name_title": {
        "en": "Invalid name",
        "sv": "Ogiltigt namn",
        "fi": "Virheellinen nimi",
    },
    "name_cannot_be_empty": {
        "en": "The name cannot be empty.",
        "sv": "Namnet får inte vara tomt.",
        "fi": "Nimi ei voi olla tyhjä.",
    },
    "invalid_folder_name_message": {
        "en": (
            "The name contains characters or a Windows-reserved "
            "name that cannot be used for a folder."
        ),
        "sv": (
            "Namnet innehåller tecken eller ett Windows-reserverat "
            "namn som inte kan användas för en mapp."
        ),
        "fi": (
            "Nimi sisältää merkkejä tai Windowsin varaaman nimen, "
            "jota ei voida käyttää kansion nimenä."
        ),
    },
    "name_already_exists_title": {
        "en": "Name already exists",
        "sv": "Namnet används redan",
        "fi": "Nimi on jo käytössä",
    },
    "name_already_exists_message": {
        "en": "Another project or folder already uses that name.",
        "sv": "Ett annat projekt eller en annan mapp använder redan namnet.",
        "fi": "Toinen projekti tai kansio käyttää jo tätä nimeä.",
    },
    "rename_failed_title": {
        "en": "Rename failed",
        "sv": "Namnändringen misslyckades",
        "fi": "Nimeäminen epäonnistui",
    },
    "rename_failed_message": {
        "en": (
            "The project folder could not be renamed:\n\n"
            "{error}"
        ),
        "sv": (
            "Projektmappens namn kunde inte ändras:\n\n"
            "{error}"
        ),
        "fi": (
            "Projektikansiota ei voitu nimetä uudelleen:\n\n"
            "{error}"
        ),
    },
    "printing_failed_title": {
        "en": "Printing failed",
        "sv": "Utskriften misslyckades",
        "fi": "Tulostaminen epäonnistui",
    },
    "printer_open_failed_message": {
        "en": "The selected printer could not be opened.",
        "sv": "Den valda skrivaren kunde inte öppnas.",
        "fi": "Valittua tulostinta ei voitu avata.",
    },
    "save_qgis_project": {
        "en": "Save QGIS project",
        "sv": "Spara QGIS-projekt",
        "fi": "Tallenna QGIS-projekti",
    },
    "qgis_project_file": {
        "en": "QGIS project (*.qgz)",
        "sv": "QGIS-projekt (*.qgz)",
        "fi": "QGIS-projekti (*.qgz)",
    },
    "save_error_title": {
        "en": "Save error",
        "sv": "Fel vid sparande",
        "fi": "Tallennusvirhe",
    },
    "project_save_failed_message": {
        "en": "The project could not be saved.",
        "sv": "Projektet kunde inte sparas.",
        "fi": "Projektia ei voitu tallentaa.",
    },
    "project_saved": {
        "en": "Project saved",
        "sv": "Projektet har sparats",
        "fi": "Projekti tallennettiin",
    },
    "vector_data_filter": {
        "en": "Vector data (*.gpkg *.shp *.geojson);;All files (*.*)",
        "sv": "Vektordata (*.gpkg *.shp *.geojson);;Alla filer (*.*)",
        "fi": "Vektoriaineistot (*.gpkg *.shp *.geojson);;Kaikki tiedostot (*.*)",
    },
    "about_content": {
        "en": (
            "<div style='min-width: 420px;'>"
            "<h2 style='color: #153854;'>Sovra</h2>"
            "<p>Renewable-energy site analysis and "
            "GIS workspace.</p>"
            "<p><b>Powered by:</b></p>"
            "<table><tr>"
            "{technology_html}"
            "</tr></table>"
            "<p style='color: #657585;'>"
            "Sovra uses open-source geospatial and "
            "application-development technologies."
            "</p>"
            "</div>"
        ),
        "sv": (
            "<div style='min-width: 420px;'>"
            "<h2 style='color: #153854;'>Sovra</h2>"
            "<p>Analys av platser för förnybar energi "
            "och GIS-arbetsyta.</p>"
            "<p><b>Byggt med:</b></p>"
            "<table><tr>"
            "{technology_html}"
            "</tr></table>"
            "<p style='color: #657585;'>"
            "Sovra använder öppna tekniker för geodata "
            "och applikationsutveckling."
            "</p>"
            "</div>"
        ),
        "fi": (
            "<div style='min-width: 420px;'>"
            "<h2 style='color: #153854;'>Sovra</h2>"
            "<p>Uusiutuvan energian sijoituspaikka-analyysi "
            "ja GIS-työtila.</p>"
            "<p><b>Toteutettu seuraavilla:</b></p>"
            "<table><tr>"
            "{technology_html}"
            "</tr></table>"
            "<p style='color: #657585;'>"
            "Sovra käyttää avoimen lähdekoodin paikkatieto- "
            "ja sovelluskehitysteknologioita."
            "</p>"
            "</div>"
        ),
    },
    "basemap_unavailable": {
        "en": "Basemap unavailable",
        "sv": "Bakgrundskartan är inte tillgänglig",
        "fi": "Taustakartta ei ole käytettävissä",
    },
    "basemap_unavailable_message": {
        "en": (
            "The selected background map could not be loaded:\n"
            "{name}"
        ),
        "sv": (
            "Den valda bakgrundskartan kunde inte läsas in:\n"
            "{name}"
        ),
        "fi": (
            "Valittua taustakarttaa ei voitu ladata:\n"
            "{name}"
        ),
    },
    "missing_analysis_source": {
        "en": "Missing analysis source",
        "sv": "Analysunderlag saknas",
        "fi": "Analyysin lähtöaineisto puuttuu",
    },
    "missing_analysis_source_message": {
        "en": (
            "Enter an estate identifier or select a custom polygon."
        ),
        "sv": (
            "Ange en fastighetsbeteckning eller välj en egen polygon."
        ),
        "fi": (
            "Anna kiinteistötunnus tai valitse oma polygoni."
        ),
    },
    "estate_not_found": {
        "en": "Estate not found",
        "sv": "Fastigheten hittades inte",
        "fi": "Kiinteistöä ei löytynyt",
    },
    "estate_not_found_message": {
        "en": (
            "No estate was found matching:\n\n"
            "{estate}\n\n"
            "Check the spelling and the order of the municipality, "
            "sector and estate identifier."
        ),
        "sv": (
            "Ingen fastighet hittades som motsvarar:\n\n"
            "{estate}\n\n"
            "Kontrollera stavningen och ordningen för kommun, "
            "trakt och fastighetsbeteckning."
        ),
        "fi": (
            "Seuraavaa vastaavaa kiinteistöä ei löytynyt:\n\n"
            "{estate}\n\n"
            "Tarkista kunnan, kylän ja kiinteistötunnuksen "
            "kirjoitusasu sekä järjestys."
        ),
    },
    "analysis_failed_message": {
        "en": (
            "The analysis could not be completed.\n\n"
            "Open the progress window details for the complete "
            "error message."
        ),
        "sv": (
            "Analysen kunde inte slutföras.\n\n"
            "Öppna detaljerna i förloppsfönstret för att se "
            "hela felmeddelandet."
        ),
        "fi": (
            "Analyysiä ei voitu suorittaa loppuun.\n\n"
            "Avaa etenemisikkunan lisätiedot nähdäksesi koko "
            "virheilmoituksen."
        ),
    },
    "open_qgis_project": {
        "en": "Open QGIS project",
        "sv": "Öppna QGIS-projekt",
        "fi": "Avaa QGIS-projekti",
    },
    "qgis_project_files": {
        "en": "QGIS projects (*.qgz *.qgs)",
        "sv": "QGIS-projekt (*.qgz *.qgs)",
        "fi": "QGIS-projektit (*.qgz *.qgs)",
    },
    "project_error": {
        "en": "Project error",
        "sv": "Projektfel",
        "fi": "Projektivirhe",
    },
    "project_open_failed_message": {
        "en": (
            "Failed to open the QGIS project:\n"
            "{path}"
        ),
        "sv": (
            "QGIS-projektet kunde inte öppnas:\n"
            "{path}"
        ),
        "fi": (
            "QGIS-projektia ei voitu avata:\n"
            "{path}"
        ),
    },
    "project_crs_error": {
        "en": "Project CRS error",
        "sv": "Fel i projektets koordinatsystem",
        "fi": "Projektin koordinaattijärjestelmävirhe",
    },
    "project_crs_error_message": {
        "en": (
            "The loaded project does not have a valid coordinate "
            "reference system."
        ),
        "sv": (
            "Det inlästa projektet saknar ett giltigt "
            "koordinatreferenssystem."
        ),
        "fi": (
            "Ladatulla projektilla ei ole kelvollista "
            "koordinaattijärjestelmää."
        ),
    },
    "renewable_energy_site_analysis": {
        "en": "Renewable-energy site analysis",
        "sv": "Analys av platser för förnybar energi",
        "fi": "Uusiutuvan energian sijoituspaikka-analyysi",
    },
    "analysis_source": {
        "en": "Analysis source",
        "sv": "Analysunderlag",
        "fi": "Analyysin lähtöaineisto",
    },
    "estate_identifier": {
        "en": "Estate identifier",
        "sv": "Fastighetsbeteckning",
        "fi": "Kiinteistötunnus",
    },
    "custom_polygon": {
        "en": "Custom polygon",
        "sv": "Egen polygon",
        "fi": "Oma polygoni",
    },
    "source_type_label": {
        "en": "Source type:",
        "sv": "Typ av underlag:",
        "fi": "Lähtöaineiston tyyppi:",
    },
    "estate_label": {
        "en": "Estate:",
        "sv": "Fastighet:",
        "fi": "Kiinteistö:",
    },
    "browse": {
        "en": "Browse…",
        "sv": "Bläddra…",
        "fi": "Selaa…",
    },
    "polygon_file_label": {
        "en": "Polygon file:",
        "sv": "Polygonfil:",
        "fi": "Polygonitiedosto:",
    },
    "select_custom_polygon": {
        "en": "Select custom polygon",
        "sv": "Välj egen polygon",
        "fi": "Valitse oma polygon",
    },
    "analysis_already_running": {
        "en": "Analysis already running",
        "sv": "Analys pågår redan",
        "fi": "Analyysi on jo käynnissä",
    },
    "analysis_already_running_message": {
        "en": "An analysis is already running.",
        "sv": "En analys pågår redan.",
        "fi": "Analyysi on jo käynnissä.",
    },
    "missing_estate": {
        "en": "Missing estate",
        "sv": "Fastighet saknas",
        "fi": "Kiinteistö puuttuu",
    },
    "enter_estate_identifier": {
        "en": "Enter an estate identifier.",
        "sv": "Ange en fastighetsbeteckning.",
        "fi": "Anna kiinteistötunnus.",
    },
    "missing_polygon": {
        "en": "Missing polygon",
        "sv": "Polygon saknas",
        "fi": "Polygoni puuttuu",
    },
    "select_custom_polygon_file": {
        "en": "Select a custom polygon file.",
        "sv": "Välj en fil som innehåller analysområdet.",
        "fi": "Valitse analyysialueen sisältävä tiedosto.",
    },
    "polygon_not_found": {
        "en": "Polygon not found",
        "sv": "Polygonen hittades inte",
        "fi": "Polygonia ei löytynyt",
    },
    "polygon_not_found_message": {
        "en": (
            "The selected polygon source does not exist:\n\n"
            "{path}"
        ),
        "sv": (
            "Den valda polygonkällan finns inte:\n\n"
            "{path}"
        ),
        "fi": (
            "Valittua polygonilähdettä ei ole olemassa:\n\n"
            "{path}"
        ),
    },
    "launcher_missing": {
        "en": "Launcher missing",
        "sv": "Startfil saknas",
        "fi": "Käynnistystiedosto puuttuu",
    },
    "launcher_missing_message": {
        "en": (
            "The analysis launcher was not found:\n\n"
            "{path}"
        ),
        "sv": (
            "Analysens startfil hittades inte:\n\n"
            "{path}"
        ),
        "fi": (
            "Analyysin käynnistystiedostoa ei löytynyt:\n\n"
            "{path}"
        ),
    },
    "large_analysis_area": {
        "en": "Large analysis area",
        "sv": "Stort analysområde",
        "fi": "Suuri analyysialue",
    },
    "large_analysis_area_message": {
        "en": (
            "The selected project area is {area} hectares.\n\n"
            "Areas larger than 500 hectares can take several "
            "minutes to analyse, depending on the computer setup."
        ),
        "sv": (
            "Det valda projektområdet är {area} hektar.\n\n"
            "Områden större än 500 hektar kan ta flera minuter "
            "att analysera, beroende på datorns prestanda."
        ),
        "fi": (
            "Valitun projektialueen pinta-ala on {area} "
            "hehtaaria.\n\n"
            "Yli 500 hehtaarin alueiden analysointi voi kestää "
            "useita minuutteja tietokoneen suorituskyvystä "
            "riippuen."
        ),
    },
    "process_error": {
        "en": "Process error",
        "sv": "Processfel",
        "fi": "Prosessivirhe",
    },
    "process_error_message": {
        "en": "Process error: {error}",
        "sv": "Processfel: {error}",
        "fi": "Prosessivirhe: {error}",
    },
    "cleanup_incomplete": {
        "en": "Cleanup incomplete",
        "sv": "Rensningen kunde inte slutföras",
        "fi": "Siivousta ei voitu suorittaa loppuun",
    },
    "cleanup_incomplete_message": {
        "en": (
            "The analysis was cancelled, but its temporary "
            "output folder could not be removed:\n\n"
            "{path}\n\n"
            "{error}"
        ),
        "sv": (
            "Analysen avbröts, men dess tillfälliga "
            "resultatmapp kunde inte tas bort:\n\n"
            "{path}\n\n"
            "{error}"
        ),
        "fi": (
            "Analyysi peruutettiin, mutta sen väliaikaista "
            "tuloshakemistoa ei voitu poistaa:\n\n"
            "{path}\n\n"
            "{error}"
        ),
    },
    "cancel_analysis": {
        "en": "Cancel analysis",
        "sv": "Avbryt analys",
        "fi": "Peruuta analyysi",
    },
    "cancel_analysis_message": {
        "en": (
            "Stop the running analysis?\n\n"
            "Files created by this incomplete analysis will "
            "be removed."
        ),
        "sv": (
            "Vill du stoppa den pågående analysen?\n\n"
            "Filer som skapats av den ofullständiga analysen "
            "kommer att tas bort."
        ),
        "fi": (
            "Pysäytetäänkö käynnissä oleva analyysi?\n\n"
            "Keskeneräisen analyysin luomat tiedostot "
            "poistetaan."
        ),
    },
    "analysis_progress_title": {
        "en": "Sovra — Analysis progress",
        "sv": "Sovra — Analysförlopp",
        "fi": "Sovra — Analyysin eteneminen",
    },
    "preparing_analysis": {
        "en": "Preparing analysis",
        "sv": "Förbereder analys",
        "fi": "Valmistellaan analyysiä",
    },
    "cancel": {
        "en": "Cancel",
        "sv": "Avbryt",
        "fi": "Peruuta",
    },
    "show_details": {
        "en": "Show more details",
        "sv": "Visa mer information",
        "fi": "Näytä lisätiedot",
    },
    "hide_details": {
        "en": "Hide details",
        "sv": "Dölj information",
        "fi": "Piilota lisätiedot",
    },
    "analysis_messages_placeholder": {
        "en": "Analysis messages will appear here.",
        "sv": "Analysmeddelanden visas här.",
        "fi": "Analyysiviestit näkyvät tässä.",
    },
    "analysis_running": {
        "en": "Analysis running…",
        "sv": "Analysen körs…",
        "fi": "Analyysi on käynnissä…",
    },
    "analysis_cancelled": {
        "en": "Analysis cancelled",
        "sv": "Analysen avbröts",
        "fi": "Analyysi peruutettiin",
    },
    "analysis_completed": {
        "en": "Analysis completed successfully",
        "sv": "Analysen slutfördes",
        "fi": "Analyysi valmistui onnistuneesti",
    },
    "analysis_failed": {
        "en": "Analysis failed",
        "sv": "Analysen misslyckades",
        "fi": "Analyysi epäonnistui",
    },
    "cancelling_analysis": {
        "en": "Cancelling analysis…",
        "sv": "Avbryter analysen…",
        "fi": "Peruutetaan analyysiä…",
    },
    "removing_incomplete_files": {
        "en": "Removing incomplete analysis files",
        "sv": "Tar bort ofullständiga analysfiler",
        "fi": "Poistetaan keskeneräisen analyysin tiedostoja",
    },
    "opening_completed_project": {
        "en": "Opening the completed project",
        "sv": "Öppnar det färdiga projektet",
        "fi": "Avataan valmistunut projekti",
    },
    "analysis_stopped_exit_code": {
        "en": "Analysis stopped with exit code {exit_code}",
        "sv": "Analysen stoppades med slutkod {exit_code}",
        "fi": "Analyysi pysähtyi poistumiskoodilla {exit_code}",
    },
    "stopping_analysis_processes": {
        "en": "Stopping analysis processes",
        "sv": "Stoppar analysprocesser",
        "fi": "Pysäytetään analyysiprosesseja",
    },
    "application_title": {
        "en": "Sovra — Renewable-energy site analysis",
        "sv": "Sovra — Platsanalys för förnybar energi",
        "fi": "Sovra — Uusiutuvan energian alueanalyysi",
    },
    "map": {
        "en": "Map",
        "sv": "Karta",
        "fi": "Kartta",
    },
    "info": {
        "en": "Info",
        "sv": "Info",
        "fi": "Tiedot",
    },
    "layers": {
        "en": "Layers",
        "sv": "Lager",
        "fi": "Tasot",
    },
    "projects": {
        "en": "Projects",
        "sv": "Projekt",
        "fi": "Projektit",
    },
    "information": {
        "en": "Information",
        "sv": "Information",
        "fi": "Tiedot",
    },
    "feature_information": {
        "en": "Feature information",
        "sv": "Objektinformation",
        "fi": "Kohteen tiedot",
    },
    "layer_information": {
        "en": "Layer information",
        "sv": "Lagerinformation",
        "fi": "Tason tiedot",
    },
    "country_overview": {
        "en": "Country overview",
        "sv": "Landsöversikt",
        "fi": "Maan yleiskuva",
    },
    "country_overview_named": {
        "en": "Country overview — {country}",
        "sv": "Landsöversikt — {country}",
        "fi": "Maan yleiskuva — {country}",
    },
    "country_selected": {
        "en": "Country selected: {country}",
        "sv": "Valt land: {country}",
        "fi": "Valittu maa: {country}",
    },
    "menu_file": {
        "en": "&File",
        "sv": "&Arkiv",
        "fi": "&Tiedosto",
    },
    "menu_edit": {
        "en": "&Edit",
        "sv": "&Redigera",
        "fi": "&Muokkaa",
    },
    "menu_view": {
        "en": "&View",
        "sv": "&Visa",
        "fi": "&Näytä",
    },
    "menu_settings": {
        "en": "&Settings",
        "sv": "&Inställningar",
        "fi": "&Asetukset",
    },
    "menu_analysis": {
        "en": "&Analysis",
        "sv": "&Analys",
        "fi": "&Analyysi",
    },
    "menu_help": {
        "en": "&Help",
        "sv": "&Hjälp",
        "fi": "&Ohje",
    },
    "basemap": {
        "en": "Basemap",
        "sv": "Bakgrundskarta",
        "fi": "Taustakartta",
    },
    "open": {
        "en": "Open",
        "sv": "Öppna",
        "fi": "Avaa",
    },
    "open_location": {
        "en": "Open location",
        "sv": "Öppna plats",
        "fi": "Avaa sijainti",
    },
    "rename_project_or_folder": {
        "en": "Rename selected project or folder",
        "sv": "Byt namn på valt projekt eller mapp",
        "fi": "Nimeä valittu projekti tai kansio uudelleen",
    },
    "delete_local_projects": {
        "en": "Delete selected local projects",
        "sv": "Ta bort valda lokala projekt",
        "fi": "Poista valitut paikalliset projektit",
    },
    "options": {
        "en": "Options…",
        "sv": "Alternativ…",
        "fi": "Asetukset…",
    },
    "configure_sovra": {
        "en": "Configure Sovra",
        "sv": "Konfigurera Sovra",
        "fi": "Määritä Sovran asetukset",
    },
    "open_project": {
        "en": "Open project…",
        "sv": "Öppna projekt…",
        "fi": "Avaa projekti…",
    },
    "save_project": {
        "en": "Save project",
        "sv": "Spara projekt",
        "fi": "Tallenna projekti",
    },
    "print_project": {
        "en": "Print project…",
        "sv": "Skriv ut projekt…",
        "fi": "Tulosta projekti…",
    },
    "exit": {
        "en": "Exit",
        "sv": "Avsluta",
        "fi": "Lopeta",
    },
    "about_sovra": {
        "en": "About Sovra",
        "sv": "Om Sovra",
        "fi": "Tietoja Sovrasta",
    },
    "export_solar_area": {
        "en": "Export eligible solar area…",
        "sv": "Exportera lämpligt område för solenergi…",
        "fi": "Vie aurinkoenergialle soveltuva alue…",
    },
    "export_solar_area_tooltip": {
        "en": "Export the eligible solar area as a GeoPackage",
        "sv": "Exportera det lämpliga solenergiområdet som ett GeoPackage",
        "fi": "Vie aurinkoenergialle soveltuva alue GeoPackage-tiedostona",
    },
    "export_wind_area": {
        "en": "Export eligible wind area…",
        "sv": "Exportera lämpligt område för vindkraft…",
        "fi": "Vie tuulivoimalle soveltuva alue…",
    },
    "export_wind_area_tooltip": {
        "en": "Export the eligible wind area as a GeoPackage",
        "sv": "Exportera det lämpliga vindkraftsområdet som ett GeoPackage",
        "fi": "Vie tuulivoimalle soveltuva alue GeoPackage-tiedostona",
    },
    "full_extent": {
        "en": "Full extent",
        "sv": "Full utbredning",
        "fi": "Koko laajuus",
    },
    "open_qgis_project_tooltip": {
        "en": "Open a QGIS project",
        "sv": "Öppna ett QGIS-projekt",
        "fi": "Avaa QGIS-projekti",
    },
    "pan_map": {
        "en": "Pan map",
        "sv": "Panorera karta",
        "fi": "Panoroi karttaa",
    },
    "identify_feature": {
        "en": "Identify feature",
        "sv": "Identifiera objekt",
        "fi": "Tunnista kohde",
    },
    "measure_distance": {
        "en": "Measure distance",
        "sv": "Mät avstånd",
        "fi": "Mittaa etäisyys",
    },
    "measure_area": {
        "en": "Measure area",
        "sv": "Mät area",
        "fi": "Mittaa pinta-ala",
    },
    "start_analysis": {
        "en": "Start analysis",
        "sv": "Starta analys",
        "fi": "Aloita analyysi",
    },
    "map_navigation": {
        "en": "Map navigation",
        "sv": "Kartnavigering",
        "fi": "Kartan navigointi",
    },
    "analysis": {
        "en": "Analysis",
        "sv": "Analys",
        "fi": "Analyysi",
    },
    "country_label": {
        "en": "Country:",
        "sv": "Land:",
        "fi": "Maa:",
    },
        "eligible_solar_area_name": {
        "en": "Eligible solar area",
        "sv": "Lämpligt område för solenergi",
        "fi": "Aurinkoenergialle soveltuva alue",
    },
    "eligible_wind_area_name": {
        "en": "Eligible wind area",
        "sv": "Lämpligt område för vindkraft",
        "fi": "Tuulivoimalle soveltuva alue",
    },
    "analysis_area_unavailable": {
        "en": "Analysis area unavailable",
        "sv": "Analysområdet är inte tillgängligt",
        "fi": "Analyysialue ei ole käytettävissä",
    },
    "analysis_area_not_found": {
        "en": "{area} could not be found in the loaded project.",
        "sv": "{area} kunde inte hittas i det inlästa projektet.",
        "fi": "{area} ei löytynyt ladatusta projektista.",
    },
    "export_failed": {
        "en": "Export failed",
        "sv": "Exporten misslyckades",
        "fi": "Vienti epäonnistui",
    },
    "area_export_failed": {
        "en": "{area} could not be exported:\n\n{error}",
        "sv": "{area} kunde inte exporteras:\n\n{error}",
        "fi": "Kohdetta {area} ei voitu viedä:\n\n{error}",
    },
    "export_completed": {
        "en": "Export completed",
        "sv": "Exporten slutfördes",
        "fi": "Vienti valmistui",
    },
    "area_export_completed": {
        "en": "{area} was exported successfully:\n\n{path}",
        "sv": "{area} exporterades:\n\n{path}",
        "fi": "{area} vietiin onnistuneesti:\n\n{path}",
    },
    "restart_required": {
        "en": "Restart required",
        "sv": "Omstart krävs",
        "fi": "Uudelleenkäynnistys vaaditaan",
    },
    "restart_required_message": {
        "en": (
            "The language setting has been saved.\n\n"
            "Sovra must be restarted before the new language "
            "is applied.\n\n"
            "Close Sovra now?"
        ),
        "sv": (
            "Språkinställningen har sparats.\n\n"
            "Sovra måste startas om innan det nya språket "
            "börjar användas.\n\n"
            "Vill du stänga Sovra nu?"
        ),
        "fi": (
            "Kieliasetus on tallennettu.\n\n"
            "Sovra on käynnistettävä uudelleen, jotta uusi "
            "kieli otetaan käyttöön.\n\n"
            "Suljetaanko Sovra nyt?"
        ),
    },
        "export_area_dialog": {
        "en": "Export {area}",
        "sv": "Exportera: {area}",
        "fi": "Vie: {area}",
    },
        "print_project_tooltip": {
        "en": "Print a layout from the current project",
        "sv": "Skriv ut en layout från det aktuella projektet",
        "fi": "Tulosta nykyisen projektin asettelu",
    },
    "save_project_tooltip": {
        "en": "Save the current QGIS project",
        "sv": "Spara det aktuella QGIS-projektet",
        "fi": "Tallenna nykyinen QGIS-projekti",
    },
    "full_extent_tooltip": {
        "en": "Zoom to the full extent of project data",
        "sv": "Zooma till all projektdata",
        "fi": "Zoomaa koko projektiaineiston laajuuteen",
    },
    "pan_map_tooltip": {
        "en": "Move around the map",
        "sv": "Flytta runt på kartan",
        "fi": "Liiku kartalla",
    },
    "identify_feature_tooltip": {
        "en": "Click a feature in the selected layer",
        "sv": "Klicka på ett objekt i det valda lagret",
        "fi": "Napsauta kohdetta valitulla tasolla",
    },
    "measure_distance_tooltip": {
        "en": "Measure a distance on the map",
        "sv": "Mät ett avstånd på kartan",
        "fi": "Mittaa etäisyys kartalla",
    },
    "measure_area_tooltip": {
        "en": "Measure an area on the map",
        "sv": "Mät en area på kartan",
        "fi": "Mittaa pinta-ala kartalla",
    },
    "export_area": {
        "en": "Export area",
        "sv": "Exportera område",
        "fi": "Vie alue",
    },
    "export_area_tooltip": {
        "en": "Export an eligible analysis area",
        "sv": "Exportera ett lämpligt analysområde",
        "fi": "Vie soveltuva analyysialue",
    },
    "select_background_map": {
        "en": "Select background map",
        "sv": "Välj bakgrundskarta",
        "fi": "Valitse taustakartta",
    },
        "source_estate": {
        "en": "Estate",
        "sv": "Fastighet",
        "fi": "Kiinteistö",
    },
    "source_predefined_area": {
        "en": "Predefined area",
        "sv": "Fördefinierat område",
        "fi": "Ennalta määritetty alue",
    },
    "source_draw_area": {
        "en": "Draw area",
        "sv": "Rita område",
        "fi": "Piirrä alue",
    },
    "no_project_loaded": {
        "en": "No project loaded",
        "sv": "Inget projekt har lästs in",
        "fi": "Projektia ei ole ladattu",
    },
    "load_project_before_printing": {
        "en": "Load a project before printing.",
        "sv": "Läs in ett projekt innan du skriver ut.",
        "fi": "Lataa projekti ennen tulostamista.",
    },
        "country_sweden": {
        "en": "Sweden",
        "sv": "Sverige",
        "fi": "Ruotsi",
    },
    "country_finland": {
        "en": "Finland",
        "sv": "Finland",
        "fi": "Suomi",
    },
        "old_projects_found": {
        "en": "Old local projects found",
        "sv": "Gamla lokala projekt hittades",
        "fi": "Vanhoja paikallisia projekteja löytyi",
    },
    "old_projects_message": {
        "en": (
            "The following local project runs have not been "
            "updated for at least one month:\n\n"
            "{projects}\n\nRemove them?"
        ),
        "sv": (
            "Följande lokala projektkörningar har inte "
            "uppdaterats på minst en månad:\n\n"
            "{projects}\n\nVill du ta bort dem?"
        ),
        "fi": (
            "Seuraavia paikallisia projektiajoja ei ole "
            "päivitetty vähintään kuukauteen:\n\n"
            "{projects}\n\nPoistetaanko ne?"
        ),
    },
    "old_projects_more": {
        "en": "…and {count} more",
        "sv": "…och ytterligare {count}",
        "fi": "…ja {count} muuta",
    },
    "project_cleanup_incomplete": {
        "en": "Project cleanup incomplete",
        "sv": "Projektstädningen slutfördes inte",
        "fi": "Projektien siivous jäi kesken",
    },
    "project_cleanup_incomplete_message": {
        "en": (
            "Removed {count} old project run(s).\n\n"
            "Some folders could not be removed:\n\n{errors}"
        ),
        "sv": (
            "Tog bort {count} gamla projektkörningar.\n\n"
            "Vissa mappar kunde inte tas bort:\n\n{errors}"
        ),
        "fi": (
            "Poistettiin {count} vanhaa projektiajoa.\n\n"
            "Joitakin kansioita ei voitu poistaa:\n\n{errors}"
        ),
    },
    "project_cleanup_completed": {
        "en": "Project cleanup completed",
        "sv": "Projektstädningen är klar",
        "fi": "Projektien siivous valmistui",
    },
    "project_cleanup_completed_message": {
        "en": "Removed {count} old local project run(s).",
        "sv": "Tog bort {count} gamla lokala projektkörningar.",
        "fi": "Poistettiin {count} vanhaa paikallista projektiajoa.",
    },
    "no_local_projects_found": {
        "en": "No local projects found",
        "sv": "Inga lokala projekt hittades",
        "fi": "Paikallisia projekteja ei löytynyt",
    },
        "open_project_title": {
        "en": "Open project",
        "sv": "Öppna projekt",
        "fi": "Avaa projekti",
    },
    "select_one_project_or_folder": {
        "en": "Select one project or project folder.",
        "sv": "Välj ett projekt eller en projektmapp.",
        "fi": "Valitse yksi projekti tai projektikansio.",
    },
    "folder_has_no_qgis_project": {
        "en": "The selected folder does not contain a QGIS project.",
        "sv": "Den valda mappen innehåller inget QGIS-projekt.",
        "fi": "Valittu kansio ei sisällä QGIS-projektia.",
    },
    "open_location_title": {
        "en": "Open location",
        "sv": "Öppna sökväg",
        "fi": "Avaa sijainti",
    },
    "no_local_folder_associated": {
        "en": (
            "No local folder is associated with the "
            "selected item."
        ),
        "sv": (
            "Ingen lokal mapp är kopplad till det "
            "valda objektet."
        ),
        "fi": (
            "Valittuun kohteeseen ei liity paikallista "
            "kansiota."
        ),
    },
    "select_one_item": {
        "en": "Select one item",
        "sv": "Välj ett objekt",
        "fi": "Valitse yksi kohde",
    },
    "select_one_item_to_rename": {
        "en": (
            "Select exactly one project or folder to rename."
        ),
        "sv": (
            "Välj exakt ett projekt eller en mapp som ska "
            "byta namn."
        ),
        "fi": (
            "Valitse täsmälleen yksi projekti tai kansio "
            "uudelleennimettäväksi."
        ),
    },
    "no_projects_selected": {
        "en": "No projects selected",
        "sv": "Inga projekt har valts",
        "fi": "Projekteja ei ole valittu",
    },
    "select_projects_before_deletion": {
        "en": (
            "Select one or more projects or analysis runs first."
        ),
        "sv": (
            "Välj först ett eller flera projekt eller "
            "analyskörningar."
        ),
        "fi": (
            "Valitse ensin yksi tai useampi projekti tai "
            "analyysiajo."
        ),
    },
    "unsafe_deletion_prevented": {
        "en": "Unsafe deletion prevented",
        "sv": "Osäker borttagning förhindrades",
        "fi": "Turvaton poistaminen estettiin",
    },
    "unsafe_deletion_message": {
        "en": (
            "Sovra refused to delete a path outside the local "
            "Projects folder:\n\n{path}"
        ),
        "sv": (
            "Sovra vägrade ta bort en sökväg utanför den "
            "lokala projektmappen:\n\n{path}"
        ),
        "fi": (
            "Sovra kieltäytyi poistamasta polkua paikallisen "
            "projektikansion ulkopuolelta:\n\n{path}"
        ),
    },
    "select_vector_layer": {
        "en": "Select a vector layer",
        "sv": "Välj ett vektorlager",
        "fi": "Valitse vektoritaso",
    },
    "select_vector_layer_before_identify": {
        "en": (
            "Select a vector layer in the Layers pane before "
            "using the identify tool."
        ),
        "sv": (
            "Välj ett vektorlager i lagerpanelen innan du "
            "använder identifieringsverktyget."
        ),
        "fi": (
            "Valitse vektoritaso Tasot-paneelista ennen "
            "tunnistustyökalun käyttämistä."
        ),
    },
    "no_print_layout": {
        "en": "No print layout",
        "sv": "Ingen utskriftslayout",
        "fi": "Tulostusasettelua ei ole",
    },
    "no_print_layout_message": {
        "en": (
            "The current project does not contain a print "
            "layout yet.\n\nA Sovra print-layout template "
            "will need to be created and added to the "
            "generated project."
        ),
        "sv": (
            "Det aktuella projektet innehåller ännu ingen "
            "utskriftslayout.\n\nEn utskriftsmall för Sovra "
            "måste skapas och läggas till i det genererade "
            "projektet."
        ),
        "fi": (
            "Nykyinen projekti ei vielä sisällä "
            "tulostusasettelua.\n\nSovralle on luotava "
            "tulostusasettelumalli ja lisättävä se luotuun "
            "projektiin."
        ),
    },
        "delete_local_projects_title": {
        "en": "Delete local projects?",
        "sv": "Ta bort lokala projekt?",
        "fi": "Poistetaanko paikalliset projektit?",
    },
    "delete_local_projects_message": {
        "en": (
            "The following local project data will be "
            "permanently deleted:\n\n{names}\n\n"
            "This includes the project report, GeoPackage "
            "and other local analysis outputs.\n\n"
            "Are you certain?"
        ),
        "sv": (
            "Följande lokala projektdata kommer att tas "
            "bort permanent:\n\n{names}\n\n"
            "Detta omfattar projektrapporten, GeoPackage-"
            "filen och andra lokala analysresultat.\n\n"
            "Är du säker?"
        ),
        "fi": (
            "Seuraavat paikalliset projektitiedot poistetaan "
            "pysyvästi:\n\n{names}\n\n"
            "Tämä sisältää projektiraportin, GeoPackage-"
            "tiedoston ja muut paikalliset analyysitulokset."
            "\n\nOletko varma?"
        ),
    },
    "deletion_incomplete": {
        "en": "Deletion incomplete",
        "sv": "Borttagningen slutfördes inte",
        "fi": "Poistaminen jäi kesken",
    },
    "deletion_incomplete_message": {
        "en": (
            "Some selected projects could not be deleted:"
            "\n\n{errors}"
        ),
        "sv": (
            "Vissa valda projekt kunde inte tas bort:"
            "\n\n{errors}"
        ),
        "fi": (
            "Joitakin valittuja projekteja ei voitu poistaa:"
            "\n\n{errors}"
        ),
    },
    "selected_local_projects_deleted": {
        "en": "Selected local projects deleted",
        "sv": "Valda lokala projekt har tagits bort",
        "fi": "Valitut paikalliset projektit poistettiin",
    },
        "project_missing": {
        "en": "Project missing",
        "sv": "Projektet saknas",
        "fi": "Projekti puuttuu",
    },
    "project_missing_message": {
        "en": (
            "The selected QGIS project no longer exists:"
            "\n\n{path}"
        ),
        "sv": (
            "Det valda QGIS-projektet finns inte längre:"
            "\n\n{path}"
        ),
        "fi": (
            "Valittua QGIS-projektia ei enää ole:"
            "\n\n{path}"
        ),
    },
    "folder_missing": {
        "en": "Folder missing",
        "sv": "Mappen saknas",
        "fi": "Kansio puuttuu",
    },
    "folder_missing_message": {
        "en": (
            "The selected folder no longer exists:"
            "\n\n{path}"
        ),
        "sv": (
            "Den valda mappen finns inte längre:"
            "\n\n{path}"
        ),
        "fi": (
            "Valittua kansiota ei enää ole:"
            "\n\n{path}"
        ),
    },
    "open_location_failed_message": {
        "en": (
            "The operating system could not open the "
            "selected folder:\n\n{path}"
        ),
        "sv": (
            "Operativsystemet kunde inte öppna den valda "
            "mappen:\n\n{path}"
        ),
        "fi": (
            "Käyttöjärjestelmä ei voinut avata valittua "
            "kansiota:\n\n{path}"
        ),
    },
        "draw_polygon_instructions": {
        "en": (
            "Draw the analysis polygon: left-click to add "
            "points, right-click to finish, or press Escape "
            "to cancel."
        ),
        "sv": (
            "Rita analyspolygonen: vänsterklicka för att "
            "lägga till punkter, högerklicka för att slutföra "
            "eller tryck på Escape för att avbryta."
        ),
        "fi": (
            "Piirrä analyysipolygoni: lisää pisteitä "
            "napsauttamalla hiiren vasenta painiketta, "
            "lopeta hiiren oikealla painikkeella tai peruuta "
            "painamalla Escape."
        ),
    },
    "polygon_drawing_cancelled": {
        "en": "Polygon drawing cancelled.",
        "sv": "Polygonritningen avbröts.",
        "fi": "Polygonin piirtäminen peruutettiin.",
    },
    "invalid_polygon": {
        "en": "Invalid polygon",
        "sv": "Ogiltig polygon",
        "fi": "Virheellinen polygoni",
    },
    "drawn_polygon_has_no_geometry": {
        "en": "The drawn polygon contains no geometry.",
        "sv": "Den ritade polygonen innehåller ingen geometri.",
        "fi": "Piirretty polygoni ei sisällä geometriaa.",
    },
    "drawn_polygon_invalid": {
        "en": (
            "The drawn polygon is not geometrically valid. "
            "Check that its edges do not cross and draw it again."
        ),
        "sv": (
            "Den ritade polygonen är inte geometriskt giltig. "
            "Kontrollera att dess kanter inte korsar varandra "
            "och rita den igen."
        ),
        "fi": (
            "Piirretty polygoni ei ole geometrisesti kelvollinen. "
            "Tarkista, etteivät sen reunat risteä, ja piirrä se uudelleen."
        ),
    },
    "invalid_map_crs": {
        "en": "Invalid map CRS",
        "sv": "Ogiltigt koordinatsystem",
        "fi": "Virheellinen kartan koordinaattijärjestelmä",
    },
    "invalid_map_crs_message": {
        "en": (
            "The map does not have a valid coordinate "
            "reference system."
        ),
        "sv": (
            "Kartan har inget giltigt koordinatreferenssystem."
        ),
        "fi": (
            "Kartalla ei ole kelvollista "
            "koordinaattiviitejärjestelmää."
        ),
    },
    "drawn_analysis_polygon": {
        "en": "Drawn analysis polygon",
        "sv": "Ritad analyspolygon",
        "fi": "Piirretty analyysipolygoni",
    },
    "polygon_error": {
        "en": "Polygon error",
        "sv": "Polygonfel",
        "fi": "Polygonivirhe",
    },
    "polygon_temporary_layer_error": {
        "en": (
            "The drawn polygon could not be added to the "
            "temporary layer."
        ),
        "sv": (
            "Den ritade polygonen kunde inte läggas till i "
            "det tillfälliga lagret."
        ),
        "fi": (
            "Piirrettyä polygonia ei voitu lisätä "
            "väliaikaiseen tasoon."
        ),
    },
    "polygon_save_error": {
        "en": "Polygon save error",
        "sv": "Fel när polygonen sparades",
        "fi": "Polygonin tallennusvirhe",
    },
    "polygon_save_error_message": {
        "en": "The drawn polygon could not be saved:\n\n{error}",
        "sv": "Den ritade polygonen kunde inte sparas:\n\n{error}",
        "fi": "Piirrettyä polygonia ei voitu tallentaa:\n\n{error}",
    },
    "polygon_preview_error": {
        "en": "Polygon preview error",
        "sv": "Fel vid förhandsvisning av polygon",
        "fi": "Polygonin esikatseluvirhe",
    },
    "polygon_preview_error_message": {
        "en": (
            "The saved polygon could not be loaded back into QGIS."
        ),
        "sv": (
            "Den sparade polygonen kunde inte läsas tillbaka till QGIS."
        ),
        "fi": (
            "Tallennettua polygonia ei voitu ladata takaisin QGISiin."
        ),
    },
    "drawn_polygon_ready": {
        "en": "Drawn analysis polygon is ready.",
        "sv": "Den ritade analyspolygonen är klar.",
        "fi": "Piirretty analyysipolygoni on valmis.",
    },
        "select_analysis_polygon": {
        "en": "Select analysis polygon",
        "sv": "Välj analyspolygon",
        "fi": "Valitse analyysipolygoni",
    },
    "unable_to_inspect_data_source": {
        "en": "Unable to inspect data source",
        "sv": "Datakällan kunde inte granskas",
        "fi": "Tietolähdettä ei voitu tarkistaa",
    },
    "unable_to_inspect_data_source_message": {
        "en": (
            "QGIS could not inspect the selected data source:"
            "\n\n{path}\n\n{error}"
        ),
        "sv": (
            "QGIS kunde inte granska den valda datakällan:"
            "\n\n{path}\n\n{error}"
        ),
        "fi": (
            "QGIS ei voinut tarkistaa valittua tietolähdettä:"
            "\n\n{path}\n\n{error}"
        ),
    },
    "polygon_layer_required": {
        "en": "Polygon layer required",
        "sv": "Ett polygonlager krävs",
        "fi": "Polygonitaso vaaditaan",
    },
    "polygon_layer_required_message": {
        "en": (
            "The selected data source does not contain a "
            "readable polygon layer.\n\nThe analysis area "
            "must be supplied as polygon or multipolygon "
            "vector data."
        ),
        "sv": (
            "Den valda datakällan innehåller inget läsbart "
            "polygonlager.\n\nAnalysområdet måste anges som "
            "vektordata av typen polygon eller multipolygon."
        ),
        "fi": (
            "Valittu tietolähde ei sisällä luettavaa "
            "polygonitasoa.\n\nAnalyysialue on annettava "
            "polygoni- tai multipolygonivektoridatana."
        ),
    },
    "select_polygon_layer": {
        "en": "Select polygon layer",
        "sv": "Välj polygonlager",
        "fi": "Valitse polygonitaso",
    },
    "multiple_polygon_layers": {
        "en": (
            "This data source contains more than one "
            "polygon layer:"
        ),
        "sv": (
            "Den här datakällan innehåller fler än ett "
            "polygonlager:"
        ),
        "fi": (
            "Tämä tietolähde sisältää useamman kuin yhden "
            "polygonitason:"
        ),
    },
    "analysis_polygon_preview": {
        "en": "Analysis polygon preview",
        "sv": "Förhandsvisning av analyspolygon",
        "fi": "Analyysipolygonin esikatselu",
    },
    "analysis_polygon_loaded": {
        "en": "Analysis polygon loaded and previewed.",
        "sv": "Analyspolygonen har lästs in och förhandsvisats.",
        "fi": "Analyysipolygoni ladattiin ja esikatseltiin.",
    },
}


def ui_text(
    language,
    key,
    **values,
):
    """
    Return translated application-interface text.

    English is used if either the requested language or key
    translation is unavailable.
    """

    language = normalise_language(
        language
    )

    translations = UI_TEXT.get(
        key,
        {},
    )

    text = translations.get(
        language,
        translations.get(
            "en",
            key,
        ),
    )

    try:
        return text.format(
            **values
        )
    except (
        KeyError,
        IndexError,
        ValueError,
    ):
        return text