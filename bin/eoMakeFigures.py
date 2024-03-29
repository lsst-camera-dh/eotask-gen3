#! /usr/bin/env python

import os
import argparse

from lsst.daf.butler import Butler
from lsst.eotask_gen3 import EoStaticPlotTask
from lsst.eotask_gen3.eoCalib import WriteReportConfigYaml


def main():

    # argument parser
    parser = argparse.ArgumentParser(prog='eoStaticReport.py')
    parser.add_argument('-b', '--butler', type=str, help='Butler Repo')
    parser.add_argument('-c', '--collection', nargs='+', help="Input collection(s)")
    parser.add_argument('-d', '--dataset_types', action='append', type=str,
                        default=None, help="Dataset types")
    parser.add_argument('-o', '--outdir', type=str, help='Path to output area')
    parser.add_argument('-w', '--where', type=str, help='selection function')

    # unpack options
    args = parser.parse_args()

    butler = Butler(args.butler)
    task = EoStaticPlotTask()

    kwargs = {}

    def filterDatasetType(dt):
        return dt.storageClass.pytype.__name__ == 'IsrCalib'

    if args.dataset_types:
        dataset_types = args.dataset_types
    else:
        dataset_types = [dt.name for dt in list(butler.registry.queryDatasetTypes()) if filterDatasetType(dt)]

    if args.where:
        kwargs['where'] = args.where

    dataClasses = []

    for dataset_type in dataset_types:
        inputRefs = list(butler.registry.queryDatasets(dataset_type, collections=args.collection, **kwargs))
        if len(inputRefs)>0:
            inst = inputRefs[0].dataId['instrument']
            cameraObj = butler.get('camera', instrument=inst, collections=args.collection) # get camera object for full focal plane plots
        inputData = [butler.get(dataset_type, inputRef.dataId,
                                collections=args.collection) for inputRef in inputRefs]
        if not inputData:
            continue
        refObj, cameraDict = task.buildCameraDict(inputData, inputRefs, butler)
        dataClasses.append(type(refObj))
        task.run(refObj, cameraDict, cameraObj, refObj.shortName(), args.outdir)

    WriteReportConfigYaml(os.path.join(args.outdir, "manifest.yaml"), dataClasses)


if __name__ == '__main__':
    main()
