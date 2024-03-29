#! /usr/bin/env python

import os
import argparse

from astropy.table import Table
from lsst.daf.butler import Butler, DatasetType


def getDataIdRecords(butler, filename):

    tokens = os.path.splitext(os.path.basename(filename))[0].split('_')
    dayObs = int(tokens[2])
    seqNum = int(tokens[3])
    where = "exposure.day_obs = dayobs and exposure.seq_num = seqnum"
    records = list(butler.registry.queryDimensionRecords("exposure",
                                                         where=where,
                                                         bind={"dayobs": dayObs, "seqnum": seqNum},
                                                         dataId={"instrument": "LSSTCam"}))
    if records:
        return records[0]

    raise KeyError("Failed to find exposure ID for %s %06i" % (dayObs, seqNum))


def setTableMetaData(table, dataIdRecords):

    table.columns[0].name = 'Time'
    table.columns[1].name = 'Current'
    table.columns[0].unit = 's'
    table.columns[1].unit = 'A'

    table.meta['OBSTYPE'] = dataIdRecords.observation_type
    table.meta['INSTRUME'] = 'LSSTCam'
    table.meta['CALIBDATE'] = dataIdRecords.timespan.end.isot
    table.meta['CALIB_ID'] = 'calibDate=%s' % dataIdRecords.timespan.end.isot
    table.meta['PD_SCEHMA'] = 'Simple'
    table.meta['PD_SCHEMA_VERSION'] = 1
    table.meta['DATE'] = dataIdRecords.timespan.end.isot
    table.meta['CALIB_CREATION_DATE'] \
        = dataIdRecords.timespan.end.strftime('%Y-%M-%d')
    table.meta['CALIB_CREATION_TIME'] \
        = dataIdRecords.timespan.end.strftime('%H:%m:%S')


def ingest_pd_files(repo, pd_files, output_run='LSSTCam/photodiode/all'):

    butler = Butler(repo, writeable=True, run=output_run)
    datasetType = DatasetType("photodiode", ("instrument", "exposure"),
                              "AstropyTable",
                              universe=butler.registry.dimensions)

    try:
        butler.registry.registerDatasetType(datasetType)
    except Exception:
        pass

    print("Found %i photodiode files" % len(pd_files))
    for i, aFile in enumerate(pd_files):

        print(i, len(pd_files), os.path.basename(aFile))\

        try:
            dataIdRecords = getDataIdRecords(butler, aFile)
        except KeyError as msg:
            print(msg)
            continue

        table = Table.read(aFile, format='ascii')

        setTableMetaData(table, dataIdRecords)
        # dataId = dict(instrument=dataIdRecords.instrument,
        # exposure=dataIdRecords.id)
        dataId = dataIdRecords.dataId

        with butler.transaction():
            butler.put(table, "photodiode", dataId=dataId)
    print("Done!")


def main():

    # argument parser
    parser = argparse.ArgumentParser(prog='eoIngestPd.py')
    parser.add_argument('-b', '--butler', type=str, help='Butler Repo')
    parser.add_argument('--output-run', type=str,
                        help="The name of the run datasets should be output to",
                        default="LSSTCam/photodiode/all")
    parser.add_argument('files', type=str, nargs='+', help='Files to import')
    # unpack options
    args = parser.parse_args()

    ingest_pd_files(args.butler, args.files, args.output_run)


if __name__ == '__main__':
    main()
