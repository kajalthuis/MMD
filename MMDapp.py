# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 14:52:55 2022

@author: KALT
"""
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from PIL import Image
import numpy as np
from datetime import timedelta

##### INPUTS #####
st.set_page_config(layout="wide")
st.title('Analyse Beaudrain-S Markermeerdijken')

##### Bestanden openen #####

Overzicht_tot = pd.read_excel('Overzicht WSM.xlsx', sheet_name='WSM')

Vakken = list(Overzicht_tot['Vak'].unique())
Vak = st.sidebar.selectbox('Kies Beaudrain-S vak', Vakken)
#Vak = 'Camping'

Pompvakken = list(Overzicht_tot[Overzicht_tot['Vak'] == Vak]['Pompvak'].unique())
Pompvak = st.sidebar.selectbox('Kies Pompvak', Pompvakken)
#Pompvak = '135_30'
Overzicht_pompvak = Overzicht_tot[(Overzicht_tot['Vak'] == Vak) & (Overzicht_tot['Pompvak'] == Pompvak)]

st.subheader(Vak + ' - ' + Pompvak)

WSMlist = list(Overzicht_pompvak['WSM'])
Zettinglist_WSM = list(Overzicht_pompvak['WSM zetting'])
Zettinglist_ZB = list(Overzicht_pompvak['Zakbaak'])
pomp_aan = Overzicht_pompvak['Pomp aan'].iloc[0]
pomp_uit = Overzicht_pompvak['Pomp uit'].iloc[0]
waterspanning_start = list(Overzicht_pompvak['Waterspanning start'])

FileWSM_ = f'{Vak}/WSM + zetting {Vak}.xlsx'
FileWSM = pd.read_excel(FileWSM_, skiprows = [0,1,2,3,4,5,6], sheet_name=f'{Pompvak} WSM')
FileWSM = FileWSM.dropna(subset=['Date'])

##### Check boxes en plot kaartje #####
plot_zetting = st.sidebar.checkbox('Plot zetting', value=False)
plot_debiet = st.sidebar.checkbox('Plot debiet', value=False)
plot_CPT = st.sidebar.checkbox('Plot CPT', value=False)

try:
    kaart = Image.open(f'{Vak}/kaart {Pompvak}.png')
    with st.expander('Kaart'):
        st.image(kaart)
except:
    pass
    
##### PLOT CPT #####
try:
    cpt = Image.open(f'{Vak}/CPT {Pompvak}.png')
    with st.expander('CPT'):
        st.image(cpt)
except:
    pass

##### PLOT ruwe data #####
WSM_plot, ax =plt.subplots(2, figsize=(15,15))

minx = FileWSM['Date'].min()-timedelta(days=10)
maxx = FileWSM['Date'].max()+timedelta(days=10)

Legend = ['Pomp aan']
ax[0].plot([pomp_aan, pomp_aan],[-100,1000], 'g--')
if not pd.isnull(pomp_uit):
    ax[0].plot([pomp_uit, pomp_uit],[-100,1000], 'b--')
    Legend.append('Pomp uit')

minlim = 125
maxlim = 195
for WSM_ in WSMlist:
    FileWSM[WSM_][FileWSM[WSM_] < 1] = np.nan  
    ax[0].plot(FileWSM['Date'], FileWSM[WSM_])
    
    minlimWSM = FileWSM[WSM_].min()
    if minlimWSM < minlim:
        minlim = minlimWSM
    maxlimWSM = FileWSM[WSM_].max()
    if maxlimWSM > maxlim:
        maxlim = maxlimWSM 
        
ax[0].grid()
ax[0].set_xlim(minx, maxx)
ax[0].set_ylim([minlim-5, maxlim+5])
ax[0].set_title('Waterspanning ruwe data', fontsize=20)
ax[0].set_ylabel('Waterspanning [kPa]', fontsize=14)
Legend = Legend + WSMlist
ax[0].legend(Legend)

##### Vacuum ongecorrigeerd voor zetting #####

for num in range(len(WSMlist)):
    FileWSM[f'{WSMlist[num]} vacuum'] = FileWSM[WSMlist[num]] - waterspanning_start[num]

##### Waterspanning gecorrigeerd voor zetting #####
Filezetting_ = 'Zetting.csv'
Filezetting = pd.read_csv(Filezetting_)
for num, WSMzetting_name in enumerate(Zettinglist_WSM):
    
    if type(WSMzetting_name) == str:
        FileWSM[f'wsm {num+1} correct'] = 0.0 *len(FileWSM)
        
        WSMzetting_data = Filezetting.loc[Filezetting['PuntNummer'] == WSMzetting_name].copy()
        WSMzetting_data.loc[:, 'Datum'] = pd.to_datetime(WSMzetting_data.loc[:, 'Datum'], format='%Y-%m-%d')
        WSMzetting_data = WSMzetting_data.set_index('Datum')
        
        nearest = WSMzetting_data.index.get_indexer(FileWSM['Date'], method='nearest')
        for i, row in enumerate(FileWSM.index):
            
            correctie = WSMzetting_data['ZettingCumulatief'].iloc[nearest[i]]
            FileWSM.loc[row, f'wsm {num+1} correct'] = FileWSM.loc[row, WSMlist[num]] - correctie*10
    else:
        FileWSM[f'wsm {num+1} correct'] = FileWSM[f'{WSMlist[num]}']
    
    FileWSM[FileWSM[f'wsm {num+1} correct'] < 1] = np.nan    
    
##### Vacuum gecorrigeerd voor zetting #####

for num in range(len(WSMlist)):
    FileWSM[f'wsm {num+1} vacuum'] = FileWSM[f'wsm {num+1} correct'] - waterspanning_start[num]
    
##### PLOT Gecorrigeerde data #####
 
aan, = plt.plot([pomp_aan, pomp_aan],[-100,1000], 'g--')
Label = [aan]

if not pd.isnull(pomp_uit):
    uit, = ax[1].plot([pomp_uit, pomp_uit],[-100,1000], 'b--')
    Label.append(uit)
    
max_vacuum = [0] * len(WSMlist)
pomptijd = [0] * len(WSMlist)
pomptijd_plan = list(Overzicht_pompvak['Geplande pomptijd'])
pomptijd_plan = [int(i) for i in pomptijd_plan]
WSM_diepte = list(Overzicht_pompvak['Diepte'])
WSM_diepte = [str(i) for i in WSM_diepte]

for num, WSM in enumerate(WSMlist):
    ax[1].plot(FileWSM['Date'], FileWSM[f'{WSM} vacuum'], 'lightgrey')
    WSM, = ax[1].plot(FileWSM['Date'], FileWSM[f'wsm {num+1} vacuum'])

    Label.append(WSM)
    vac = FileWSM[FileWSM[f'wsm {num+1} vacuum'] > -100]
    max_vacuum[num] = round(vac[f'wsm {num+1} vacuum'].min())
    try:
        time_pomp = pomp_uit - pomp_aan
        pomptijd[num] = int(time_pomp.days)
    except:
        pomptijd[num] = '-'
    
ax[1].grid()
ax[1].set_xlim(minx, maxx)
ax[1].set_ylim([-100, 20])
ax[1].set_title('Vacuüm gecorrigeerd voor zetting', fontsize=20)
ax[1].set_ylabel('Vacuümdruk [kPa]', fontsize=14)

df_info = pd.DataFrame(list(zip(WSMlist,
                                WSM_diepte,
                                max_vacuum,
                                pomptijd_plan,
                                pomptijd)),
                       columns =['WSM',
                                 'Diepte [m NAP]',
                                 'Max. vacuüm [kPa]',
                                 'Geplande pomptijd [dagen]',
                                 'Echte pomptijd [dagen]'])

df_info = df_info.set_index('WSM')

with st.expander('Overzicht per WSM'):
    st.dataframe(df_info)

#### Pomp ####
try:
    FilePomp = pd.read_excel(f'{Vak}/WSM + zetting {Vak}.xlsx', sheet_name = f'{Pompvak} pomp')
    FilePomp = FilePomp.dropna(subset=['Datum'])
    FilePomp['Vacuum'] = FilePomp['Vacuum']*100
    Pomp_meting, = ax[1].plot(FilePomp['Datum'], FilePomp['Vacuum'], 'ro-')
    Label.append(Pomp_meting)
    Legend.append('Pomp meting')
except:
    pass

ax[1].legend(Label, Legend)    
with st.expander('Waterspanning'):
    st.pyplot(WSM_plot)

## Zakbaakmetingen ##
ZBzetting_name = Overzicht_pompvak['Zakbaak'].iloc[0]

if not pd.isnull(ZBzetting_name):
    ZB_plot, ax = plt.subplots(figsize=(15,8))
    ax2 = ax.twinx()

    if type(ZBzetting_name) == str:
        ZBzetting_data = Filezetting.loc[Filezetting['PuntNummer'] == ZBzetting_name].copy()
        ZBzetting_data.loc[:, 'Datum'] = pd.to_datetime(ZBzetting_data.loc[:, 'Datum'], format='%Y-%m-%d')
        ZBzetting_data['ZettingCumulatief'] = ZBzetting_data['ZettingCumulatief'] * -1
    
    p1 = ax.plot(ZBzetting_data['Datum'], ZBzetting_data['ZettingCumulatief'], label='Zetting [m]')
    p2 = ax2.plot(ZBzetting_data['Datum'], ZBzetting_data['Dikte'], 'orange', label='Zandophoging [m]')
    p3 = ax.plot([pomp_aan, pomp_aan],[-100,1000], 'g--', label='Pomp aan')
    
    if not pd.isnull(pomp_uit):
        p4 = ax.plot([pomp_uit, pomp_uit],[-100,1000], 'b--', label='Pomp uit')
    
    ax.grid()
    ax.set_xlim(minx, maxx)
    ax.set_ylim(ZBzetting_data['ZettingCumulatief'].min()-0.1, 0)
    ax.set_title('Zakbaakmetingen', fontsize=20)
    ax.set_ylabel('Zetting [m]', fontsize=14)
    ax2.set_ylabel('Zandophoging [m]', fontsize=14)
    
    try:
        ax.legend(handles=p1+p2+p3+p4)
    except:
        ax.legend(handles=p1+p2+p3)
    
    with st.expander('Zetting'):
        st.pyplot(ZB_plot)
else:
    pass