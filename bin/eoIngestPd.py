
import os
import argparse

from lsst.data.butler import Butler


def getDataId(butler, filename):

    tokens = os.path.splitext(os.path.basename(filename))[0].split('_')
    dayObs = tokens[2]
    seqNum = tokens[3]    
    import pdb
    pdb.set_trace()
    dataSet = butler.registry.findDataset(instrument="LSSTCam")





def main():

    # argument parser
    parser = argparse.ArgumentParser(prog='eoIngestPd.py')
    parser.add_argument('-r', '--repo', type=str, help='Butler Repo')

    parser.add_argument('file', type=str, nargs='+', help='files to import')
    # unpack options
    args = parser.parse_args()

    butler = Butler(args.repo)
    for aFile in args.files:
        dataId = getDataId(butler, aFile)
        
        
        

if __name__ == '__main__':
    main()
    
    
