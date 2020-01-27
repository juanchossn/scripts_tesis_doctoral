#!/usr/bin/env python
# coding: utf-8

# # Welcome to the TSM worflow exercise!
# 
# ### Part II: Apply BLR (Baseline Residual) atmospheric correction to OLCI images
# 
# This .ipynb file corresponds to Part II, where you will:
# 
# Learn the different steps and how to apply a simple atmospheric correction specifically designed for OLCI at sediment-dominated turbid waters (Río de la Plata and Estuario do Tejo) based on Base Line Residuals (BLR).
# 
# More detailed description of the BLR atmospheric correction can be found in:
# 
# 
# *Gossn, J.I., K.G. Ruddick and A.I. Dogliotti (2019) Atmospheric Correction of OLCI Imagery over Extremely Turbid Waters Based on the Red, NIR and 1016 nm Bands and a New Baseline Residual Technique, Remote Sensing, 2072-4292, vol. 11-3, 220, doi:10.3390/rs11030220, http://www.mdpi.com/2072-4292/11/3/220*
# 
# The water reflectance images you will obtain by applying this algorithm will be used to compute satellite-derived TSM values at Part III, which will be compared with other TSM satellite products as well as with *in situ* TSM values.
# 
# 
# 
# #### WARNING: To execute this script you should have executed part I at both regions TAGUS and RDP.

# ## What is an *atmospheric correction*??
# In optical imagery, either from land or water targets, the atmosphere that stands between the target of interest and the satellite has a non negligible contribution on the radiance budget that arrives at the sensor. To remove this contribution, it is necessary to design an *atmospheric correction* algorithm. 
# 
# The latter was a very brief explanation to refresh what you saw at the lectures. You can internalize more on the topic by reading:
# 
# #### To start:
# 
# *GSP216, Introduction to Remote Sensing: Radiometric Corrections. Humboldt State University. Humboldt Geospatial Online http://gsp.humboldt.edu/olm_2015/Courses/GSP_216_Online/lesson4-1/radiometric.html*
# 
# #### Advanced (mainly Ocean Color):
# 
# *Mobley, C.; Werdell, J.; Franz, B.; Ahmad, Z.; Bailey, S. Atmospheric Correction for Satellite Ocean Color Radiometry; Technical report; NASA Goddard Space Flight Center: Greenbelt, MD, USA, 2016.*

# ### BLR scheme: Refreshing what you saw at the lectures
# Just to refresh what will be seen at the lectures, the BLR-AC is based on spectral magnitudes called here "baseline residuals", which are quasi-invariant under atmospheric conditions. These are defined by means of triplets of bands as Fig. 1 shows [Figure 2 @ Gossn *et al.* 2019]:

# <img src="blrExamples.png" style="width:900px;height:450px;">
# 
# <caption><center> <u>Figure 1 [Fig. 2 G19]</u>:
# (a) RGB Composite of OLCI-A image on the Río de la Plata, OLCI-A 2017-10-31T12:47:23Z, using Rayleigh-corrected (RC) reflectances at 620 nm (R) 560 nm (G) and 442 nm (B). (b) Rayleigh-corrected reflectances of the red, near-infrared, short-wave-infra-red (RNS) bands used for the baseline residual atmospheric correction (BLR-AC) approach at the sites A, B and C, together with the BLR values (vertical black solid lines). Notice that BLR values approach to 0 at site C (i.e. quasi-linear RC reflectance), where water relfectance is close to 0 in the RNS. <br> </center></caption>.

# The BLR-AC requires a small amount of simple steps to be computed, which you'll be performing throughout this script. They are presented in this scheme:

# <img src="blrScheme.png" style="width:600px;height:400px;">
# 
# <caption><center> <u>Figure 2 [Fig. 7 G19]</u>: Different steps to perform "BLR" atmospheric correction. This algorithm is designed to estimate water reflectance just above the surface, $\rho_{w}$. <br> </center></caption>.

# We won't be computing the first step of this chain since it requires the use of another software like the SeaDAS software, or SNAP. It consists of a Rayleigh correction, i.e., the subtraction of the molecular scattering caused by air molecules in the atmosphere such as $O_{2}$ and $N_{2}$ (also described in Part I).
# 
# Let's get started with the rest of the steps... 

