# -*- coding: utf-8 -*-
"""
Get data for DW tools
"""

#%% import packages
import ulmo  #package for public hydrology/climate data https://ulmo.readthedocs.io/en/latest/; the Ulmo package has weird dependency issues with the "suds-jurko" package and cannot be included in a deployed app via streamlit

import pandas

import arrow

import numpy

import os

import io
import requests
#%% SNOTEL site info
#import and store site data for ALL Snotel Sites

wsdlurl='https://hydroportal.cuahsi.org/Snotel/cuahsi_1_1.asmx?WSDL'
sites = ulmo.cuahsi.wof.get_sites(wsdlurl)

sites_df = pandas.DataFrame.from_dict(sites, orient='index').dropna()
sites_df.head()
sites_df=sites_df.reset_index()

#sites_df.to_csv("SNOTEL_sites.csv.gz",index=False)

#%% Get available measurements
#ulmo.cuahsi.wof.get_site_info(wsdlurl, "SNOTEL:335_CO_SNTL")['series'].keys()
#%% SNOTEL data SNOTEL: WTEQ_D
variablecode='SNOTEL:WTEQ_D'
    
sitecode = [
    'SNOTEL:335_CO_SNTL',
    'SNOTEL:938_CO_SNTL',
    'SNOTEL:913_CO_SNTL',
    'SNOTEL:415_CO_SNTL',
    'SNOTEL:936_CO_SNTL',
    'SNOTEL:1186_CO_SNTL',
    'SNOTEL:485_CO_SNTL',
    'SNOTEL:505_CO_SNTL',
    'SNOTEL:1187_CO_SNTL',
    'SNOTEL:531_CO_SNTL',
    'SNOTEL:935_CO_SNTL',
    'SNOTEL:970_CO_SNTL',
    'SNOTEL:937_CO_SNTL',
    'SNOTEL:1014_CO_SNTL',
    'SNOTEL:939_CO_SNTL']

# start and end dates needed for initial data fetch
startY=1950
startM=10
startD=1
start_date = "%s-%s-0%s"%(startY,startM,startD) #if start day is single digit, add leading 0
end_date = arrow.now().format('YYYY-MM-DD')

def snotel_fetch(sitecode, variablecode=variablecode, start_date=start_date, end_date=end_date):
    #print(sitecode, variablecode, start_date, end_date)
    values_df = None
    try:
        #Request data from the server
        site_values = ulmo.cuahsi.wof.get_values(wsdlurl, sitecode, variablecode, start=start_date, end=end_date)
        #Convert to a Pandas DataFrame   
        values_df = pandas.DataFrame.from_dict(site_values['values'])
        #Parse the datetime values to Pandas Timestamp objects
        values_df['datetime'] = pandas.to_datetime(values_df['datetime'], utc=True)
        #Set the DataFrame index to the Timestamps
        #values_df = values_df.set_index('datetime')
        #Convert values to float and replace -9999 nodata values with NaN
        values_df['value'] = pandas.to_numeric(values_df['value']).replace(-9999, numpy.nan)
        #Remove any records flagged with lower quality
        values_df = values_df[values_df['quality_control_level_code'] == '1']
    except:
        print("Unable to fetch %s" % variablecode)

    return values_df

# SITE info
data_raw=pandas.DataFrame()
siteNamesList=[]
siteNamesListCode=[]

for row in sitecode:
    print(row)
    values_df = snotel_fetch(row, variablecode, start_date, end_date)
    temp=values_df[['datetime','value']].copy()
    name=sites_df['name'][sites_df['index']==row].iloc[0]
    temp['Site']=name
    
    data_raw=pandas.concat([data_raw,temp])
    siteNamesList.append(name)
    siteNamesListCode.append([name,row])
        
data_raw.rename({'datetime': 'Date', 'value': 'SWE_in', 'name':'Site'}, axis=1, inplace=True)

with open ("siteNamesList.txt","w") as output:
    output.write(str(siteNamesList))

siteNamesListCode=pandas.DataFrame(siteNamesListCode)
siteNamesListCode.to_csv('siteNamesListCode.csv',index=False)

data_raw.to_csv("SNOTEL_data_raw.csv.gz",index=False)

#%% TEMPERATURE data
wd=os.getcwd()
path=os.path.join(wd,"Weather_Data\\") #put all DW files in one directory with nothing else
weather_files = os.listdir(path)

weather=pandas.DataFrame()
for item in weather_files:
    file=pandas.read_excel(os.path.join(path,item))
    file['site']=item[:2]
    weather=pandas.concat([weather,file])
    
weather.to_csv("DW_weather.csv.gz",index=False)
