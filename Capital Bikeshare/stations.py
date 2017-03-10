# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import pyproj
from lxml import etree
import httplib, urllib, base64
import simplejson as json
import os
from elevation import elevationModel

proj = pyproj.Proj(proj='utm',zone=18)


def readCaBiStations():
    doc = etree.parse("stations.xml")
    station = doc.find("station")
    fieldNames = [node.tag for node in station.iterchildren()]
#    fieldConstructors = [int, str, int, int, float, float, bool, bool, int, int, bool, bool, int, int, int]
    stations = [[node.find(name).text for name in fieldNames] for node in doc.findall("station")]
    stationData = pd.DataFrame(stations, columns=fieldNames) #.set_index("terminalName").drop("id",1)

    for field in ('lat', 'long'):
        stationData[field] = pd.to_numeric(stationData[field], errors='ignore')
    for field in ('lastCommWithServer', 'installDate', 'terminalName',
                  'removalDate', 'nbBikes', 'nbEmptyDocks', 'latestUpdateTime'):
        stationData[field] = pd.to_numeric(stationData[field], errors='ignore', downcast='integer')
    for field in ('temporary','public','installed','locked'):
        stationData[field] = stationData[field].apply(lambda s: s == 'true')

    stationData = stationData.set_index("terminalName").drop("id",1)
    stationData['capacity'] = stationData['nbBikes'] + stationData['nbEmptyDocks']
    
    xy = [proj(lon,lat) for lon,lat in zip(stationData.long, stationData.lat)]
    stationData['x'], stationData['y'] = zip(*xy)
    
    return stationData


# Retrieve WMATA stations

railCodes = {
    'RD':'red',
    'BL':'blue',
    'YL':'yellow',
    'OR':'orange',
    'SV':'silver'
}

def retrieveWMATAStations():
    headers = {
        # Request headers
        'api_key': '6b700f7ea9db408e9745c207da7ca827',
    }

    def WMATA_stations_json(lineCode='RD'):
        params = urllib.urlencode({
            # Request parameters
            'LineCode': lineCode,
        })
    
        try:
            conn = httplib.HTTPSConnection('api.wmata.com')
            conn.request("GET", "/Rail.svc/json/jStations?%s" % params, "{body}", headers)
            response = conn.getresponse()
            data = response.read()
            conn.close()
            return data
        except Exception as e:
            print("[Errno {0}] {1}".format(e.errno, e.strerror))
            raise e

    for code,color in railCodes.iteritems():
        fn = color + '.json'
        if not os.path.exists(fn):
            railStationsRaw = WMATA_stations_json(code)
            with open(fn,'w') as f:
                f.write(railStationsRaw)


def readWMATAStations():
    
    railData = {}
    for metroLine in railCodes.itervalues():
        with open(metroLine + '.json', 'r') as f:
            jdata = json.loads(f.read())['Stations']
        railData[metroLine] = pd.io.json.json_normalize(jdata).set_index("Code")
    
    railStations = pd.concat(railData.values()).drop_duplicates('Name')

    xy = [proj(lon,lat) for lon,lat in zip(railStations.Lon, railStations.Lat)]
    #x, y = zip(*lonlat)
    railStations['x'], railStations['y'] = zip(*xy)
    
    return railStations


def findNearestWMATA(stationData, railStations):
    def getDist(x,y):
        distances = np.sqrt((x - railStations.x) ** 2 + (y - railStations.y) ** 2)
        return distances.min(), distances.argmin() 
    
    distances = [getDist(tup.x,tup.y) for tup in stationData.itertuples()]
    stationData['railDist'], stationData['closestRail'] = zip(*distances)
    return stationData


def findElevation(stationData):
    dem = elevationModel()

    xy = [dem.proj(row.long,row.lat) for row in stationData.itertuples()]

#    stationData['elevation'] = [dem.elevation(*dem.proj(row.long,row.lat)) for row in stationData.itertuples()]
    stationData['elevation'] = [dem.elevation(*xy_) for xy_ in xy]
    stationData['pixel'] = [dem.map2raster(*xy_) for xy_ in xy]
    
    return stationData

def load():
    stationData = readCaBiStations()
    retrieveWMATAStations()
    railStations = readWMATAStations()
    stationData = findNearestWMATA(stationData, railStations)
    stationData = findElevation(stationData)
    
    
    return stationData
