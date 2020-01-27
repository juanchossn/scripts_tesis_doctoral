#%% Read LTOAs
olciWave = np.loadtxt(path0 + '/olciBandsLambdaMedian')
Nbands = len(olciWave)
ltoa = np.zeros((Nbands,R,C))

for b in range(0,Nbands):
	numBand = '%02d' % (b+1)
	ltoaNc4b = Dataset(img + '/Oa' + numBand + '_radiance.nc','r')
	ltoa[b,:,:] = ltoaNc4b.variables['Oa' + numBand + '_radiance'][rmin:(rmax+1),cmin:(cmax+1)]


#%% PPE correction

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