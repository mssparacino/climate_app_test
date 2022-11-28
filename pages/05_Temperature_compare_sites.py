# -*- coding: utf-8 -*-
"""
@author: msparacino
"""
#%% Import Libraries
import pandas #for dataframe

import matplotlib.pyplot as plt #for plotting

from matplotlib import colors #for additional colors

import streamlit as st #for displaying on web app

import datetime #for date/time manipulation

import arrow #another library for date/time manipulation

import pymannkendall as mk #for trend anlaysis

from PIL import Image #for map

import matplotlib
import numpy as np
import matplotlib.pyplot as plt

#%% Website display information
st.set_page_config(page_title="Temperature Site Comparison", page_icon="📈")

#%% Stations display information

image=Image.open("Maps/2_Weather_Stations.png")
st.image(image, caption="Static Elevation Map of the Weather Station Locations")

#%% Define data download as CSV function
@st.cache
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')
#%% Read in raw weather data
data_raw=pandas.read_csv('DW_weather.csv.gz')

#%% Get site list
sites=data_raw['site'].drop_duplicates()

sumSites=pandas.DataFrame(sites)
sumSites=sumSites.set_index(['site']) #empty dataframe with sites as index

#%% add POR
data=data_raw
data=data_raw[['site','Month','maxt','mint','meant']]
dates_new=pandas.to_datetime(data_raw.loc[:]['date'])
data=pandas.concat([data,dates_new],axis=1)
data['CY']=data['date'].dt.year

#%%select months

