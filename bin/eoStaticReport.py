#! /usr/bin/env python

import argparse

from lsst.eotask_gen3 import write_run_report


def main():

    # argument parser
    parser = argparse.ArgumentParser(prog='eoStaticReport.py')
    parser.add_argument('-r', '--run', type=str, help='Run number')
    parser.add_argument('-i', '--inputbase', type=str, help="Path to input files")
    parser.add_argument('-o', '--outbase', type=str, help='Path to output area')
    parser.add_argument('-t', '--template_file', type=str, help='Path to template yaml file')
    parser.add_argument('-c', '--css_file', type=str, help='Path to .css style file')

    # unpack options
    args = parser.parse_args()
    write_run_report(**args.__dict__)


if __name__ == '__main__':
    main()