#%% Import modules:

from netCDF4 import Dataset
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from sklearn.neighbors import NearestNeighbors
import os
import sys


#pathImg = '/home/gossn/Dropbox/Documents/inSitu/Database/matchUpImages/OLCI'
pathImg = '/home/gossn/Dropbox/Documents/Cap1_Intro/RGB_OLCI'
#pathImg = '/home/usuario/Downloads'
pathL2gen = '/home/gossn/seadas/bin/l2gen'
path0 = '/home/gossn/Dropbox/Documents/Lineas/BLR/OLCIHomeMadeProcessor/blrPython'

pathModules = '/home/gossn/Dropbox/Documents/pyHomeMadeModules'
sys.path.append(pathModules)



import roiNcdf as rn # This last module is home-made for the purpose of this course. Its defined apart because the functions that are defined inside it are used in several ocassions at the three main scripts, TSM_01, 02 and 03. These functions are defined at roinNcdf.py

#%% Main fix inputs for processing (do not modify them) 
# Mode 'tCorr' means we will apply an "equivalent transmittance factor" to the computed BLRs.
mode = 'tCorr'

# These are the bands we currently use to perform the AC on OLCI (620, 709, 779, 865 and 1016 nm).
blrBands     = np.array([6,10,15,16,20])

# These are the parameters to perform the epsilon correction step:
blrCorrBands = {'ctor':20,'cted':16} # The "corrector" (1016nm) and "corrected" (865nm) bands 
epsRange     = np.array([0.85,1.25]) # rhoa(cted)/rhoa(ctor)

# The bands that will be corrected using this scheme.
rhowBands    = np.array([6,7,10,15,16,20])

# BLR calibration dataset
calDS     = pd.read_csv(path0 + '/blrAncillary/blrCalDS')

# List of mean OLCI wavelengths (in integer format):
olciWave = [int(wave) for wave in list(open(path0 + '/blrAncillary/olciBandsWave','r'))]
NOlci = len(olciWave)

# List of Rayleigh optical thicknesses to compute transmittances:
tauRay   = np.array([float(tau)  for tau  in list(open(path0 + '/blrAncillary/rayleigh_olci','r'))])



level   = 'L1'

#imgSets = {'RDP': ['RDP_set1']}
#imgSets = {'RDP': ['RDP_set1'], 'GIR': ['renosh_20190201']}
#imgSets = {'BBL': ['BBL_set1']}
#imgSets = {'RDP': ['portwims'], 'TAGUS': ['portwims']}
imgSets = {'RDP': ['RDP_20200112']}

#%% FUNCTIONS

#%% Functions: Determine nearest neighbor corresponding to BLR calibration grid
def nearest_neighbors(pixelBLRs, calBLRs, nbr_neighbors):
    '''
    This function will return which BLR triplet from the set "calBLRs" is the closest to each of the BLR triplets 
    in pixlBLRs.
    '''
    nn = NearestNeighbors(nbr_neighbors, metric='euclidean', algorithm='brute').fit(calBLRs)
    dists, idxs = nn.kneighbors(pixelBLRs)
    KNN = {'dists':dists,'idxs':idxs}
    return KNN

#%% Functions: Compute Rayleigh transmittance factor
def tRay(mu,tau,bb,band):
    '''
    Compute transmittance factor with the following model: T = exp(-bb.tau.mu), where
    mu  = air mass factor
    bb  = backscattering of the atmospheric species at band "band"
    tau = optical thickness of the atmospheric species at band "band"
    
    (For the moment, only corrects for one component, i.e. Rayleigh Scattering)
    '''
    if tau.ndim == 1 and np.size(bb) == 1:
        tRay = (np.exp(-mu)**(bb*tau[band]))
    else:
        pass # for the moment...
    return tRay
