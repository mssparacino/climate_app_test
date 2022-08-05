# -*- coding: utf-8 -*-
"""
Created on Thu Sep 24 14:15:03 2020

@author: msparacino
"""
import pandas

import streamlit as st

import datetime

import arrow

import numpy

import matplotlib.pyplot as plt

from matplotlib import colors

import pymannkendall as mk

#%% set working directory
st.set_page_config(page_title="SNOTEL Site Comparison", page_icon="📈")

st.header("Site Comparison")
st.sidebar.header("Site Comparison")


#%% read measurement data
data_raw=pandas.read_csv('SNOTEL_data_raw.csv.gz')

#%% get raw end date
end_dateRaw = arrow.now().format('YYYY-MM-DD')

#%% read site data
sites_df=pandas.read_csv('SNOTEL_sites.csv.gz')
with open("siteNamesListNS.txt") as f:
    siteNamesList=f.read().split(", ")
siteNamesList = [s.replace("[", "") for s in siteNamesList]
siteNamesList = [s.replace("]", "") for s in siteNamesList]
siteNamesList = [s.replace("'", "") for s in siteNamesList]
siteNames=pandas.DataFrame([sub.split(",") for sub in siteNamesList])
siteNames.columns=['Site','System']

siteKey=sites_df[['index','name']]
siteKey.columns=['code','Site']

#%% merged df
combo_data=pandas.merge(data_raw,siteKey,on="Site",how='inner')
combo_data1=pandas.merge(combo_data,siteNames,on="Site",how='inner')
#combo_data2=pandas.merge(combo_data1,sites_POR,on="code",how='inner')
combo_data2=combo_data1
combo_data2=combo_data2.set_index('Site')

#get WY
combo_data2['Date']=pandas.to_datetime(combo_data2['Date'])
combo_data2['CalDay']=combo_data2['Date'].dt.dayofyear
combo_data2['CY']=pandas.DatetimeIndex(combo_data2['Date']).year
combo_data2['WY']=numpy.where(combo_data2['CalDay']>=274,combo_data2['CY']+1,combo_data2['CY'])

#check for full WY and keep if current WY
fullWYcheck=combo_data2.groupby([combo_data2.index,combo_data2['WY']]).count().reset_index()
fullWYcheck.drop(fullWYcheck [ (fullWYcheck['Date'] <365) & (fullWYcheck['WY'] < int(end_dateRaw[:4])) ].index,inplace=True)
fullWYcheck=fullWYcheck.set_index('Site')

#%% get POR median
manKPOR=[]
median=[]
por_record=[]

for row in siteNames['Site']:
    temp=combo_data2[combo_data2.index==row]
    tempfullWYcheck=fullWYcheck[fullWYcheck.index==row]
    temp=temp[temp['WY'].isin(tempfullWYcheck['WY'])]
    tempMedian=temp[['WY','Date','SWE_in']]
    temp_median=tempMedian.groupby(tempMedian['WY']).max().median()[0]
    median.append([row,temp_median])
    por_start=str(tempMedian['Date'].min())
    por_end=str(tempMedian['Date'].max())
    por_record.append([row,por_start,por_end])
    
    #Man Kendall Test
    tempPOR=temp[['WY','SWE_in']]
    tempPORMKMedian=tempPOR.groupby(tempPOR['WY']).median()
    tempPORManK=mk.original_test(tempPORMKMedian)
    if tempPORManK[2]>0.1:
        manKPOR.append([row,float('nan')])
    else:
        manKPOR.append([row,tempPORManK[7]])       #slope value 
        
medianPOR=pandas.DataFrame(median)
medianPOR.columns=(['Site','MedianPOR'])
medianPOR=medianPOR.set_index('Site')

por_record=pandas.DataFrame(por_record)
por_record=por_record.set_index([0])
por_record.columns=(['por_start','por_end'])

manKPOR=pandas.DataFrame(manKPOR)
manKPOR.columns=(['Site','ManKPOR'])
manKPOR=manKPOR.set_index('Site')

#%%System Selection
system=combo_data2['System'].drop_duplicates()

container=st.sidebar.container()
all=st.sidebar.checkbox("Select both systems")

if all:
    system_select = container.multiselect('Select your system(s):', system, system)
    
else: 
    system_select = container.multiselect('Select your system(s):', system, default=system.iloc[0])
    
def systemfilter():
    return combo_data2[combo_data2['System'].isin(system_select)]

system_data=systemfilter()

#%% multi site selection
tempSD=system_data.reset_index()
sites=tempSD['Site'].drop_duplicates()

#sites=['Fremont Pass']

container=st.sidebar.container()
all=st.sidebar.checkbox("Select all")

if all:
    multi_site_select = container.multiselect('Select one or more sites:', sites, sites)

else:
    multi_site_select = container.multiselect('Select one or more sites:', sites,default=sites.iloc[0])

def multisitefilter():
    return system_data[system_data.index.isin(multi_site_select)]
    
system_site_data=multisitefilter()

#%% filter for parameter
#get parameter list

