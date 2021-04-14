## EoBiasStabilityData
#### Current Schema
##### DataClass: EoBiasStabilityData
##### SchemaClass: EoBiasStabilityDataSchemaV0
| Name | Class | Version | Length |
|-|-|-|-|
| ampExposure | EoBiasStabilityAmpExpData | 0 | nExposure |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|
| mean | MEAN | float | [1] | adu |  | 
| stdev | STDEV | float | [1] | adu |  | 


|-|-|-|-|-|-|
| Name | Class | Version | Length |
|-|-|-|-|
| detExposure | EoBiasStabilityDetExpData | 0 | nExposure |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|
| seqnum | SEQNUM | int | [1] |  |  | 
| mjd | MJD | float | [1] |  |  | 
| temp | TEMP | float | ['nTemp'] |  |  | 


|-|-|-|-|-|-|


## EoBrighterFatterData
#### Current Schema
##### DataClass: EoBrighterFatterData
##### SchemaClass: EoBrighterFatterDataSchemaV0
| Name | Class | Version | Length |
|-|-|-|-|
| ampExposure | EoBrighterFatterAmpExpData | 0 | nExposure |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|
| mean | MEAN | float | [1] | electron |  | 
| covarience | COV | float | ['nCov', 'nCov'] | electron**2 |  | 
| covarienceError | COV_ERROR | float | ['nCov', 'nCov'] | electron**2 |  | 


|-|-|-|-|-|-|
| Name | Class | Version | Length |
|-|-|-|-|
| amps | EoBrighterFatterAmpRunData | 0 | nAmp |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|
| bfMean | BF_MEAN | float | [1] |  |  | 
| bfXCorr | BF_XCORR | float | [1] |  |  | 
| bfXCorrErr | BF_XCORR_ERR | float | [1] |  |  | 
| bfXSlope | BF_SLOPEX | float | [1] |  |  | 
| bfXSlopeErr | BF_SLOPEX_ERR | float | [1] |  |  | 
| bfYCorr | BF_YCORR | float | [1] |  |  | 
| bfYCorrErr | BF_YCORR_ERR | float | [1] |  |  | 
| bfYSlope | BF_SLOPEY | float | [1] |  |  | 
| bfYSlopeErr | BF_SLOPEY_ERR | float | [1] |  |  | 


|-|-|-|-|-|-|


## EOCtiData
#### Current Schema
##### DataClass: EOCtiData
##### SchemaClass: EOCtiDataSchemaV0
| Name | Class | Version | Length |
|-|-|-|-|
| amps | EoCtiAmpRunData | 0 | nAmp |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|
| ctiSerial | CTI_SERIAL | float | [1] |  |  | 
| ctiSerialError | CTI_SERIAL_ERR | float | [1] |  |  | 
| ctiParallel | CTI_PARALLEL | float | [1] |  |  | 
| ctiParallelError | CTI_PARALLEL_ERR | float | [1] |  |  | 


|-|-|-|-|-|-|


## EoDarkCurrentData
#### Current Schema
##### DataClass: EoDarkCurrentData
##### SchemaClass: EoDarkCurrentDataSchemaV0
| Name | Class | Version | Length |
|-|-|-|-|
| amps | EoDarkCurrentAmpRunData | 0 | nAmp |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|
| darkCurrent95 | DARK_CURRENT_95 | float | [1] | electron/s |  | 
| darkCurrentMedian | DARK_CURRENT_MEDIAN | float | [1] | electron/s |  | 


|-|-|-|-|-|-|


## EoDefectData
#### Current Schema
##### DataClass: EoDefectData
##### SchemaClass: EoDefectDataSchemaV0
| Name | Class | Version | Length |
|-|-|-|-|
| amps | EoDefectAmpRunData | 0 | nAmp |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|
| nBrightPixel | NUM_BRIGHT_PIXELS | int | [1] |  |  | 
| nBrightColumn | NUM_BRIGHT_COLUMNS | int | [1] |  |  | 
| nDarkPixel | NUM_DARK_PIXELS | int | [1] |  |  | 
| nDarkColumn | NUM_DARK_COLUMNS | int | [1] |  |  | 
| nTraps | NUM_TRAPS | int | [1] |  |  | 


|-|-|-|-|-|-|