#%% Functions: Campaign List
def imageSets(imgSets,level,pathImg):
    '''Returns list of images that correspond to image sets specified at 
    IMGSETS of level specified at LEVEL (L1,L2...). IMGSETS is a dictionary 
    whose keys are the regions to process and whose values are the particular 
    sets at each region. If "all" is introduced as value, all the sets of the 
    region will be listed. PATHIMG indicated the path to the image database.'''
    imgList = {}
    for reg in imgSets.keys():
        pathRegion = pathImg + '/' + reg
        if imgSets[reg] == 'all':
            sets = os.listdir(pathRegion)
        else:
            sets = imgSets[reg]
            if type(sets) is str:
                sets = [sets]
                try:
                    sets.remove('logs')
                except:
                    pass
        for s in sets:
            # Create DER directory
            try:
                os.mkdir(pathImg + '/' + reg + '/' + s + '/DER')
            except:
                pass
            # Read ROI file
            with open(pathRegion + '/' + s + '/roi') as f:
                roi = dict(x.rstrip().split(None, 1) for x in f)
            for n in roi.keys():
                roi[n] = float(roi[n])
            # Store image data in dictionary imgList
            for img in os.listdir(pathRegion + '/' + s + '/' + level):
                if img.endswith(".SEN3"):
                    imgList[img] = {}
                    imgList[img]['path'   ] = pathRegion + '/' + s + '/' + level + '/' + img
                    imgList[img]['pathSet'] = pathRegion + '/' + s
                    imgList[img]['boxRoi' ] = roi
                    imgList[img]['reg'    ] = reg
                    imgList[img]['set'    ] = s
    return imgList
#%% Functions: ppeCorrection
def ppeCorrection(pathIn,pathOut,ppeBands,ROI):
    ''''''
#    pathIn = '/home/gossn/Dropbox/Documents/inSitu/Database/matchUpImages/OLCI/RdP/matchUps/L1/S3A_OL_1_EFR____20170126T125424_20170126T125624_20171011T142221_0119_013_323______MR1_R_NT_002.SEN3'
#    pathOut = '/home/gossn/Dropbox/Documents/inSitu/Database/matchUpImages/OLCI/RdP/matchUps/DER/S3A_OL_2_DER____20170126T125424_20170126T125624_20171011T142221_0119_013_323______MR1_R_NT_002.SEN3'
#    ppeBands = np.array([ 6, 10, 15, 16, 20])
#    ROI = { 'rm': 1746,
#            'rM': 2728,
#            'cm': 683,
#            'cM': 1804,
#            'R0': 2728,
#            'C0': 4865,
#            'R' : 982,
#            'C' : 1121}
    
    #ppeOut = ppeCorrection(imgs[img]['path'],blrBands,ROI)
    Nbands = len(ppeBands)
    
    # OUTPUTS = 
    # PPE flag (ppeFlag)
    # Corrected radiance @ TOA (ltoaCorr)
    
    R = ROI['R']
    C = ROI['C']
    
    # Read LTOAs
    ltoa = np.zeros((Nbands,R,C))

    b0 = 0
    for b in ppeBands:
        numBand = '%02d' % (b+1)
        ltoaNc4b = Dataset(pathIn + '/Oa' + numBand + '_radiance.nc','r')
        ltoa[b0,:,:] = ltoaNc4b.variables['Oa' + numBand + '_radiance'][ROI['rm']:ROI['rM'],ROI['cm']:ROI['cM']]
        ltoaNc4b.close() # para poder abrir el archivo con r+
        b0+=1
    # PPE correction
    
    XPpe = np.ravel(np.transpose(ltoa,(0,2,1)))
    YPpe = [np.roll(XPpe,-2),np.roll(XPpe,-1),np.roll(XPpe,1),np.roll(XPpe,2)]
    YMedianPpe = np.median(YPpe,axis=0)
    YMadPpe = np.median(np.absolute(YPpe-YMedianPpe),axis=0)
    ppeFlag = np.abs(XPpe-YMedianPpe) > np.maximum(10*YMadPpe,0.7)
    XPpeCorr = XPpe*~ppeFlag + YMedianPpe*ppeFlag
    ppeFlag = np.transpose(np.reshape(ppeFlag,(Nbands,C,R)),(0,2,1))
    ltoaCorr = np.transpose(np.reshape(XPpeCorr,(Nbands,C,R)),(0,2,1))
    ltoaCorr[:,[0,1,R-2,R-1],:] = ltoa[:,[0,1,R-2,R-1],:]
    ppeFlag[:,[0,1,R-2,R-1],:] = False
    
    varPpeCorr = {}

    b0 = 0
    for b in ppeBands:
        numBand = '%02d' % (b+1)
        #https://stackoverflow.com/questions/31865410/python-replacing-values-in-netcdf-file-using-netcdf4
        ltoaNc4bPpe = Dataset(pathIn + '/Oa' + numBand + '_radiance.nc','r+', format="NETCDF4")
        ltoaBand = ltoaNc4bPpe.variables['Oa' + numBand + '_radiance'][:,:]
        ltoaBand[ROI['rm']:ROI['rM'],ROI['cm']:ROI['cM']] = ltoaCorr[b0,:,:]

        ltoaNc4bPpe.variables['Oa' + numBand + '_radiance'][:,:] = ltoaBand
        ltoaNc4bPpe.close() # if you want to write the variable back to disk

        varPpeCorr['Oa' + numBand + '_radiance'] = {'val'  :ltoaCorr[b0,:,:]   ,\
                        'desc' :'PPE-corrected TOA radiance @ band ' + numBand ,\
                        'units':'mW.m-2.sr-1.nm-1'                              }

        varPpeCorr['ppeFlag' + numBand         ] = {'val'  : ppeFlag[b0,:,:]   ,\
                        'desc' :'PPE.corrected pixels (flag) @ band ' + numBand,\
                        'units':'boolean'                                       }
        b0+=1

    rn.img2NetCDF4('ppeCorr',pathOut,varPpeCorr ,'geo-coordinates, Solar-Viewing angles, BLRs')
    
