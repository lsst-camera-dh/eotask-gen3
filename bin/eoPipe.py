#! /usr/bin/env python

import argparse

associate_raw_template = 'butler associate {repo} {base}/raw/{run} --collections LSSTCam/raw/all --where \"instrument = \'LSSTCam\' and exposure.science_program = \'{run}\'\"'  # noqa 

associate_pd_template = 'butler associate {repo} {base}/photodiode/{run} --collections LSSTCam/photodiode/all --where \"instrument = \'LSSTCam\' and exposure.science_program = \'{run}\'\"'  # noqa 

pipe_1_template = 'pipetask run {selection} -b {repo} -i {base}/raw/{run},LSSTCam/calib/unbounded --output-run {base}/analysis/{run} -p eoPipe.yaml#protocalRunNoPd --no-versions --register-dataset-types'  # noqa 

pipe_2_template = 'pipetask run {selection} -b {repo} -i {base}/analysis/{run},{base}/raw/{run},{base}/photodiode/{run},LSSTCam/calib/unbounded --output-run {base}/analysis/{run} -p eoPipe.yaml#protocalRunPd --no-versions --register-dataset-types --extend-run'  # noqa 

plot_template = 'eoMakeFigures.py -b {repo} -c {base}/analysis/{run} -o plots/{run}'  # noqa 

report_template = 'eoStaticReport.py -r {run} -i plots/{run} -o html/{run} -t plots/{run}/manifest.yaml -c style.css'  # noqa 


commands = [associate_raw_template, associate_pd_template,
            pipe_1_template, pipe_2_template, plot_template, report_template]


def print_commands(**kwargs):
    for c in commands:
        print("")
        print(c.format(**kwargs))


def main():

    # argument parser
    parser = argparse.ArgumentParser(prog='eoStaticReport.py')
    parser.add_argument('--run', type=str, help='Run number')
    parser.add_argument('--repo', type=str, default='bot_data', help='Path to butler repo')
    parser.add_argument('--selection', type=str, default='', help='Data selection')
    parser.add_argument('--base', type=str, default='u/echarles', help='Output base path')

    # unpack options
    args = parser.parse_args()
    print_commands(**args.__dict__)


if __name__ == '__main__':
    main()
