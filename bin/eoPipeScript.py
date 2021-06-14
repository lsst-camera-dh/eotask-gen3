#! /usr/bin/env python

import argparse

RUN="12622"
TEST_REPO="test_repo"
CALIB_COLL="u/echarles/run_12622/cpDefects,LSSTCam/calib/unbounded"
PD_COLL="LSSTCam/photodiode/all"
PIPE_YAML="eoPipe.yaml"

TASKS = ['eoBias',
         'eoDark',
         'eoFlatLow',
         'eoFlatHigh',
         'eoBrightPixels',
         'eoDarkPixels',
         'eoDefects',
         'eoPtc',
         'eoNonlinearity',
         'eoBiasStability',
         'eoDarkCurrent',
         'eoReadNoise',
         'eoOverscan',
         'eoBrighterFatter',
         'eoGainStability',
         'eoPersistenceBias',
         'eoPersistence',
         'eoTearing',
         'eoFe55Bias']

BROKEN = ['eoFe55',
          'eoCti']
    
def main():

    # argument parser
    parser = argparse.ArgumentParser(prog='eoPipeScript.py')
    parser.add_argument('-b', '--butler', type=str, help='Butler Repo', default=TEST_REPO)
    parser.add_argument('-p', '--pipe_yaml', type=str, help='Pipeline yaml file', default=PIPE_YAML)
    parser.add_argument('--run', type=str, help="Run Number", default=RUN)
    # unpack options
    args = parser.parse_args()

    inputColl="LSSTCam/raw/run_{RUN}".format(RUN=args.run)
    outputColl="u/echarles/run_{RUN}/outputs".format(RUN=args.run)

    first = True

    formatDict = dict(REPO=args.butler, INPUT_COLL=inputColl, CALIB_COLL=CALIB_COLL, PD_COLL=PD_COLL, OUTPUT_COLL=outputColl, PIPE_YAML=args.pipe_yaml)

    for task in TASKS:
        formatDict['TASK'] = task
        cmdStr = 'pipetask run -d "instrument =\'LSSTCam\' AND detector = 98" -b {REPO} --output {OUTPUT_COLL} -p {PIPE_YAML}#{TASK} --register-dataset-types --no-versions'.format(**formatDict)
        if first:
            cmdStr += " -i {INPUT_COLL},{CALIB_COLL},{PD_COLL}".format(**formatDict)
            first = False
    
        print(cmdStr)

if __name__ == '__main__':
    main()






