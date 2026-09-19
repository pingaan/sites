"""
Basemap definitions inherited from Anna.

Entries are ordered from top to bottom in the map.
These sources are for presentation, not constraint analysis.
"""

BASEMAPS = [
    {
        "id": "google_roads",
        "name": "Google Roads",
        "url": "https://mt1.google.com/vt/lyrs=h&x={x}&y={y}&z={z}",
        "min_zoom": 0,
        "max_zoom": 21,
        "visible": True,
    },
    {
        "id": "google_satellite",
        "name": "Google Satellite",
        "url": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        "min_zoom": 0,
        "max_zoom": 21,
        "visible": True,
    },
]