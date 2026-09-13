# Enter the estate below
estate = ''

#%% ~~ Importing Modules ~~

import datetime
import re
import qgis.utils
import requests
import csv
import os
import processing
import shutil
import time
import math
import shapefile
import concurrent.futures
import fnmatch
import time
import glob
import sys
import pyproj
import platform
import rasterio
import pandas as pd
import numpy as np
import geopandas as gpd
import multiprocessing as mp
import matplotlib.pyplot as plt

from pushbullet import Pushbullet
from astral import LocationInfo
from astral.sun import elevation, Observer
from shapely.geometry import shape
from rasterio.mask import mask
from rasterio.features import shapes
from osgeo import gdal, osr, ogr
from shapely.geometry import Point
from collections import defaultdict
from pushbullet import Pushbullet
from qgis import processing
from datetime import datetime, timedelta
from os.path import join, normpath, dirname
from multiprocessing.pool import ThreadPool
from qgis.PyQt.QtCore import QVariant, Qt
from qgis.gui import QgsLayerTreeView
from qgis.utils import iface
from qgis.PyQt.QtGui import QColor
from qgis.core import (QgsVectorLayer, QgsGeometry, QgsProject, QgsProcessing, QgsLayerTreeGroup, 
                       QgsProcessingFeatureSourceDefinition, QgsField, QgsFeature, QgsFillSymbol,
                       QgsExpression, QgsCoordinateReferenceSystem, QgsVectorFileWriter, 
                       QgsSimpleFillSymbolLayer, QgsSymbol, QgsRasterLayer, QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource, QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterFolderDestination, QgsSingleSymbolRenderer, QgsRendererCategory,
                       QgsCoordinateTransform, QgsProcessingFeedback, QgsProcessingException,
                       QgsSimpleLineSymbolLayer, QgsSimpleMarkerSymbolLayer, QgsGraduatedSymbolRenderer,
                       QgsRendererRange, QgsLayerTreeLayer, QgsCategorizedSymbolRenderer, QgsPointXY,
                       QgsSvgMarkerSymbolLayer, QgsMarkerSymbol, QgsProperty, QgsLineSymbol,
                       QgsMarkerLineSymbolLayer, QgsCsException, QgsSpatialIndex, QgsDistanceArea)

#%% ~~ OS-check ~

def get_paths():
    os_name = platform.system()

    if os_name == "Windows":
        base_path = 'D:\\Dropbox\\GIS-data (sverige)\\anna2.0'
        paths = {
            "data_path": base_path,
            "csv_file": os.path.join(base_path, 'estates.csv'),
            "estates_layer": os.path.join(base_path, 'estates.shp'),
            "path_dem": os.path.normpath(r'D:\\Dropbox\\GIS-data (sverige)\\DEM_1m\\'),
            "pot_path": os.path.join('D:\\Dropbox\\GIS-data (sverige)', 'Potentiella fastigheter'),
            "svg_path": 'C:\\Program Files\\QGIS 3.28.13\\apps\\qgis-ltr\\svg\\arrows\\Arrow_05.svg',
            "empty_shapefile_path": os.path.join(base_path, 'artportal_red_empty.shp')
        }
    elif os_name == "Darwin": 
        base_path = '/Users/pingaan/Dropbox/Documents/GIS-data (sverige)/anna2.0'
        paths = {
            "data_path": base_path,
            "csv_file": os.path.join(base_path, 'estates.csv'),
            "estates_layer": os.path.join(base_path, 'estates.shp'),
            "path_dem": os.path.normpath(r'/Users/pingaan/Dropbox/Documents/GIS-data (sverige)/DEM_1m/'),
            "pot_path": os.path.join('/Users/pingaan/Dropbox/Documents/GIS-data (sverige)', 'Potentiella fastigheter'),
            "svg_path": '/Applications/QGIS.app/Contents/Resources/svg/arrows/Arrow_05.svg',
            "empty_shapefile_path": os.path.join(base_path, 'artportal_red_empty.shp')
        }
    elif os_name == "Linux":
        base_path = '/media/GIS-Data/gis_data/anna2.0'
        paths = {
            "data_path": base_path,
            "csv_file": os.path.join(base_path, 'estates.csv'),
            "estates_layer": os.path.join(base_path, 'estates.shp'),
            "path_dem": os.path.normpath(r'/media/GIS-Data/gis_data/DEM_1m/'),
            "pot_path": os.path.join('/media/GIS-Data/gis_data', 'Potentiella fastigheter'),
            "svg_path": '/usr/share/qgis/svg/arrows/Arrow_05.svg',
            "empty_shapefile_path": os.path.join(base_path, 'artportal_red_empty.shp')
        }
    else:
        raise OSError("Unsupported operating system")

    return paths

paths = get_paths()

#%% ~~ Definitions ~~

neg_bad_slope_area = 150
parts = estate.upper().split()
data_path = paths["data_path"]
csv_file = paths["csv_file"]
estates_layer = paths["estates_layer"]
path_dem = paths["path_dem"]
pot_path = paths["pot_path"]
svg_path = paths["svg_path"]
empty_shapefile_path = paths["empty_shapefile_path"]
lon = None
lat = None
final_layer = None
folder_name = None
folder_path = None
path_temp = None
output_layer_path = None
project = QgsProject.instance()
root = project.layerTreeRoot()
pb = Pushbullet("o.DS2a9Ikj9w6dRIZgt2PumUqEd2FdFJFC")
phone = pb.devices[0]

#%% ~~ Aspect & slope lists ~~

slope_list = [11, 11.3, 11.8, 12.5, 13.2, 14, 
              14.8, 15.7, 16.7, 17.7, 18.8, 20
]

aspect_list_1 = [[0, 15], [15, 30], [30, 45], [45, 60], [60, 75], [75, 90], 
                 [90, 105], [105, 120], [120, 135], [135, 150], [150, 165], [165, 180]
]

aspect_list_2 = [[345, 360], [330, 345], [315, 330], [300, 315], [285, 300], [270, 285], 
                 [255, 270], [240, 255], [225, 240], [210, 225], [195, 210], [180, 195]
]

#%% ~~ Listing Layers ~~

layers = [
    #['name-of-file.shp', '#colour', 'name-when-loaded', 'solar-buffer', 'wind-buffer', 'type-of-layer', 'special', 'folder', 'visibility']
    ['powerlines-300-500.shp', '#ff0004', '300-500 kV ledning', 55, 300, 'line', 'size 4', 'no_folder', 'show'],
    ['powerlines-underground.shp', '#ff2bb8', 'Nedgrävd ledning', 15, 15, 'line', 'size 4', 'no_folder', 'show'],
    ['powerlines-170-220.shp', '#cb00c8', '170-220 kV ledning', 55, 300, 'line', 'size 4', 'no_folder', 'show'],
    ['powerlines-80-170.shp', '#0000ff', '80-170 kV ledning', 55, 300, 'line', 'size 4', 'no_folder', 'show'],
    ['powerlines-10-80.shp', '#00ff88', '10-80 kV ledning', 55, 300, 'line', 'size 4', 'no_folder', 'show'],
    ['powerlines-null.shp', '#e18e00', 'Okänd ledning', 55, 300, 'line', 'size 4', 'no_folder', 'show'],
    ['estates.shp', '#000000', 'Fastighetskarta', 0, 0, 'poly', 'dotted', 'no_folder', 'show'],
    ['soil_types.shp', '#000000', 'Jordtyper', 0, 0, 'poly', 'soil', 'no_folder', 'hide'],
    ['power_stations_poly.shp', '#37ff00', 'Transformatorstation', 15, 300, 'point', 'minus_poly', 'no_folder', 'show'],
    ['nature_memory_points_poly.shp', '#ff73b9', 'Naturminne', 10, 10, 'point', 'minus_poly', 'no_folder', 'show'],
    ['misc_poly.shp', '#8c8c8c', 'Övrigt', 0, 0, 'point', 'minus_poly', 'no_folder', 'show'],
    ['hiking_trails.shp', '#ff2693', 'Vandringsled', 50, 300, 'line', 'walking', 'no_folder', 'show'],
    ['peat_extractions_poly.shp', '#b7484b', 'Torvtäkt', 0, 0, 'point', 'minus_poly', 'no_folder', 'show'],
    ['weather_station_temp_poly.shp', '#00b7cf', 'Väderstation (temperatur)', 100, 100, 'point', 'minus_poly', 'no_folder', 'show'],
    ['weather_station_wind_poly.shp', '#00a1b3', 'Väderstation (vind)', 100, 3000, 'point', 'minus_poly', 'no_folder', 'show'],
    ['railway.shp', '#474747', 'Järnväg', 15, 350, 'line', 'rail', 'no_folder', 'show'],
    ['roads.shp', '#999999', 'Väg', 8, 50, 'line', 'none', 'no_folder', 'hide'],
    ['bike_lane.shp', '#e9f0e4', 'Cykelbana', 0, 50, 'line', 'bike', 'no_folder', 'show'],
    ['rest_stop_poly.shp', '#00cf98', 'Rastplats', 50, 50, 'point', 'minus_poly', 'no_folder', 'show'],
    #['flood_risk.shp', '#ff0004', 'Översvämningsrisk', 0, 0, 'poly', 'polka', 'wind', 'show'], #Flooding #https://gisapp.msb.se/apps/oversvamningsportal/hemta-data.html - google översvämming öppna data
    ['swamp_forest.shp', '#f67fff', 'Sumpskog', 0, 0, 'poly', 'apolka', 'no_folder', 'show'],
    ['vmi_low.shp', '#f673ff', 'VMI, klass 3-4', 0, 0, 'poly', 'polka', 'no_folder', 'show'],
    ['cultural_reserve.shp', '#0004ff', 'Kulturmiljövård (MB3, kap. 6)', 0, 0, 'poly', 'polka', 'no_folder', 'show'],
    ['outdoor_life_areas.shp', '#a200f3', 'Friluftsliv (rörligt, MB3-4, kap. 1-2, 6)', 50, 50, 'poly', 'polka', 'no_folder', 'show'],
    ['protected_water_courses.shp', '#006eff', 'Skyddsområde (vattendrag, MB4, kap. 6)', 0, 0, 'poly', 'polka', 'no_folder', 'show'],
    ['noble_forest.shp', '#19b800', 'Ädelskog', 0, 0, 'poly', 'apolka', 'no_folder', 'show'],
    ['water_flow_poly.shp', '#006eff', 'Flödesriktning', 0, 0, 'point', 'arrow', 'no_folder', 'show'],
    ['water_courses.shp', '#006eff', 'Vattendrag', 15, 50, 'line', 'size 4', 'no_folder', 'show'],
    ['water_surfaces.shp', '#006eff', 'Sjö/större vattendrag', 50, 50, 'poly', 'trans 15', 'no_folder', 'show'],
    ['ancient_remains_points_poly.shp', '#fff761', 'Lämning', 10, 10, 'point', 'minus_poly', 'no_folder', 'show'],
    ['ancient_remains_lines.shp', '#fff761', 'Lämning', 10, 10, 'line', 'none', 'no_folder', 'show'],
    ['ancient_remains_polygons.shp', '#fff761', 'Lämning', 10, 10, 'poly', 'trans 15', 'no_folder', 'show'],
    ['landslide_slope-instability.shp', '#ff0004', 'Rasrisk', 6, 6, 'poly', 'trans 15', 'no_folder', 'show'],
    ['natura2000.shp', '#ffb2d7', 'Natura 2000', 50, 550, 'poly', 'trans 15', 'no_folder', 'show'],    
    ['inaccessable.shp', '#ffa6d1', 'Otillgängligt område', 6, 6, 'poly', 'trans 15', 'no_folder', 'show'],
    ['rich_birdlife.shp', '#ff99ca', 'Rikt fågelliv', 50, 550, 'poly', 'trans 15', 'no_folder', 'show'],
    ['biotopes.shp', '#ff8cc4', 'Biotopskyddsområde', 50, 550, 'poly', 'trans 15', 'no_folder', 'show'],    
    ['sensitive_wilderness.shp', '#ff66b3', 'Känslig vildmark', 50, 550, 'poly', 'trans 15', 'no_folder', 'show'],    
    ['protected_state_forests.shp', '#ff59ac', 'Skyddad skog', 50, 550, 'poly', 'trans 15', 'no_folder', 'show'],    
    ['wildlife_preserve.shp', '#ff4ca6', 'Vildmarksbevaring', 50, 550, 'poly', 'trans 15', 'no_folder', 'show'],
    ['nature_reserves.shp', '#ff40a0', 'Naturreservat', 50, 550, 'poly', 'trans 15', 'no_folder', 'show'],
    ['nature_conservations.shp', '#ff3399', 'Naturvård', 50, 550, 'poly', 'trans 15', 'no_folder', 'show'],
    ['nature_memory_polygons.shp', '#ff73b9', 'Naturminne', 10, 10, 'poly', 'trans 15', 'no_folder', 'show'],
    ['vmi_very_high.shp', '#f64cff', 'VMI, klass 1', 6, 0, 'poly', 'trans 15', 'no_folder', 'show'],
    ['vmi_high.shp', '#f459ff', 'VMI, klass 2', 6, 0, 'poly', 'trans 15', 'no_folder', 'show'],
    ['wet_soil.shp', '#f58cff', 'Torv', 0, 10, 'poly', 'trans 15', 'wind', 'show'],
    ['military_areas.shp', '#00e8bd', 'Miltärt område', 50, 50, 'poly', 'trans 15', 'no_folder', 'show'],
    ['arable_land.shp', '#b97b3e', 'Jordbruk', 6, 6, 'poly', 'trans 15', 'no_folder', 'show'],
    ['grazing_areas.shp', '#b6ad00', 'Betesmark', 6, 6, 'poly', 'trans 15', 'no_folder', 'show'],
    ['reindeer_info.shp', '#8e8571', 'Rennäring', 6, 6, 'poly', 'trans 15', 'no_folder', 'show'],
    ['residental_buildings.shp', '#b2b2b2', 'Bostadsus', 50, 1500, 'poly', 'none', 'no_folder', 'show'],
    ['accessory_building.shp', '#a6a6a6', 'Tillbyggnation', 50, 50, 'poly', 'none', 'no_folder', 'show'],
    ['barn.shp', '#a6a6a6', 'Lada', 50, 300, 'poly', 'none', 'no_folder', 'show'],
    ['other_building.shp', '#999999', 'Byggnad (övrig)', 50, 50, 'poly', 'none', 'no_folder', 'show'],
    ['facilities.shp', '#8c8c8c', 'Anläggning', 50, 50, 'poly', 'none', 'no_folder', 'show'],
    ['industry.shp', '#808080', 'Industri', 50, 50, 'poly', 'none', 'no_folder', 'show'],
    ['public_function.shp', '#737373', 'Samhällsfunktion', 50, 50, 'poly', 'none', 'no_folder', 'show'],
    ['air_trafic_areas.shp', '#1ca600', 'Flygtrafik', 50, 0, 'poly', 'none', 'no_folder', 'show'],
    ['helicopterpads.shp', '#1ca600', 'Närliggande helikopterplatta', 0, 6, 'poly', 'trans 15', 'wind', 'show'],
    ['landing_strips.shp', '#179900', 'Närliggande landningsbana', 0, 6, 'poly', 'trans 15', 'wind', 'show'],
    ['minor_airports.shp', '#138c00', 'Närliggande mindre flyplats', 0, 6, 'poly', 'polka', 'wind', 'show'],
    ['major_airports.shp', '#118000', 'Närliggande större flyplats', 0, 6, 'poly', 'polka', 'wind', 'show'],
    ['ditches.gpkg', '#006eff', 'Diken', 0, 0, 'line', 'none', 'no_folder', 'show'],
    ['municip_borders.shp', '#00e8bd', 'Kommungräns', 0, 0, 'poly', 'apolka', 'wind', 'show'],
]


