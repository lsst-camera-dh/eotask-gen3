"""Class to analyze the overscan bias as a function of row number"""

import numpy as np

from astropy.table import Table

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT


from .utils import REGION_KEYS, REGION_NAMES, REGION_LABELS,\
    get_dimension_arrays_from_ccd, get_raw_image, get_amp_offset,\
    get_geom_regions, get_amp_list, get_image_frames_2d, array_struct, unbias_amp


__all__ = ["BiasStructTask", "BiasStructTaskConfig"]


class BiasStructConnections(pipeBase.PipelineTaskConnections,
                            dimensions=("instrument", "exposure", "detector")):
    inputExp = cT.Input(
        name="raw",
        doc="Extract Structure from Bias Frames.",
        storageClass="Exposure",
        dimensions=("instrument", "exposure", "detector"),
    )

    outputBiasStruct_s_row = cT.Output(
        name="biasStruct_serial_row",
        doc="Table of row-wise bias structure in serial overscan",
        storageClass="AstropyTable",
        dimensions=("instrument", "exposure", "detector"),
    )

    outputBiasStruct_p_row = cT.Output(
        name="biasStruct_parallel_row",
        doc="Table of row-wise bias structure in parallel overscan",
        storageClass="AstropyTable",
        dimensions=("instrument", "exposure", "detector"),
    )

    outputBiasStruct_i_row = cT.Output(
        name="biasStruct_image_row",
        doc="Table of row-wise bias structure in image region",
        storageClass="AstropyTable",
        dimensions=("instrument", "exposure", "detector"),
    )

    outputBiasStruct_s_col = cT.Output(
        name="biasStruct_serial_col",
        doc="Table of col-wise bias structure in serial overscan",
        storageClass="AstropyTable",
        dimensions=("instrument", "exposure", "detector"),
    )

    outputBiasStruct_p_col = cT.Output(
        name="biasStruct_parallel_col",
        doc="Table of col-wise bias structure in parallel overscan",
        storageClass="AstropyTable",
        dimensions=("instrument", "exposure", "detector"),
    )

    outputBiasStruct_i_col = cT.Output(
        name="biasStruct_image_col",
        doc="Table of col-wise bias structure in image region",
        storageClass="AstropyTable",
        dimensions=("instrument", "exposure", "detector"),
    )


class BiasStructTaskConfig(pipeBase.PipelineTaskConfig, pipelineConnections=BiasStructConnections):
    pass


    
class BiasStructTask(pipeBase.PipelineTask,
                     pipeBase.CmdLineTask):
    """Analyze the structure of the bias frames"""

    ConfigClass = BiasStructTaskConfig
    _DefaultName = "biasStruct"

    def run(self, inputExp):
        """Plot the row-wise and col-wise struture
        in a series of bias frames

        Parameters
        ----------
        inputExp : `lsst.afw.image.Exposure`
            Raw exposure to analyze.

        Returns
        -------
        """
        ccd = inputExp

        dims = get_dimension_arrays_from_ccd(ccd)
        biasstruct_data = dict(outputBiasStruct_s_col=dict(idx=dims['col_s']),
                               outputBiasStruct_p_col=dict(idx=dims['col_p']),
                               outputBiasStruct_i_col=dict(idx=dims['col_i']),
                               outputBiasStruct_s_row=dict(idx=dims['row_s']),
                               outputBiasStruct_p_row=dict(idx=dims['row_p']),
                               outputBiasStruct_i_row=dict(idx=dims['row_i']))
                               
        self.get_ccd_data(ccd, biasstruct_data, bias_type=None, bias_type_col=None)

        out_data = {}
        for key, val in biasstruct_data.items():
            out_data[key] = Table(val)

        return pipeBase.Struct(**out_data)

    
    def get_ccd_data(self, ccd, data, **kwargs):
        """Get the bias values and update the data dictionary

        Parameters
        ----------
        ccd : `MaskedCCD`
            The ccd we are getting data from
        data : `dict`
            The data we are updating

        Keywords
        --------
        bias_type : `str`
            Method to use to construct bias
        std : `bool`
            Used standard deviation instead of mean
        """
        bias_type = kwargs.get('bias_type', None)
        bias_type_col = kwargs.get('bias_type_col', None)
        amps = get_amp_list(ccd)
        for i, amp in enumerate(amps):
            regions = get_geom_regions(ccd, amp)
            serial_oscan = regions['serial_overscan']
            parallel_oscan = regions['parallel_overscan']
            img = get_raw_image(ccd, amp)
            image = unbias_amp(img, serial_oscan,
                               bias_type=bias_type,
                               bias_type_col=bias_type_col,
                               parallel_oscan=parallel_oscan)
            frames = get_image_frames_2d(image, regions)

            for key, region in zip(REGION_KEYS, REGION_NAMES):
                framekey_row = "outputBiasStruct_%s_row" % key
                framekey_col = "outputBiasStruct_%s_col" % key
                struct = array_struct(frames[region], do_std=False)
                key_str = "biasst_a%02i" % i
                data[framekey_row][key_str] = struct['rows']
                data[framekey_col][key_str] = struct['cols']


