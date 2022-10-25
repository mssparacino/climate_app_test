# -*- coding: utf-8 -*-
"""
Created on Tue Oct 11 11:53:06 2022

@author: msparacino
"""
#%% import packages

import streamlit as st #for displaying on web app

import pandas as pd

import requests

import datetime #for date/time manipulation

import arrow #another library for date/time manipulation

import pymannkendall as mk #for trend anlaysis

import numpy as np
import matplotlib.pyplot as plt #for plotting
from matplotlib import colors #for additional colors

#%% Define data download as CSV function
#functions
@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')

def convert_to_WY(row):
    if row.month>=10:
        return(pd.datetime(row.year+1,1,1).year)
    else:
        return(pd.datetime(row.year,1,1).year)
    
def background_gradient(s, m=None, M=None, cmap='gist_earth_r', low=0.1, high=1):
    if m is None:
        m = s.min().min()
    if M is None:
        M = s.max().max()
    rng = M - m
    norm = colors.Normalize(m - (rng * low),
                            M + (rng * high))
    normed = s.apply(norm)

    cm = plt.cm.get_cmap(cmap)
    c = normed.applymap(lambda x: colors.rgb2hex(cm(x)))
    ret = c.applymap(lambda x: 'background-color: %s' % x)

    return ret 

#dictionaries
months={1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}

#constants
startY=1950
startM=10
startD=1

#%% Site data
siteNamesRaw = pd.read_csv("siteNamesListCode.csv", dtype=str)

AllsiteNames = siteNamesRaw.replace('SNOTEL:','', regex=True)
AllsiteNames = AllsiteNames.replace("_", ":",regex=True)

#%% Load SMS data
data_raw=pd.read_csv('SNOTEL_SMS.csv.gz')

#%% Left Filters

#%% 01 Select System
container=st.sidebar.container()

all=st.sidebar.checkbox("Select both systems")

if all:
    system_selected = container.multiselect('Select your system(s):', AllsiteNames.iloc[:,2].drop_duplicates(), AllsiteNames.iloc[:,2].drop_duplicates())
else: 
    system_selected = container.multiselect('Select your system(s):', AllsiteNames.iloc[:,2].drop_duplicates(), default='North')

siteNames=AllsiteNames[AllsiteNames['2'].isin(system_selected)]

#%% 02 Select Site 
all_sites=st.sidebar.checkbox("Select all sites")
if all:
    site_selected = container.multiselect('Select your site:', siteNames.iloc[:,0], siteNames.iloc[:,0])
else: 
    site_selected = container.multiselect('Select your site:', siteNames.iloc[:,0], default=siteNames.iloc[0,0])

siteCodes=siteNames[siteNames['0'].isin(site_selected)].iloc[:,1]
siteNames=siteNames[siteNames['0'].isin(site_selected)].iloc[:,0]

#%% 03 select months
monthOptions=pd.DataFrame({'Month':['Sep','Oct','Nov','Dec','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug',],
                               'Season':['Fall','Fall','Fall','Winter','Winter','Winter','Spring','Spring','Spring','Summer','Summer','Summer',],
                               'Num':[9,10,11,12,1,2,3,4,5,6,7,8]})
monthSelect=monthOptions['Month']


fallMonths=monthOptions.loc[monthOptions['Season']=='Fall']['Month']
winterMonths=monthOptions.loc[monthOptions['Season']=='Winter']['Month']
springMonths=monthOptions.loc[monthOptions['Season']=='Spring']['Month']
summerMonths=monthOptions.loc[monthOptions['Season']=='Summer']['Month']

container=st.sidebar.container()

fall=st.sidebar.checkbox("Fall")
summer=st.sidebar.checkbox("Summer")
spring=st.sidebar.checkbox("Spring")
winter=st.sidebar.checkbox("Winter")

#multiseasons
if winter and spring and (fall==False) and (summer==False):
    month_select = container.multiselect('Select month(s):',pd.concat([winterMonths,springMonths]), pd.concat([winterMonths,springMonths]))