#%% ~~ Functions ~~

def capitalize_first_letters(text):
    return ' '.join(word.capitalize() for word in text.split())

def save_print_to_file(message):
    with open(output_file_path, 'a') as output_file:  
        output_file.write(message + '\n')
        print(message)  

def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=50, fill='█', print_end="\r"):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=print_end)
    if iteration == total:
        print()

def search_chunk(chunk, match):
    return chunk[(chunk['BOROUGH'] == match[0]) &
                 (chunk['SECTOR'] == match[1]) &
                 (chunk['SEGMENT'] == match[2])]

def sequential_search(csv_file, match):
    iterator = pd.read_csv(csv_file, chunksize=10000)

    results = []
    for chunk in iterator:
        chunk_result = search_chunk(chunk, match)
        results.append(chunk_result)

    result_df = pd.concat(results)

    if not result_df.empty:
        return result_df.index.values
    else:
        return None
    
def check_overlap(layer1, layer2):
    for feature1 in layer1.getFeatures():
        geom1 = feature1.geometry()
        for feature2 in layer2.getFeatures():
            geom2 = feature2.geometry()
            if geom1.intersects(geom2):
                return True
    return False

#%% ~~ Starting point - Reprojecting the Project ~~ 

start = time.time()

QgsProject.instance().setCrs(QgsCoordinateReferenceSystem(3006))

#%% ~~ Fine tuning/Locating the Estate ~~

active_layer = iface.activeLayer()

if active_layer:

    layer_node = root.findLayer(active_layer.id())
    
    if layer_node:
        layer_node.setItemVisibilityChecked(False)
    else:
        pass
else:
    pass

update_area = iface.activeLayer()

estates_path = os.path.join(data_path, 'estates.shp')

