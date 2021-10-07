# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema
from .eoPlotUtils import EoPlotMethod, nullFigure

__all__ = ["EoNonlinearityAmpRunData",
           "EoNonlinearityData"]


class EoNonlinearityAmpRunDataSchemaV0(EoCalibTableSchema):
    """Schema definitions for output data for per-amp, per-run tables
    for EoNonlinearityTask.

    This are the 'profile' parameters of the non-linearity correction.
    I.e., means and errors on the correction coefficients as at
    given ADU values
    """

    TABLELENGTH = 'nAmp'

    profX = EoCalibField(name="PROF_X", dtype=float, unit='adu', shape=['nProf'])
    profYCorr = EoCalibField(name="PROF_YCORR", dtype=float, unit='adu', shape=['nProf'])
    profYErr = EoCalibField(name="PROF_YERR", dtype=float, unit='adu', shape=['nProf'])


class EoNonlinearityAmpRunData(EoCalibTable):
    """Container class and interface for per-amp, per-exposure-pair tables
    for EoNonlinearityTask."""

    SCHEMA_CLASS = EoNonlinearityAmpRunDataSchemaV0

    def __init__(self, data=None, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates class properties with columns
        """
        super(EoNonlinearityAmpRunData, self).__init__(data=data, **kwargs)
        self.profX = self.table[self.SCHEMA_CLASS.profX.name]
        self.profYCorr = self.table[self.SCHEMA_CLASS.profYCorr.name]
        self.profYErr = self.table[self.SCHEMA_CLASS.profYErr.name]


class EoNonlinearityDataSchemaV0(EoCalibSchema):
    """Schema definitions for output data for EoNonlinearityTask.

    This defines correct versions of the sub-tables"""

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoNonlinearityAmpRunData)


class EoNonlinearityData(EoCalib):
    """Container class and interface for EoNonlinearityTask outputs."""

    SCHEMA_CLASS = EoNonlinearityDataSchemaV0

    _OBSTYPE = 'flat'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates instance properties with
        sub-tables
        """
        super(EoNonlinearityData, self).__init__(**kwargs)
        self.amps = self['amps']


@EoPlotMethod(EoNonlinearityData, "curve", "slot", "nonlinearity", "Linearity")
def plotLinearity(obj):
    return nullFigure()


@EoPlotMethod(EoNonlinearityData, "resids", "slot", "nonlinearity", "Linearity residual")
def plotLinearityResidual(obj):
    return nullFigure()


RegisterEoCalibSchema(EoNonlinearityData)


AMPS = ["%02i" % i for i in range(16)]
NPROFILE = 20
EoNonlinearityData.testData = dict(testCtor=dict(nAmp=len(AMPS), nProf=NPROFILE))
