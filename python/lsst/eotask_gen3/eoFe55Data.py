# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, RegisterEoCalibTableSchema
from .eoCalib import EoCalibTableHandle, EoCalibSchema, EoCalib, RegisterEoCalibSchema

__all__ = ["EoFe55AmpHitData",
           "EoFe55AmpRunData",
           "EoFe55Data"]


class EoFe55AmpHitDataSchemaV0(EoCalibTableSchema):

    VERSION = 0
    TABLELENGTH = "nHit"

    xPos = EoCalibField(name='XPOS', dtype=float, unit='pixel')
    yPos = EoCalibField(name='YPOS', dtype=float, unit='pixel')
    sigmaX = EoCalibField(name='SIGMAX', dtype=float, unit='pixel')
    sigmaY = EoCalibField(name='SIGMAY', dtype=float, unit='pixel')
    dn = EoCalibField(name='DN', dtype=float, unit='ADU')
    dnFpSum = EoCalibField(name='DN_FP_SUM', dtype=float, unit='ADU')
    chiProb = EoCalibField(name='CHIPROB', dtype=float)
    chi2 = EoCalibField(name='CHI2', dtype=float)
    dof = EoCalibField(name='DOF', dtype=float)
    maxDn = EoCalibField(name='MAXDN', dtype=float, unit='ADU')
    xPeak = EoCalibField(name='XPEAK', dtype=int, unit='pixel')
    yPeak = EoCalibField(name='YPEAK', dtype=int, unit='pixel')
    p9Data = EoCalibField(name='P9_DATA', dtype=float, shape=[3, 3], unit='ADU')
    p9Model = EoCalibField(name='P9_MODEL', dtype=float, shape=[3, 3], unit='ADU')
    pRectData = EoCalibField(name='PRECT_DATA', dtype=float, shape=[7, 7], unit='ADU')


class EoFe55AmpHitData(EoCalibTable):  # pylint: disable=too-many-instance-attributes

    SCHEMA_CLASS = EoFe55AmpHitDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoFe55AmpHitData, self).__init__(data=data, **kwargs)
        self.xPos = self.table[self.SCHEMA_CLASS.xPos.name]
        self.yPos = self.table[self.SCHEMA_CLASS.yPos.name]
        self.sigmaX = self.table[self.SCHEMA_CLASS.sigmaX.name]
        self.sigmaY = self.table[self.SCHEMA_CLASS.sigmaY.name]
        self.dn = self.table[self.SCHEMA_CLASS.dn.name]
        self.dnFpSum = self.table[self.SCHEMA_CLASS.dnFpSum.name]
        self.chiProb = self.table[self.SCHEMA_CLASS.chiProb.name]
        self.chi2 = self.table[self.SCHEMA_CLASS.chi2.name]
        self.dof = self.table[self.SCHEMA_CLASS.dof.name]
        self.maxDn = self.table[self.SCHEMA_CLASS.maxDn.name]
        self.xPeak = self.table[self.SCHEMA_CLASS.xPeak.name]
        self.p9Data = self.table[self.SCHEMA_CLASS.p9Data.name]
        self.p9Model = self.table[self.SCHEMA_CLASS.p9Model.name]
        self.pRectData = self.table[self.SCHEMA_CLASS.pRectData.name]


class EoFe55AmpRunDataSchemaV0(EoCalibTableSchema):

    VERSION = 0
    TABLELENGTH = "nAmp"

    gain = EoCalibField(name="GAIN", dtype=float)
    gainError = EoCalibField(name="GAIN_ERROR", dtype=float)
    psfSigma = EoCalibField(name="PSF_SIGMA", dtype=float, unit='pixel')


class EoFe55AmpRunData(EoCalibTable):

    SCHEMA_CLASS = EoFe55AmpRunDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoFe55AmpRunData, self).__init__(data=data, **kwargs)
        self.gain = self.table[self.SCHEMA_CLASS.gain.name]
        self.gainError = self.table[self.SCHEMA_CLASS.gainError.name]
        self.psfSigma = self.table[self.SCHEMA_CLASS.psfSigma.name]


class EoFe55DataSchemaV0(EoCalibSchema):

    ampHits = EoCalibTableHandle(tableName="ampHit_{key}",
                                 tableClass=EoFe55AmpHitData,
                                 multiKey="amps")

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoFe55AmpRunData)


class EoFe55Data(EoCalib):

    SCHEMA_CLASS = EoFe55DataSchemaV0

    _OBSTYPE = 'bias'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.VERSION

    def __init__(self, **kwargs):
        super(EoFe55Data, self).__init__(**kwargs)
        self.ampHits = self._tables['ampHits']
        self.amps = self._tables['amps']


RegisterEoCalibTableSchema(EoFe55AmpHitData)
RegisterEoCalibTableSchema(EoFe55AmpRunData)
RegisterEoCalibSchema(EoFe55Data)

AMPS = ["%02i" % i for i in range(16)]
NHIT = 100

testData = EoFe55Data(amps=AMPS, nAmp=len(AMPS), nHit=NHIT)