monthOptions=pandas.DataFrame({'Month':['Sep','Oct','Nov','Dec','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug',],
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
    month_select = container.multiselect('Select month(s):',pandas.concat([winterMonths,springMonths]), pandas.concat([winterMonths,springMonths]))
elif winter and summer and (fall==False) and (spring==False):
    month_select = container.multiselect('Select month(s):',pandas.concat([winterMonths,summerMonths]), pandas.concat([winterMonths,summerMonths]))
elif winter and fall and (spring==False) and (summer==False):
    month_select = container.multiselect('Select month(s):',pandas.concat([winterMonths,fallMonths]), pandas.concat([winterMonths,fallMonths]))
elif winter and (fall==False) and (spring==False) and (summer==False):
    month_select = container.multiselect('Select month(s):',winterMonths, winterMonths)
elif spring and (fall==False) and (winter==False) and (summer==False):
    month_select = container.multiselect('Select month(s):',springMonths, springMonths)
elif fall and spring and (winter==False) and (summer==False):
    month_select = container.multiselect('Select month(s):',pandas.concat([springMonths,fallMonths]), pandas.concat([springMonths,fallMonths]))
elif spring and summer and (winter==False) and (fall==False):
    month_select = container.multiselect('Select month(s):',pandas.concat([springMonths,summerMonths]), pandas.concat([springMonths,summerMonths]))
elif summer and fall and (winter==False) and (spring==False):
    month_select = container.multiselect('Select month(s):',pandas.concat([summerMonths,fallMonths]), pandas.concat([summerMonths,fallMonths]))
elif summer and (fall==False) and (winter==False) and (spring==False):
    month_select = container.multiselect('Select month(s):',summerMonths, summerMonths)
elif fall and (spring==False) and (winter==False) and (summer==False):
    month_select = container.multiselect('Select month(s):',fallMonths, fallMonths)
elif fall and summer and spring and (winter==False):
    month_select = container.multiselect('Select month(s):',pandas.concat([springMonths,summerMonths,fallMonths]), pandas.concat([springMonths,summerMonths,fallMonths]))
elif fall and summer and winter and (spring==False):
    month_select = container.multiselect('Select month(s):',pandas.concat([winterMonths,summerMonths,fallMonths]), pandas.concat([winterMonths,summerMonths,fallMonths]))
elif spring and summer and winter and (fall==False):
    month_select = container.multiselect('Select month(s):',pandas.concat([winterMonths,springMonths,summerMonths]), pandas.concat([winterMonths,springMonths,summerMonths]))
elif spring and fall and summer and winter:
    month_select = container.multiselect('Select month(s):',pandas.concat([springMonths,winterMonths,summerMonths,fallMonths]), pandas.concat([springMonths,winterMonths,summerMonths,fallMonths]))

else:
    month_select = container.multiselect('Select month(s):', monthSelect,default=monthSelect)

monthNum_select=pandas.DataFrame(month_select)
monthNum_select=monthOptions.loc[monthOptions['Month'].isin(month_select)]['Num']
    
def monthfilter():
    return data[data['Month'].isin(monthNum_select)]

data=monthfilter()

#filter by day count threshold

if len(month_select)==12:
    dayCountThres=330
    g=data.groupby(['site','CY'])
    data=g.filter(lambda x: len(x)>=dayCountThres)
else:
    dayCountThres=25
    g=data.groupby(['site','CY','Month'])
    data=g.filter(lambda x: len(x)>=dayCountThres)

#data.to_csv('temp.csv')
#%%select stat
#statistic

paramsDF=pandas.DataFrame({0:['maxt','mint','meant'], 'long': ['Max Temp (F)', 'Min Temp (F)', 'Mean Temp (F)']})
paramsSelect=paramsDF['long']

stat_select= st.sidebar.selectbox(
     'Select one statistic:', paramsSelect)

#stat_select='Mean Temp (F)'
stat_selection=paramsDF.loc[paramsDF['long']==stat_select][0]

#%%calulcate params for POR
manKPOR=[]
por=[]
medstat=[]
for site in sites:
    dataBySite=data[data['site']==site]
    
    porS=dataBySite['date'].min()
    porE=dataBySite['date'].max()
    por.append([site,porS,porE])
    
    #get medians
    dataBySiteParam=dataBySite[stat_selection.iloc[0]]
    tempstat=dataBySiteParam.median()
    medstat.append(tempstat)
    
    #Man Kendall Test
    dataforMK=dataBySite[[stat_selection.iloc[0],'CY']]
    tempPORMKMedian=dataforMK.groupby(dataforMK['CY']).median()
    tempPORManK=mk.original_test(tempPORMKMedian)
    if tempPORManK[2]>0.1:
        manKPOR.append([site,None])
    else:
        manKPOR.append([site,tempPORManK[7]])       #slope value 

manKPOR=pandas.DataFrame(manKPOR)
manKPOR=manKPOR.set_index([sites])
manKPOR.columns=(['Site','POR Trend'])
    
pordf=pandas.DataFrame(por)
pordf=pordf.set_index([0])
pordf.columns=["POR Start","POR End"]

medstatdf=pandas.DataFrame(medstat)
medstatdf=medstatdf.set_index([sites])
medstatdf.columns=['POR Stat']

sumSites=pandas.concat([pordf,medstatdf,manKPOR],axis=1)

sumSites['POR Start']=pandas.to_datetime(sumSites["POR Start"]).dt.strftime('%Y-%m-%d')
sumSites['POR End']=pandas.to_datetime(sumSites["POR End"]).dt.strftime('%Y-%m-%d')

#%%make selections
sites=pandas.DataFrame(data['site'].drop_duplicates())
sites['long']=['Antero (AN)','Cheesman (CM)','DIA (DI)','Dillon (DL)','DW Admin (DW)','Evergreen (EG)',
               'Eleven Mile (EM)','Gross (GR)','Kassler (KS)','Moffat HQ (MF)','Ralston (RS)','Central Park (SP)',
               'Strontia (ST)','Williams Fork (WF)']

container=st.sidebar.container()
all=st.sidebar.checkbox("Select all")

if all:
    multi_site_select_long = container.multiselect('Select one or more sites:', sites['long'], sites['long'])

else:
    multi_site_select_long = container.multiselect('Select one or more sites:', sites['long'],default=sites['long'].iloc[0])
 
multi_site_select=sites['site'][sites['long'].isin(multi_site_select_long)]

def multisitefilter():
    return data[data['site'].isin(multi_site_select)]
    
data_sites=multisitefilter()

#%%start and end dates needed for initial data fetch
startY=1900
startM=10
startD=1
start_date = "%s-%s-0%s"%(startY,startM,startD) #if start day is single digit, add leading 0
end_dateRaw = arrow.now().format('YYYY-MM-DD')

#dates for st slider need to be in datetime format:
min_date = datetime.datetime(startY,startM,startD)
max_date = datetime.datetime.today() #today

# with st.sidebar: 
startYear = st.sidebar.number_input('Enter Beginning Water Year:', min_value=startY, max_value=int(end_dateRaw[:4]), value=startY)
endYear = st.sidebar.number_input('Enter Ending Water Year:',min_value=startY, max_value=int(end_dateRaw[:4]),value=2022)

def startDate():
    return "%s-0%s-0%s"%(int(startYear),1,1)

start_date=startDate()

def endDate():
    return "%s-%s-%s"%(int(endYear),12,31)

end_date=endDate()

#change dates to similar for comparison
start_date1=pandas.to_datetime(start_date)
end_date1=pandas.to_datetime(end_date) 

#%%threshold filter
thresholdHigh = st.sidebar.number_input('Set Upper %s threshold:'%stat_select,step=1,min_value=0, value=100)

thresholdLow = st.sidebar.number_input('Set Lower %s threshold:'%stat_select,step=1,min_value=-200, value=0)

#%%FILTERED DATA
data_sites_years=data_sites[(data_sites['date']>start_date1)&(data_sites['date']<=end_date1)]

#%% calculate params for selected period

manKPORSelect=[]
medstatSelect=[]

siteSelect=data_sites_years['site'].drop_duplicates()

for site in sites['site']:
    dataBySite=data_sites_years[data_sites_years['site']==site]
    #filter by day count threshold

    dataBySite=dataBySite.groupby('CY').filter(lambda x : len(x)>=dayCountThres)

    #get medians
    dataBySiteParam=dataBySite[stat_selection]
    tempstat=dataBySiteParam.median()
    medstatSelect.append(tempstat[0])
    
    #Man Kendall Test
    try:
        dataforMKSelect=dataBySite[[stat_selection.iloc[0],'CY']]
        tempPORMKMedian=dataforMKSelect.groupby(dataforMKSelect['CY']).median()
        tempPORManK=mk.original_test(tempPORMKMedian)
    except:
        pass
    if tempPORManK[2]>0.1:
        manKPORSelect.append(float('nan'))
    else:
        manKPORSelect.append(tempPORManK[7])       #slope value 

manKPORSelect=pandas.DataFrame(manKPORSelect)
manKPORSelect=manKPORSelect.set_index([sites['site']])
manKPORSelect.columns=(['Select CY Trend'])
manKPORSelect=manKPORSelect[manKPORSelect.index.isin(siteSelect)]

medstatSelectdf=pandas.DataFrame(medstatSelect)
medstatSelectdf=medstatSelectdf.set_index([sites['site']])
medstatSelectdf.columns=(['Select CY Stat'])
medstatSelectdf=medstatSelectdf[medstatSelectdf.index.isin(siteSelect)]

sumSites=pandas.concat([sumSites,medstatSelectdf,manKPORSelect],axis=1)      
sumSites=sumSites.drop("Site",axis=1)

sumSites1=sumSites[sumSites.index.isin(multi_site_select)]
sumSites1['long']=""

for i in range(0,len(sumSites1)):
    idx=sumSites1.index[i]
    site_long=sites[sites.site==idx].long.iloc[0]
    sumSites1.long.iloc[i]=site_long
    
sumSites1=sumSites1.set_index('long')
sumSitesDisplay=sumSites1.style\
    .format({'POR Stat':"{:.1f}",'POR Trend':"{:.2f}"
              ,'Select CY Stat':"{:.1f}",'Select CY Trend':"{:.2f}"})\
    .set_table_styles([dict(selector="th",props=[('max-width','3000px')])])

st.header("Site Comparison")
st.markdown("Compares the median (in degrees) for selected temperature statistic and trend (Theil-Sen Slope in degrees/year) if Mann-Kendall trend test is significant (p-value <0.1); otherwise nan)")
st.markdown("Date range for selected months: %s through %s"%(start_date, end_date))
sumSitesDisplay

#%% download Summary Table data

csv = convert_df(sumSites1)

st.download_button(
     label="Download Summary Table as CSV",
     data=csv,
     file_name='Summary_Table.csv',
     mime='text/csv',
 )

#%%Temp CY Median / Temp POR Median

compData=data_sites_years[['site',stat_selection.iloc[0],'CY']]
selectCY=compData['CY'].drop_duplicates()
selectSite=compData['site'].drop_duplicates()

compList=[]
for CYrow in selectCY:
    tempCYdata=compData[compData['CY']==CYrow]
    try:
        for siterow in selectSite:
            site_long=sites[sites.site==siterow].long.iloc[0]
            tempSiteData=tempCYdata[tempCYdata['site']==siterow]
            tempSiteCY=tempSiteData[stat_selection.iloc[0]].median()
            
            #median for selected POR
            tempPORmed=medstatSelectdf[medstatSelectdf.index==siterow]
            tempMedNorm=tempSiteCY-tempPORmed.iloc[0][0]
            
            compList.append([site_long,CYrow,tempMedNorm,tempSiteCY])
    except:
        compList.append([site_long,CYrow,None,None])
compListDF=pandas.DataFrame(compList)
compListDF.columns=['Site','CY','NormMed','CY Value']

#%%transpose to get days as columns

list=compListDF['CY'].drop_duplicates()
finalSites=compListDF['Site'].drop_duplicates()
list=list.sort_values()
yearList=pandas.DataFrame(index=finalSites)
for n in list:
    temp1=compListDF[compListDF['CY']==n]
    temp1=temp1.set_index('Site')
    temp2=temp1.iloc[:,[1]].copy()
    temp2.columns=[n]
    yearList[n]=temp2

#%%colormap

def hex_to_rgb(value):
    '''
    Converts hex to rgb colours
    value: string of 6 characters representing a hex colour.
    Returns: list length 3 of RGB values'''
    value = value.strip("#") # removes hash symbol if present
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


def rgb_to_dec(value):
    '''
    Converts rgb to decimal colours (i.e. divides each value by 256)
    value: list (length 3) of RGB values
    Returns: list (length 3) of decimal values'''
    return [v/256 for v in value]

def get_continuous_cmap(hex_list, float_list=None):
    ''' creates and returns a color map that can be used in heat map figures.
        If float_list is not provided, colour map graduates linearly between each color in hex_list.
        If float_list is provided, each color in hex_list is mapped to the respective location in float_list. 
        
        Parameters
        ----------
        hex_list: list of hex code strings
        float_list: list of floats between 0 and 1, same length as hex_list. Must start with 0 and end with 1.
        
        Returns
        ----------
        colour map'''
    rgb_list = [rgb_to_dec(hex_to_rgb(i)) for i in hex_list]
    if float_list:
        pass
    else:
        float_list = list(np.linspace(0,1,len(rgb_list)))
        
    cdict = dict()
    for num, col in enumerate(['red', 'green', 'blue']):
        col_list = [[float_list[i], rgb_list[i][num], rgb_list[i][num]] for i in range(len(float_list))]
        cdict[col] = col_list
    cmp = matplotlib.colors.LinearSegmentedColormap('my_cmp', segmentdata=cdict, N=256)
    return cmp


hex_list = ['#0080ff',
'#66b3ff',
'#ccccff',
'#ffcccc',
'#ff6666',
'#ff0000']


new_cmap=get_continuous_cmap(hex_list)

def background_gradient(s, m=None, M=None, cmap=new_cmap,low=0, high=0):
    #print(s.shape)
    if m is None:
        m = s.min().min()
    if M is None:
        M = s.max().max()
    rng = M - m
    norm = colors.CenteredNorm(vcenter=0)
    normed = s.apply(norm)

  #  cm = plt.cm.get_cmap(cmap)
  
    c = normed.applymap(lambda x: colors.rgb2hex(new_cmap(x)))
    ret = c.applymap(lambda x: 'background-color: %s' % x)
    return ret 

yearList = yearList.reindex(sorted(yearList.columns,reverse=True), axis=1)

#select_col=yearList.columns[:]
yearList1=yearList.style\
    .set_properties(**{'width':'10000px'})\
    .apply(background_gradient, axis=None)\
    .format('{:,.1f}')

    #.background_gradient(cmap='Blues',low=0,high=1.02,axis=None, subset=select_col)\    
st.header("%s CY Median - %s Selected CY Median"%(stat_select,stat_select))
st.markdown("Date range for selected months: %s through %s"%(start_date, end_date))
yearList1

#%% download temp comparison data
csv = convert_df(yearList)

st.download_button(
     label="Download Temperature Comparison as CSV",
     data=csv,
     file_name='Temp_comp.csv',
     mime='text/csv',
 )
#%%transpose to get days as columns

list=compListDF['CY'].drop_duplicates()
finalSites=compListDF['Site'].drop_duplicates()
list=list.sort_values()
yearList=pandas.DataFrame(index=finalSites)
for n in list:
    temp1=compListDF[compListDF['CY']==n]
    temp1=temp1.set_index('Site')
    temp2=temp1.iloc[:,[2]].copy()
    temp2.columns=[n]
    yearList[n]=temp2

#%%colormap
def background_gradient(s, m=None, M=None, cmap=new_cmap,low=0.2, high=0):
    #print(s.shape)
    if m is None:
        m = s.min().min()
    if M is None:
        M = s.max().max()
    rng = M - m
    norm = colors.Normalize(m - (rng * low),
                            M + (rng * high))
    normed = s.apply(norm)
   
    
   #cm = plt.cm.get_cmap(cmap)
    c = normed.applymap(lambda x: colors.rgb2hex(new_cmap(x)))
    ret = c.applymap(lambda x: 'background-color: %s' % x)
    return ret 

yearList = yearList.reindex(sorted(yearList.columns,reverse=True), axis=1)

#select_col=yearList.columns[:]
yearList2=yearList.style\
    .set_properties(**{'width':'10000px'})\
    .apply(background_gradient, axis=None)\
    .format('{:,.1f}')

    #.background_gradient(cmap='Blues',low=0,high=1.02,axis=None, subset=select_col)\    
st.header("%s CY Median"%(stat_select))
st.markdown("Date range for selected months: %s through %s"%(start_date, end_date))
yearList2

#%% download medians data

csv = convert_df(yearList)

st.download_button(
     label="Download Medians as CSV",
     data=csv,
     file_name='Temp_CY_value_comp.csv',
     mime='text/csv',
 )

#%%FOR THRESHOLD
#%%calc statistic for all months
compListCount=[]
for CYrow in selectCY:
    tempCYdata=compData[compData['CY']==CYrow]
    try:
        for siterow in selectSite:
            site_long=sites[sites.site==siterow].long.iloc[0]
            tempSiteData=tempCYdata[tempCYdata['site']==siterow]
            tempSiteData=tempSiteData.drop(columns=['site','CY'])
            count=tempSiteData[(tempSiteData < thresholdHigh)&(tempSiteData > thresholdLow)].count()[0]
            if (len(tempSiteData)==0):
                compListCount.append([site_long,CYrow,None])
            else:
                compListCount.append([site_long,CYrow,count])
    except:
        compListCount.append([site_long,CYrow,None])
        
compListCountDF=pandas.DataFrame(compListCount)
compListCountDF.columns=['Site','CY','Count']

#%%transpose to get Months as columns

countList=pandas.DataFrame(index=finalSites)
for n in list:
    #n=1979
    temp1=compListCountDF[compListCountDF['CY']==n]
    temp1=temp1.set_index('Site')
    temp2=temp1.iloc[:,[1]].copy()
    temp2.columns=[n]
    countList[n]=temp2
countList = countList.reindex(sorted(countList.columns,reverse=True), axis=1)

#%%colormap
def background_gradient(s, m=None, M=None, cmap='OrRd',low=0, high=0):
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

#select_col=yearList.columns[:]
countList1=countList.style\
    .set_properties(**{'width':'10000px'})\
    .format('{:,.0f}')\
    .apply(background_gradient, axis=None)\

    #.background_gradient(cmap='Blues',low=0,high=1.02,axis=None, subset=select_col)\    
st.header("Count of days with %s between %s and %s %s"%(stat_select,thresholdLow, thresholdHigh, stat_select))
st.markdown("Date range for selected months: %s through %s"%(start_date, end_date))
countList1

#%% download temp count data

csv = convert_df(countList)

st.download_button(
     label="Download Temperature Count Comparison as CSV",
     data=csv,
     file_name='Temp_count_comp.csv',
     mime='text/csv',
 )