## EoFe55Data
#### Current Schema
##### DataClass: EoFe55Data
##### SchemaClass: EoFe55DataSchemaV0
| Name | Class | Version | Length |
|-|-|-|-|
| ampHits | EoFe55AmpHitData | 0 | nHit |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|
| xPos | XPOS | float | [1] | pixel |  | 
| yPos | YPOS | float | [1] | pixel |  | 
| sigmaX | SIGMAX | float | [1] | pixel |  | 
| sigmaY | SIGMAY | float | [1] | pixel |  | 
| dn | DN | float | [1] | adu |  | 
| dnFpSum | DN_FP_SUM | float | [1] | adu |  | 
| chiProb | CHIPROB | float | [1] |  |  | 
| chi2 | CHI2 | float | [1] |  |  | 
| dof | DOF | float | [1] |  |  | 
| maxDn | MAXDN | float | [1] | adu |  | 
| xPeak | XPEAK | int | [1] | pixel |  | 
| yPeak | YPEAK | int | [1] | pixel |  | 
| p9Data | P9_DATA | float | [3, 3] | adu |  | 
| p9Model | P9_MODEL | float | [3, 3] | adu |  | 
| pRectData | PRECT_DATA | float | [7, 7] | adu |  | 


|-|-|-|-|-|-|
| Name | Class | Version | Length |
|-|-|-|-|
| amps | EoFe55AmpRunData | 0 | nAmp |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|
| gain | GAIN | float | [1] |  |  | 
| gainError | GAIN_ERROR | float | [1] |  |  | 
| psfSigma | PSF_SIGMA | float | [1] | pixel |  | 


|-|-|-|-|-|-|


## EoFlatPairData
#### Current Schema
##### DataClass: EoFlatPairData
##### SchemaClass: EoFlatPairDataSchemaV0
| Name | Class | Version | Length |
|-|-|-|-|
| ampExposure | EoFlatPairAmpExpData | 0 | nPair |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|
| signal | SIGNAL | float | [1] | electron |  | 
| flat1Signal | FLAT1_SIGNAL | float | [1] | electron |  | 
| flat2Signal | FLAT2_SIGNAL | float | [1] | electron |  | 
| rowMeanVar | ROW_MEAN_VAR | float | [1] | electron**2 |  | 


|-|-|-|-|-|-|
| Name | Class | Version | Length |
|-|-|-|-|
| amps | EoFlatPairAmpRunData | 0 | nAmp |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|
| fullWell | FULL_WELL | float | [1] | adu |  | 
| maxFracDev | MAX_FRAC_DEV | float | [1] |  |  | 
| rowMeanVarSlope | ROW_MEAN_VAR_SLOPE | float | [1] |  |  | 
| maxObservedSignal | MAX_OBSERVED_SIGNAL | float | [1] | adu |  | 
| linearityTurnoff | LINEARITY_TURNOFF | float | [1] | adu |  | 


|-|-|-|-|-|-|
| Name | Class | Version | Length |
|-|-|-|-|
| detExposure | EoFlatPairDetExpData | 0 | nPair |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|
| flux | FLUX | float | [1] |  |  | 
| seqnum | SEQNUM | int | [1] |  |  | 
| dayobs | DAYOBS | int | [1] |  |  | 


|-|-|-|-|-|-|


## EoGainStabilityData
#### Current Schema
##### DataClass: EoGainStabilityData
##### SchemaClass: EoGainStabilityDataSchemaV0
| Name | Class | Version | Length |
|-|-|-|-|
| ampExposure | EoGainStabilityAmpExpData | 0 | nExposure |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|
| signal | SIGNAL | float | [1] | electron |  | 


|-|-|-|-|-|-|
| Name | Class | Version | Length |
|-|-|-|-|
| detExposure | EoGainStabilityDetExpData | 0 | nExposure |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|
| mjd | MJD | float | [1] | electron |  | 
| seqnum | SEQNUM | int | [1] |  |  | 
| flux | FLUX | float | [1] |  |  | 


|-|-|-|-|-|-|


## EoOverscanData
#### Current Schema
##### DataClass: EoOverscanData
##### SchemaClass: EoOverscanDataSchemaV0
| Name | Class | Version | Length |
|-|-|-|-|
| ampExposure | EoOverscanAmpExpData | 0 | nExposure |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|
| columnMean | COLUMN_MEAN | float | ['nCol'] | electron |  | 
| columnVariance | COLUMN_VARIANCE | float | ['nCol'] | electron |  | 
| rowMean | ROW_MEAN | float | ['nRow'] | electron |  | 
| rowVariance | ROW_VARIANCE | float | ['nRow'] | electron |  | 
| flatFeildSignal | FLATFIELD_SIGNAL | float | [1] | electron |  | 
| serialOverscanNoise | SERIAL_OVERSCAN_NOISE | float | [1] | electron |  | 
| parallenOverscanNoise | PARALLEL_OVERSCAN_NOISE | float | [1] | electron |  | 


