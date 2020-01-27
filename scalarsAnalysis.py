#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 24 17:08:45 2019

@author: gossn
"""
#%%
import numpy as np
import pandas as pd
import sys
import os
import fileinput
import glob
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.lines import Line2D
path0 = '/home/gossn/Dropbox/Documents/inSitu/Database'
#import seaborn as sns
#sns.set(style='ticks')
import itertools
from string import ascii_lowercase
from sklearn.linear_model import TheilSenRegressor
from sklearn.datasets import make_regression

#Theil-Sen Regressor:
#https://www.youtube.com/watch?v=2Ca7VgSICro&t=7s

#from scipy import stats
pathAbs = '/home/gossn/Dropbox/Documents/ancillary/global'

import cartopy.crs as ccrs
from cartopy.io import shapereader
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cartopy.io.img_tiles as cimgt



font = {'family' : 'DejaVu Sans','weight' : 'bold','size'   : 18}
plt.rc('font', **font)
#mad = stats.median_absolute_deviation(x)

#%% Define some functions!

def make_map(projection=ccrs.PlateCarree()):
    fig, ax = plt.subplots(figsize=(9, 13),
                           subplot_kw=dict(projection=projection))
    gl = ax.gridlines(draw_labels=True)
    gl.xlabels_top = gl.ylabels_right = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    return fig, ax

def MAD(x):
    ''' Compute Median Absolute Deviation '''
#    x = np.array([1,2,1,2,1,2,3,2,123,12,3])
#    madx = MAD(x)
    if not type(x) is np.ndarray:
        ValueError('x must be a numpy array')
    MAD = np.median(np.abs(x-np.median(x)))
    return MAD

def get_axis_limits(ax, scale=.9):
    return ax.get_xlim()[1]*scale, ax.get_ylim()[1]*scale

#%% Read scalars
scalars = pd.read_excel(path0 + '/general/scalars.xlsx', header=1,index_col='StationID')

# Usar para reflectancias hiperespectrales
turb = scalars['T_Dogliotti[FNU]_Mean'].copy()

# Exclude turbidities (Dogliotti) above 1000:
scalars.loc[scalars['T_Dogliotti[FNU]_Mean']>1000,['T_Dogliotti[FNU]_Mean','T_Dogliotti[FNU]_CV']] = np.nan

# Disregard SPM values at Punta Piedras:
scalars.loc[scalars['Subregion'] == 'Punta Piedras',['SPM[mg/l]_Mean','SPM[mg/l]_CV']] = np.nan

# Disregard SS values at station BALakes_20170131_Ch2:
scalars.loc['BALakes_20170131_Ch2',['T_OBS501_SS[FNU]_Mean','T_OBS501_SS[FNU]_CV']] = np.nan




## Supress data from Swimming pools!:
#swimming = pd.Series()
#for st in scalars.index:
#    if 'Swimming Pool' in scalars.loc[st,'Pontoon/Vessel/Place']:
#        swimming.loc[st] = True
#    else:
#        swimming.loc[st] = False
#scalars = scalars.loc[~ swimming,:]



M = {'T_Dogliotti' :'FNU' ,\
     'T_HACH'      :'FNU' ,\
     'T_OBS501_BS' :'FBU' ,\
     'T_OBS501_SS' :'FNU' ,\
     'SPM_Nechad'  :'mg/l',\
     'SPM'         :'mg/l',\
     'SOM'         :'mg/l'}

#     'T_Dog_w'     :'-'   ,\
#     'CHL'        :'ug/l' }

#MPairs = list(itertools.combinations(M.keys(),2))

MPairs = {\
 ('T_HACH'     ,'T_Dogliotti'):{'fit_intercept':True  },
 ('SPM'        ,'SPM_Nechad' ):{'fit_intercept':True  },
 ('T_HACH'     ,'SPM'        ):{'fit_intercept':False },
 ('T_HACH'     ,'T_OBS501_SS'):{'fit_intercept':True  },
 ('SPM'        ,'SOM'        ):{'fit_intercept':False },
 ('T_OBS501_BS','T_OBS501_SS'):{'fit_intercept':True  }}
# ('T_HACH'     ,'T_Dog_w'    ):{'fit_intercept':True  },
# ('HACH'     ,'CHL'       ),

means = [k + '[' + v + ']_Mean' for (k,v) in M.items()]
cvs   = [k + '[' + v + ']_CV'   for (k,v) in M.items()]
stds  = [k + '[' + v + ']_std'  for (k,v) in M.items()]

# Delete values with high CV
for (m,c,s) in zip(means,cvs,stds):
    highCV = scalars[c] > 15
    scalars.loc[highCV,m] = np.nan
    scalars.loc[highCV,c] = np.nan
    scalars[s] = scalars[c]*scalars[m]/100

# Disregard the following regions
ROIs   = ['EPEA','GSJ']
notROI = pd.Series(True,index=scalars.index)
for roi in ROIs:
    notROI = notROI & (scalars.Region != roi)

## Disregard RdP que no son PLATAGUS
#notPlatagus = ~ ((scalars.Region=='RdP') & (~ scalars.index.str.contains('RdP_20181105_PTG-')))
#
## Disregard RdP que no son PLATAGUS
#notBarreiro = ~ ((scalars.Region=='Tagus') & (~ scalars.index.str.contains('Tagus_20190617')))

# Disregard BALakes: all except Chascomus Lake
notChasco = ~ ((scalars.Region=='BALakes') & (scalars.Subregion!='Chascomus Lake'))

# Disregard RdP: Tigre
notTigreRdP = ~ ((scalars.Region=='RdP') & (scalars.Subregion=='Tigre'))

# Disregard st 'RdP_20110321_1' [Laguna las Chilcas]
notChiclas = scalars.index != 'RdP_20110321_1'

# Delete Stations withouth "scalars"
noScalars = ~ scalars.loc[:,means].isna().all(axis=1)

condSelec = notChasco & notTigreRdP & notROI & notChiclas & noScalars# & notPlatagus & notBarreiro

scalars = scalars.loc[condSelec,:]
turb    = turb.loc[   condSelec]

# Divide df by regions and subregions
scalarsRegion    = dict(list(scalars.groupby(['Region']            )))
scalarsSubregion = dict(list(scalars.groupby(['Region','Subregion'])))

regions    = list(scalarsRegion.keys()   )
regions    = ['RdP','Tagus','BALakes']
subregions = list(scalarsSubregion.keys())



#%% Trios Hyper

#Read absorption coefficients!
a_pig = pd.read_excel(pathAbs + '/hyperspectral_absorption_w_phyto.xlsx',sheet_name='a_pig').set_index('Wavelength(nm)')
a_w   = pd.read_excel(pathAbs + '/hyperspectral_absorption_w_phyto.xlsx',sheet_name='a_w').set_index('Wavelength(nm)')

#plt.close('all')
#Definir la escala de colores de turbidez
n = 1000
colors0  = plt.cm.jet(np.linspace(0,1,n))

tPower   = np.logspace(-1,3,n)


sm = plt.cm.ScalarMappable(cmap=plt.cm.jet,norm=plt.Normalize(np.min(tPower),np.max(tPower)))
sm._A = []

colTurb = pd.DataFrame(index=scalars.index,columns=range(4))

for st in turb.index:
    colIdx = np.argmin(np.abs(tPower - turb.loc[st]))
    colTurb.loc[st,:] = colors0[colIdx,:]


trios = pd.read_excel(path0 + '/general/all_Trios.xlsx', sheet_name='Rhow',header=1,index_col='StationID')

trios = trios.loc[condSelec,:]



fig = plt.figure()

wP = np.array(a_pig.index)
aP = 0.0410*np.exp(-0.0123*(wP-443))


wave  = np.array([float(w) for w in list(trios.columns)]).reshape(-1,1)
sp = 0
for region in regions:
    sp+=1
    regFlag = scalars.Region==region
    rho = trios.loc[regFlag,:]
    ax = plt.subplot(1,len(regions),sp)
    for st in rho.index:
        plt.plot(wave,rho.loc[st,:].values,color=list(colTurb.loc[st,:].values),label='_')

    plt.plot(a_w.index,a_w['a_{w}[1/m]']/100,color='k',label='Absorción del agua pura, ' + r'$0.01 \times a_{w}[1/m]$')
    acol = 0
    for a,leg in zip(a_pig.columns,['clorofila-a','ficocianina','picoeritrina']):
        if leg == 'picoeritrina':
            continue
        acol+=0.2
        plt.plot(a_pig.index,a_pig[a],'--',color=[acol,acol,1-acol,1],label='Absorción específica de la ' + leg + ', ' + r'$' + a + '$')
    acol+=0.2
    plt.plot(wP,aP,'--',color=[0,acol,1-acol,1],label='Absorción específica de las partículas, ' + r'$a_{p}^{*}[m^{2}/g]$')
    if sp == 1:
        plt.ylabel('Reflectancia del agua, ' + r'$\rho_{w}$' + '\n' + 'Absorción, ' + r'$a$')        
    if sp == 2:
        plt.xlabel('Longitud de onda [nm]')
    if sp>1:
        plt.setp(ax.get_yticklabels(), visible=False)
    if sp == len(regions):
        plt.legend()
    plt.title(region + '[TriOS]')
    plt.xlim(400,900)
    plt.ylim(0,0.15)
fig.subplots_adjust(right=0.9)
cbar_ax = fig.add_axes([0.9, 0.15, 0.02, 0.7])
#from matplotlib.ticker import LogFormatter
#formatter = LogFormatter(10, labelOnlyBase=False) 
cbar = fig.colorbar(sm, cax=cbar_ax)
cbar.set_ticks(np.linspace(1,1000,5))
cbar.set_ticklabels([r'$10^{-1}$',r'$10^{0}$',r'$10^{1}$',r'$10^{2}$',r'$10^{3}$'])
cbar.ax.set_ylabel('T_Dogliotti [FNU]', rotation=270)

plt.show()
#
#data = np.arange(100, 0, -1).reshape(10, 10)
#cbar_ax = fig.add_axes([0.85, 0.15, 0.05, 0.7])
#data = np.arange(100, 0, -1).reshape(10, 10)
#im = plt.imshow(data, cmap='jet')
#fig.colorbar(im, cax=cbar_ax)
#
#plt.show()
#%% ASD Hyper

plt.close('all')

asd = pd.read_excel(path0 + '/general/all_ASD.xlsx', sheet_name='Rhow',header=1).T
asd.columns = asd.iloc[0,:]
asd = asd.iloc[1:,:]

asd = asd.loc[condSelec,:]


asd.loc[['RdP_20130416_M0413-01','RdP_20130416_M0413-07'],:] = np.nan

wave  = np.array([float(w) for w in list(asd.columns)]).reshape(-1,1)

region = 'RdP'

regFlag = scalars.Region==region

rho = asd.loc[regFlag,:]
fig, ax = plt.subplots()
for st in rho.index:
    plt.plot(wave,rho.loc[st,:].values,color=list(colTurb.loc[st,:].values),label='_')

#acol = 0
#for a,leg in zip(a_pig.columns,['clorofila-a','picocianina','???']):
#    acol+=0.25
#    plt.plot(a_pig.index,a_pig[a],'--',color=[0,acol,1-acol,1],label='Absorción específica ' + leg + ', ' + r'$\times ' + a + '$')

plt.xlabel('Longitud de onda [nm]')

ax2 = ax.twinx()
ax2.plot(a_w.index,a_w['a_{w}[1/m]'],color='k',label='Absorción del agua pura, ' + r'$a_{w}[1/m]$')
ax2.set_yscale('log')

ax.set_ylabel('Reflectancia del agua, ' + r'$\rho_{w}$')
ax2.set_ylabel('Absorción, ' + r'$a$', rotation=270)
plt.legend()
plt.title(region + '[ASD]')

ax.set_xlim(400,1300)
ax.set_ylim(0,0.215)
ax2.set_ylim(0.001,1000)

fig.subplots_adjust(right=0.85)
cbar_ax = fig.add_axes([0.9, 0.15, 0.02, 0.7])
#from matplotlib.ticker import LogFormatter
#formatter = LogFormatter(10, labelOnlyBase=False) 
cbar = fig.colorbar(sm, cax=cbar_ax)
cbar.set_ticks(np.linspace(1,1000,5))
cbar.set_ticklabels([r'$10^{-1}$',r'$10^{0}$',r'$10^{1}$',r'$10^{2}$',r'$10^{3}$'])
cbar.ax.set_ylabel('T_Dogliotti [FNU]', rotation=270)

plt.show()

#%% Regressions

MPairsName = {comb:comb[1] + '[' + M[comb[1]] + ']' + ' vs. ' + comb[0] + '[' + M[comb[0]] + ']' for comb in MPairs.keys()}

colummsStats = ['Slope_YvsX','Intercept_YvsX','R2','MAD_YvsX','N']

MPairsStats = {}

for region in regions:
    MPairsStatsRegion = pd.DataFrame(columns=colummsStats,index=list(MPairsName.values()))

    for comb in MPairs.keys():
        x = scalarsRegion[region][comb[0] + '[' + M[comb[0]] + ']_Mean']
        y = scalarsRegion[region][comb[1] + '[' + M[comb[1]] + ']_Mean']

        nanCond = ~(np.isnan(x) | np.isnan(y))
        x = x[nanCond]
        y = y[nanCond]

        N = len(x)

        if N == 0:
            continue

        x = np.array(x).reshape(-1,1)
        y = np.array(y).reshape(-1,)

        regyx          = TheilSenRegressor(fit_intercept=MPairs[comb]['fit_intercept'], random_state=0).fit(x, y)
        if MPairs[comb]['fit_intercept']:
            Slope_YvsX     = regyx.coef_[0]
        else:
            Slope_YvsX     = regyx.coef_
        Intercept_YvsX = regyx.intercept_
        R2             = np.abs(regyx.score(x, y))
        MAD_YvsX       = MAD(y-(Slope_YvsX*x+Intercept_YvsX).reshape(-1,1))
#        MAE_YvsX       = np.sum(np.abs(y-(Slope_YvsX*x+Intercept_YvsX).reshape(-1,1)))/N

        x = np.array(x).reshape(-1)
        y = np.array(y).reshape(-1,1)

        regxy          = TheilSenRegressor(fit_intercept=MPairs[comb]['fit_intercept'], random_state=0).fit(y, x)
        if MPairs[comb]['fit_intercept']:
            Slope_XvsY     = regxy.coef_[0]
        else:
            Slope_XvsY     = regxy.coef_
        Intercept_XvsY = regxy.intercept_
        MAD_XvsY       = MAD(x.reshape(-1,1)-(Slope_XvsY*y+Intercept_XvsY))
#        MAE_XvsY       = np.sum(np.abs(x.reshape(-1,1)-(Slope_XvsY*y+Intercept_XvsY).reshape(-1,1)))/N

        MPairsStatsRegion.loc[MPairsName[comb],:] = [Slope_YvsX,Intercept_YvsX,R2,MAD_YvsX,N]

        MPairsStatsRegion.to_excel(path0 + '/general/Tesis_Cap2/scalarsLinearFits_' + region + '.xlsx', index = True, sheet_name=region,startrow = 1)

    MPairsStats[region] = MPairsStatsRegion

#%% Colores

colors  = {regions[i]   : cm.get_cmap('tab20')(2*i)      for i in range(len(regions))   }
markers = {subregions[i]: list(Line2D.filled_markers)[i] for i in range(len(subregions))}
#%% MAPA!

font = {'family' : 'DejaVu Sans','weight' : 'bold','size'   : 16}
plt.rc('font', **font)

plt.close('all')
maps = {'BARdp'     :                                                                   \
       {'extension' :[-56, -58.8, -34, -36.6]                                            ,\
        'regions'   :['RdP','BALakes']                                                 ,\
        'subregions':'all'                                                            },\
        'CABA'      :                                                                   \
       {'extension' :[-57.819601, -58.837209, -34.332873, -34.840503]                  ,\
        'regions'   :['RdP']                                                           ,\
        'subregions':['Dredging Zone','CABA','CABA-Colonia','CABA-MDQ','Quilmes']},\
        'Tagus'     :                                                                   \
       {'extension' :[-8.8, -9.4, 38.9, 38.6]                                          ,\
        'regions'   :['Tagus']                                                         ,\
        'subregions':'all'                                                            },\
        'Chascomus' :                                                                   \
       {'extension' :[-57.792212, -58.168493, -35.502406, -35.717329]                  ,\
        'regions'   :['BALakes']                                                       ,\
        'subregions':['Chascomus Lake']                                               }}
#       BARdP con Kakel y Junin: {'extension' :[-56, -61.2, -34, -37]                                            ,\
#        'Junin'     :                                                                   \
#       {'extension' :[-60.804535, -61.177383,-34.518648,-34.737589]                    ,\
#        'regions'   :['BALakes']                                                       ,\
#        'subregions':['Carpincho Lake','Gomez Lake']                                  },\
#        'Kakel'     :                                                                   \
#       {'extension' :[-57.655559,-57.920310,-36.745266,-36.899445]                     ,\
#        'regions'   :['BALakes']                                                       ,\
#        'subregions':['Kakel Huincul Lake']                                           }}



for mapreg in maps.keys():
    extent = maps[mapreg]['extension']
    request = cimgt.GoogleTiles(style = 'satellite')

    fig, ax = make_map(projection=request.crs)
    fig.figsize=(30.0, 25.0)
    ax.set_extent(extent)
    ax.add_image(request, 10)
    for region in maps[mapreg]['regions']:
        for subregion in subregions:
            regMap = maps[mapreg]['subregions']
            if regMap  != 'all':
                if subregion[1] not in regMap:
                    continue
            if subregion[0] == region:
                subreg = (scalars.Region == subregion[0]) & (scalars.Subregion == subregion[1])
                plt.scatter(scalars.loc[subreg,'Lon'],scalars.loc[subreg,'Lat'],color=colors[subregion[0]],marker=markers[subregion],edgecolor='k',s=100,transform=ccrs.Geodetic(),label=subregion[0] + ': ' + subregion[1])
    plt.legend(fontsize=12)
    figOut = path0 + '/general/scalarsAnalysis/MAP_' + mapreg + '.png'
#    fig.savefig(figOut)

#%% Scatter Plots
plt.close('all'); lett = 'ABCDEFGHI'
for comb in MPairs.keys():
    fig = plt.figure(figsize=(30.0, 25.0)); sp = 0
    for scale in ['linear','log']:
        sp+=1; ax = plt.subplot(1,2,sp)
        for region in regions:
            x = np.array(scalarsRegion[region][comb[0] + '[' + M[comb[0]] + ']_Mean'])
            y = np.array(scalarsRegion[region][comb[1] + '[' + M[comb[1]] + ']_Mean'])
            nanCond = ~(np.isnan(x) | np.isnan(y))
            x = x[nanCond]
            if len(x) == 0:
                continue
            if comb[1] != 'T_Dog_w':
                x0  = np.geomspace(0.9*np.min(x),1.1*np.max(x))
                myx = MPairsStats[region].loc[MPairsName[comb],'Slope_YvsX']
                byx = MPairsStats[region].loc[MPairsName[comb],'Intercept_YvsX']
                R2  = MPairsStats[region].loc[MPairsName[comb],'R2']
                if MPairs[comb]['fit_intercept']:
                    fitStr = region + ': y = ' + '%2.2f' % round(myx,2) + 'x ' + '%+2.2f' % round(byx,2)
                else:
                    fitStr = region + ': y = ' + '%2.2f' % round(myx,2) + 'x'
                fitStr = fitStr + ' [R2 = ' + '%.2f' % round(R2,2) + '] [N = ' + str(MPairsStats[region].loc[MPairsName[comb],'N']) + ']'
                plt.plot(x0,myx*x0+byx,'-',color=colors[region],label=fitStr)
            for subregion in subregions:
                if subregion[0] != region:
                    continue
                x    = scalarsSubregion[subregion][comb[0] + '[' + M[comb[0]] + ']_Mean']
                y    = scalarsSubregion[subregion][comb[1] + '[' + M[comb[1]] + ']_Mean']
                xerr = scalarsSubregion[subregion][comb[0] + '[' + M[comb[0]] + ']_std' ]
                yerr = scalarsSubregion[subregion][comb[1] + '[' + M[comb[1]] + ']_std' ]
                if np.all(np.isnan(x) | np.isnan(y)):
                    continue
                plt.errorbar(x, y, yerr=yerr, xerr=xerr, c=colors[subregion[0]],fmt=markers[subregion], capsize=0, elinewidth=0.5,ms=0, ecolor='k',label='_')
                plt.scatter(x, y, c=colors[subregion[0]], marker=markers[subregion], s=100, edgecolor='k',label='_')
        #        plt.errorbar(x, y, yerr=yerr, xerr=xerr, c=colors[subregion[0]], fmt=markers[subregion], capsize=2, elinewidth=0.5,ms=7, ecolor='g',label='_')
                plt.scatter([], [], c=colors[subregion[0]], marker=markers[subregion], s=100,edgecolor='k',label=subregion[0] + ': ' + subregion[1])
                plt.xscale(scale)
                plt.yscale(scale)
        ax.title.set_text(scale.upper())
        if comb[1] != 'T_Dog_w':
            lims = [np.min([ax.get_xlim(), ax.get_ylim()]),np.max([ax.get_xlim(), ax.get_ylim()])]
            ax.plot(lims, lims, '--k', alpha=0.3, zorder=0,label='1:1')
        else:
            plt.xlim(0,110)
        if scale == 'linear':
            plt.legend(fontsize=12)
        plt.xlabel(comb[0] + '[' + M[comb[0]] + ']', y=0)
        plt.ylabel(comb[1] + '[' + M[comb[1]] + ']', x=0)
    figOut = path0 + '/general/scalarsAnalysis/Scatter' + comb[1] + 'vs' + comb[0] + '.png'
#    fig.savefig(figOut)
#    plt.close()
#%% weight factor in TDogliotti 2015
fig = plt.figure(figsize=(30.0, 25.0)); sp = 0
for scale in ['linear','log']:
    sp+=1; ax = plt.subplot(1,2,sp)
    for region in regions:
        x = scalarsRegion[region]['T_HACH[FNU]_Mean']
        y = trios.loc[scalars.Region == region,'645.0']
        cond0 = list(set(x.index) & set(y.index))
        x = np.array(x.loc[cond0])
        y = np.array(y.loc[cond0])
        
        nanCond = ~(np.isnan(x) | np.isnan(y))
        x = x[nanCond]
        if len(x) == 0:
            continue
        for subregion in subregions:
            if subregion[0] != region:
                continue
            x    = scalarsSubregion[subregion][comb[0] + '[' + M[comb[0]] + ']_Mean']
            y    = scalarsSubregion[subregion][comb[1] + '[' + M[comb[1]] + ']_Mean']
            xerr = scalarsSubregion[subregion][comb[0] + '[' + M[comb[0]] + ']_std' ]
            yerr = scalarsSubregion[subregion][comb[1] + '[' + M[comb[1]] + ']_std' ]
            if np.all(np.isnan(x) | np.isnan(y)):
                continue
            plt.errorbar(x, y, yerr=yerr, xerr=xerr, c=colors[subregion[0]],fmt=markers[subregion], capsize=0, elinewidth=0.5,ms=0, ecolor='k',label='_')
            plt.scatter(x, y, c=colors[subregion[0]], marker=markers[subregion], s=100, edgecolor='k',label='_')
    #        plt.errorbar(x, y, yerr=yerr, xerr=xerr, c=colors[subregion[0]], fmt=markers[subregion], capsize=2, elinewidth=0.5,ms=7, ecolor='g',label='_')
            plt.scatter([], [], c=colors[subregion[0]], marker=markers[subregion], s=100,edgecolor='k',label=subregion[0] + ': ' + subregion[1])
            plt.xscale(scale)
            plt.yscale(scale)
    ax.title.set_text(scale.upper())
    lims = [np.min([ax.get_xlim(), ax.get_ylim()]),np.max([ax.get_xlim(), ax.get_ylim()])]
    ax.plot(lims, lims, '--k', alpha=0.3, zorder=0,label='1:1')
    if scale == 'linear':
        plt.legend(fontsize=12)
    plt.xlabel(comb[0] + '[' + M[comb[0]] + ']', y=0)
    plt.ylabel(comb[1] + '[' + M[comb[1]] + ']', x=0)
figOut = path0 + '/general/scalarsAnalysis/Scatter' + comb[1] + 'vs' + comb[0] + '.png'
#%% Boxplots
# Random test data

font = {'family' : 'DejaVu Sans','weight' : 'bold','size'   : 16}
plt.rc('font', **font)

fig = plt.figure(figsize=(30.0, 25.0))
sp = 0
for m in list(M.keys()) + ['SOM/SPM']:
    sp += 1; yMin = np.nan; yMax = np.nan
    ax = plt.subplot(2,4,sp)
    all_data = []
    labels   = []
    for region in regions:
        if m != 'SOM/SPM':
            x = np.array(scalarsRegion[region][m + '[' + M[m] + ']_Mean'])
        else:
            x = np.array(scalarsRegion[region]['SOM[mg/l]_Mean'])/np.array(scalarsRegion[region]['SPM[mg/l]_Mean'])
        x = x[~np.isnan(x)]
        all_data.append(x)
        
        try:
            yMin = np.nanmin([yMin,np.min(np.abs(x))])
            yMax = np.nanmax([yMax,np.max(x)])
        except:
            pass
    # notch shape box plot
    bplot2 = plt.boxplot(all_data,
                             showfliers=True,
                             notch=False,  # notch shape
                             vert=True,  # vertical box alignment
                             patch_artist=True,  # fill with color
                             labels=regions)  # will be used to label x-ticks
    plt.setp(bplot2['medians'], color='k')
    ax.set_yscale('log')
    if m != 'SOM/SPM':
        plt.title(m + '[' + M[m] + ']')
    else:
        plt.title(m)
    plt.ylim(yMin*0.5,yMax*2)
#    ax.annotate(lett[sp-1], xy=get_axis_limits(ax))
    for patch, color in zip(bplot2['boxes'], colors.values()):
        patch.set_facecolor(color)


#%% Scatter: TriOS

font = {'family' : 'DejaVu Sans','weight' : 'bold','size'   : 12}
plt.rc('font', **font)

xOLCI = 865
yOLCI = [400,442.5,510,560,708.75,753.75]

plt.close('all')

trios = pd.read_excel(path0 + '/general/all_Trios.xlsx', sheet_name='OLCI',header=1).set_index('StationID')
trios = trios.loc[condSelec,:]


sp=0
for y in yOLCI:
    sp+=1
    ax = plt.subplot(2,3,sp)
    for subregion in subregions:
        rhoCond = (scalars.Region == subregion[0]) & (scalars.Subregion == subregion[1])
        plt.scatter(trios.loc[rhoCond,float(xOLCI)],trios.loc[rhoCond,float(y)],color=colors[subregion[0]], s=60, marker=markers[subregion],label=subregion[0] + ': ' + subregion[1],edgecolor='k')
    plt.xlim(-0.01,0.1 )
    plt.ylim(-0.01,0.15)
    if sp == 1:
        plt.legend()
#    if sp != 1 and sp != 4:
#        plt.setp(ax.get_yticklabels(), visible=False)
#    if sp <4:
#        plt.setp(ax.get_xticklabels(), visible=False)
    plt.xlabel(r'$\rho_{w}[' + str(xOLCI) + ']$')
    plt.ylabel(r'$\rho_{w}[' + str(y)     + ']$')
#%% Scatter: ASD

font = {'family' : 'DejaVu Sans','weight' : 'bold','size'   : 12}
plt.rc('font', **font)

xOLCI = 865
yOLCI = [400,442.5,510,560,708.75,753.75]

plt.close('all')

asd = pd.read_excel(path0 + '/general/all_ASD.xlsx', sheet_name='OLCI',header=1).set_index('StationID')
asd = asd.loc[condSelec,:]
asd.loc[['RdP_20130416_M0413-01','RdP_20130416_M0413-07'],:] = np.nan

sp=0
for y in yOLCI:
    sp+=1
    ax = plt.subplot(2,3,sp)
    for subregion in [s for s in subregions if s[0]=='RdP']:
        rhoCond = (scalars.Region == subregion[0]) & (scalars.Subregion == subregion[1])
        plt.scatter(asd.loc[rhoCond,float(xOLCI)],asd.loc[rhoCond,float(y)],color=colors[subregion[0]], s=60, marker=markers[subregion],label=subregion[0] + ': ' + subregion[1],edgecolor='k')
    plt.xlim(-0.01,0.1 )
    plt.ylim(-0.01,0.2)
    if sp == 1:
        plt.legend()
#    if sp != 1 and sp != 4:
#        plt.setp(ax.get_yticklabels(), visible=False)
#    if sp <4:
#        plt.setp(ax.get_xticklabels(), visible=False)
    plt.xlabel(r'$\rho_{w}[' + str(xOLCI) + ']$')
    plt.ylabel(r'$\rho_{w}[' + str(y)     + ']$')