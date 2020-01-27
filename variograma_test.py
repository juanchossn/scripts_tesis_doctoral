#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec 16 10:32:45 2019

@author: gossn
"""
#%%
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import TheilSenRegressor

from matplotlib import rc
font = {'family' : 'DejaVu Sans','weight' : 'bold','size'   : 16}
plt.rc('font', **font)

#%% Exploro la posibilidad de hacer un variograma a mano, dado que los que 
# vienen por default en Python son dificiles de entender

# Uso métrica Manhattan, asuminedo que el desarrollo teórico del paper de 
# Curran & Dungan 1989 no asume una métrica de lags necesariamente euclídea...
# Se asume que sqrt(Nugget) = std(noise) (Eq. 12)

#rc('text', usetex=True)

plt.close('all')

Noise = 8

nugget     = np.zeros((Noise,1))
sigmaNoise = np.zeros((Noise,1))

for n in range(Noise):
    noise = n*np.random.randn(50,50)

    sigmaNoise[n] = np.std(noise.flatten())
    
    A = noise.copy()


    R,C = np.shape(A)
    
    for r in range(R):
        for c in range(C):
            A[r,c] = A[r,c] + 9*np.exp(-(((r-R/2)**2+(c-C/2)**2)/100))
#            if c > C/2:
#                A[r,c] = A[r,c] + 3
    
    B = np.empty((3*R-2,3*C-2))
    B[:] = np.nan
    
    B[(R-1):(2*R-1),(C-1):(2*C-1)] = A
    
    gamma = np.zeros(((R-1)+(C-1)+1,1))
    Nh    = np.zeros(((R-1)+(C-1)+1,1))
    
    for r in range(2*R-1):
        for c in range(2*C-1):
    
            W = B[r:(r+R),c:(c+C)]
    
            h = np.abs(r-(R-1)) + np.abs(c-(C-1))
            N = np.sum(~ np.isnan(W))
    
            WA = np.nansum((W-A)**2)
                    
            gamma[h] = gamma[h] + WA
            Nh[h]    = Nh[h]    + N    
    
    vario = np.divide(gamma,2*Nh)
    
    #        print('R' + str(r) + 'C' + str(c) + 'H' + str(h) + 'N' + str(N))
    #        print(W)
    
    nuggetFitLags     = range(1,3)
    nuggetFitLagsPlot = np.linspace(0,5,100) 
    lin = np.polyfit(nuggetFitLags,np.log(vario[nuggetFitLags]),1)
    
    nugget[n] = np.exp(lin[1])
    
    plt.subplot(np.ceil(Noise/2),2,n+1)
    plt.imshow(A, vmin = -3, vmax = 9)
    plt.title(r'$A \rightarrow A + N[\mu=0, \sigma = ' + str(n) + ']$')
    plt.xticks([])
    plt.yticks([])
    plt.colorbar()
#    plt.plot(vario,'.-k')
#    plt.plot(nuggetFitLagsPlot,np.exp(lin[0]*nuggetFitLagsPlot + lin[1]))
#    plt.yscale('log')



fig = plt.figure()

plt.subplot(1,2,1)
plt.plot(range(Noise),sigmaNoise,'.-r',label=r'Estimated from noise matrix, $\sigma[N_{n}]$')
plt.plot(range(Noise),np.sqrt(nugget),'.-g',label=r'Estimated from variogram, $\sqrt{C_{0}}$')
plt.xlabel(r'Noise amplitude set to random generator')
plt.ylabel(r'Estimated noise amplitude')
plt.legend()


x = sigmaNoise
y = np.sqrt(nugget).ravel()

regyx = TheilSenRegressor(fit_intercept=True, random_state=0).fit(x,y)
Slope_YvsX     = regyx.coef_[0]
Intercept_YvsX = regyx.intercept_
R2 = np.abs(regyx.score(x, y))

plt.subplot(1,2,2)
plt.plot(sigmaNoise,np.sqrt(nugget),'.-b',label='Y = ' + '%.2f' % Slope_YvsX + 'X ' + '%+.2f' % Intercept_YvsX + '\n' + r'$R^{2}$ = ' + '%.3f' % R2)
lims = [np.min([sigmaNoise, np.sqrt(nugget)]),np.max([sigmaNoise, np.sqrt(nugget)])]
plt.plot(lims, lims, '--k', alpha=0.9, linewidth=1,label='1:1')
#plt.aspect('equal')
plt.xlim(lims)
plt.ylim(lims)
plt.xlabel(r'Estimated from noise matrix, $\sigma[A_{n}]$')
plt.ylabel(r'Estimated from variogram, $\sqrt{C_{0}}$')
plt.legend()
#%%
def variogramaJG(A):
    R,C = np.shape(A)

    B = np.empty((3*R-2,3*C-2))
    B[:] = np.nan
    
    B[(R-1):(2*R-1),(C-1):(2*C-1)] = A
    
    gamma = np.zeros(((R-1)+(C-1)+1,1))
    Nh    = np.zeros(((R-1)+(C-1)+1,1))
    
    for r in range(2*R-1):
        for c in range(2*C-1):
    
            W = B[r:(r+R),c:(c+C)]
    
            h = np.abs(r-(R-1)) + np.abs(c-(C-1))
            N = np.sum(~ np.isnan(W))
    
            WA = np.nansum((W-A)**2)
                    
            gamma[h] = gamma[h] + WA
            Nh[h]    = Nh[h]    + N    
    
    vario = np.divide(gamma,2*Nh)
    
    #        print('R' + str(r) + 'C' + str(c) + 'H' + str(h) + 'N' + str(N))
    #        print(W)
    
    nuggetFitLags     = range(1,3)
    nuggetFitLagsPlot = np.linspace(0,5,100) 
    lin = np.polyfit(nuggetFitLags,np.log(vario[nuggetFitLags]),1)
    
    nugget = np.exp(lin[1])
    
    out = {}

    out['nugget'] = nugget
    out['vario' ] = vario
    out['Nh'    ] = Nh

    return out
#%%

noise = 3*np.random.rand(50,50)

A = noise.copy()


R,C = np.shape(A)

for r in range(R):
    for c in range(C):
        A[r,c] = A[r,c] + 10*(r*c/(R*C) + 3*np.exp(-(((r-R/2)**2+(c-C/2)**2)/20)))

V = variogramaJG(A)