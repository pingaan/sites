from qgis.PyQt.QtCore import QSettings


settings = QSettings(
    "Sovra",
    "Sovra",
)

settings.remove(
    "layers"
)

settings.sync()

print(
    "Sovra layer settings reset."
)