if not estate or estate.strip() == '':
    print("Estate is empty, skipping estate processing.")
    
   # Clip the estates layer to the extent of the active layer
    clipped_estates_path = os.path.join(pot_path, 'estates_clipped.shp')
    processing.run("native:clip", {
        'INPUT': estates_path,
        'OVERLAY': update_area,
        'OUTPUT': clipped_estates_path
    })

    # Load the clipped estates layer
    clipped_estates = QgsVectorLayer(clipped_estates_path, "Clipped Estates", "ogr")
    if not clipped_estates.isValid():
        print("Clipped estates layer failed to load!")
    else:
        # Get the first feature's values for BOROUGH, SECTOR, and SEGMENT fields
        feature = next(clipped_estates.getFeatures())
        borough = feature["BOROUGH"] if feature["BOROUGH"] else "UnknownBorough"
        sector = feature["SECTOR"] if feature["SECTOR"] else "UnknownSector"
        segment = feature["SEGMENT"] if feature["SEGMENT"] else "UnknownSegment"
        
        # Create the folder name based on these fields
        folder_name = f"{borough} {sector} {segment} (Clip)".replace(":", "-")
    
    folder_path = os.path.join(pot_path, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    path_temp = os.path.join(folder_path, 'temp')
    os.makedirs(path_temp, exist_ok=True)
    
    if not update_area.isValid():
        print("update_area layer failed to load!")
    else:
        
        fields = update_area.fields().names()
        if "AREA" not in fields:
            
            update_area_joined = os.path.join(path_temp, 'Fastigheten_joined_.shp')
            
            processing.run("native:joinattributesbylocation", {
                'INPUT': update_area,
                'JOIN': clipped_estates_path,
                'PREDICATE': [0],
                'JOIN_FIELDS': [],
                'METHOD': 0,
                'DISCARD_NONMATCHING': False,
                'PREFIX': '',
                'OUTPUT': update_area_joined
            })
            
            update_area_diss = os.path.join(path_temp, 'Fastigheten_diss_.shp')
            
            processing.run("native:dissolve", {
                'INPUT': update_area_joined,
                'FIELD': [],
                'OUTPUT': update_area_diss
            })
            
            expression = '$area * 0.0001'
            
            output_layer_path = os.path.join(folder_path, 'Clip.shp')
            
            result = processing.run("native:fieldcalculator", {
                'INPUT': update_area_diss,
                'FIELD_NAME': 'AREA',
                'FIELD_TYPE': 0,
                'FIELD_LENGTH': 10,
                'FIELD_PRECISION': 3,
                'FORMULA': expression,
                'OUTPUT': output_layer_path
            })
            
            if not result:
                print("Field calculator process failed.")
            else:
                updated_area = QgsVectorLayer(output_layer_path, "Uppritad yta", "ogr")
                if not updated_area.isValid():
                    print("Updated area layer failed to load!")
                else:
                    QgsProject.instance().addMapLayer(updated_area)
                    
                    processing.run("native:createspatialindex", {
                        'INPUT': updated_area
                    })
                    
        else:
            QgsVectorFileWriter.writeAsVectorFormat(update_area, output_layer_path, "UTF-8", update_area.crs(), "ESRI Shapefile")
            updated_area = QgsVectorLayer(output_layer_path, "Uppritad yta", "ogr")
            if not updated_area.isValid():
                print("Updated area layer failed to load!")
            else:
                QgsProject.instance().addMapLayer(updated_area)
                
                processing.run("native:createspatialindex", {
                    'INPUT': updated_area
                })
                
else:
    
    if len(parts) == 4:  
        match = (parts[0], parts[1] + " " + parts[2], parts[3])
    elif len(parts) == 3:  
        match = tuple(parts)
    else:
        raise ValueError("Invalid format of estate entry.")

    row_indices = sequential_search(csv_file, match)
    if row_indices is not None:
        print(f"Estate located at indices: {row_indices}")
    else:
        print("No estate found by that entry.")
    
    estates = QgsVectorLayer(estates_layer, "estates", "ogr")

    if not estates.isValid():
        print("Layer failed to load!")
    else:
        folder_name = " ".join(match).replace(":", "-")  
        folder_path = os.path.join(pot_path, folder_name)
        os.makedirs(folder_path, exist_ok=True)  
        path_temp = os.path.join(folder_path, 'temp')
        os.makedirs(path_temp, exist_ok=True) 
        
        extracted_layers = []

        for row_index in row_indices:
            extracted_feature_path = os.path.join(path_temp, f"fastigheten_{row_index}.shp")

            feature_id = None
            current_index = 0

            for feature in estates.getFeatures():
                if current_index == row_index:
                    feature_id = feature.id()
                    break
                current_index += 1

            if feature_id is not None:
                estates.selectByIds([feature_id])

                writer = QgsVectorFileWriter.writeAsVectorFormat(estates, extracted_feature_path, "UTF-8", estates.crs(), "ESRI Shapefile", onlySelected=True)

                if writer[0] == QgsVectorFileWriter.NoError:
                    extracted_layers.append(extracted_feature_path)
                else:
                    print(f"Error saving extracted feature for row {row_index}. Writer error code:", writer[0])
                estates.removeSelection()
            else:
                print(f"Row index {row_index} out of range")

        merged_layer_path = os.path.join(path_temp, "Fastigheten_merged.shp")
        processing.run("native:mergevectorlayers", {'LAYERS': extracted_layers, 'OUTPUT': merged_layer_path})
        
        processing.run("native:createspatialindex", {
            'INPUT': merged_layer_path
        })
        
        dissolved_layer_path = os.path.join(path_temp, "Fastigheten_dissolved.shp")
        processing.run("native:dissolve", {
            'INPUT': merged_layer_path, 
            'OUTPUT': dissolved_layer_path
        })
        
        processing.run("native:createspatialindex", {
            'INPUT': dissolved_layer_path
        })
        
        singleparts_layer_path = os.path.join(path_temp, "Fastigheten_singleparts.shp")
        processing.run("native:multiparttosingleparts", {
            'INPUT': dissolved_layer_path, 
            'OUTPUT': singleparts_layer_path
        })
        
        processing.run("native:createspatialindex", {
            'INPUT': singleparts_layer_path
        })    
        
        reprojected_layer_path = os.path.join(path_temp, "Fastigheten_reprojected.shp")
        processing.run("native:reprojectlayer", {
            'INPUT': singleparts_layer_path,
            'TARGET_CRS': 'EPSG:3006',
            'OUTPUT': reprojected_layer_path
        })

        processing.run("native:createspatialindex", {
            'INPUT': reprojected_layer_path
        })     
        
        final_layer = QgsVectorLayer(reprojected_layer_path, "Fastigheten", "ogr")

        expression = '$area * 0.0001'
        output_layer_path = os.path.join(folder_path, "Fastigheten.shp")
        processing.run("native:fieldcalculator", {
            'INPUT': final_layer,
            'FIELD_NAME': 'area',
            'FIELD_TYPE': 0,
            'FIELD_LENGTH': 10,
            'FIELD_PRECISION': 3,
            'FORMULA': expression,
            'OUTPUT': output_layer_path
        })
        
        updated_area = QgsVectorLayer(output_layer_path, "Fastigheten", "ogr")
        if updated_area.isValid():
            QgsProject.instance().addMapLayer(updated_area)
            processing.run("native:createspatialindex", {
                'INPUT': updated_area
            })
        else:
            print("Final updated area layer failed to load!")

#%% ~~ Creating limiting Buffer Zones ~~

if 'updated_area' in locals() and updated_area.isValid():
    hundred_m_buffered_layer_path = os.path.join(path_temp, "Fastigheten_100m_buff.shp")
    processing.run("native:buffer", {
        'INPUT': updated_area,
        'DISTANCE': 100,
        'SEGMENTS': 5,
        'OUTPUT': hundred_m_buffered_layer_path
    })
else:
    print("updated_area layer is not valid, skipping buffer zone creation.")

processing.run("native:createspatialindex", {
    'INPUT': hundred_m_buffered_layer_path
})

five_km_buffered_layer_path = os.path.join(path_temp, "Fastigheten_5km_buff.shp")
processing.run("native:buffer", {
    'INPUT': updated_area,
    'DISTANCE': 5000,
    'SEGMENTS': 25,
    'OUTPUT': five_km_buffered_layer_path
})

processing.run("native:createspatialindex", {
    'INPUT': five_km_buffered_layer_path
})

#%% ~~ Extracting and Updating Neighbouring Estates  ~~

neighbouring_estates = os.path.join(folder_path, "neighbouring_estates.shp")
processing.run("native:extractbylocation", {
    'INPUT':estates_layer,
    'PREDICATE':[0],'INTERSECT':hundred_m_buffered_layer_path,
    'OUTPUT': neighbouring_estates
})

processing.run("native:createspatialindex", {
    'INPUT': neighbouring_estates
})
 
neighbouring_estates_layer = QgsVectorLayer(neighbouring_estates, "neighbouring_estates", "ogr")

feature_groups = defaultdict(list)
for feature in neighbouring_estates_layer.getFeatures():
    key = (feature["BOROUGH"], feature["SECTOR"], feature["SEGMENT"])
    feature_groups[key].append(feature)

reprojected_layers_paths = []

for idx, (group_key, features) in enumerate(feature_groups.items()):
    group_layer = QgsVectorLayer("Polygon?crs=epsg:4326", f"group_{idx}", "memory")
    group_layer_data = group_layer.dataProvider()
    group_layer_data.addAttributes(neighbouring_estates_layer.fields())
    group_layer.updateFields()

    for feature in features:
        group_layer_data.addFeature(feature)

    temp_layer_file = os.path.join(path_temp, f"temp_group_{idx}.shp")
    QgsVectorFileWriter.writeAsVectorFormat(group_layer, temp_layer_file, "UTF-8", group_layer.crs(), "ESRI Shapefile")

    processing.run("native:createspatialindex", {
        'INPUT': temp_layer_file
    })

    dissolved_layer_file = os.path.join(path_temp, f"dissolved_group_{idx}.shp")
    processing.run("native:dissolve", {
        'INPUT': temp_layer_file, 
        'OUTPUT': dissolved_layer_file
    })

    processing.run("native:createspatialindex", {
        'INPUT': dissolved_layer_file
    })

    singlepart_layer_file = os.path.join(path_temp, f"singlepart_group_{idx}.shp")
    processing.run("native:multiparttosingleparts", {
        'INPUT': dissolved_layer_file, 
        'OUTPUT': singlepart_layer_file
    })
    
    processing.run("native:createspatialindex", {
        'INPUT': singlepart_layer_file
    })

    reprojected_layer_file = os.path.join(path_temp, f"reprojected_group_{idx}.shp")
    processing.run("native:reprojectlayer", {
        'INPUT': singlepart_layer_file,
        'TARGET_CRS': 'EPSG:4326',
        'OUTPUT': reprojected_layer_file
    })
    
    processing.run("native:createspatialindex", {
        'INPUT': reprojected_layer_file
    })

    reprojected_layers_paths.append(reprojected_layer_file)

merged_layer_file = os.path.join(path_temp, "merged_final_layer.shp")
processing.run("native:mergevectorlayers", {
    'LAYERS': reprojected_layers_paths,
    'OUTPUT': merged_layer_file
})

merged_layer = QgsVectorLayer(merged_layer_file, "Merged_Reprojected_Final_Layer", "ogr")

processing.run("native:createspatialindex", {
    'INPUT': merged_layer
})

neighbouring_estates_final = os.path.join(path_temp, "Grannar.shp")
processing.run("native:difference", {
    'INPUT': merged_layer,
    'OVERLAY': updated_area,
    'OUTPUT': neighbouring_estates_final
})

processing.run("native:createspatialindex", {
    'INPUT': neighbouring_estates_final
})

neighbouring_estates_layer = QgsVectorLayer(neighbouring_estates_final, "Grannar", "ogr")

feature_groups = defaultdict(list)
for feature in neighbouring_estates_layer.getFeatures():
    key = (feature["BOROUGH"], feature["SECTOR"], feature["SEGMENT"])
    feature_groups[key].append(feature)

reprojected_layers_paths = []

for idx, (group_key, features) in enumerate(feature_groups.items()):
    group_layer = QgsVectorLayer("Polygon?crs=epsg:4326", f"group_{idx}", "memory")
    group_layer_data = group_layer.dataProvider()
    group_layer_data.addAttributes(neighbouring_estates_layer.fields())
    group_layer.updateFields()

    for feature in features:
        group_layer_data.addFeature(feature)

    temp_layer_file = os.path.join(path_temp, f"temp_group_{idx}.shp")
    QgsVectorFileWriter.writeAsVectorFormat(group_layer, temp_layer_file, "UTF-8", group_layer.crs(), "ESRI Shapefile")
    
    processing.run("native:createspatialindex", {
        'INPUT': temp_layer_file
    })

    dissolved_layer_file = os.path.join(path_temp, f"dissolved_group_{idx}.shp")
    processing.run("native:dissolve", {
        'INPUT': temp_layer_file, 
        'OUTPUT': dissolved_layer_file
    })
    
    processing.run("native:createspatialindex", {
        'INPUT': dissolved_layer_file
    })

    singlepart_layer_file = os.path.join(path_temp, f"singlepart_group_{idx}.shp")
    processing.run("native:multiparttosingleparts", {
        'INPUT': dissolved_layer_file, 
        'OUTPUT': singlepart_layer_file
    })

    processing.run("native:createspatialindex", {
        'INPUT': singlepart_layer_file
    })

    reprojected_layer_file = os.path.join(path_temp, f"reprojected_group_{idx}.shp")
    processing.run("native:reprojectlayer", {
        'INPUT': singlepart_layer_file,
        'TARGET_CRS': 'EPSG:4326',
        'OUTPUT': reprojected_layer_file
    })

    processing.run("native:createspatialindex", {
        'INPUT': reprojected_layer_file
    })

    reprojected_layers_paths.append(reprojected_layer_file)

merged_layer_file = os.path.join(path_temp, "merged_final_layer.shp")
processing.run("native:mergevectorlayers", {
    'LAYERS': reprojected_layers_paths,
    'OUTPUT': merged_layer_file
})

merged_layer = QgsVectorLayer(merged_layer_file, "Merged_Reprojected_Final_Layer", "ogr")

processing.run("native:createspatialindex", {
    'INPUT': merged_layer
})

neighbouring_estates_final = os.path.join(path_temp, "Grannar.shp")
processing.run("native:difference", {
    'INPUT': merged_layer,
    'OVERLAY': updated_area,
    'OUTPUT': neighbouring_estates_final
})

neighbouring_estates_layer = QgsVectorLayer(neighbouring_estates_final, "Grannar", "ogr")

reprojected_neighbouring_estates_path = os.path.join(folder_path, "neighbouring_estates_reprojected.shp")

processing.run("native:createspatialindex", {
    'INPUT': neighbouring_estates_layer
})

reprojected_result = processing.run("native:reprojectlayer", {
    'INPUT': neighbouring_estates,
    'TARGET_CRS': 'EPSG:3006',
    'OUTPUT': reprojected_neighbouring_estates_path
}, feedback=None)

reprojected_neighbouring_estates_layer = QgsVectorLayer(reprojected_result['OUTPUT'], "Grannar", "ogr")
QgsProject.instance().addMapLayer(reprojected_neighbouring_estates_layer)
    
processing.run("native:createspatialindex", {
    'INPUT': reprojected_neighbouring_estates_layer
})

#%% ~~ Finding the coordinates of the selected layer ~~

layer_pathing = QgsVectorLayer(five_km_buffered_layer_path, "hejhej", "ogr")
source = five_km_buffered_layer_path

shape = shapefile.Reader(five_km_buffered_layer_path, encoding = "ISO8859-1")

all_points = []
for feature in shape.shapeRecords():
    points = feature.shape.points
    all_points.extend(points)

all_points = [list(i) for i in all_points]

poly_max = np.max(all_points, axis=0)
poly_min = np.min(all_points, axis=0)
poly = [poly_max[0], poly_max[1], poly_min[0], poly_min[1]]

#%% ~~ Picking the correct DEM files ~~

path_dem_clip = os.path.join(path_temp, 'clip')
os.makedirs(path_dem_clip, exist_ok=True)  
    
def process_row(row):
    x = row['x']
    y = row['y']
    file = row['FILENAME']

    if x_min < x < x_max and y_min < y < y_max:
        if not os.path.isfile(os.path.join(path_dem_clip, file)):
            shutil.copy(os.path.join(path_dem, file), path_dem_clip)

df = pd.read_csv(os.path.join(data_path, 'DEM_masterfile.csv'))

df['x'] = df['x'].astype(float)
df['y'] = df['y'].astype(float)

x_max = poly[0]
y_max = poly[1]
x_min = poly[2]
y_min = poly[3]

with ThreadPool(mp.cpu_count()) as pool:
    pool.map(process_row, df.to_dict('records'))
    
#%% ~~ Clipping raster files to extent ~~

merged_raster_path = os.path.join(path_temp, 'merged_raster.tif')

files = [os.path.join(path_dem_clip, f) for f in os.listdir(path_dem_clip) if f.endswith('.tif')]

processing.run("gdal:merge", {
    'INPUT': files,
    'PCT': False,
    'SEPARATE': False,
    'NODATA': None,
    'DATATYPE': None,
    'OPTIONS': '',
    'EXTRA': '',
    'OUTPUT': merged_raster_path
})

clipped_raster_path = os.path.join(folder_path, 'raster_clipped.tif')

processing.run("gdal:cliprasterbymasklayer", {
    'INPUT': merged_raster_path,
    'MASK': updated_area,
    'SOURCE_CRS': None,
    'TARGET_CRS': None,
    'NODATA': 0,
    'ALPHA_BAND': False,
    'CROP_TO_CUTLINE': True,
    'KEEP_RESOLUTION': False,
    'SET_RESOLUTION': False,
    'X_RESOLUTION': None,
    'Y_RESOLUTION': None,
    'MULTITHREADING': False,
    'OPTIONS': '',
    'DATA_TYPE': 0,
    'EXTRA': '',
    'OUTPUT': clipped_raster_path
})

clipped_raster_layer = QgsRasterLayer(clipped_raster_path, "Clipped Raster")
#QgsProject.instance().addMapLayer(clipped_raster_layer)


#%% ~~ Creating grid to extract the slopes by ~~

print('Creating work grid...')

# Check if the layer is valid
if not updated_area.isValid():
    print("Layer failed to load!")
else:
    
    # Create a new field for sum_area if it doesn't exist
    field_name = 'sum_area'
    if field_name not in [field.name() for field in updated_area.fields()]:
        updated_area.dataProvider().addAttributes([QgsField(field_name, QVariant.Double)])
        updated_area.updateFields()
    
    # Calculate the sum of the "area" field for each feature and update the new field
    updated_area.startEditing()
    for feature in updated_area.getFeatures():
        geom = feature.geometry()
        area_value = geom.area()  # Assuming the area field is a calculated geometry field
        feature.setAttribute(updated_area.fields().indexFromName(field_name), area_value)
        updated_area.updateFeature(feature)
    updated_area.commitChanges()
    
    # Define area_hectares using the new "sum_area" field
    for feature in updated_area.getFeatures():
        area_hectares = feature[field_name] * 0.0001  # Convert square meters to hectares
    
        # Here you can print or use the area_hectares as needed
        print(f"Feature ID: {feature.id()}, Area in hectares: {area_hectares}")

    # Initialize total area in hectares
    total_area_hectares = 0

    # Sum the area of all features
    for feature in updated_area.getFeatures():
        total_area_hectares += feature["sum_area"] / 10000  # Convert square meters to hectares

    # Initialize cell size
    cell_size = 2000

    # Function to check if grid size is valid
    def is_grid_size_valid(size):
        try:
            extent = updated_area.extent()
            x_count = int((extent.xMaximum() - extent.xMinimum()) / size)
            y_count = int((extent.yMaximum() - extent.yMinimum()) / size)
            if x_count > 0 and y_count > 0:
                return True
            else:
                return False
        except Exception as e:
            print(f"Exception: {e}")
            return False

    # Reduce cell size until a valid one is found
    while cell_size >= 50:
        if is_grid_size_valid(cell_size):
            break
        cell_size -= 50

    if cell_size < 50:
        print("No valid cell size found")
    else:
        # Print or use the determined cell size
        print("Determined cell size:", cell_size)
        time.sleep(3)



extent = updated_area.extent()

extent_str = f"{extent.xMinimum()},{extent.xMaximum()},{extent.yMinimum()},{extent.yMaximum()}"

grid_output = os.path.join(path_temp, 'grid.shp')
processing.run("native:creategrid", {
    'TYPE':2,
    'EXTENT':extent_str,
    'HSPACING':cell_size,
    'VSPACING':cell_size,
    'HOVERLAY':0,
    'VOVERLAY':0,
    'CRS':QgsCoordinateReferenceSystem('EPSG:3006'),
    'OUTPUT':grid_output})

processing.run("native:createspatialindex", {
    'INPUT': grid_output
})

grid_clipped = os.path.join(path_temp, 'grid_clipped.shp')
processing.run("native:clip", {
    'INPUT':grid_output,
    'OVERLAY':updated_area,
    'OUTPUT':grid_clipped
})

processing.run("native:createspatialindex", {
    'INPUT': grid_clipped
})

grid_layer = QgsVectorLayer(grid_clipped, "grid_layer", "ogr")

raster_layer = QgsRasterLayer(clipped_raster_path, "raster_layer")

output_dir = os.path.join(path_temp, 'temp_dem')
os.makedirs(output_dir, exist_ok=True)  

total_features = grid_layer.featureCount()
current_feature_number = 0

for i, feature in enumerate(grid_layer.getFeatures()):
    current_feature_number += 1
    
    geom = feature.geometry()
    bbox = geom.boundingBox()
    bbox_str = f"{bbox.xMinimum()}, {bbox.xMaximum()}, {bbox.yMinimum()}, {bbox.yMaximum()}"
    output_path = os.path.join(output_dir, f"clipped_{feature.id()}.tif")
    
    params = {
        'INPUT': raster_layer,
        'PROJWIN': bbox_str,
        'OUTPUT': output_path
    }
    processing.run("gdal:cliprasterbyextent", params)
    
    # Update progress bar
    print_progress_bar(current_feature_number, total_features, prefix='Clipping to grid cells:', suffix='Complete', length=50)

# Print new line after complete
print_progress_bar(total_features, total_features, prefix='Clipping to grid cells:', suffix='Complete', length=50)

#%% ~~ Extracting ineligible slopes ~~

def merge_by_aspect(input_folder, aspect_list_1, aspect_list_2, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    print('\nMerging by aspect...')
    total_aspects = len(aspect_list_1)  # Assuming both lists have the same length
    
    for i, (aspect_range_1, aspect_range_2) in enumerate(zip(aspect_list_1, aspect_list_2), start=1):
        
        pattern_1 = f"*aspect_{aspect_range_1[0]}_{aspect_range_1[1]}.shp"
        pattern_2 = f"*aspect_{aspect_range_2[0]}_{aspect_range_2[1]}.shp"
        
        shapefiles = [os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.endswith('.shp') and (fnmatch.fnmatch(f, pattern_1) or fnmatch.fnmatch(f, pattern_2))]
        
        if shapefiles:
            output_file = os.path.join(output_folder, f"bad_slopes_{i}.shp")
            processing.run("native:mergevectorlayers", {
                'LAYERS': shapefiles,
                'CRS': 'EPSG:4326',
                'OUTPUT': output_file
            })
            
            processing.run("native:createspatialindex", {
                'INPUT': output_file
            })
            
        else:
            print(f"No shapefiles matched for aspect ranges {aspect_range_1} and {aspect_range_2}")
        
        # Update progress bar
        print_progress_bar(i, total_aspects, prefix='Merging by aspect:', suffix='Complete', length=50)
    
    # Print new line after complete
    print_progress_bar(total_aspects, total_aspects, prefix='Merging by aspect:', suffix='Complete', length=50)

def get_associated_files(base_filepath):
    base, ext = os.path.splitext(base_filepath)
    return [f"{base}{ext}" for ext in ['.shp', '.shx', '.dbf', '.prj'] if os.path.exists(f"{base}{ext}")]

def merge_shapefiles(shapefiles, output_path):
    """Merge a list of shapefiles into a single output."""
    driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(output_path):
        # Remove all associated files of the output to avoid conflicts
        for file in get_associated_files(output_path):
            os.remove(file)
    out_ds = driver.CreateDataSource(output_path)
    out_layer = None

    for shp in shapefiles:
        ds = driver.Open(shp, 0)
        if ds is None:
            print(f"Warning: Could not open {shp}. Skipping.")
            continue
        layer = ds.GetLayer()
        if out_layer is None:
            out_layer = out_ds.CreateLayer(layer.GetName(), layer.GetSpatialRef(), layer.GetGeomType())
            # Copy fields
            layer_def = layer.GetLayerDefn()
            for i in range(layer_def.GetFieldCount()):
                out_layer.CreateField(layer_def.GetFieldDefn(i))
        for feature in layer:
            out_feat = ogr.Feature(out_layer.GetLayerDefn())
            out_feat.SetGeometry(feature.GetGeometryRef())
            for i in range(feature.GetFieldCount()):
                out_feat.SetField(i, feature.GetField(i))
            out_layer.CreateFeature(out_feat)
            out_feat = None
        ds.Destroy()

    out_ds.Destroy()
    return output_path

def merge_all_layers(input_folder, output_file):
    
    shapefiles = [os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.endswith('.shp')]
    
    if not shapefiles:
        print("No shapefiles found to merge. Check the input folder and file patterns.")
        return
    
    valid_layers = []
    for shapefile_path in shapefiles:
        layer = QgsVectorLayer(shapefile_path, os.path.basename(shapefile_path), 'ogr')
        if not layer.isValid():
            print(f"Invalid shapefile skipped: {shapefile_path}")
            print("Layer error: ", layer.error().message())
        else:
            valid_layers.append(layer)
    
    if not valid_layers:
        print("No valid shapefiles found to merge.")
        return
    
    print('Commencing big merge of extracted slopes...')
    
    try:
        processing.run("native:mergevectorlayers", {
            'LAYERS': valid_layers,
            'OUTPUT': output_file
        })
        print('Big merge finished!')
    except QgsProcessingException as e:
        print(f"Failed to merge layers: {str(e)}")

def process_raster(raster_path, shape_output_folder, final_shape_output_folder, slope_list, aspect_list_1, aspect_list_2):
    if not os.path.exists(final_shape_output_folder):
        os.makedirs(final_shape_output_folder)

    raster_ds = gdal.Open(raster_path)
    crs_wkt = raster_ds.GetProjection()
    gt = raster_ds.GetGeoTransform()
    raster_ds = None

    slope_output = os.path.join(shape_output_folder, os.path.basename(raster_path).replace(".tif", "_slope.tif"))
    aspect_output = os.path.join(shape_output_folder, os.path.basename(raster_path).replace(".tif", "_aspect.tif"))
    slope_ds = gdal.DEMProcessing(slope_output, raster_path, 'slope', computeEdges=True)
    aspect_ds = gdal.DEMProcessing(aspect_output, raster_path, 'aspect', computeEdges=True)
    slope_ds = None
    aspect_ds = None

    slope_ds = gdal.Open(slope_output)
    slope_array = slope_ds.GetRasterBand(1).ReadAsArray()
    slope_ds = None
    aspect_ds = gdal.Open(aspect_output)
    aspect_array = aspect_ds.GetRasterBand(1).ReadAsArray()
    aspect_ds = None

    indices = np.ndindex(slope_array.shape)
    df = pd.DataFrame([(i, j, slope_array[i, j], aspect_array[i, j]) for (i, j) in indices],
                      columns=['row', 'col', 'SLOPE', 'ASPECT'])

    df['geometry'] = df.apply(lambda row: Point(gt[0] + row['col'] * gt[1] + row['row'] * gt[2], 
                                                gt[3] + row['col'] * gt[4] + row['row'] * gt[5]), axis=1)

    gdf = gpd.GeoDataFrame(df, geometry='geometry')
    gdf.crs = pyproj.CRS.from_wkt(crs_wkt)

    for i, slope_threshold in enumerate(slope_list):
        for aspect_range in [aspect_list_1[i], aspect_list_2[i]]:
            condition = (gdf['SLOPE'] > slope_threshold) & (gdf['ASPECT'] >= aspect_range[0]) & (gdf['ASPECT'] <= aspect_range[1])
            filtered_gdf = gdf[condition]

            if filtered_gdf.empty:
                continue

            filename_suffix = f"slope_gt_{str(slope_threshold).replace('.', 'p')}_aspect_{aspect_range[0]}_{aspect_range[1]}"
            output_filename = os.path.basename(raster_path).replace(".tif", f"_{filename_suffix}.shp")
            output_path = os.path.join(final_shape_output_folder, output_filename)

            filtered_gdf.to_file(output_path, driver='ESRI Shapefile')

#%% ~~ Create additional folders ~~

final_points_output = os.path.join(path_temp, 'final_points')
shape_output_folder = os.path.join(path_temp, 'temp_slope_shapes')
final_shape_output_folder = os.path.join(path_temp, 'final_shapes')
big_mash_up_path = os.path.join(path_temp, 'big_mash_up.shp')
new_output_folder = os.path.join(path_temp, 'temp_dem_new')
clipped_path = os.path.join(path_temp, 'clipped')
buffered_clipped_solar = os.path.join(path_temp, 'buffered_clipped_solar')
buffered_clipped_wind = os.path.join(path_temp, 'buffered_clipped_wind')
dissolved_folder_path = os.path.join(path_temp, 'dissolved')
buffered_folder_path = os.path.join(path_temp, 'buffered')
merge_folder_path = os.path.join(path_temp, 'merged')

folders = [shape_output_folder, 
           final_shape_output_folder, 
           new_output_folder, 
           clipped_path, 
           buffered_clipped_solar, 
           buffered_clipped_wind,
           dissolved_folder_path,
           buffered_folder_path,
           merge_folder_path,
           final_points_output
]

for folder_name_loop in folders:
    os.makedirs(folder_name_loop, exist_ok=True)  
    
""" Deleting and recreating  prints.txt """

output_file_path = os.path.join(folder_path, f'prints ({folder_name}).txt')

try:
    os.remove(output_file_path)
except FileNotFoundError:
    pass  

os.close(os.open(output_file_path, os.O_CREAT))

#%% ~~ Extracting ineligible slopes (continued) ~~

search_pattern = os.path.join(output_dir, "*.tif")
clipped_rasters = glob.glob(search_pattern)
total_rasters = len(clipped_rasters)
rasters_processed = 0

for i, raster_path in enumerate(clipped_rasters):
    process_raster(raster_path, shape_output_folder, final_shape_output_folder, slope_list, aspect_list_1, aspect_list_2)
    rasters_processed += 1

    # Update progress bar
    print_progress_bar(rasters_processed, total_rasters, prefix='Extracting slopes:', suffix='Complete', length=50)

# Print new line after complete
print_progress_bar(total_rasters, total_rasters, prefix='Extracting slopes:', suffix='Complete', length=50)

for filename in os.listdir(final_shape_output_folder):
    source_path = os.path.join(final_shape_output_folder, filename)
    destination_path = os.path.join(final_points_output, filename)
    
    try:
        if os.path.exists(destination_path):
            os.remove(destination_path)
 
        shutil.move(source_path, destination_path)
        
    except Exception as e:
        pass

print('Starting the polygonizing process.')
shapefiles = [f for f in os.listdir(final_points_output) if f.endswith('.shp')]
total_files = len(shapefiles)
current_file_number = 0

for i, filename in enumerate(shapefiles):
    current_file_number += 1

    input_path = os.path.join(final_points_output, filename)
    output_path = os.path.join(final_shape_output_folder, filename)

    params = {
        'INPUT': input_path,
        'DISTANCE': 0.5,
        'SEGMENTS': 1,
        'END_CAP_STYLE': 2,
        'JOIN_STYLE': 0,
        'MITER_LIMIT': 2,
        'DISSOLVE': False,
        'OUTPUT': output_path
    }

    processing.run("native:buffer", params)

    # Update progress bar
    print_progress_bar(i + 1, total_files, prefix='Polygonizing files:', suffix='Complete', length=50)

# Print new line after complete
print_progress_bar(total_files, total_files, prefix='Polygonizing files:', suffix='Complete', length=50)
            
files_to_merge = defaultdict(list)
for filename in os.listdir(final_shape_output_folder):
    if filename.startswith("clipped_") and filename.endswith(".shp"):
        identifier = filename.split("_")[1]
        files_to_merge[identifier].append(os.path.join(final_shape_output_folder, filename))

print('Merging bad slopes per cell...')

total_files = len(files_to_merge)
current_file_number = 0

for i, (identifier, files) in enumerate(files_to_merge.items()):
    if not files:
        continue

    merge_output_path = os.path.join(merge_folder_path, f"merged_{identifier}.shp")
    processing.run("native:mergevectorlayers", {
        'LAYERS': files,
        'CRS': None,
        'OUTPUT': merge_output_path
    }, feedback=QgsProcessingFeedback())

    processing.run("native:createspatialindex", {
        'INPUT': merge_output_path
    })

    merged_layer = QgsVectorLayer(merge_output_path, f"merged_{identifier}", "ogr")
    if not merged_layer.isValid():
        print(f"Merged layer {merge_output_path} failed to load.")
        continue

    dissolved_layer = processing.run("native:dissolve", {
        'INPUT': merged_layer,
        'FIELD': [],
        'OUTPUT': 'memory:'
    }, feedback=QgsProcessingFeedback())['OUTPUT']

    dissolved_file_path = os.path.join(dissolved_folder_path, f"dissolved_{identifier}.shp")
    QgsVectorFileWriter.writeAsVectorFormat(dissolved_layer, dissolved_file_path, "UTF-8", merged_layer.crs(), "ESRI Shapefile")

    buffered_layer = processing.run("native:buffer", {
        'INPUT': dissolved_layer,
        'DISTANCE': 1.0,
        'SEGMENTS': 5,
        'OUTPUT': 'memory:'
    }, feedback=QgsProcessingFeedback())['OUTPUT']

    buffered_file_path = os.path.join(buffered_folder_path, f"buffered_{identifier}.shp")
    QgsVectorFileWriter.writeAsVectorFormat(buffered_layer, buffered_file_path, "UTF-8", merged_layer.crs(), "ESRI Shapefile")

    processing.run("native:createspatialindex", {
        'INPUT': buffered_file_path
    })

    # Update progress bar
    print_progress_bar(i + 1, total_files, prefix='Merging bad slopes per cell:', suffix='Complete', length=50)

# Print new line after complete
print_progress_bar(total_files, total_files, prefix='Merging bad slopes per cell:', suffix='Complete', length=50)
    
shapefile_extensions = ['.shp', '.shx', '.dbf', '.prj', '.sbn', '.sbx', '.fbn', '.fbx', '.ain', '.aih', '.ixs', '.mxs', '.atx', '.shp.xml', '.cpg', '.qix']

pattern = re.compile(r'^buffered_\d+$')

processed_base_filenames = []

for file in os.listdir(buffered_folder_path):
    base_name, extension = os.path.splitext(file)
    
    if base_name in processed_base_filenames:
        continue
    
    if not pattern.match(base_name) or extension.lower() not in shapefile_extensions:
        for ext in shapefile_extensions:
            file_to_delete = f"{base_name}{ext}"
            file_path = os.path.join(buffered_folder_path, file_to_delete)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        processed_base_filenames.append(base_name)
    else:
        processed_base_filenames.append(base_name)

merge_by_aspect(final_shape_output_folder, aspect_list_1, aspect_list_2, new_output_folder)

shapefiles = glob.glob(os.path.join(buffered_folder_path, "buffered_*.shp"))
shapefile_paths = [os.path.join(buffered_folder_path, shapefile) for shapefile in shapefiles]

geodataframes = []
for shp in shapefile_paths:
    try:
        gdf = gpd.read_file(shp)
        geodataframes.append(gdf)
    except Exception as e:
        print(f"Failed to read {shp}: {str(e)}")

merged_gdf = gpd.GeoDataFrame(pd.concat(geodataframes, ignore_index=True))

merged_gdf.to_file(big_mash_up_path)

processing.run("native:createspatialindex", {
    'INPUT': big_mash_up_path
})

src_folder_aspects = os.path.join(path_temp, 'temp_dem_new')
dest_folder = folder_path 

search_pattern = os.path.join(src_folder_aspects, '*')

for file_path in glob.glob(search_pattern):
    file_name = os.path.basename(file_path)
    dest_file_path = os.path.join(folder_path, file_name)
    
    if os.path.exists(dest_file_path):
        os.remove(dest_file_path)
    
    shutil.move(file_path, folder_path)
    
#%% ~~ Ruling out areas with ineligible slopes ~~

print('\nRuling out <'+str(neg_bad_slope_area)+' m² areas with ineligible slopes...')

reprojected_layer_path = os.path.join(path_temp, 'big_mash_up_reproj.shp')
processing.run("native:reprojectlayer", {
    'INPUT': big_mash_up_path,
    'TARGET_CRS': 'EPSG:3006',
    'OUTPUT': reprojected_layer_path
})

processing.run("native:createspatialindex", {
    'INPUT': reprojected_layer_path
})

big_buffer = os.path.join(path_temp, 'big_buffer.shp')
processing.run("native:buffer", {
    'INPUT':reprojected_layer_path,
    'DISTANCE':2,
    'SEGMENTS':5,
    'END_CAP_STYLE':0,
    'JOIN_STYLE':0,
    'MITER_LIMIT':2,
    'DISSOLVE':False,
    'OUTPUT':big_buffer
})

processing.run("native:createspatialindex", {
    'INPUT': big_buffer
})

neg_buffer = os.path.join(path_temp, 'neg_buffer.shp')
processing.run("native:buffer", {
    'INPUT':big_buffer,
    'DISTANCE':-7,
    'SEGMENTS':5,
    'END_CAP_STYLE':0,
    'JOIN_STYLE':0,
    'MITER_LIMIT':2,
    'DISSOLVE':False,
    'OUTPUT':neg_buffer
})

processing.run("native:createspatialindex", {
    'INPUT': neg_buffer
})

four_buffer = os.path.join(path_temp, 'four_buffer.shp')
processing.run("native:buffer", {
    'INPUT':neg_buffer,
    'DISTANCE':4,
    'SEGMENTS':5,
    'END_CAP_STYLE':0,
    'JOIN_STYLE':0,
    'MITER_LIMIT':2,
    'DISSOLVE':False,
    'OUTPUT':four_buffer
})

processing.run("native:createspatialindex", {
    'INPUT': four_buffer
})

singlepart_slopes = os.path.join(path_temp, 'bad_slopes_single.shp')
processing.run("native:multiparttosingleparts", {
    'INPUT':four_buffer,
    'OUTPUT':singlepart_slopes
})

processing.run("native:createspatialindex", {
    'INPUT': singlepart_slopes
})

add_field = os.path.join(path_temp, 'add_field.shp')
processing.run("native:addfieldtoattributestable", {
    'INPUT':singlepart_slopes,
    'FIELD_NAME':'area','FIELD_TYPE':1,
    'FIELD_LENGTH':10,
    'FIELD_PRECISION':0,
    'OUTPUT':add_field
})

processing.run("native:createspatialindex", {
    'INPUT': add_field
})

field_calc = os.path.join(path_temp, 'field_calc.shp')
processing.run("native:fieldcalculator", {
    'INPUT':add_field,
    'FIELD_NAME':'area',
    'FIELD_TYPE':0,
    'FIELD_LENGTH':0,
    'FIELD_PRECISION':0,
    'FORMULA':'$area',
    'OUTPUT':field_calc
})

processing.run("native:createspatialindex", {
    'INPUT': field_calc
})

bad_slopes_area = os.path.join(folder_path, 'bad_slopes_area.shp')
processing.run("native:extractbyexpression", {
    'INPUT':field_calc,
    'EXPRESSION':'area > ' + str(neg_bad_slope_area),
    'OUTPUT':bad_slopes_area
})

processing.run("native:createspatialindex", {
    'INPUT': bad_slopes_area
})

print('Finished ruling out the areas!')

#%% ~~ Creating contour ~~

print('\nCreating contour lines...')

contour_lines_layer = os.path.join(folder_path, 'contour_lines.shp')
processing.run("gdal:contour", {
    'INPUT': merged_raster_path,
    'BAND': 1,
    'INTERVAL': 5,
    'FIELD_NAME': 'ELEV',
    'CREATE_3D': False,
    'IGNORE_NODATA': False,
    'NODATA': None,
    'OFFSET': 0,
    'EXTRA': '',
    'OUTPUT': contour_lines_layer
})

processing.run("native:createspatialindex", {
    'INPUT': contour_lines_layer
})

contour_layer = QgsVectorLayer(contour_lines_layer, "Contour Lines", "ogr")
if not contour_layer.isValid():
    print("Layer failed to load!")
else:
    QgsProject.instance().addMapLayer(contour_layer)
    pass

print('Finished creating contour lines!')

#%% ~~ Clipping and buffering layers ~~

print('\nClipping and buffering national data to the estate, plus a 4km radius...')

total_layers = len(layers)
layers_processed = 0

total_layers = len(layers)
layers_processed = 0

for i, layer_info in enumerate(layers):
    if len(layer_info) < 5:
        print(f"Skipping layer due to insufficient information: {layer_info}")
        continue

    layer_filename = layer_info[0]
    solar_buffer_distance = layer_info[3]
    wind_buffer_distance = layer_info[4]

    layer_to_clip = QgsVectorLayer(os.path.join(data_path, layer_filename), layer_filename, "ogr")
    if not layer_to_clip.isValid():
        print(f"Layer {layer_filename} is not valid and cannot be processed.")
        continue

    overlay_layer = QgsVectorLayer(five_km_buffered_layer_path, "Overlay Layer", "ogr")
    if not overlay_layer.isValid() or overlay_layer.geometryType() != QgsWkbTypes.PolygonGeometry:
        print(f"Overlay layer is not suitable for clipping points (either not loaded or not a polygon).")
        continue

    clipped_output_path = os.path.join(clipped_path, layer_filename)
    clipping_params = {
        'INPUT': layer_to_clip,
        'OVERLAY': overlay_layer,
        'OUTPUT': clipped_output_path
    }

    try:
        clipped_layer = processing.run("native:clip", clipping_params)["OUTPUT"]
    except Exception as e:
        print(f"Error clipping {layer_filename}: {str(e)}")
        continue

    # Example solar buffering operation, if applicable
    if solar_buffer_distance > 0:
        solar_buffer_filename = f"{os.path.splitext(layer_filename)[0]}.shp"
        solar_buffer_output_path = os.path.join(buffered_clipped_solar, solar_buffer_filename)
        solar_buffer_params = {
            'INPUT': clipped_layer,
            'DISTANCE': solar_buffer_distance,
            'SEGMENTS': 5,
            'OUTPUT': solar_buffer_output_path
        }
        try:
            processing.run("native:buffer", solar_buffer_params)
            processing.run("native:createspatialindex", {'INPUT': solar_buffer_output_path})
        except Exception as e:
            print(f"Error buffering solar layer for {layer_filename}: {str(e)}")

    # Example wind buffering operation, if applicable
    if wind_buffer_distance > 0:
        wind_buffer_filename = f"{os.path.splitext(layer_filename)[0]}.shp"
        wind_buffer_output_path = os.path.join(buffered_clipped_wind, wind_buffer_filename)
        wind_buffer_params = {
            'INPUT': clipped_layer,
            'DISTANCE': wind_buffer_distance,
            'SEGMENTS': 5, 
            'OUTPUT': wind_buffer_output_path
        }
        try:
            processing.run("native:buffer", wind_buffer_params)
            processing.run("native:createspatialindex", {'INPUT': wind_buffer_output_path})
        except Exception as e:
            print(f"Error buffering wind layer for {layer_filename}: {str(e)}")

    # Update progress bar
    print_progress_bar(i + 1, total_layers, prefix='Clipping to national data:', suffix='Complete', length=50)

# Print new line after complete
print_progress_bar(total_layers, total_layers, prefix='Clipping to national data:', suffix='Complete', length=50)

shutil.copytree(clipped_path, folder_path, dirs_exist_ok=True)

#%% ~~ Creating centroids from orignal point layers (doh-work-around) ~~

def process_polygon_layers(folder_path):
    found_files = False
    for filename in os.listdir(folder_path):
        if filename.endswith("_poly.shp"):
            found_files = True
            try:
                full_path = os.path.join(folder_path, filename)
                gdf = gpd.read_file(full_path)
                
                gdf['geometry'] = gdf['geometry'].centroid
                
                new_filename = filename.replace("_poly", "")  # Remove "_poly" from the filename
                centroid_path = os.path.join(folder_path, new_filename)
                gdf.to_file(centroid_path)
                
                base_name = filename[:-4]  # Remove the '.shp' extension
                extensions = ['.shp', '.shx', '.dbf', '.prj', '.cpg', '.qix', '.fix', '.sbn', '.sbx', '.fbn', '.fbx', '.ain', '.aih', '.ixs', '.mxs', '.atx', '.shp.xml']
                for ext in extensions:
                    file_to_remove = os.path.join(folder_path, base_name + ext)
                    if os.path.exists(file_to_remove):
                        os.remove(file_to_remove)
                  
            except Exception as e:
                pass
                

    if not found_files:
        print("No files ending with '_poly.shp' found in the specified folder.")

process_polygon_layers(folder_path)

#%% ~~ Clipping the layer to surrounding extent ~~



total_layers = len(layers)

for i, layer_info in enumerate(layers):
    layer_filename, _, layer_name, *__ = layer_info

    full_layer_path = os.path.join(buffered_clipped_solar, layer_filename)
    layer = QgsVectorLayer(full_layer_path, layer_name, "ogr")

    if not layer.isValid():
        continue

    result = processing.run("native:difference", {
        'INPUT': updated_area,
        'OVERLAY': layer,
        'OUTPUT': 'memory:'
    }, feedback=QgsProcessingFeedback())

    if result['OUTPUT'].featureCount() == 0:
        pass

    updated_area = result['OUTPUT']

    print_progress_bar(i + 1, total_layers, prefix='Checking obsticles (solar):', suffix='Complete', length=50)

print_progress_bar(total_layers, total_layers, prefix='Checking obsticles (solar):', suffix='Complete', length=50)

diff_area = os.path.join(path_temp, 'diff_area.shp')

error = QgsVectorFileWriter.writeAsVectorFormat(updated_area, diff_area, "utf-8", driverName="ESRI Shapefile")
if error[0] == QgsVectorFileWriter.NoError:
    pass
else:
    print(f"Failed to save the diff_area file: {error[1]}")

byggbar_minus_slopes = os.path.join(path_temp, 'byggbar_minus_slopes.shp')

if not os.path.exists(diff_area):
    print(f"{diff_area} does not exist. Skipping the block.")
else:
    if updated_area.isValid() and updated_area.featureCount() > 0:
        error = QgsVectorFileWriter.writeAsVectorFormat(updated_area, diff_area, "utf-8", driverName="ESRI Shapefile")
        if error[0] == QgsVectorFileWriter.NoError:
            pass
        else:
            print("Failed to save the file:", error[1])
    else:
        print("Final updated_area layer is empty.")

    final_byggbar = os.path.join(path_temp, 'almost_done_solar.shp')

    processing.run("native:difference", {
        'INPUT': diff_area,
        'OVERLAY': bad_slopes_area,
        'OUTPUT': final_byggbar
    })

    processing.run("native:createspatialindex", {
        'INPUT': final_byggbar
    })

    final_byggbar_no_holes = os.path.join(path_temp, 'buildable_solar_no_holes.shp')

    processing.run("native:deleteholes", {
        'INPUT':final_byggbar,
        'MIN_AREA':0,
        'OUTPUT':final_byggbar_no_holes
    })
    
    processing.run("native:createspatialindex", {
        'INPUT': final_byggbar_no_holes
    })

    not_final_byggbar = os.path.join(path_temp, 'buildable_solar_not_final.shp')
    
    processing.run("native:buffer", {
        'INPUT':final_byggbar_no_holes,
        'DISTANCE':-10,
        'SEGMENTS':5,
        'END_CAP_STYLE':0,
        'JOIN_STYLE':0,
        'MITER_LIMIT':2,
        'DISSOLVE':False,
        'OUTPUT':not_final_byggbar
    })

    processing.run("native:createspatialindex", {
        'INPUT': not_final_byggbar
    })

    final_byggbar_igen = os.path.join(path_temp, 'almost_done_solar_igen.shp')

    processing.run("native:difference", {
        'INPUT': not_final_byggbar,
        'OVERLAY': bad_slopes_area,
        'OUTPUT': final_byggbar_igen
    })

    processing.run("native:createspatialindex", {
        'INPUT': final_byggbar_igen
    })

    final_byggbar_igen_igen = os.path.join(path_temp, 'almost_done_solar_igen_igen.shp')

    processing.run("native:dissolve", {
        'INPUT':final_byggbar_igen,
        'FIELD':[],
        'OUTPUT':final_byggbar_igen_igen
    })

    processing.run("native:createspatialindex", {
        'INPUT': final_byggbar_igen_igen
    })

    final_byggbar_multi = os.path.join(folder_path, 'buildable_solar.shp')

    processing.run("native:multiparttosingleparts", {
        'INPUT': final_byggbar_igen_igen,
        'OUTPUT':final_byggbar_multi
    })
    
    processing.run("native:createspatialindex", {
        'INPUT': final_byggbar_multi
    })

    if os.path.exists(final_byggbar_multi):
        byggbar = QgsVectorLayer(final_byggbar_multi, "Lämplig yta - Sol", "ogr")
        if byggbar.isValid():
            QgsProject.instance().addMapLayer(byggbar)
            
            symbol = byggbar.renderer().symbol()
            symbol.setColor(QColor.fromRgb(255, 255, 255))
            byggbar.triggerRepaint()
            
            layer = QgsProject.instance().mapLayersByName('Lämplig yta - Sol')[0]
            
            with edit(layer):
                total_area = 0
                for feature in layer.getFeatures():
                    geom = feature.geometry()
                    area_hectares = geom.area() / 10000
                    
                    feature['AREA'] = area_hectares
                    total_area += area_hectares
                    
                    layer.updateFeature(feature)
                
                for feature in layer.getFeatures():
                    feature['sum_area'] = total_area
                    layer.updateFeature(feature)
            
            layer.commitChanges()
        else:
            print("Failed to load the layer. Please check the file path and data.")
    else:
        print("Output file does not exist.")
        
total_layers = len(layers)

for i, layer_info in enumerate(layers):
    layer_filename, _, layer_name, *__ = layer_info
    
    full_layer_path_wind = os.path.join(buffered_clipped_wind, layer_filename)
    layer = QgsVectorLayer(full_layer_path_wind, layer_name, "ogr")
    
    if not layer.isValid():
        continue
    
    result = processing.run("native:difference", {
        'INPUT': updated_area,
        'OVERLAY': layer,
        'OUTPUT': 'memory:'
    }, feedback=QgsProcessingFeedback())

    if result['OUTPUT'].featureCount() == 0:
        pass
        
    updated_area = result['OUTPUT']
    
    print_progress_bar(i + 1, total_layers, prefix='Checking obsticles (wind):', suffix='Complete', length=50)

print_progress_bar(total_layers, total_layers, prefix='Checking obsticles (wind):', suffix='Complete', length=50)


diff_area_wind = os.path.join(path_temp, 'diff_area_wind.shp')

error = QgsVectorFileWriter.writeAsVectorFormat(updated_area, diff_area_wind, "utf-8", driverName="ESRI Shapefile")
if error[0] == QgsVectorFileWriter.NoError:
    pass
else:
    print(f"Failed to save the diff_area_wind file: {error[1]}")

byggbar_minus_wet = os.path.join(folder_path, 'wet_soil.shp')

if not os.path.exists(diff_area_wind):
    print(f"{diff_area_wind} does not exist. Skipping the block.")
else:
    if updated_area.isValid() and updated_area.featureCount() > 0:
        error = QgsVectorFileWriter.writeAsVectorFormat(updated_area, diff_area_wind, "utf-8", driverName="ESRI Shapefile")
        if error[0] == QgsVectorFileWriter.NoError:
            pass
        else:
            print("Failed to save the file:", error[1])
    else:
        pass

    final_byggbar_wind = os.path.join(path_temp, 'almost_done_wind.shp')

    processing.run("native:difference", {
        'INPUT': diff_area_wind,
        'OVERLAY': byggbar_minus_wet,
        'OUTPUT': final_byggbar_wind
    })

    processing.run("native:createspatialindex", {
        'INPUT': final_byggbar_wind
    })

    final_byggbar_wind_igen = os.path.join(path_temp, 'almost_done_wind_igen.shp')

    processing.run("native:dissolve", {
        'INPUT':final_byggbar_wind,
        'FIELD':[],
        'OUTPUT':final_byggbar_wind_igen
    })

    processing.run("native:createspatialindex", {
        'INPUT': final_byggbar_wind_igen
    })

    final_byggbar_multi_wind = os.path.join(folder_path, 'buildable_wind.shp')

    processing.run("native:multiparttosingleparts", {
        'INPUT': final_byggbar_wind_igen,
        'OUTPUT':final_byggbar_multi_wind
    })
    
    processing.run("native:createspatialindex", {
        'INPUT': final_byggbar_multi_wind
    })

    if os.path.exists(final_byggbar_multi_wind):
        byggbar_wind = QgsVectorLayer(final_byggbar_multi_wind, "Lämplig yta - Vind", "ogr")
        if byggbar_wind.isValid():
            QgsProject.instance().addMapLayer(byggbar_wind)
            
            symbol = byggbar_wind.renderer().symbol()
            symbol.setColor(QColor.fromRgb(255, 255, 255))
            byggbar_wind.triggerRepaint()
            
            layer = QgsProject.instance().mapLayersByName('Lämplig yta - Vind')[0]
            
            with edit(layer):
                total_area = 0
                for feature in layer.getFeatures():
                    geom = feature.geometry()
                    area_hectares = geom.area() / 10000
                    
                    feature['AREA'] = area_hectares
                    total_area += area_hectares
                    
                    layer.updateFeature(feature)
                
                for feature in layer.getFeatures():
                    feature['sum_area'] = total_area
                    layer.updateFeature(feature)
            
            layer.commitChanges()
        else:
            print("Failed to load the layer. Please check the file path and data.")
    else:
        print("Output file does not exist.")

file_paths = [
    os.path.join(folder_path, 'roads.shp'),
    os.path.join(folder_path, 'roads.shx'),
    os.path.join(folder_path, 'roads.dbf'),
    os.path.join(folder_path, 'roads.prj')
]

for file_path in file_paths:
    if os.path.exists(file_path):
        os.remove(file_path)
        pass
    else:
        print(f"File {file_path} does not exist.")

#%% ~~ Intermediate step: adding satellite imagery, roads and creating folders

service_url = "mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}" 
service_uri = "type=xyz&zmin=0&zmax=21&url=https://"+requests.utils.quote(service_url)
tms_layer = iface.addRasterLayer(service_uri, "Google Sat", "wms")

service_url = "mt1.google.com/vt/lyrs=h&x={x}&y={y}&z={z}" 
service_uri = "type=xyz&zmin=0&zmax=21&url=https://"+requests.utils.quote(service_url)
tms_layer = iface.addRasterLayer(service_uri, "Google Roads", "wms")

folders_ = {
    "no_folder": project.layerTreeRoot(),
    "wind": project.layerTreeRoot().addGroup("Vind"),
    "solar": project.layerTreeRoot().addGroup("Sol"),
    "misc": project.layerTreeRoot().addGroup("Annat"),
    "slopes": project.layerTreeRoot().addGroup("Branta sluttningar")
}

folders_["wind"].setItemVisibilityChecked(False)
folders_["solar"].setItemVisibilityChecked(False)
folders_["misc"].setItemVisibilityChecked(False)
folders_["slopes"].setItemVisibilityChecked(False)

#%% ~~ Adding the layers ~~

def delete_empty_shapefiles(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(".shp"):
            shp_path = os.path.join(folder_path, filename)
          
            driver = ogr.GetDriverByName('ESRI Shapefile')
            dataSource = driver.Open(shp_path, 0)  # 0 means read-only
          
            if dataSource is None:
                continue
          
            layer = dataSource.GetLayer()
          
            if layer.GetFeatureCount() == 0:
                for ext in ['.shp', '.dbf', '.shx', '.prj']:
                    file_to_delete = shp_path.replace('.shp', ext)
                    if os.path.exists(file_to_delete):
                        os.remove(file_to_delete)

delete_empty_shapefiles(folder_path)

def apply_no_special_styling(symbol, color):
    symbol.setColor(QColor(color))

def apply_arrow_styling(symbol, layer):
    svg_layer = QgsSvgMarkerSymbolLayer(svg_path)
    svg_layer.setSize(5)

    rotation_expression = QgsProperty.fromExpression('"DIRECTION"')
    svg_layer.setDataDefinedProperty(QgsSvgMarkerSymbolLayer.PropertyAngle, rotation_expression)
    
    symbol = QgsMarkerSymbol()
    symbol.changeSymbolLayer(0, svg_layer)
    
    renderer = QgsSingleSymbolRenderer(symbol)
    
    layer.setRenderer(renderer)

    layer.triggerRepaint()
    iface.layerTreeView().refreshLayerSymbology(layer.id())
    layer.setName(layer.name().replace("_poly", ""))

def apply_minus_poly_styling(layer):
    layer.setName(layer.name().replace("_poly", ""))

def apply_size_1_styling(symbol):
    symbol.symbolLayer(0).setWidth(1)

def apply_size_4_styling(symbol):
    symbol.symbolLayer(0).setWidth(1.1)

def apply_trans_15_styling(symbol):
    symbol.setOpacity(0.85)  # 85% opacity, which is 15% transparency

def apply_dotted_styling(layer):
    fill_symbol = QgsFillSymbol.createSimple({
        'style': 'no',
        'outline_style': 'dash',
        'outline_color': '#cccccc',
        'outline_width': '0.1'
    })
    layer.renderer().setSymbol(fill_symbol)

def apply_soil_styling(layer):
    categories = []
    unique_values = layer.dataProvider().uniqueValues(layer.fields().indexFromName("TYPE"))
    color1 = QColor("#e6a55c")
    color2 = QColor("#5e3506")
    for i, value in enumerate(unique_values):
        r = int(color1.red() + (color2.red() - color1.red()) * i / len(unique_values))
        g = int(color1.green() + (color2.green() - color1.green()) * i / len(unique_values))
        b = int(color1.blue() + (color2.blue() - color1.blue()) * i / len(unique_values))
        category_color = QColor(r, g, b)
        category_symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        category_symbol.setColor(category_color)
        category = QgsRendererCategory(value, category_symbol, str(value))
        categories.append(category)
    renderer = QgsCategorizedSymbolRenderer("TYPE", categories)
    layer.setRenderer(renderer)

def apply_polka_styling(symbol):
    fill_symbol = QgsSimpleFillSymbolLayer()
    fill_symbol.setBrushStyle(Qt.BDiagPattern)
    symbol.changeSymbolLayer(0, fill_symbol)
    
def apply_apolka_styling(symbol):
    fill_symbol = QgsSimpleFillSymbolLayer()
    fill_symbol.setBrushStyle(Qt.FDiagPattern)
    symbol.changeSymbolLayer(0, fill_symbol)

def apply_road_styling(layer, color):
    symbol = QgsLineSymbol()

    outer_line = QgsSimpleLineSymbolLayer.create({
        'color': 'black',
        'width': '1.2',
        'joinstyle': 'Round',
        'capstyle': 'Round'
    })
    
    inner_line = QgsSimpleLineSymbolLayer.create({
        'color': color,
        'width': '1',
        'joinstyle': 'Round',
        'capstyle': 'Round'
    })
    
    symbol.appendSymbolLayer(outer_line)
    symbol.appendSymbolLayer(inner_line)
    
    layer.renderer().setSymbol(symbol)

def apply_rail_styling(layer, color):
    symbol = QgsLineSymbol()
    marker_layer = QgsMarkerLineSymbolLayer.create({
        'width': '2.4',
        'color': color
    })
    marker_layer.setSubSymbol(QgsMarkerSymbol.createSimple({
        'name': 'walking',
        'color': color,
        'width': '2.4',
    }))
    
    symbol.appendSymbolLayer(marker_layer)
    
    layer.renderer().setSymbol(symbol)

def apply_walking_styling(layer, color):
    symbol = QgsLineSymbol()
    marker_layer = QgsMarkerLineSymbolLayer.create({
        'width': '1',
        'color': color
    })
    marker_layer.setSubSymbol(QgsMarkerSymbol.createSimple({
        'name': 'walking',
        'color': color,
        'width': '0.8',
    }))
    
    symbol.appendSymbolLayer(marker_layer)
    
    layer.renderer().setSymbol(symbol)

def apply_bike_styling(layer, color):
    symbol = QgsLineSymbol()

    outer_line = QgsSimpleLineSymbolLayer.create({
        'color': 'black',
        'width': '2',
        'joinstyle': 'Round',
        'capstyle': 'Round'
    })
    
    inner_line = QgsSimpleLineSymbolLayer.create({
        'color': color,
        'width': '1.46',
        'joinstyle': 'Round',
        'capstyle': 'Round'
    })
    
    symbol.appendSymbolLayer(outer_line)
    symbol.appendSymbolLayer(inner_line)
    
    layer.renderer().setSymbol(symbol)

def apply_special_styling(layer, special, layer_type, color):
    symbol = QgsSymbol.defaultSymbol(layer.geometryType())
    if special == "none":
        apply_no_special_styling(symbol, color)
    elif special == "arrow":
        apply_arrow_styling(symbol, layer)
    elif special == "minus_poly":
        apply_minus_poly_styling(layer)
    elif special == "size 1":
        apply_size_1_styling(symbol)
    elif special == "size 4":
        apply_size_4_styling(symbol)
    elif special == "trans 15":
        apply_trans_15_styling(symbol)
    elif special == "dotted":
        apply_dotted_styling(layer)
        return 
    elif special == "soil":
        apply_soil_styling(layer)
        return 
    elif special == "polka":
        apply_polka_styling(symbol)
    elif special == "apolka":
        apply_apolka_styling(symbol)
    elif special == "road":
        apply_road_styling(layer, color)
        return
    elif special == "rail":
        apply_rail_styling(layer, color)
        return
    elif special == "walking":
        apply_walking_styling(layer, color)
        return
    elif special == "bike":
        apply_bike_styling(layer, color)
        return
    
    if special not in ["dotted", "soil", "road", "rail", "walking", "bike"]:
        symbol.setColor(QColor(color))
    
    layer.renderer().setSymbol(symbol)

total_layers = len(layers)

for i, layer_info in enumerate(layers):
    file_path = os.path.join(folder_path, layer_info[0])
    color = layer_info[1]
    layer_name = layer_info[2]
    solar_buffer = layer_info[3]
    wind_buffer = layer_info[4]
    layer_type = layer_info[5]
    special = layer_info[6]
    folder = layer_info[7]
    visibility = layer_info[8]

    if special in ["arrow", "minus_poly"]:
        file_path = file_path.replace("_poly", "")

    layer = QgsVectorLayer(file_path, layer_name, "ogr")
    if not layer.isValid():
        continue
    else:
        pass

    apply_special_styling(layer, special, layer_type, color)

    project.addMapLayer(layer, False)
    layer_tree_layer = folders_[folder].addLayer(layer)
    if layer_tree_layer:
        layer_tree_layer.setItemVisibilityChecked(visibility == 'show')
    else:
        print(f"Failed to add layer to project: {layer_name}")

    # Update progress bar
    print_progress_bar(i + 1, total_layers, prefix='Adding layers to the project:', suffix='Complete', length=50)

# Print new line after complete
print_progress_bar(total_layers, total_layers, prefix='Adding layers to the project:', suffix='Complete', length=50)

layer_path = os.path.join(folder_path, 'water_flow.shp')
layer = None

for lyr in QgsProject.instance().mapLayers().values():
    if lyr.source() == layer_path:
        layer = lyr
        break

if not layer or layer.geometryType() != QgsWkbTypes.PointGeometry:
    print("The layer could not be found or is not a point geometry layer.")
else:
    svg_layer = QgsSvgMarkerSymbolLayer(svg_path)
    svg_layer.setSize(3)  # Set the size of the symbol
    svg_layer.setColor(QColor('#006eff'))  # Set the color of the symbol

    rotation_expression = QgsProperty.fromExpression('"DIRECTION"')
    svg_layer.setDataDefinedProperty(QgsSvgMarkerSymbolLayer.PropertyAngle, rotation_expression)
    
    symbol = QgsMarkerSymbol()
    symbol.changeSymbolLayer(0, svg_layer)
    
    renderer = QgsSingleSymbolRenderer(symbol)
    
    layer.setRenderer(renderer)

    layer.triggerRepaint()
    iface.layerTreeView().refreshLayerSymbology(layer.id())

#%% ~~ Adding data from "Artportalen" ~~

print('\nFetching data from Artportalen...')

wms_url = 'https://sosgeo.artdata.slu.se/geoserver/SOS/ows?'

layers_to_add = {
    'SpeciesObservationsRedlisted': 'Rödlistad artobservation'
}

for layer_name, layer_title in layers_to_add.items():
    uri = f"crs=EPSG:3006&layers={layer_name}&styles=&format=image/png&url={wms_url}"
    
    wms_layer = QgsRasterLayer(uri, layer_title, 'wms')
    QgsProject.instance().addMapLayer(wms_layer)

print('Data from Artportalen added!')

#%% ~~ Starting prints ~~

formatted_folder_name = ' '.join(
    word.capitalize() if ':' not in word else ':'.join([part.capitalize() for part in word.split(':')])
    for word in folder_name.split()
)

gdf_estate = gpd.read_file(output_layer_path)

gdf_estate['area_ha'] = gdf_estate.geometry.area / 10000
total_area_ha = gdf_estate['area_ha'].sum()

folder_name_print = formatted_folder_name.replace("-", ":")  

save_print_to_file(folder_name_print+':')
save_print_to_file(f"Area: {total_area_ha:.2f} ha")
for tariffzone in gdf_estate['TARIFFZONE']:
    save_print_to_file('Tariff zone: SE'+str(tariffzone))
    
    
    
    


# input_shapefile_path = os.path.join(data_path, 'area_concessions.shp')  # Change to your actual input file

# # Load the shapefiles
# clip_layer = gpd.read_file(output_layer_path)
# input_layer = gpd.read_file(input_shapefile_path)

# # Ensure CRS match
# if clip_layer.crs != input_layer.crs:
#     input_layer = input_layer.to_crs(clip_layer.crs)

# # Perform spatial clip
# clipped_layer = gpd.overlay(input_layer, clip_layer, how="intersection")

# # Extract unique values from the "FöretagNa" field
# if "FöretagNa" in clipped_layer.columns:
#     unique_companies = clipped_layer["FöretagNa"].dropna().unique()
#     print("Unique values in FöretagNa field within the clipped area:")
#     for company in unique_companies:
#         print(company)
# else:
#     print("Field 'FöretagNa' not found in the input shapefile.")

# # Optionally, save the clipped result
# clipped_output_path = os.path.join(path_temp, "area_concessions_clipped.shp")
# clipped_layer.to_file(clipped_output_path)


    
    
    
    

#%% ~~ Embedding STRÅNG ~~

parameter_descriptions = {
    117: "Global Horizontal Irradiation",
    118: "Direct Normal Irradiation",
    122: "Diffuse Horizontal Irradiation"
}

strång_area = gpd.read_file(output_layer_path)

source_crs = "EPSG:3006"
target_crs = "EPSG:4326"

strång_area = strång_area.to_crs(target_crs)

if not strång_area.empty:
    centroid = strång_area.geometry.centroid.iloc[0]

    lon, lat = centroid.x, centroid.y
    save_print_to_file(f'\nIrradiance data for {lat:.4f}, {lon:.4f}:')
    
    parameters = [117, 118, 122]
    
    for param in parameters:
        url = f"https://opendata-download-metanalys.smhi.se/api/category/strang1g/version/1/geotype/point/lon/{lon:.4f}/lat/{lat:.4f}/parameter/{param}/data.json?from=2010-01-01&to=2023-12-31"
        
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            if data and isinstance(data, list):
                file_path = os.path.join(folder_path, f'STRÅNG_param_{param}.csv')
                
                with open(file_path, 'w', newline='', encoding='utf-8') as file:
                    fieldnames = data[0].keys() if data else []
                    
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    
                    for row in data:
                        writer.writerow(row)
            else:
                print(f"Data for parameter {param} is not in expected format (list of dictionaries).")
        else:
            print(f"Failed to fetch data for parameter {param}. Status code: {response.status_code}")
else:
    print("No features found in the shapefile.")

try:
    param_117_value = None  
    
    for param in parameters:
        file_path = os.path.join(folder_path, f'STRÅNG_param_{param}.csv')
        
        if os.path.exists(file_path):
            description = parameter_descriptions.get(param, "Unknown Parameter")
            
            df = pd.read_csv(file_path, parse_dates=['date_time'])

            df = df[df['value'] > 0]

            df.set_index('date_time', inplace=True)

            daily_sum = df['value'].resample('D').sum()

            average_daily_sum = daily_sum.mean()

            average_yearly_kwh_per_sqm = average_daily_sum * 365 / 1000
            
            average_daily_sum_hourly = average_yearly_kwh_per_sqm * 1000 / 8765
            
            average_irradiance = df['value'].mean() 
            save_print_to_file(f'{description}: {average_yearly_kwh_per_sqm:.2f} kWh/m² ({average_daily_sum_hourly:.2f} W/m²)')

            if param == 117:
                param_117_value = average_yearly_kwh_per_sqm

            monthly_avg = df.resample('M').mean()

            plt.figure(figsize=(10, 6))
            plt.plot(np.array(df.index), df['value'].values, label=f'Irradiance ({description})', alpha=0.5)
            plt.plot(np.array(monthly_avg.index), monthly_avg['value'].values, color='red', label=f'Monthly Average ({description})', linewidth=2)
            plt.title(f'Irradiance Over Time ({description})')
            plt.xlabel('Date')
            plt.ylabel('Irradiance (W/m²)')
            plt.legend()
            plt.tight_layout()
            plt.savefig(os.path.join(folder_path, f'irradiance_plot_param_{param}.png'))
            plt.close()
        else:
            print(f"The file 'STRÅNG_param_{param}.csv' was not found. Please check the file path and try again.")

    if param_117_value is not None:
        modified_value = param_117_value * 1.053
        save_print_to_file(f"Specific photovoltaic power output: {modified_value:.2f} kWh/kWp")
    else:
        print("Parameter 117 value was not found.")
    
except FileNotFoundError:
    print(f"One or more files were not found. Please check the file paths and try again.")




#%% ~~ Calculating the average solar inclination ~~

def calculate_hourly_solar_elevation(latitude, longitude, date):
    observer = Observer(latitude=latitude, longitude=longitude)
    elevations = []

    for hour in range(24):
        time = datetime.combine(date, datetime.min.time()) + timedelta(hours=hour)
        elev = elevation(observer, time)
        if elev > 0:  
            elevations.append(elev)
    return elevations

def average_hourly_solar_elevation(latitude, longitude, start_date, end_date):
    total_elevations = []
    current_date = start_date

    while current_date <= end_date:
        elevations = calculate_hourly_solar_elevation(latitude, longitude, current_date)
        total_elevations.extend(elevations)
        current_date += timedelta(days=1)

    average_elevation = sum(total_elevations) / len(total_elevations) if total_elevations else 0
    return average_elevation

gdf = gpd.read_file(output_layer_path)

gdf = gdf.to_crs(epsg=3006)

gdf['centroid'] = gdf.geometry.centroid

gdf = gdf.set_geometry('centroid')
gdf = gdf.to_crs(epsg=4326)

centroid = gdf.geometry.iloc[0]
latitude, longitude = centroid.y, centroid.x

start_date = datetime(2024, 2, 1)
end_date = datetime(2024, 11, 30)

average_elevation = average_hourly_solar_elevation(latitude, longitude, start_date, end_date)
save_print_to_file(f"Average Hourly Solar Elevation Angle: {average_elevation:.2f} degrees (1st Feb - 30th Nov)")

#%% ~~ Calculate meteorological values ~~

""" Calculate average wind speed """

save_print_to_file("\nMeteorological data")

wind_clipped = os.path.join(path_temp, 'wind_map.shp')

processing.run("native:clip", {
    'INPUT':os.path.join(data_path, 'wind_map.shp'),
    'OVERLAY':output_layer_path,
    'OUTPUT':wind_clipped
})

wind_clipped_read = gpd.read_file(wind_clipped)

z_average = wind_clipped_read['Z'].mean()
save_print_to_file(f"The average wind speed at 140 m is {z_average:.2f} m/s")

for windload in gdf_estate['WINDLOAD']:
    save_print_to_file(f"Windload: {windload} m/s (source: Boverket)")

average_values = {
    "Humidity": None,
    "Temperature": None,
    "Air Pressure": None,
    "Snow data": {
        "January": None,
        "February": None,
        "March": None,
        "April": None,
        "May": None,
        "June": None,
        "July": None,
        "August": None,
        "September": None,
        "October": None,
        "November": None,
        "December": None,
    }
}

raster_data = [
    "humidity_data.tif",
    "temp_data.tif",
    "air_pressure_data.tif",
    "snow_depth_jan.tif",
    "snow_depth_feb.tif",
    "snow_depth_mar.tif",
    "snow_depth_apr.tif",
    "snow_depth_may.tif",
    "snow_depth_jun.tif",
    "snow_depth_jul.tif",
    "snow_depth_aug.tif",
    "snow_depth_sep.tif",
    "snow_depth_oct.tif",
    "snow_depth_nov.tif",
    "snow_depth_dec.tif"
]

categories = {
    "humidity_data.tif": "Humidity",
    "temp_data.tif": "Temperature",
    "air_pressure_data.tif": "Air Pressure",
    "snow_depth_jan.tif": "January",
    "snow_depth_feb.tif": "February",
    "snow_depth_mar.tif": "March",
    "snow_depth_apr.tif": "April",
    "snow_depth_may.tif": "May",
    "snow_depth_jun.tif": "June",
    "snow_depth_jul.tif": "July",
    "snow_depth_aug.tif": "August",
    "snow_depth_sep.tif": "September",
    "snow_depth_oct.tif": "October",
    "snow_depth_nov.tif": "November",
    "snow_depth_dec.tif": "December"
}

for rast in raster_data:
    raster_temp = os.path.join(path_temp, f"clipped_{rast}")
    
    try:
        result = processing.run("gdal:cliprasterbymasklayer", {
            'INPUT': os.path.join(data_path, rast),
            'MASK': hundred_m_buffered_layer_path,
            'SOURCE_CRS': QgsCoordinateReferenceSystem('EPSG:3006'),
            'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:3006'),
            'NODATA': None,
            'ALPHA_BAND': False,
            'CROP_TO_CUTLINE': True,
            'KEEP_RESOLUTION': False,
            'SET_RESOLUTION': False,
            'X_RESOLUTION': None,
            'Y_RESOLUTION': None,
            'MULTITHREADING': False,
            'OPTIONS': '',
            'DATA_TYPE': 0,
            'EXTRA': '',
            'OUTPUT': raster_temp
        })
    except Exception as e:
        print("Failed to retrieve meteorological data")
        continue

    if not os.path.exists(raster_temp):
        print("Failed to retrieve meteorological data")
        continue
    
    raster_shapes = os.path.join(path_temp, rast.replace(".tif", ".shp"))
    
    try:
        processing.run("native:pixelstopolygons", {
            'INPUT_RASTER': raster_temp,
            'RASTER_BAND': 1,
            'FIELD_NAME': 'VALUE',
            'OUTPUT': raster_shapes
        })
    except Exception as e:
        print("Failed to retrieve meteorological data")
        continue
    
    raster_pixels_temps = os.path.join(path_temp, rast.replace(".tif", "_pixel.shp"))
    
    try:
        final_output = processing.run("native:clip", {
            'INPUT': raster_shapes,
            'OVERLAY': final_byggbar_multi,
            'OUTPUT': raster_pixels_temps
        })['OUTPUT']
    except Exception as e:
        print("Failed to retrieve meteorological data")
        continue

    final_layer = QgsVectorLayer(final_output, "final_layer", "ogr")
    
    if not final_layer.isValid():
        print("Failed to retrieve meteorological data")
        continue
    
    total_value = 0
    feature_count = 0
    
    try:
        for feature in final_layer.getFeatures():
            total_value += feature['VALUE']
            feature_count += 1
    except Exception as e:
        print("Failed to retrieve meteorological data")
        continue
    
    if feature_count > 0:
        average_value = total_value / feature_count
        if categories[rast] in average_values:
            average_values[categories[rast]] = average_value
        else:
            average_values["Snow data"][categories[rast]] = average_value
    else:
        if categories[rast] in average_values:
            average_values[categories[rast]] = None
        else:
            average_values["Snow data"][categories[rast]] = None

try:
    save_print_to_file(f"Average humidity: {average_values['Humidity']:.1f} %")
    save_print_to_file(f"Average temperature: {average_values['Temperature']:.2f} °C")
    save_print_to_file(f"Average air Pressure: {average_values['Air Pressure']:.2f} hPa")
    for snowload in gdf_estate['SNOWLOAD']:
        save_print_to_file(f"Snowload: {snowload} kN/m² (source: Boverket)")
    save_print_to_file("Average snow data:")
    for month, value in average_values["Snow data"].items():
        save_print_to_file(f"    * {month}: {value:.3f} m")
except Exception as e:
    print("Failed to retrieve meteorological data")

#%% ~~ Municipality political check ~~

# Main parties dictionary
main_parties = {
    'M': 'Moderaterna',
    'SD': 'Sverigedemokraterna',
    'KD': 'Kristdemokraterna',
    'L': 'Liberalerna',
    'S': 'Socialdemokraterna',
    'C': 'Centerpartiet',
    'MP': 'Miljöpartiet',
    'V': 'Vänsterpartiet'
}

def identify_parties(political_control):
    parties = political_control.split('+')
    identified_parties = []
    for party in parties:
        if party in main_parties:
            identified_parties.append(main_parties[party])
        else:
            identified_parties.append(f'Minor local party ({party})')
    return '+'.join(identified_parties)

def calculate_influence(row, ruling_parties):
    total_seats = row['TOT']
    influence = {}
    for party in ruling_parties:
        if party in main_parties:
            seats = row[party]
            influence[main_parties[party]] = round((seats / total_seats) * 100, 1)
        else:
            influence[f'Minor local party ({party})'] = 'Present'
    return influence

def normalize_string(input_string):
    if isinstance(input_string, str):
        return input_string.lower()
    return input_string

gdf = gpd.read_file(output_layer_path, encoding='utf-8')
boroughs = gdf['BOROUGH'].apply(normalize_string)

csv_file_path = os.path.join(data_path, 'parties.csv')
df = pd.read_csv(csv_file_path, encoding='utf-8')

df['Kommun'] = df['Kommun'].apply(normalize_string)

matched_municipalities = df[df['Kommun'].isin(boroughs)].copy()

matched_municipalities['Identified Parties'] = matched_municipalities['Kommunal Politiskt styre'].apply(identify_parties)

matched_municipalities['Ruling Influence'] = matched_municipalities.apply(
    lambda row: calculate_influence(row, row['Kommunal Politiskt styre'].split('+')), axis=1
)

output = []
for index, row in matched_municipalities.iterrows():
    output.append(f"\nMunicipality: {row['Kommun'].title()}")
    major_parties = []
    minor_parties = []
    for party, influence in row['Ruling Influence'].items():
        if party.startswith('Minor local party'):
            minor_parties.append(f"{party}")
        else:
            major_parties.append(f"{party} ({influence}%)")
    output.extend(major_parties + minor_parties)
    output.append("")

for line in output:
    save_print_to_file(line)

# #%% ~~ Calculating BoS coverage ~~

# final_byggbar_layer = QgsVectorLayer(final_byggbar_multi, "final_byggbar_multi", "ogr")

# total_area = 0
# for feature in final_byggbar_layer.getFeatures():
#     geom = feature.geometry()
#     area_ha = geom.area() / 10000  # Convert area from square meters to hectares
#     total_area += area_ha

# # Check if total area is less than 1 hectare
# if total_area < 1:
#     pass
# else:

#     landcover = os.path.join(data_path, 'landcover.tif')
#     landcover_100 = os.path.join(path_temp, 'landcover_100.tif')
    
#     processing.run("gdal:cliprasterbymasklayer", {
#         'INPUT':landcover,
#         'MASK':hundred_m_buffered_layer_path,
#         'SOURCE_CRS':QgsCoordinateReferenceSystem('EPSG:3006'),
#         'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:3006'),
#         'NODATA':0,
#         'ALPHA_BAND':False,
#         'CROP_TO_CUTLINE':True,
#         'KEEP_RESOLUTION':False,
#         'SET_RESOLUTION':False,
#         'X_RESOLUTION':None,
#         'Y_RESOLUTION':None,
#         'MULTITHREADING':False,
#         'OPTIONS':'',
#         'DATA_TYPE':0,
#         'EXTRA':'',
#         'OUTPUT':landcover_100
#     })
    
#     landcover_poly_100 = os.path.join(path_temp, 'landcover_poly_100.shp')
    
#     processing.run("native:pixelstopolygons", {
#         'INPUT_RASTER':landcover_100,
#         'RASTER_BAND':1,
#         'FIELD_NAME':'VALUE',
#         'OUTPUT':landcover_poly_100
#     })
    
#     landcover_poly_suit = os.path.join(path_temp, 'landcover_poly_suit.shp')
    
#     processing.run("native:clip", {
#         'INPUT':landcover_poly_100,
#         'OVERLAY':final_byggbar_multi,
#         'OUTPUT':landcover_poly_suit
#     })
    
#     peat_data = os.path.join(data_path, 'wet_soil.shp')
#     torv_clipped = os.path.join(path_temp, 'wet_soil_suit.shp')
    
#     processing.run("native:clip", {
#         'INPUT':peat_data,
#         'OVERLAY':final_byggbar_multi,
#         'OUTPUT':torv_clipped
#     })
    
#     wet_suit_pixel = os.path.join(path_temp, 'wet_suit_pixel.shp')
    
#     gdf = gpd.read_file(landcover_poly_suit)
#     filtered_gdf = gdf[gdf['VALUE'].isin([2, 125, 127])]
#     filtered_gdf.to_file(wet_suit_pixel)
    
#     wet_suit = os.path.join(path_temp, 'wet_suit.shp')
    
#     if filtered_gdf.empty:
#         wet_suit = torv_clipped
#     else:
#         processing.run("native:mergevectorlayers", {
#             'LAYERS': [torv_clipped, wet_suit_pixel],
#             'CRS': QgsCoordinateReferenceSystem('EPSG:3006'),
#             'OUTPUT': wet_suit
#         })
        
#     rocky_terrain = os.path.join(data_path, 'rocky_terrain.shp')
#     rocky_terrain_suit = os.path.join(path_temp, 'rocky_terrain_suit.shp')
    
#     processing.run("native:clip", {
#         'INPUT':rocky_terrain,
#         'OVERLAY':final_byggbar_multi,
#         'OUTPUT':rocky_terrain_suit
#     })
    
#     peat_quarry_data = os.path.join(data_path, 'peat_quarry.shp')
#     peat_quarry_suit = os.path.join(path_temp, 'peat_quarry_suit.shp')
    
#     processing.run("native:clip", {
#         'INPUT':peat_quarry_data,
#         'OVERLAY':final_byggbar_multi,
#         'OUTPUT':peat_quarry_suit
#     })
    
#     rocky_terrain_suit_diss = os.path.join(path_temp, 'rocky_terrain_suit_diss.shp')
    
    
#     processing.run("native:dissolve", {
#         'INPUT':rocky_terrain_suit,
#         'FIELD':[],
#         'OUTPUT':rocky_terrain_suit_diss
#     })
    
#     landcover_poly_suit = gpd.read_file(os.path.join(path_temp, 'landcover_poly_suit.shp'))
    
#     dissolved_gdf = landcover_poly_suit.dissolve(by='VALUE')
    
#     dissolved_file_path = os.path.join(path_temp, 'landcover_poly_suit_dissolved.shp')
#     dissolved_gdf.to_file(dissolved_file_path)
    
#     landcover_poly_suit_dissolved_layer = QgsVectorLayer(dissolved_file_path, 'landcover_poly_suit_dissolved', 'ogr')
    
#     poly_minus_rocky_step = os.path.join(path_temp, 'poly_minus_rocky.shp')
#     processing.run("native:difference", {
#         'INPUT': landcover_poly_suit_dissolved_layer,  
#         'OVERLAY': rocky_terrain_suit_diss,
#         'OUTPUT': poly_minus_rocky_step
#     })
    
#     poly_minus_rocky_multi = os.path.join(path_temp, 'poly_minus_rocky_multi.shp')
#     processing.run("native:multiparttosingleparts", {
#         'INPUT': poly_minus_rocky_step,
#         'OUTPUT': poly_minus_rocky_multi
#     })
    
#     poly_minus_rocky = os.path.join(path_temp, 'poly_minus_rocky_final.shp')
#     processing.run("native:extractbyexpression", {
#         'INPUT': poly_minus_rocky_multi,
#         'EXPRESSION': ' $area >= 0.001 ',
#         'OUTPUT': poly_minus_rocky
#     })
    
#     rocky_minus_wet = os.path.join(path_temp, 'rocky_minus_wet.shp')
    
#     processing.run("native:difference", {
#         'INPUT':rocky_terrain_suit,
#         'OVERLAY':wet_suit,
#         'OUTPUT':rocky_minus_wet
#     })
    
#     poly_minus_wet = os.path.join(path_temp, 'poly_minus_wet.shp')
    
#     processing.run("native:difference", {
#         'INPUT':poly_minus_rocky,
#         'OVERLAY':wet_suit,
#         'OUTPUT':poly_minus_wet
#     })
    
#     rocky_suit_field = os.path.join(path_temp, 'rocky_suit_field.shp')
    
#     processing.run("native:addfieldtoattributestable", {
#         'INPUT':rocky_minus_wet,
#         'FIELD_NAME':'VALUE',
#         'FIELD_TYPE':0,
#         'FIELD_LENGTH':10,
#         'FIELD_PRECISION':0,
#         'OUTPUT':rocky_suit_field
#     })
    
#     rocky_suit_field_200 = os.path.join(path_temp, 'rocky_suit_field_200.shp')
    
#     processing.run("qgis:fieldcalculator", {
#         'INPUT': rocky_suit_field,
#         'FIELD_NAME': 'VALUE',
#         'FIELD_TYPE': 0,
#         'FIELD_LENGTH': 10,
#         'FIELD_PRECISION': 0,
#         'NEW_FIELD': False,
#         'FORMULA': '200',
#         'OUTPUT': rocky_suit_field_200
#     })
    
#     wet_minus_peat = os.path.join(path_temp, 'wet_minus_peat.shp')
    
#     processing.run("native:difference", {
#         'INPUT':wet_suit,
#         'OVERLAY':peat_quarry_suit,
#         'OUTPUT':wet_minus_peat
#     })
    
#     bos_merged = os.path.join(path_temp, 'bos_merged.shp')
    
#     processing.run("native:mergevectorlayers", {
#         'LAYERS':[rocky_suit_field_200,
#                   peat_quarry_suit,
#                   poly_minus_wet,
#                   wet_minus_peat],
#         'CRS':QgsCoordinateReferenceSystem('EPSG:3006'),
#         'OUTPUT':bos_merged
#     })
    
#     bos_merged_field = os.path.join(path_temp, 'bos_merged_field.shp')
    
#     processing.run("native:addfieldtoattributestable", {
#         'INPUT':bos_merged,
#         'FIELD_NAME':'VALUE',
#         'FIELD_TYPE':0,
#         'FIELD_LENGTH':10,
#         'FIELD_PRECISION':0,
#         'OUTPUT':bos_merged_field
#     })
    
#     bos_merged_field_area = os.path.join(path_temp, 'bos_merged_field_area.shp')
    
#     processing.run("qgis:fieldcalculator", {
#         'INPUT': bos_merged_field,
#         'FIELD_NAME': 'AREA',
#         'FIELD_TYPE': 0,
#         'FIELD_LENGTH': 10,
#         'FIELD_PRECISION': 6,
#         'NEW_FIELD': False,
#         'FORMULA': '$area * 0.0001',
#         'OUTPUT': bos_merged_field_area
#     })
    
#     gdf = gpd.read_file(bos_merged_field_area)
    
#     gdf['AREA'] = gdf['AREA'].astype(str).str.replace(',', '.').astype(float)
    
#     gdf['VALUE'] = gdf['VALUE'].astype(int)
    
#     dissolved_gdf = gdf.dissolve(by='VALUE')
    
#     dissolved_gdf['AREA'] = dissolved_gdf.geometry.area / 10000  # Convert to hectares
    
#     dissolved_gdf = dissolved_gdf.reset_index()
    
#     # Landcover index
#     # ~~~~~
#     # 2: Våtmark
#     # 3: Åkermark
#     # 41: Övrig öppen mark utan vegetation
#     # 42: Övrig öppen mark med vegetation
#     # 51: Exploaterad mark byggnad
#     # 52: Exploaterad mark ej byggnad eller väg/järnväg
#     # 53: Exploaterad mark väg/järnväg
#     # 61: Sjö och vattendrag
#     # 62: Hav
#     # 111: Tallskog utanför våtmark
#     # 112: Granskog utanför våtmark
#     # 113: Barrblandskog utanför våtmark
#     # 114: Lövblandad barrskog utanför våtmark
#     # 115: Trivialskog utanför våtmark
#     # 116: Ädelskog utanför våtmark
#     # 117: Trivialskog med ädellövinslag utanför våtmark
#     # 118: Temporarät ej skog utanför våtmark
#     # 121: Tallskog på våtmark
#     # 122: Granskog på våtmark
#     # 123: Barrblandskog på våtmark
#     # 124: Lövblandad barrskog på våtmark
#     # 125: Trivialskog på våtmark
#     # 126: Ädellovskog på våtmark
#     # 127: Triviallövskog med ädelinslag på våtmark
#     # 128: Temporärt ej skog på våtmark
#     # 200: Stenig/hård mark
#     # ~~~~
    
#     open_field_values = [3, 41, 42, 115, 117]
#     forest_values = [111, 112, 113, 114, 116, 118, 121, 122, 123, 124, 126, 128]
#     wetlands_values = [2, 125, 127]
#     rocky_terrain = [200]
#     peat_quarry = [201]
    
#     hectares = {
#         'Open field': 0,
#         'Peat quarry': 0,
#         'Forest': 0,
#         'Wetland': 0,
#         'Rocky Terrain': 0
#     }
    
#     for _, row in dissolved_gdf.iterrows():
#         value = row['VALUE']
#         area_ha = row['AREA'] 
        
#         if value in open_field_values:
#             hectares['Open field'] += area_ha
#         elif value in peat_quarry:
#             hectares['Peat quarry'] += area_ha
#         elif value in forest_values:
#             hectares['Forest'] += area_ha
#         elif value in wetlands_values:
#             hectares['Wetland'] += area_ha
#         elif value in rocky_terrain:
#             hectares['Rocky Terrain'] += area_ha
    
#     total_hectares = sum(hectares.values())
    
#     save_print_to_file("BoS groups:")
#     for group, area in hectares.items():
#         percentage = (area / total_hectares) * 100 if total_hectares > 0 else 0
#         save_print_to_file(f"{group}: {percentage:.2f}% ({area:.2f} ha) ")
    
#%% ~~ Calculating the soil type coverage ~~

save_print_to_file("\nSoil types")

soil_types_clipped = os.path.join(path_temp, "soil_types_clipped.shp")
soil_types = os.path.join(folder_path, "soil_types.shp")

processing.run("native:clip", {
    'INPUT': soil_types,
    'OVERLAY': final_byggbar_multi,
    'OUTPUT': soil_types_clipped
})

gdf = gpd.read_file(soil_types_clipped)

dissolved_gdf = gdf.dissolve(by='TYPE')

dissolved_gdf['AREA'] = dissolved_gdf.geometry.area / 10000  

dissolved_gdf = dissolved_gdf.reset_index()

total_area = dissolved_gdf['AREA'].sum()

dissolved_gdf['PERCENTAGE'] = (dissolved_gdf['AREA'] / total_area) * 100

for _, row in dissolved_gdf.iterrows():
    save_print_to_file(f"{row['TYPE']}: {row['PERCENTAGE']:.2f}% ({row['AREA']:.2f} ha)")

#%% ~~ Rounding up ~~

""" Moving the layers to the correct folder """

layers_to_groups = {
    "Lämplig yta - Sol": "Sol",
    "Lämplig yta - Vind": "Vind",
    "Grannar": "Annat",
    "Fastigheten": "Annat",
    "Contour Lines": "Annat",
    "Uppritad yta": "Annat",
    "Diken": "Annat",
    "Översvämningsrisk": "Vind",
    "Kommungräns": "Vind",
    "Sumpskog": "Annat",
    "Cykelbana": "Annat",
    "Jordtyper": "Annat"
}

for layer_name, group_name in layers_to_groups.items():
    
    layer = None
    for lyr in project.mapLayers().values():
        if lyr.name() == layer_name:
            layer = lyr
            break

    if layer is None:
        continue

    group = None
    for child in root.children():
        if child.name() == group_name and isinstance(child, QgsLayerTreeGroup):
            group = child
            break

    if group is None:
        continue

    layer_node = root.findLayer(layer.id())
    cloned_layer_node = layer_node.clone()
    group.insertChildNode(0, cloned_layer_node)
    root.removeChildNode(layer_node)

""" Renaming the power line layers """    
    
layers_to_rename = {
    'powerlines-10-80.shp': '10-80 kV ledning',
    'powerlines-80-170.shp': '80-170 kV ledning',
    'powerlines-170-220.shp': '170-220 kV ledning',
    'powerlines-300-500.shp': '300-500 kV ledning'
}

project = QgsProject.instance()

def get_max_voltag(layer):
    max_voltag_value = None
    for feature in layer.getFeatures():
        max_voltag = feature['max_voltag']
        if isinstance(max_voltag, QVariant):
            if max_voltag.isNull():
                continue
            max_voltag = max_voltag.toDouble()[0] 
        if max_voltag is not None and max_voltag != '':
            max_voltag_value = f"{int(float(max_voltag) / 1000)} kV"
            break
    return max_voltag_value

for layer_filename, original_name in layers_to_rename.items():
    layer_path = os.path.join(folder_path, layer_filename)
    
    if os.path.exists(layer_path):
        loaded_layer = project.mapLayersByName(original_name)
        
        if loaded_layer:
            layer = loaded_layer[0]
            max_voltag_value = get_max_voltag(layer)
            
            if max_voltag_value:
                new_name = f"{max_voltag_value} ledning"
                layer.setName(new_name)

""" Adding the empty "Artportalen"-layer """

shapefile_path = os.path.join(data_path, "artportal_red_empty.shp")

layer = QgsVectorLayer(empty_shapefile_path, "Rödlistad artobservation", "ogr")

""" Movingthe folders to the bottom """

if not layer.isValid():
    print(f"Failed to load the layer: {empty_shapefile_path}")
else:
    QgsProject.instance().addMapLayer(layer, False)
    root.addLayer(layer) 
    
    symbol = QgsMarkerSymbol.createSimple({'color': '#c71c42', 'outline_color': '#000000'})
    
    layer.renderer().setSymbol(symbol)

    layer.triggerRepaint()

def move_group_to_bottom(group_name):
    project = QgsProject.instance()
    
    root = project.layerTreeRoot()
    
    group_node = root.findGroup(group_name)
    
    if group_node:
        parent = group_node.parent()
        
        cloned_group = group_node.clone()
        
        parent.insertChildNode(len(parent.children()), cloned_group)
        
        parent.removeChildNode(group_node)
        
    else:
        print(f"Group '{group_name}' not found.")

move_group_to_bottom('Vind')
move_group_to_bottom('Sol')
move_group_to_bottom('Annat')

""" Moving the satellite imagery to the bottom """

def move_layer_to_bottom(layer_name):
    project = QgsProject.instance()
    
    root = project.layerTreeRoot()
    
    layer_node = root.findLayer(project.mapLayersByName(layer_name)[0].id())
    
    if layer_node:
        parent = layer_node.parent()
        
        cloned_layer = layer_node.clone()
        
        parent.insertChildNode(len(parent.children()), cloned_layer)
        
        parent.removeChildNode(layer_node)
        
    else:
        print(f"Layer '{layer_name}' not found.")

move_layer_to_bottom('Google Sat')

""" Loading the bad slopes """

shapefiles = [os.path.join(folder_path, f'bad_slopes_{i}.shp') for i in range(1, 13)]

folders_to_collapse = ["Branta sluttningar", "Vind", "Sol", "Annat"]

start_color = QColor("#ff4104")
end_color = QColor("#b10000")

project = QgsProject.instance()
root = project.layerTreeRoot()

def create_graduated_renderer(layer, field_name, start_color, end_color):
    field_index = layer.fields().indexOf(field_name)
    min_value = layer.minimumValue(field_index)
    max_value = layer.maximumValue(field_index)
    
    steps = 10
    step_value = (max_value - min_value) / steps
    ranges = []
    
    for i in range(steps):
        lower = min_value + (i * step_value)
        upper = min_value + ((i + 1) * step_value)
        color = QColor(
            start_color.red() + ((end_color.red() - start_color.red()) * i // steps),
            start_color.green() + ((end_color.green() - start_color.green()) * i // steps),
            start_color.blue() + ((end_color.blue() - start_color.blue()) * i // steps)
        )
        symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        symbol.setColor(color)
        symbol.symbolLayer(0).setStrokeColor(QColor(0, 0, 0, 0)) 
        renderer_range = QgsRendererRange(lower, upper, symbol, f'{lower:.2f} - {upper:.2f}')
        ranges.append(renderer_range)
    
    renderer = QgsGraduatedSymbolRenderer(field_name, ranges)
    renderer.setMode(QgsGraduatedSymbolRenderer.Quantile)
    return renderer

""" Save the project """

project.write(os.path.join(folder_path, f'{folder_name}.qgz'))

""" Send notification """

push = pb.push_note("Wakie wakie!", "All done with"+" "+folder_name)

""" Sort slopes """

def collapse_folder(folder_name):
    folder = root.findGroup(folder_name)
    if folder:
        folder.setExpanded(False)
    else:
        print(f"Folder '{folder_name}' not found.")

for folder_name in folders_to_collapse:
    collapse_folder(folder_name)

folder = root.findGroup("Branta sluttningar")
if not folder:
    print(f"Folder 'Branta sluttningar' not found.")
else:
    for shapefile in shapefiles:
        layer = QgsVectorLayer(shapefile, shapefile.split('/')[-1], 'ogr')
        if not layer.isValid():
            # print(f"Failed to load {shapefile}")
            continue
        renderer = create_graduated_renderer(layer, 'SLOPE', start_color, end_color)
        layer.setRenderer(renderer)
        project.addMapLayer(layer, False)
        folder.addLayer(layer)

""" Checking suitability for wind and solar """

save_print_to_file(f"\nPotential of the project area")

def check_suitability(layer_name, field_name, energy_type):
    # Get the layer by name
    layer = QgsProject.instance().mapLayersByName(layer_name)
    
    if not layer:
        QgsMessageLog.logMessage(f"Layer '{layer_name}' not found.", level=Qgis.Critical)
        return

    layer = layer[0]
    
    # Get the first feature in the layer
    features = layer.getFeatures()
    first_feature = next(features, None)
    
    if not first_feature:
        QgsMessageLog.logMessage(f"No features found in '{layer_name}'.", level=Qgis.Critical)
        return
    
    # Get the value of the specified field
    sum_area = first_feature[field_name]
    
    # Check the value and print the message
    if sum_area < 1:
        QgsMessageLog.logMessage(f"Not suitable for {energy_type} energy.", level=Qgis.Warning)


check_suitability("Lämplig yta - Vind", "sum_area", "wind")

layer_vind = QgsProject.instance().mapLayersByName('Lämplig yta - Vind')[0]
total_area_wind = sum(f['AREA'] for f in layer_vind.getFeatures())
new_name_vind = f"Suitable area - Wind ({abs(total_area_wind):.1f} ha)"
layer_vind.setName(new_name_vind)
save_print_to_file(f"{new_name_vind}")

if total_area_wind > 0.5 and total_area_wind < 3:
    num_turbines = 1  
elif total_area_wind >= 3:
    num_turbines = total_area_wind // 3  
else:
    num_turbines = 0 
  
save_print_to_file(f"{int(num_turbines)} turbine(s) á 3.5 MW")

check_suitability("Lämplig yta - Sol", "sum_area", "solar")

layer_sol = QgsProject.instance().mapLayersByName('Lämplig yta - Sol')[0]
total_area_solar = sum(f['AREA'] for f in layer_sol.getFeatures())
new_name_sol = f"Suitable area - Solar ({abs(total_area_solar):.1f} ha)"
layer_sol.setName(new_name_sol)
dc_value_solar = total_area_solar * 0.9
save_print_to_file(f"{new_name_sol}")

save_print_to_file(f"{dc_value_solar:.1f} MWp PV-panels (650 W)")

dc_value = num_turbines*3.5+dc_value_solar
ac_value = dc_value / 1.3

bess_value = round(ac_value * 0.2)

save_print_to_file(f"{bess_value} MW BESS")

save_print_to_file(f"DC/AC: {dc_value:.2f}/{ac_value:.2f}")

""" Changing the projection of the project """

QgsProject.instance().setCrs(QgsCoordinateReferenceSystem(3006))

""" Zooming in on the original polygon """

def load_and_zoom_to_layer(layer_path):

    if not updated_area.isValid():
        print(f"Failed to load layer from '{layer_path}'")
        return
    
    extent = updated_area.extent()
    
    iface.mapCanvas().setExtent(extent)
    iface.mapCanvas().refresh()

load_and_zoom_to_layer(output_layer_path)

""" Printing the distance to the power lines """

save_print_to_file(f"\nPower line info")

layers_to_check = {
    'powerlines-null.shp': 'Unknown power line',
    'powerlines-10-80.shp': 'kV power line',
    'powerlines-80-170.shp': 'kV power line',
    'powerlines-170-220.shp': 'kV power line',
    'powerlines-300-500.shp': 'kV power line',
    'powerlines-underground.shp': 'Underground power line',
    'power_stations.shp': 'Transformer station'
}

def format_distance(distance):
    if distance < 1000:
        return f"{int(distance)} m"
    else:
        return f"{distance / 1000:.2f} km"

def get_max_voltag(feature):
    if 'max_voltag' not in feature.fields().names():
        return "Unknown"
    
    max_voltag = feature['max_voltag']
    if isinstance(max_voltag, QVariant):
        if max_voltag.isNull():
            return "Unknown"
        max_voltag = max_voltag.toDouble()[0] 
    if max_voltag is None or max_voltag == '':
        return "Unknown"
    try:
        return f"{float(max_voltag) / 1000:.0f} kV"
    except (TypeError, ValueError):
        return "Unknown"

def get_power_station_voltages(feature):
    v_primary = feature['v_primary'] if 'v_primary' in feature.fields().names() else None
    v_secondar = feature['v_secondar'] if 'v_secondar' in feature.fields().names() else None

    voltages = []

    if v_primary and not isinstance(v_primary, QVariant):
        voltages.append(f"Primary Voltage: {float(v_primary) / 1000:.0f} kV")
    
    if v_secondar and not isinstance(v_secondar, QVariant):
        voltages.append(f"Secondary Voltage: {float(v_secondar) / 1000:.0f} kV")

    return " | ".join(voltages) if voltages else "Unknown"

def calculate_min_distance(layer1, layer2, layer_name):
    min_distance = float('inf') 
    closest_feature_info = None

    index = QgsSpatialIndex(layer2.getFeatures())

    for feature1 in layer1.getFeatures():
        geom1 = feature1.geometry()

        nearest_ids = index.nearestNeighbor(geom1.boundingBox().center(), 5)

        for nearest_id in nearest_ids:
            nearest_feature = next(layer2.getFeatures(QgsFeatureRequest(nearest_id)))
            geom2 = nearest_feature.geometry()

            distance = geom1.distance(geom2)

            if distance < min_distance:
                min_distance = distance
                if layer_name == 'power_stations.shp':
                    closest_feature_info = get_power_station_voltages(nearest_feature)
                else:
                    closest_feature_info = get_max_voltag(nearest_feature)

    return min_distance, closest_feature_info

if os.path.exists(final_byggbar_multi):
    final_byggbar_multi = QgsVectorLayer(final_byggbar_multi, "Buildable Solar Layer", "ogr")

    if not final_byggbar_multi.isValid():
        save_print_to_file("Failed to load the buildable solar layer, skipping distance calculations.")
        final_byggbar_multi = None
else:
    final_byggbar_multi = None
    save_print_to_file("The buildable solar layer does not exist, skipping distance calculations.")

if final_byggbar_multi:
    powerline_found = False 
    for layer_file, display_name in layers_to_check.items():
        layer_path = os.path.join(folder_path, layer_file)

        if os.path.exists(layer_path):
            layer_to_check = QgsVectorLayer(layer_path, display_name, 'ogr')

            if not layer_to_check.isValid():
                save_print_to_file(f"Failed to load {display_name}, skipping this layer.")
                continue

            min_distance, closest_feature_info = calculate_min_distance(final_byggbar_multi, layer_to_check, layer_file)

            if min_distance < 70:
                if display_name == 'kV power line' and closest_feature_info != "Unknown":
                    save_print_to_file(f"{closest_feature_info} {display_name}, distance: crossing the area")
                else:
                    save_print_to_file(f"{display_name}, distance: crossing the area")
                powerline_found = True
            else:
                formatted_distance = format_distance(min_distance)
                if display_name == 'kV power line' and closest_feature_info != "Unknown":
                    save_print_to_file(f"{closest_feature_info} {display_name}, distance: {formatted_distance}")
                    powerline_found = True
                else:
                    save_print_to_file(f"{display_name}, distance: {formatted_distance}")
                    powerline_found = True

    if not powerline_found:
        save_print_to_file("No power line or transformer station nearby.")
else:
    save_print_to_file("The buildable solar layer does not exist, skipping distance calculations.")


""" Removing temp files """

#shutil.rmtree(path_temp) #ss clears out /temp

""" Printing time elapsed """

end = time.time()

elapsed_time = end - start

hours, remainder = divmod(elapsed_time, 3600)
minutes, seconds = divmod(remainder, 60)

if hours > 0:
    elapsed_time_str = f"{int(hours)} hours, {int(minutes)} minutes, and {int(seconds)} seconds"
elif minutes > 0:
    elapsed_time_str = f"{int(minutes)} minutes and {int(seconds)} seconds"
else:
    elapsed_time_str = f"{int(seconds)} seconds"

""" Complete! """
    
print(f"\nProcessing completed. Total elapsed time: {elapsed_time_str}")
    
    
    


    



#clean up unwanted files, zip everything down to one -> copy shapes and layout to x's folder. Name files by date.
