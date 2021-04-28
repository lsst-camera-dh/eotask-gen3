#!/usr/bin/env python

import os
import argparse

COMLINE = 'astrometadata -p lsst.obs.lsst.translators write-index --content=metadata {dirpath}'

def main():

    # argument parser
    parser = argparse.ArgumentParser(prog='makeIndexJson.py')
    parser.add_argument('dirs', type=str, nargs='+', help="Directories")
    # unpack options
    args = parser.parse_args()

    for arg_ in args:
        comline = COMLINE.format(dirpath=arg_)
        os.system(comline)


if __name__ == "__main__":
    main()