|-|-|-|-|-|-|


## EoPersistenceData
#### Current Schema
##### DataClass: EoPersistenceData
##### SchemaClass: EoPersistenceDataSchemaV0
| Name | Class | Version | Length |
|-|-|-|-|
| ampExposure | EoPersistenceAmpExpData | 0 | nExposure |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|
| mean | MEAN | float | [1] | adu |  | 
| stdev | STDEV | float | [1] | adu |  | 


|-|-|-|-|-|-|


## EoPtcData
#### Current Schema
##### DataClass: EoPtcData
##### SchemaClass: EoPtcDataSchemaV0
| Name | Class | Version | Length |
|-|-|-|-|
| ampExposure | EoPtcAmpExpData | 0 | nExposure |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|
| mean | MEAN | float | [1] | adu |  | 
| var | VAR | float | [1] | adu**2 |  | 
| discard | DISCARD | int | [1] | pixel |  | 


|-|-|-|-|-|-|
| Name | Class | Version | Length |
|-|-|-|-|
| amps | EoPtcAmpRunData | 0 | nAmp |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|
| ptcGain | PTC_GAIN | float | [1] | adu/electron |  | 
| ptcGainError | PTC_GAIN_ERROR | float | [1] | adu/electron |  | 
| ptcA00 | PTC_A00 | float | [1] |  |  | 
| ptcA00Error | PTC_A00_ERROR | float | [1] |  |  | 
| ptcNoise | PTC_NOISE | float | [1] | adu |  | 
| ptcNoiseError | PTC_NOISE_ERROR | float | [1] | adu |  | 
| ptcTurnoff | PTC_TURNOFF | float | [1] | adu |  | 


|-|-|-|-|-|-|
| Name | Class | Version | Length |
|-|-|-|-|
| detExposure | EoPtcDetExpData | 0 | nExposure |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|
| exposure | EXPOSURE | float | [1] |  |  | 
| seqnum | SEQNUM | int | [1] |  |  | 
| dayobs | DAYOBS | int | [1] |  |  | 


|-|-|-|-|-|-|


## EoReadNoiseData
#### Current Schema
##### DataClass: EoReadNoiseData
##### SchemaClass: EoReadNoiseDataSchemaV0
| Name | Class | Version | Length |
|-|-|-|-|
| ampExposure | EoReadNoiseAmpExpData | 0 | nExposure |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|
| totalNoise | TOTAL_NOISE | float | ['nSample'] | electron |  | 


|-|-|-|-|-|-|
| Name | Class | Version | Length |
|-|-|-|-|
| amps | EoReadNoiseAmpRunData | 0 | nAmp |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|
| readNoise | READ_NOISE | float | [1] | electron |  | 
| totalNoise | TOTAL_NOISE | float | [1] | electron |  | 
| systemNoise | SYSTEM_NOISE | float | [1] | electron |  | 


|-|-|-|-|-|-|


