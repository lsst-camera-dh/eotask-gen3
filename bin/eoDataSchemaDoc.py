#! /usr/bin/env python

import os

import sys

import argparse

from lsst.eotask_gen3 import WriteSchemaMarkdown


def main():

    # argument parser
    parser = argparse.ArgumentParser(prog='eoDataSchemaDoc.py')
    parser.add_argument('-o', '--output', type=str, help='Output File')
    # unpack options
    args = parser.parse_args()

    outputType = os.path.splitext(args.output)[-1]

    writeFuncDict = {'.md': WriteSchemaMarkdown}
    try:
        writeFunc = writeFuncDict[outputType]
    except KeyError as msg:
        raise KeyError("Only output types %s are supported, not %s" %
                       (list(writeFuncDict.keys()), outputType)) from msg
    writeFunc(args.output)


if __name__ == '__main__':
    main()
    
    
