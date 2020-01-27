#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 13 17:51:44 2019

@author: gossn
"""
#%%

import numpy as np
import matplotlib.pyplot as plt
from netCDF4 import Dataset
import os

import sys

pathHomeMadeModules = '/home/gossn/Dropbox/Documents/pyHomeMadeModules'

sys.path.append(pathHomeMadeModules)
import roiNcdf as rn


font = {'family' : 'DejaVu Sans','weight' : 'bold','size'   : 50}
plt.rc('font', **font, 'lines', linewidth=7)

#%%
def variograma2D(A):
    
#    A = raster0
#    plt.imshow(raster0)
    
    R,C = np.shape(A)

    B = np.empty((3*R-2,3*C-2))
    B[:] = np.nan
    
    B[(R-1):(2*R-1),(C-1):(2*C-1)] = A
    
    gamma = np.zeros(((R-1)+(C-1)+1,1))
    Nh    = np.zeros(((R-1)+(C-1)+1,1))
    
    for r in range(2*R-1):
#        print(str(r/(2*R-1)))
        for c in range(2*C-1):
    
            W = B[r:(r+R),c:(c+C)]
    
            h = np.abs(r-(R-1)) + np.abs(c-(C-1))
#            N = np.sum(~ np.isnan(W))

            WMA = (W-A)**2

            WA = np.nansum(WMA)
            N = np.sum(~ np.isnan(WMA))

            gamma[h] = gamma[h] + WA
            Nh[h]    = Nh[h]    + N

    vario = np.divide(gamma,2*Nh)
    
    #        print('R' + str(r) + 'C' + str(c) + 'H' + str(h) + 'N' + str(N))
    #        print(W)
    
#    nuggetFitLags     = range(1,3)
#    lin = np.polyfit(nuggetFitLags,np.log(vario[nuggetFitLags]),1)
#    nugget = np.exp(lin[1])

#    nuggetFitLags     = range(1,4)
#    lin = np.polyfit(nuggetFitLags,vario[nuggetFitLags],1)
#    nugget = lin[1]

    out = {}

    out['nugget'] = vario[1]
    out['vario' ] = vario
    out['Nh'    ] = Nh
    out['N'     ] = np.sum(~ np.isnan(A))
    out['mu'    ] = np.sum(A[~ np.isnan(A)])/out['N']
    
    return out
#%%
def variograma1D(A):
    R = len(A)

    B = np.empty(3*R-2)
    B[:] = np.nan
    
    B[(R-1):(2*R-1)] = A
    
    gamma = np.zeros((R,1))
    Nh    = np.zeros((R,1))
    
    for r in range(2*R-1):
        W = B[r:(r+R)]

        h = np.abs(r-(R-1))
#            N = np.sum(~ np.isnan(W))

        WMA = (W-A)**2

        WA = np.nansum(WMA)
        N = np.sum(~ np.isnan(WMA))

        gamma[h] = gamma[h] + WA
        Nh[h]    = Nh[h]    + N

    vario = np.divide(gamma,2*Nh)
    

    out = {}

    out['nugget'] = vario[1]
    out['vario' ] = vario
    out['Nh'    ] = Nh
    out['N'     ] = np.sum(~ np.isnan(A))
    out['mu'    ] = np.sum(A[~ np.isnan(A)])/np.sum(~ np.isnan(A))
    return out
#%% VARIOGRAMAS: 2D, todas
#    
#pathL2Img = '/home/gossn/Dropbox/Documents/inSitu/Database/matchUpImages/MA/RdP/matchUps/L2'
#
#imgList = os.listdir(pathL2Img)
#
#flag0 = True
#
#V = {}
#
#img0 = 0
#
#for img in imgList:
#    img0+=1
#    V[img] = {}
#    rhos = Dataset(pathL2Img + '/' + img + '/' + img + '.L2_RC','r')
#    
#    if flag0:
#        bandsImgAll = [int(b[len('rhos_'):]) for b in list(rhos['geophysical_data'].variables) if b[:len('rhos_')] == 'rhos_']
#        flag0 = False
#
#    for b in bandsImgAll:
#
#        print(img + '[' + str(img0) + '] ' + str(b))        
#
#        raster = rhos['geophysical_data']['rhos_' + str(b)][:,:]
#        raster[raster.mask] = np.nan
#        V[img][str(b)] = variogramaJG(raster)
#
#np.save('/home/gossn/Dropbox/Documents/Lineas/PCA/VariogramasMODIS.npy', V)

#%% VARIOGRAMAS todas, 

pathL2Img = '/home/gossn/Dropbox/Documents/inSitu/Database/matchUpImages/MA/RdP/matchUps/L2'

imgList = os.listdir(pathL2Img)

imgList = ['A2014006174500', 'A2012321174500', 'A2012319175500', 'A2018312175000']
#imgList = ['A2012319175500']

flag0 = True

V = {}

img0 = 0


varioDim = '2D'

plt.close('all')

for img in imgList:
    img0+=1
    V[img] = {}
    rhos = Dataset(pathL2Img + '/' + img + '/' + img + '.L2_RC','r')

    lat = rhos['navigation_data']['latitude' ][:,:]
    lon = rhos['navigation_data']['longitude'][:,:]

    roi = {'N':-35.255,'S':-35.52,'W':-57.05,'E':-56.7}
    
    
    ROI = rn.selectROI(lat,lon,roi)
#    ROI = rn.selectROI(lat,lon,{'N':-35.255,'S':-35.52,'W':-57.05,'E':-56.7})


    if flag0:
        bandList = [int(b[len('rhos_'):]) for b in list(rhos['geophysical_data'].variables) if b[:len('rhos_')] == 'rhos_']
#        bandList.remove(667 )
#        bandList.remove(678 )
#        bandList.remove(748 )
#        bandList.remove(1640)
        flag0 = False

    for b in bandList:

        print(img + '[' + str(img0) + '] ' + str(b))        

        raster0 = rhos['geophysical_data']['rhos_' + str(b)][:,:]

        raster0 = rn.sliceFromROI(raster0,ROI)
        raster0[raster0.mask] = np.nan
            
        R,C = np.shape(raster0)

        if varioDim == '1D':
            it0 = 0; noData = True
            while noData:
                raster = raster0[int(np.floor(R/2)+it0),:]
                if np.sum(np.isnan(raster)) < C-1:
                    noData = False
                else:
                    it0 += 1
                    del(raster)
            raster0 = raster
                
            V[img][str(b)] = variograma1D(raster0)
            if V[img][str(b)]['N'] == 0:
                print('ZERO: ' + img + '[' + str(img0) + ']' + str(b) + 'it' + str(it0))

        elif varioDim == '2D':
            V[img][str(b)] = variograma2D(raster0)
        else:
            pass

        fig = plt.figure(img + '; ' + str(b), figsize=(30.0, 25.0))
        plt.subplot(2,1,1)
        
        ptm = np.percentile(raster0.ravel(), 5)
        ptM = np.percentile(raster0.ravel(), 95)
        
        plt.imshow(raster0.T,vmin=ptm,vmax=ptM)


        lat_locs = np.linspace(0,R,5)
        lat_lbls = np.round(100*np.linspace(roi['W'],roi['E'],5))/100
        plt.xticks(lat_locs, lat_lbls,rotation=30)

        lon_locs = np.linspace(0,C,5)
        lon_lbls = np.round(100*np.linspace(roi['N'],roi['S'],5))/100
        plt.yticks(lon_locs, lon_lbls)

        plt.xlabel('Longitud')
        plt.ylabel('Latitud')

        cbar = plt.colorbar()
        cbar.ax.set_ylabel(r'$\rho_{RC}$' + '(' + str(b) + ')', rotation=270,fontsize=30, labelpad=40)
        
        plt.title('IMG: ' + img)
        
        ax = plt.subplot(2,1,2)
        plt.plot(             V[img][str(b)]['vario' ],'.-b',label=r'$\gamma(h)$' + \
                 '\n' + r'$\sigma$: ' + str('%0.5f' % np.sqrt(V[img][str(b)]['nugget'][0])))
        plt.ylabel('Variograma' + r'$\gamma(h)$')
        plt.legend()
        plt.xlabel('Desfasaje, h [px]')
        
        ax2 = ax.twinx()
        ax2.plot(V[img][str(b)]['Nh' ],'.-g',label='N(h)')
#        ax2.set_yscale('log')
        plt.xlabel('Desfasaje, h [px]')
        plt.ylabel('Número de pares, N(h)')
        plt.legend()


        fig.savefig('/home/gossn/Dropbox/Documents/Lineas/PCA/figures/VARIO_' + str(b) + '_' + img + '.png')
        
        plt.close()
        
np.save('/home/gossn/Dropbox/Documents/Lineas/PCA/VariogramasMODIS_' + varioDim + '.npy', V)

#%%
plt.close('all')
V = np.load('/home/gossn/Dropbox/Documents/Lineas/PCA/VariogramasMODIS_' + varioDim + '.npy', allow_pickle=True).item()

pathL2Img = '/home/gossn/Dropbox/Documents/inSitu/Database/matchUpImages/MA/RdP/matchUps/L2'
    
bandList = [int(b) for b in list(V[imgList[0]].keys())]

nugget = np.zeros((len(imgList),len(bandList)))
nh     = np.zeros((len(imgList),len(bandList)))
mu     = np.zeros((len(imgList),len(bandList)))
img0 = -1

for img in imgList:
    b0 = -1
    img0 += 1
#    rhos = Dataset(pathL2Img + '/' + img + '/' + img + '.L2_RC','r')
    for b in bandList:
        b0 += 1
        nugget[img0,b0] = V[img][str(b)]['nugget']
        mu[    img0,b0] = V[img][str(b)]['mu'    ]
        nh[    img0,b0] = V[img][str(b)]['Nh' ][1]

#nuggetAvg = np.sqrt(np.sum(np.divide(nugget*nh,np.sum(nh,axis=0)),axis=0))
#muAvg     = np.sum(np.divide(mu*nh    ,np.sum(nh,axis=0)),axis=0)
nuggetAvg = np.sqrt(np.nanmin(nugget,axis=0))
#muAvg     = np.sum(np.divide(mu*nh    ,np.sum(nh,axis=0)),axis=0)



plt.plot(bandList, nuggetAvg,'.-b')
plt.xlabel('Longitud de onda [nm]')
plt.ylabel('Error absoluto estimado, ' + r'$\sigma$')
#plt.yscale('log')
#plt.plot(bandList, muAvg    ,'.-g')
#plt.plot(bandList, muAvg/nuggetAvg    ,'.-k')

#%% CORRER 1 SOLA VEZ: Correccion: originalmente no dividi el vario por 2... 

#import numpy as np
#V = np.load('/home/gossn/Dropbox/Documents/Lineas/PCA/VariogramasMODIS.npy', allow_pickle=True).item()
#imgList = list(V.keys())
#bandList = [int(b) for b in list(V[imgList[0]].keys())]
#
#for img in imgList:
#    for b in bandList:
#        V[img][str(b)]['vario' ] = 0.5*V[img][str(b)]['vario' ]
#        V[img][str(b)]['nugget'] = 0.5*V[img][str(b)]['nugget']
#
#np.save('/home/gossn/Dropbox/Documents/Lineas/PCA/VariogramasMODIS.npy', V)

#%%

plt.close('all')

V = np.load('/home/gossn/Dropbox/Documents/Lineas/PCA/VariogramasMODIS_1D.npy', allow_pickle=True).item()

pathL2Img = '/home/gossn/Dropbox/Documents/inSitu/Database/matchUpImages/MA/RdP/matchUps/L2'
    
imgList = list(V.keys())
bandList = [int(b) for b in list(V[imgList[0]].keys())]

for img in imgList:
    rhos = Dataset(pathL2Img + '/' + img + '/' + img + '.L2_RC','r')
    for b in [869]:
        vario = V[img][str(b)]['vario']
        nh    = V[img][str(b)]['Nh']
        raster = rhos['geophysical_data']['rhos_' + str(b)][:,:]

        plt.figure()
        plt.subplot(1,2,1)
        plt.imshow(raster,vmin=0,vmax=0.01)
        plt.title(str(b))

        plt.subplot(1,2,2)
        plt.plot(vario,'b')
        plt.plot(nh/100000,'g')
        plt.ylim(0,0.005)
        plt.title(str(V[img][str(b)]['nugget'][0]))
    
    plt.plot(vario,'b')

#%%