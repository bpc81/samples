# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd


def load():
    raw = pd.read_csv('weather.csv').drop(['STATION','STATION_NAME'],1)

    raw['DATE'] = pd.to_datetime(raw.DATE, format="%Y%m%d")
    raw = raw.set_index('DATE')


    weather = (raw[['PRCP','TMAX','TMIN','AWND','WSF2','WSF5']]
                .rename(columns={'PRCP':'precip',
                                 'TMAX': 'tempHigh',
                                 'TMIN': 'tempLow',
                                 'AWND': 'avgWind',
                                 'WSF2': 'gust2',
                                 'WSF5': 'gust5'}))
    weather['rain'] = ((raw.WT14 > 0) | (raw.WT15 > 0) | (raw.WT16 > 0) | (raw.WT17 > 0))
    return weather