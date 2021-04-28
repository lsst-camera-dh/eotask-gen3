
RUN="12781"
REPO="repo"
ALL_RAWS="LSSTCam/raw/all"
CALIB_COL="LSSTCam/calib,/calib/run_12781"
CALIB_RUN_COL="u/echarles/calib/bias/run_12781/20210324T162502Z,u/echarles/calib/defects/run_12781/20210324T164529Z"
PIPE_DIR="examples/config"

cmd_str =  'pipetask run -d "instrument =\'LSSTCam\' AND exposure.observation_type = \'bias\' AND exposure.science_program IN ( \'{RUN}\' ) AND detector = 29" -b {REPO} -i {ALL_RAWS},{CALIB_COL} -o u/echarles/examples/run_{RUN} -p {PIPE_DIR}/isrBias.yaml --register-dataset-types'.format(RUN=RUN, REPO=REPO, ALL_RAWS=ALL_RAWS, PIPE_DIR=PIPE_DIR, CALIB_COL=CALIB_COL)

print(cmd_str)

cmd_str =  'pipetask run -d "instrument =\'LSSTCam\' AND exposure.observation_type = \'bias\' AND exposure.science_program IN ( \'{RUN}\' ) AND detector = 29" -b {REPO} -i u/echarles/examples/run_{RUN} -o u/echarles/examples/run_{RUN} -t examples.eoSimpleExample.EoSimpleExampleTask --register-dataset-types'.format(RUN=RUN, REPO=REPO, ALL_RAWS=ALL_RAWS, PIPE_DIR=PIPE_DIR, CALIB_COL=CALIB_COL)

print(cmd_str)

cmd_str =  'pipetask run -d "instrument =\'LSSTCam\' AND exposure.observation_type = \'bias\' AND exposure.science_program IN ( \'{RUN}\' ) AND detector = 29" -b {REPO} -i {ALL_RAWS},{CALIB_RUN_COL} -o u/echarles/examples/run_{RUN} -t examples.eoSimpleExample.EoIsrExampleTask --register-dataset-types'.format(RUN=RUN, REPO=REPO, ALL_RAWS=ALL_RAWS, PIPE_DIR=PIPE_DIR, CALIB_RUN_COL=CALIB_RUN_COL)

print(cmd_str)



