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