paramsDF=pandas.DataFrame(['NormMed','Peak SWE Day','First Zero SWE Day','First Zero SWE Day'])
paramsDF['long']=['Median Peak SWE Statistic','Peak SWE Day','First Zero SWE Day','Melt Day Count']
paramsDF['title']=["WY Peak SWE / Median of Annual Peak SWE (for Select WY Range)",
                   "Peak SWE Day",
                   "First Zero SWE Day",
                   "Melt Day Count"]
paramsDF['format']=["{:,.0%}","{:.0f}","{:.0f}","{:.0f}"]
paramsSelect=paramsDF['long']

params_select = st.sidebar.selectbox('Select one parameter:', paramsSelect)
#params_select = str('Peak SWE Day')
param=paramsDF.loc[paramsDF['long']==params_select][0]
title=paramsDF['title'][paramsDF['long']==params_select]
format_Dec=paramsDF['format'][paramsDF['long']==params_select]


#%%start and end dates needed for initial data fetch
startY=1950
startM=10
startD=1
start_date = "%s-%s-0%s"%(startY,startM,startD) #if start day is single digit, add leading 

#dates for st slider need to be in datetime format:
min_date = datetime.datetime(startY,startM,startD)
max_date = datetime.datetime.today() #today

# with st.sidebar: 
st.sidebar.header("Define Select WY Range")
    
startYear = st.sidebar.number_input('Enter Beginning Water Year:', min_value=startY, max_value=int(end_dateRaw[:4]), value=1950)
endYear = st.sidebar.number_input('Enter Ending Water Year:',min_value=startY+1, max_value=int(end_dateRaw[:4]),value=2022)

def startDate():
    return "%s-%s-0%s"%(int(startYear-1),10,1)

start_date=startDate()

def endDate():
    return "%s-0%s-%s"%(int(endYear),9,30)

end_date=endDate()

#change dates to similar for comparison
start_date1=pandas.to_datetime(start_date,utc=True) 
end_date1=pandas.to_datetime(end_date,utc=True) 

final_data=system_site_data[(system_site_data['Date']>start_date1)&(system_site_data['Date']<=end_date1)]

#%%for selected period
summary=pandas.DataFrame()
siteSelect=final_data.index.drop_duplicates()

tempManK=[]
manK=[]
median=[]
for row in siteSelect:
    temp=final_data[final_data.index==row]
    tempMedian=temp[['WY','Date','SWE_in']]
    tempfullWYcheck=fullWYcheck[fullWYcheck.index==row]
    tempMedian=tempMedian[tempMedian['WY'].isin(tempfullWYcheck['WY'])]
    temp_median=tempMedian.groupby(tempMedian['WY']).max().median()[0]
    
    median.append(temp_median)
    
    #Man Kendall Test
    try:
        tempMK=temp[['WY','SWE_in']]
        tempMKMedian=tempMK.groupby(tempMK['WY']).median()
        tempManK=mk.original_test(tempMKMedian)
        if tempManK[2]>0.1:
            manK.append(float('nan'))
        else:
            manK.append(tempManK[7])  
    except:
         manK.append(float('nan'))
    
    temp1=temp['System']
    temp1=temp1.drop_duplicates()
    summary=pandas.concat([summary,temp1],ignore_index=True)

summary=summary.set_index(siteSelect)

  
median=pandas.DataFrame(median)
median=median.set_index(siteSelect)
median.columns=(['Select WY Stat'])
median=median[median.index.isin(siteSelect)]

manK=pandas.DataFrame(manK)
manK=manK.set_index(siteSelect)
manK.columns=(['Select WY Trend'])
manK=manK[manK.index.isin(siteSelect)]

#%%combine POR with Selected stats

por_record=por_record[por_record.index.isin(siteSelect)]
manKPOR=manKPOR[manKPOR.index.isin(siteSelect)]
medianPOR=medianPOR[medianPOR.index.isin(siteSelect)]

summary=pandas.concat([summary,por_record,manKPOR,medianPOR,manK,median],axis=1)
summary=summary[[0,'por_start','por_end','MedianPOR','ManKPOR','Select WY Stat','Select WY Trend']]

summary.columns=['System','POR Start','POR End','POR Stat','POR Trend','Select WY Stat','Select WY Trend']
summary["POR Start"] = pandas.to_datetime(summary["POR Start"]).dt.strftime('%Y-%m-%d')
summary["POR End"] = pandas.to_datetime(summary["POR End"]).dt.strftime('%Y-%m-%d')

summary1=summary.style\
.format({'POR Stat':"{:.1f}",'POR Trend':"{:.2f}"
          ,'Select WY Stat':"{:.1f}",'Select WY Trend':"{:.2f}"})

st.markdown("Compares SWE Statistic (median of annual peak SWE values, inches) and trend (Theil-Sen Slope (inches/year) if Mann-Kendall trend test is significant (p-value <0.1); otherwise nan)")
summary1

# download data
@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')

csv = convert_df(summary)