## EOSummaryData
#### Current Schema
##### DataClass: EOSummaryData
##### SchemaClass: EOSummaryDataSchemaV0
| Name | Class | Version | Length |
|-|-|-|-|
| amps | EoSummaryAmpTable | 0 | nAmp |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|
| amp | AMP | int | [1] |  |  | 
| detector | DETECTOR | int | [1] |  |  | 
| dc95ShotNoise | DC95_SHOT_NOISE | float | [1] |  |  | 
| readNoise | READ_NOISE | float | [1] | electron |  | 
| totalNoise | TOTAL_NOISE | float | [1] | electron |  | 
| systemNoise | SYSTEM_NOISE | float | [1] | electron |  | 
| darkCurrent95 | DARK_CURRENT_95 | float | [1] | electron/s |  | 
| darkCurrentMedian | DARK_CURRENT_MEDIAN | float | [1] | electron/s |  | 
| ctiLowSerial | CTI_SERIAL_LOW | float | [1] |  |  | 
| ctiLowSerialError | CTI_SERIAL_ERR_LOW | float | [1] |  |  | 
| ctiLowParallel | CTI_PARALLEL_LOW | float | [1] |  |  | 
| ctiLowParallelError | CTI_PARALLEL_ERR_LOW | float | [1] |  |  | 
| ctiHighSerial | CTI_SERIAL_HIGH | float | [1] |  |  | 
| ctiHighSerialError | CTI_SERIAL_ERR_HIGH | float | [1] |  |  | 
| ctiHighParallel | CTI_PARALLEL_HIGH | float | [1] |  |  | 
| ctiHighParallelError | CTI_PARALLEL_ERR_HIGH | float | [1] |  |  | 
| ptcGain | PTC_GAIN | float | [1] | adu/electron |  | 
| ptcGainError | PTC_GAIN_ERROR | float | [1] | adu/electron |  | 
| ptcA00 | PTC_A00 | float | [1] |  |  | 
| ptcA00Error | PTC_A00_ERROR | float | [1] |  |  | 
| ptcNoise | PTC_NOISE | float | [1] | adu |  | 
| ptcNoiseError | PTC_NOISE_ERROR | float | [1] | adu |  | 
| ptcTurnoff | PTC_TURNOFF | float | [1] | adu |  | 
| bfMean | BF_MEAN | float | [1] |  |  | 
| bfXCorr | BF_XCORR | float | [1] |  |  | 
| bfXCorrErr | BF_XCORR_ERR | float | [1] |  |  | 
| bfXSlope | BF_SLOPEX | float | [1] |  |  | 
| bfXSlopeErr | BF_SLOPEX_ERR | float | [1] |  |  | 
| bfYCorr | BF_YCORR | float | [1] |  |  | 
| bfYCorrErr | BF_YCORR_ERR | float | [1] |  |  | 
| bfYSlope | BF_SLOPEY | float | [1] |  |  | 
| bfYSlopeErr | BF_SLOPEY_ERR | float | [1] |  |  | 
| fullWell | FULL_WELL | float | [1] | adu |  | 
| maxFracDev | MAX_FRAC_DEV | float | [1] |  |  | 
| rowMeanVarSlope | ROW_MEAN_VAR_SLOPE | float | [1] |  |  | 
| maxObservedSignal | MAX_OBSERVED_SIGNAL | float | [1] | adu |  | 
| linearityTurnoff | LINEARITY_TURNOFF | float | [1] | adu |  | 
| gain | GAIN | float | [1] |  |  | 
| gainError | GAIN_ERROR | float | [1] |  |  | 
| psfSigma | PSF_SIGMA | float | [1] | pixel |  | 
| nBrightPixel | NUM_BRIGHT_PIXELS | int | [1] |  |  | 
| nBrightColumn | NUM_BRIGHT_COLUMNS | int | [1] |  |  | 
| nDarkPixel | NUM_DARK_PIXELS | int | [1] |  |  | 
| nDarkColumn | NUM_DARK_COLUMNS | int | [1] |  |  | 
| nTraps | NUM_TRAPS | int | [1] |  |  | 


|-|-|-|-|-|-|
| Name | Class | Version | Length |
|-|-|-|-|
| dets | EoSummaryDetTable | 0 | nDet |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|


|-|-|-|-|-|-|


## EoTearingData
#### Current Schema
##### DataClass: EoTearingData
##### SchemaClass: EoTearingDataSchemaV0
| Name | Class | Version | Length |
|-|-|-|-|
| amps | EoTearingAmpRunData | 0 | nAmp |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|
| nDetection | NDETECT | int | [1] |  |  | 


|-|-|-|-|-|-|


## EoTestData
#### Current Schema
##### DataClass: EoTestData
##### SchemaClass: EoTestDataSchemaV1
| Name | Class | Version | Length |
|-|-|-|-|
| ampExposure | EoTestAmpExpData | 1 | nExposure |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|
| varExp2 | VAR2 | float | ['nSample'] |  |  | 
| varExp1 | VAR1 | float | [1] | s | A variables | 


|-|-|-|-|-|-|
| Name | Class | Version | Length |
|-|-|-|-|
| amps | EoTestAmpRunData | 0 | nAmp |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|
| varAmp1 | VARAMP1 | float | [1] |  |  | 


|-|-|-|-|-|-|
#### Previous Schema
##### SchemaClass: EoTestDataSchemaV0
| Name | Class | Version | Length |
|-|-|-|-|
| amps | EoTestAmpRunData | 0 | nAmp |


| Name | Column | Datatype | Shape | Units | Description |
|-|-|-|-|-|-|
| varAmp1 | VARAMP1 | float | [1] |  |  | 


|-|-|-|-|-|-|