elif winter and summer and (fall==False) and (spring==False):
    month_select = container.multiselect('Select month(s):',pd.concat([winterMonths,summerMonths]), pd.concat([winterMonths,summerMonths]))
elif winter and fall and (spring==False) and (summer==False):
    month_select = container.multiselect('Select month(s):',pd.concat([winterMonths,fallMonths]), pd.concat([winterMonths,fallMonths]))
elif winter and (fall==False) and (spring==False) and (summer==False):
    month_select = container.multiselect('Select month(s):',winterMonths, winterMonths)
elif spring and (fall==False) and (winter==False) and (summer==False):
    month_select = container.multiselect('Select month(s):',springMonths, springMonths)
elif fall and spring and (winter==False) and (summer==False):
    month_select = container.multiselect('Select month(s):',pd.concat([springMonths,fallMonths]), pd.concat([springMonths,fallMonths]))
elif spring and summer and (winter==False) and (fall==False):
    month_select = container.multiselect('Select month(s):',pd.concat([springMonths,summerMonths]), pd.concat([springMonths,summerMonths]))
elif summer and fall and (winter==False) and (spring==False):
    month_select = container.multiselect('Select month(s):',pd.concat([summerMonths,fallMonths]), pd.concat([summerMonths,fallMonths]))
elif summer and (fall==False) and (winter==False) and (spring==False):
    month_select = container.multiselect('Select month(s):',summerMonths, summerMonths)
elif fall and (spring==False) and (winter==False) and (summer==False):
    month_select = container.multiselect('Select month(s):',fallMonths, fallMonths)
elif fall and summer and spring and (winter==False):
    month_select = container.multiselect('Select month(s):',pd.concat([springMonths,summerMonths,fallMonths]), pd.concat([springMonths,summerMonths,fallMonths]))
elif fall and summer and winter and (spring==False):
    month_select = container.multiselect('Select month(s):',pd.concat([winterMonths,summerMonths,fallMonths]), pd.concat([winterMonths,summerMonths,fallMonths]))
elif spring and summer and winter and (fall==False):
    month_select = container.multiselect('Select month(s):',pd.concat([winterMonths,springMonths,summerMonths]), pd.concat([winterMonths,springMonths,summerMonths]))
elif spring and fall and summer and winter:
    month_select = container.multiselect('Select month(s):',pd.concat([springMonths,winterMonths,summerMonths,fallMonths]), pd.concat([springMonths,winterMonths,summerMonths,fallMonths]))

else:
    month_select = container.multiselect('Select month(s):', monthSelect,default=monthSelect)

monthNum_select=pd.DataFrame(month_select)
monthNum_select=monthOptions.loc[monthOptions['Month'].isin(month_select)]['Num']
    

#%% 04 Select Depths
elementDF=pd.DataFrame({0:["SMS:-2:value","SMS:-4:value", "SMS:-8:value","SMS:-20:value","SMS:-40:value"], 
                           'long': ['2 inch depth', '4 inch depth','8 inch depth', '20 inch depth','40 inch depth']})

container=st.sidebar.container()
paramsSelect=elementDF['long']
element_select=container.multiselect('Select depth(s):',paramsSelect,default=elementDF['long'])
element_select=elementDF.loc[elementDF['long'].isin(element_select)][0]
elementStr= ','.join(element_select)

#04 Select Water Year
start_date = "%s-%s-0%s"%(startY,startM,startD) 
end_dateRaw = arrow.now().format('YYYY-MM-DD')

min_date = datetime.datetime(startY,startM,startD) #dates for st slider need to be in datetime format:
max_date = datetime.datetime.today() 

startYear = st.sidebar.number_input('Enter Beginning Water Year:', min_value=startY, max_value=int(end_dateRaw[:4]),value=startY)
endYear = st.sidebar.number_input('Enter Ending Water Year:',min_value=startY, max_value=int(end_dateRaw[:4]),value=2021)


#%% Filter raw data by sites and dates

data_sites=data_raw[data_raw.site.isin(siteCodes)]
data_sites['year']=pd.DatetimeIndex(data_sites['Date']).year
data_sites['month']=pd.DatetimeIndex(data_sites['Date']).month
data_sites['WY']= data_sites.apply(lambda x: convert_to_WY(x), axis=1)