st.download_button(
     label="Download SNOTEL Comparison Summary as CSV",
     data=csv,
     file_name='SNOTEL_POR_summary.csv',
     mime='text/csv',
 )
#%% full comparison
final_data['CalDay']=final_data['Date'].dt.dayofyear
final_data['CY']=pandas.DatetimeIndex(final_data['Date']).year
final_data['WY']=numpy.where(final_data['CalDay']>=274,final_data['CY']+1,final_data['CY'])

compData=final_data[['SWE_in','CalDay','WY']]
selectWY=compData['WY'].drop_duplicates()
selectSite=compData.index.drop_duplicates()

compList=[]
for WYrow in selectWY:
    tempWYdata=compData[compData['WY']==WYrow]
    try:
        for siterow in selectSite:
            tempSiteData=tempWYdata[tempWYdata.index==siterow]
            tempfullWYcheck=fullWYcheck[fullWYcheck.index==siterow]
            tempSiteData=tempSiteData[tempSiteData['WY'].isin(tempfullWYcheck['WY'])]    
            
            #peak SWE
            tempSiteWYPeak=tempSiteData['SWE_in'].max()
                     
            #POR Median Peak SWE
            tempPORmed=median[median.index==siterow]
            tempMedNorm=tempSiteWYPeak/tempPORmed.iloc[0][0]
            
            #peak SWE day
            tempSiteWYPeakDay=tempSiteData.loc[tempSiteData['SWE_in']==tempSiteWYPeak].iloc[-1][1]
            
            # #first Zero SWE day
            tempZeroAll=tempSiteData[(tempSiteData['SWE_in']==0)&(tempSiteData['CalDay']>tempSiteWYPeakDay)]
            tempZeroAll=tempZeroAll.sort_values(by=['CalDay'])
            tempZeroDay=tempZeroAll['CalDay'].iloc[0]
            
            compList.append([siterow,WYrow,tempSiteWYPeak,tempMedNorm,tempSiteWYPeakDay,tempZeroDay])
    except:
        compList.append([siterow,WYrow,None,None,None,None])
compListDF=pandas.DataFrame(compList)
compListDF.columns=['Site','WY','Peak SWE (in)','NormMed','Peak SWE Day','First Zero SWE Day']
compListDF['Melt Day Count']=compListDF['First Zero SWE Day']-compListDF['Peak SWE Day']


#%%transpose to get days as columns and prent % peak of median

list=compListDF['WY'].drop_duplicates()
finalSites=compListDF['Site'].drop_duplicates()
list=list.sort_values()
yearList=pandas.DataFrame(index=finalSites)
for n in list:
    #n=1979
    temp1=compListDF[compListDF['WY']==n]
    temp1=temp1.set_index('Site')
    temp2=temp1.loc[:,[param.iloc[0]]].copy()
    temp2.columns=[n]
    yearList[n]=temp2
#yearList=yearList.fillna("NaN")
#%%colormap
def background_gradient(s, m=None, M=None, cmap='Blues',low=0, high=0):
    #print(s.shape)
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

yearList = yearList.reindex(sorted(yearList.columns,reverse=True), axis=1)

yearList.insert(0,'System',summary["System"])

select_col=yearList.columns[1:]
yearList1=yearList.style\
    .set_properties(**{'width':'10000px'})\
    .apply(background_gradient, axis=None,subset=select_col)\
    .format('%s'%format_Dec.iloc[0],subset=select_col)
   
st.header("%s"%title.iloc[0])
st.markdown("Date range: %s through %s"%(start_date, end_date))
yearList1

# download data
@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')

csv = convert_df(yearList)

st.download_button(
     label="Download SNOTEL Comparison as CSV",
     data=csv,
     file_name='SNOTEL_comp.csv',
     mime='text/csv',
 )

#%%transpose to get days as columns and present actual SWE value
yearListPeak=pandas.DataFrame(index=finalSites)
for n in list:
    #n=1979
    temp1=compListDF[compListDF['WY']==n]
    temp1=temp1.set_index('Site')
    temp2=temp1.loc[:,['Peak SWE (in)']].copy()
    temp2.columns=[n]
    yearListPeak[n]=temp2

#%%colormap
def background_gradient(s, m=None, M=None, cmap='Blues',low=0, high=0):
    #print(s.shape)
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

yearListPeak = yearListPeak.reindex(sorted(yearListPeak.columns,reverse=True), axis=1)

yearListPeak.insert(0,'System',summary["System"])

yearListPeak1=yearListPeak.style\
    .set_properties(**{'width':'10000px'})\
    .apply(background_gradient, axis=None,subset=select_col)\
    .format('{:.1f}',subset=select_col)

st.header("WY Peak SWE (inches)")
st.markdown("Date range: %s through %s"%(start_date, end_date))
yearListPeak1

# download data
@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')

csv = convert_df(yearListPeak)

st.download_button(
     label="Download SNOTEL Peak SWE Comparison as CSV",
     data=csv,
     file_name='SNOTEL_peakSWE_comp.csv',
     mime='text/csv',
 )