#%% Main variable inputs for processing: 


#imgSets = {'CHN': ['20190403']}

## Load stored ROI (computed in Part I for both TAGUS and RDP)
#boxRoi = np.load(region + '/boxRoi.npy', allow_pickle=True).item()

imgs = imageSets(imgSets,level,pathImg)
#%% Create general DER directory for image set
for reg in imgSets.keys():
    for s in imgSets[reg]:
        try:
            os.mkdir(pathImg + '/' + reg + '/' + s + '/DER')
        except:
            pass
#%% IMG LOOP
imgNum = 0
for img in imgs.keys():
    imgNum+=1
    print(imgNum/len(imgs.keys())*100)
    reg    = imgs[img]['reg']
    s      = imgs[img]['set']
    imgDer = img.replace('1_EFR','2_DER')
    pathDer = pathImg + '/' + reg + '/' + s + '/DER/' + imgDer
    # Create directory of derived products from image
    imgs[img]['pathDer'] = pathDer
    if not os.path.isdir(pathDer):
        os.mkdir(pathDer)
    else:
        print('DER directory already exists for set: ' + s + '!')
    #% Extract subset of lat/lon/radiance values in track geometry (row-col) according to selected ROI
    
    geo  = Dataset(imgs[img]['path'] + '/geo_coordinates.nc','r') # Read netCDF file
    lat0 = geo.variables['latitude'] [:,:]
    lon0 = geo.variables['longitude'][:,:]
    
    ROI  = rn.selectROI(lat0,lon0,imgs[img]['boxRoi'])
    
    lat  = rn.sliceFromROI(lat0,ROI)
    lon  = rn.sliceFromROI(lon0,ROI)
    #% APPLY PPE
    if not os.path.isfile(pathDer + '/ppeCorr'):
        ppeCorrection(imgs[img]['path'],imgs[img]['pathDer'],blrBands,ROI)
    else:
        print('ppeCorr file already exists for ' + img + '!')
        #% APPLY L2GEN to obtain rhos_nn
    if not os.path.isfile(pathDer + '/rhos'):
        l2GenStr = pathL2gen + \
        ' ifile="' + imgs[img]['path'] + '/Oa01_radiance.nc" ' + \
        'ofile="' + imgs[img]['pathDer'] + '/' + 'rhos' + '" ' + \
        'l2prod=rhos_nnn aer_opt=-2 aer_wave_short=865 aer_wave_long=1012 brdf_opt=0 maskhilt=0 maskglint=0 cloud_wave=1012 cloud_thresh=0.1 ' + \
        'spixl=' + str(ROI['cm']+1) + ' ' + \
        'epixl=' + str(ROI['cM']  ) + ' ' + \
        'sline=' + str(ROI['rm']+1) + ' ' + \
        'eline=' + str(ROI['rM']  ) + ' '
        #print(l2GenStr)
        os.system(l2GenStr)
        #rhos620 = Dataset(imgs[img]['pathDer'] + '/' + 'rhos','r') # Read netCDF file
        #rhos620 = rhos620['geophysical_data']['rhos_620'][:,:]
        #plt.imshow(rhos620,vmin=0,vmax=0.05)
    else:
        print('rhos file already exists for ' + img + '!')
        #% Extract subset of lat/lon/radiance values in track geometry (row-col) according to selected ROI
    if not os.path.isfile(pathDer + '/geoBlr'):
        # This will be the "caché" (a Python dictionary) where all the main steps will be stored
        im = {'lat':lat,'lon':lon}
    
        rcSeadas = Dataset(imgs[img]['pathDer'] + '/rhos','r')
        rcVar = ['rhos_' + str(olciWave[o]) for o in range(len(olciWave)) if o in rhowBands] + ['l2_flags']
        for v in rcVar:
            print(v)
            v0 = v
            if v0 == 'rhos_1016':
                v0 = 'rhos_1012'
            matrixRoi = rcSeadas['geophysical_data'][v0][:,:]
            im[v] = matrixRoi
        print(imgNum/len(imgs.keys())*100)    
        #% Compute air mass factor $\mu$
        # https://sentinel.esa.int/web/sentinel/user-guides/sentinel-3-olci/coverage
        # Read the lat/lon matrices at the tie points:
        tieGeo=Dataset(imgs[img]['path'] + '/tie_geo_coordinates.nc','r')
        latTie = tieGeo.variables['latitude'][:,:]
        lonTie = tieGeo.variables['longitude'][:,:]
        
        # Read the SZA and OZA matrices at the tie points:
        sunSenTie = Dataset(imgs[img]['path'] + '/tie_geometries.nc','r')
        sunSenSor = ['sza','oza']
        
        # Perform the interpolation to fill in the gaps
        for geo in sunSenSor:
            geoTie = sunSenTie.variables[geo.upper()][:,:]
            sunSenInterp2 = griddata(np.transpose((latTie.ravel(),lonTie.ravel())),geoTie.ravel(),np.transpose((lat.ravel(),lon.ravel())),method='linear')
            # Store in our caché "im":
            im[geo] = np.reshape(sunSenInterp2,np.shape(im['lat']))
        
        # Compute air mass factor and store in caché
        im['mu'] = 1/np.cos(np.deg2rad(im['sza'])) + 1/np.cos(np.deg2rad(im['oza']))
    

        #% Compute BLRs and perform transmittance correction factor

        # 
        # As you have seen in the first cells of this file, the BLRs are computed from Rayleigh-corrected reflectances. The main hypothesis of this algorithm is that the dependence of BLRs with the atmosphere can be represented by a global transmittance factor that depends only on the air mass factor, $\mu$:
        # 
        # $BLR(\rho_{RC}) \approx t_{BLR}(\mu)BLR(\rho_{w})$
        # 
        # This factor was computed using radiative tranfer simulations and is can be approximated as:
        # 
        # $t_{BLR}(\mu) = slope(\mu-2) + offset$
        
        # <img src="blrTransmittance.png" style="width:800px;height:500px;">
        # 
        # <caption><center> <u>Figure 4 [Fig. 4 G19]</u>: Equivalent transmittance ($t_{BLR}$) and bias vs. air mass factor, $\mu=\frac{1}{cos(\theta_{S})}+\frac{1}{cos(\theta_{O})}$, for each of the BLRs used in this work. Turquoise (violet) dots represent subsets of simulations corresponding to different sun-view geometries with (without) direct sunglint. Dashed lines represent linear regressions.
        
        #% Compute BLRs
        
        blrNum   = len(blrBands)-2 # 3
        blrWave  = [olciWave[b] for b in blrBands] # wavelengths of the corresponding bands
        
        blrImg      = np.zeros((ROI['R'],ROI['C'],blrNum)) # Initialize BLR matrix
        blrTGainImg = np.zeros((ROI['R'],ROI['C'],blrNum)) # Initialize BLR matrix, corrected with transmittance factor
        
        ldL = np.zeros((blrNum,1)) # Wavlength ratios, defined below...
        ldM = np.zeros((blrNum,1))
        ldR = np.zeros((blrNum,1))
        
        for blr in range(blrNum):
            ldL[blr] = (blrWave[1 + blr]-blrWave[2 + blr])/(blrWave[2 + blr]-blrWave[0 + blr])
            ldM[blr] = 1
            ldR[blr] = (blrWave[1 + blr]-blrWave[0 + blr])/(blrWave[0 + blr]-blrWave[2 + blr])
        
            blrImg[:,:,blr] = ldL[blr]*im['rhos_' + str(blrWave[blr+0])] +                       ldM[blr]*im['rhos_' + str(blrWave[blr+1])] +                       ldR[blr]*im['rhos_' + str(blrWave[blr+2])]
        
        #% # BLR transmittances: slopes and offsets for the relation:
        # tBLR = slope*(mu-2) + offset
        blrTGainOffset = [ 0.9335, 0.9213, 0.9565]
        blrTGainSlope  = [-0.0480,-0.0510,-0.0300]
        
        for blr in range(blrNum):
            if mode == 'tCorr':
                G = blrTGainSlope[blr]*(im['mu'] - 2) + blrTGainOffset[blr]
            else:
                G = 1
            blrTGainImg[:,:,blr] =  blrImg[:,:,blr]/G
        
        im['blrTGainImg'] = blrTGainImg
        
        #% Write intermediate steps to netCDF ("geoBlr")
        # The function "img2NetCDF4" defined in the "rn" module is based on the steps that appear here:
        # 
        # http://www.ceda.ac.uk/static/media/uploads/ncas-reading-2015/11_create_netcdf_python.pdf
    
        # Build a dictionary with the names of the variables, their values, description and units.
    
        # Latitude and Longitude
        varNcGeoBlr = {}
        varNcGeoBlr['lat'        ] = {'val'  :im['lat']                 ,\
                                      'desc':'Latitude'                 ,\
                                      'units':'degree_north [WGS84+DEM]' }
    
        varNcGeoBlr['lon'        ] = {'val'  :im['lon']                 ,\
                                      'desc':'Longitude'                ,\
                                     'units':'degree_east  [WGS84+DEM]'  }
    
        varNcGeoBlr['blrTGainImg'] = {'val'  :im['blrTGainImg']         ,\
                                      'desc' :'BLRs (t-factor: applied)',\
                                      'units':'dimensionless'            }
    
        varNcGeoBlr['sza'        ] = {'val'  :im['sza']                 ,\
                                      'desc' :'Solar Zenith Angle (SZA)',\
                                      'units':'degrees'                  }
    
        varNcGeoBlr['oza'        ] = {'val'  :im['oza']                 ,\
                                      'desc' :'View  Zenith Angle (OZA)',\
                                      'units':'degrees'                  }
    
        varNcGeoBlr['mu'         ] = {'val'  :im['mu']                  ,\
                                      'desc' :'Viewing Zenith Angle'    ,\
                                      'units':'degrees'                  }
    
    
        rn.img2NetCDF4('geoBlr',imgs[img]['pathDer'],varNcGeoBlr ,'geo-coordinates, Solar-Viewing angles, BLRs')
    else:
        print('geoBlr file already exists for ' + img + '!')        
        #% Find closest match between BLR at each pixel to BLR calibration grid
    if not os.path.isfile(pathDer + '/rhoWBlr'):        
        # This might take a bit longer to compute than other cells
        
        # The computed BLRs at each pixel are compared with a BLR calibration grid in order to assign to them the corresponding water reflectances at the NIR/SWIR bands 865 nm and 1016 nm. To do this, a point from the calibration grid (in BLR space) is assigned in order to minimize the distance to the BLR triplet at the corresponding pixel.
        
        blrCal    = calDS.iloc[:,0:blrNum]
        blrImgLin = np.reshape(blrImg, [ROI['R']*ROI['C'],blrNum], order='F')
        
        blrNN = nearest_neighbors(blrImgLin, blrCal, nbr_neighbors=1)
        blrNN['idxs'] = [blr[0] for blr in blrNN['idxs']]
        
        
        for b in blrCorrBands.values():
            wave = str(olciWave[b])
            im['rhow_' + wave] = np.array(calDS['rhowDS[' + wave + ']'].iloc[blrNN['idxs']])
            im['rhow_' + wave] = np.reshape(im['rhow_' + wave], [ROI['R'],ROI['C']], order='F')
            im['rhoa_' + wave] = im['rhos_' + wave] - tRay(im['mu'],tauRay,0.51,b)*im['rhow_' + wave]
        
        
        #% Correct for anomalous $\epsilon_{a}(865,1016)$ (restrict to range "epsRange") to correct for anomalous values
        # NB: $\epsilon_{a}(865,1016) := \frac{\rho_{a}(865)}{\rho_{a}(1016)}$, where $\rho_{a}$ is the aerosol reflectance
        # 
        # This last correction is performed on $\rho_{a}(865)$ to restrain the derived $\epsilon_{a}(865,1016)$ inside the range of (0.85;1.25). These bounds were determined as the extreme values taken over a set of 82 different selected windows of size $15px \times 15px$ from OLCI-A scenes of clear water regions close to Río de la Plata, Bahía Blanca, North Sea, Yellow Sea, Amazonas and North Australia. Also these bounds are consistent with what was obtained over the CNES-SOS simulations. This correction is performed by imposing the following condition on a pixel-by-pixel basis:
        # 
        # $0.85\rho_{a}(1016)≤\rho_{a,new}(865)≤1.25\rho_{a}(1016)$
        
        # ... which in Python is expressed as:
        cted = blrCorrBands['cted']
        ctor = blrCorrBands['ctor']
        ctedWave = olciWave[cted]
        ctorWave = olciWave[ctor]
        rhoaCtedRange = np.array([im['rhoa_' + str(ctorWave)]*epsRange[b] for b in range(len(epsRange))]).transpose(1,2,0)
        rhoaCted      = np.min([np.max([im['rhoa_' + str(ctedWave)],rhoaCtedRange[:,:,0]],axis=0),rhoaCtedRange[:,:,1]],axis=0)
        im['rhoa_' + str(ctedWave)] = rhoaCted
        
        #% Perform simple linear extrapolation to specified bands
        for band in rhowBands:
            wave = olciWave[band]
            if band!=cted and band!=ctor:
                im['rhoa_' + str(wave)] = (im['rhoa_' + str(ctedWave)] - im['rhoa_' + str(ctorWave)])*(wave - ctorWave)/(ctedWave - ctorWave) + im['rhoa_' + str(ctorWave)]
            # store in caché
            im['rhow_' + str(wave)] = (im['rhos_' + str(wave)] - im['rhoa_' + str(wave)])/tRay(im['mu'],tauRay,0.51,band)
        
        #% Write BLR output to netCDF ("rhoWBlr")
        # The function "img2NetCDF4" defined in the "rn" module is based on the steps that appear here:
        # 
        # http://www.ceda.ac.uk/static/media/uploads/ncas-reading-2015/11_create_netcdf_python.pdf
    
        # Build a dictionary with the names of the variables, their values, description and units.
    
        # Latitude and Longitude
        varNcRhowBlr = {'lat': {'val':im['lat'],'desc':'Latitude' ,'units':'degree_north [WGS84+DEM]'},\
                        'lon': {'val':im['lon'],'desc':'Longitude','units':'degree_east  [WGS84+DEM]'}}
    
        # All the retrieved water/aerosol reflectances:
        mag = {'rhow_':'Water','rhoa_':'Aerosol'}
        for band in rhowBands:
            for m in mag.keys():
                varName = m + str(olciWave[band])
                varNcRhowBlr[varName] = {'val':im[varName],'desc': mag[m] + ' reflectance at ' + str(olciWave[band]) + ' (OLCI band ' + str(band+1) + ')','units':'dimensionless'}
    
        rn.img2NetCDF4('rhoWBlr',imgs[img]['pathDer'],varNcRhowBlr,'Water and aerosol reflectances retrieved by BLR-AC scheme')
    else:
        print('rhoWBlr file already exists for ' + img + '!')
    #%% END