#filter by WY
dateFilterWY=data_sites[(data_sites['WY']>=startYear)&(data_sites['WY']<=endYear)]

#filter by month
def monthfilter():
    return dateFilterWY[dateFilterWY['month'].isin(monthNum_select)]

data=monthfilter()

st.header("Soil Moisture Percent (pct) Start of Day Values")

data.set_index('Date')

csv = convert_df(data)
st.download_button(
     label="Download Daily Soil Moisture Data",
     data=csv,
     file_name='SMS_data.csv',
     mime='text/csv',
 )


#%% Create pivot table using average soil moisture and show medians by WY
data['averageSoilMoisture']=(data[data.columns[1:-4]]).mean(axis=1)
data_nonans = data.dropna(subset=['averageSoilMoisture'])

#filter by months with days > 25 that have average soil moisture data 
#filter years by days > 330 days

smData=data_nonans

# if len(month_select)==12:
#     dayCountThres=330
#     smData=data_nonans.groupby(['month','WY']).filter(lambda x : len(x)>=dayCountThres)
# else:
#     dayCountThres=25
#     smData=data_nonans.groupby(['month','WY']).filter(lambda x : len(x)>=dayCountThres)

pvTable=pd.pivot_table(smData, values=['averageSoilMoisture'],index='site', columns={'WY'},aggfunc=np.nanmedian, margins=False, margins_name='Total')
pvTable=pvTable["averageSoilMoisture"].head(len(pvTable))

pvTable["Site"]=AllsiteNames[AllsiteNames['1'].isin(pvTable.index.to_list())].iloc[:,0].to_list()
pvTable["System"]=AllsiteNames[AllsiteNames['1'].isin(pvTable.index.to_list())].iloc[:,2].to_list()
pvTable=pvTable.set_index(["Site","System"],drop=True)


# pvTable=pvTable.rename(columns = months)

st.header("Soil Moisture % WY Median ")

#display pivot table 
tableData=pvTable.style\
    .set_properties(**{'width':'10000px','color':'white'})\
    .apply(background_gradient, axis=None)\
    .format(precision=1)

st.dataframe(tableData)

#download pivot table
csv = convert_df(pvTable)
st.download_button(
     label="Download Table Data as CSV",
     data=csv,
     file_name='Median_SoilMoisture_byWY_CompareSites.csv',
     mime='text/csv',
 )


#%% Statistics Table

# medianTable=pvTable.median()
# medianTable=medianTable.to_frame('Median')
# medianTable=medianTable.transpose()

# #calculate trends using data that has no nans and count of days > 25
# trendData=smData[['averageSoilMoisture','month','WY']]
# trendData=trendData.set_index('WY').sort_index(ascending=True)
# months_list=trendData.month.unique()
# # trendData=trendData.set_index('month')
# manK=[]
# for i in months_list:
#     try:
#         print(str(i))
#         tempMK=mk.original_test(trendData[trendData.month==i][['averageSoilMoisture']])
#         print(tempMK)
#         if tempMK[2]>0.1:
#             manK.append(float('nan'))
#         else:
#             manK.append(tempMK[7])  
#     except:
#         manK.append(float('nan'))

# manKdf=pd.DataFrame(manK,columns={'Trend'}).transpose()
# manKdf.columns=[months[x] for x in months_list]

# medianTableData=medianTable.append(manKdf)

# #display pivot table 
# st.markdown("Trend (Theil-Sen Slope (inches/year) if Mann-Kendall trend test is significant (p-value <0.1); otherwise nan). Months with less than 25 days of data are not included in the analysis.")

# displayTableData=medianTableData.style\
#     .set_properties(**{'width':'10000px','color':'white'})\
#     .apply(background_gradient, axis=None)\
#     .format(precision=2)

# st.dataframe(displayTableData)

# #download pivot table
# csv = convert_df(medianTableData)
# st.download_button(
#      label="Download Statistics Table Data as CSV",
#      data=csv,
#      file_name='StatisticsTablebyMonth.csv',
#      mime='text/csv',
#  )
