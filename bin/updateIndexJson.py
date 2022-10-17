#!/usr/bin/env python

import sys
import os
import argparse
import json
import glob
from astropy.io import fits


CHKSUMS = ['CHECKSUM', 'SEQCKSUM', 'ZHECKSUM', 'ZDATASUM', 'DATASUM']
CCDKEYS = ['DATE', 'MJD', 'SEQFILE']


def clean_template(t_dict):
    """ Remove checksums from a template dictionary """
    for k, v in t_dict.items():
        if k in ['__CONTENT__', '__COMMON__']:
            continue
        for chks in CHKSUMS:
            v.pop(chks)


def do_dir(dirname, t_dict):
    """ Write an _index.json file for a directory using a template dict """    
    files = glob.glob(os.path.join(dirname, 'MC_C*.fits'))
    tmp_exp = list(t_dict.keys())[2][:-13]

    e2v = None
    itl = None

    o_dict = dict(__CONTENT__=t_dict['__CONTENT__'])

    first = True
    for file_ in files:
        exp_name = os.path.basename(file_)[0:20]
        tmp_key = tmp_exp + os.path.basename(file_)[20:]
        tmp_dict = t_dict[tmp_key]
        ccd_dict = tmp_dict.copy()

        if ccd_dict['CCD_MANU'] == 'E2V':
            if e2v is None:
                e2v = fits.open(os.path.join(file_))[0].header
            tmpl = e2v
        elif ccd_dict['CCD_MANU'] == 'ITL':
            if itl is None:
                itl = fits.open(os.path.join(file_))[0].header
            tmpl = itl
        for kk in CCDKEYS:
            ccd_dict[kk] = tmpl[kk]
        if first:
            o_common = t_dict['__COMMON__'].copy()
            for kk in o_common.keys():
                try:
                    o_common[kk] = tmpl[kk]
                except Exception:
                    pass
            o_dict['__COMMON__'] = o_common
            first = False    
        o_dict[os.path.basename(file_)] = ccd_dict

    try:
        os.unlink(os.path.join(dirname, '_index.json'))
    except Exception:
        pass
    with open(os.path.join(dirname, '_index.json'), 'w') as fout:
        json.dump(o_dict, fout)
            
    

def main():
    
    # argument parser
    parser = argparse.ArgumentParser(prog='updateIndexJson.py')
    parser.add_argument('-t', '--template', default='_index.json', type=str, help='Template json file')
    parser.add_argument('dirs', type=str, nargs='+', help="Directories")
    # unpack options
    args = parser.parse_args()

    t_dict = json.load(open(args.template))
    clean_template(t_dict)

    for dir_ in args.dirs:
        abspath = os.path.abspath(dir_)
        subdirs = glob.glob(os.path.join(abspath, 'MC_C_*'))
        for subdir_ in subdirs:
            try:
                do_dir(subdir_, t_dict)
            except Exception as msg:
                print("Failed to make _index.json for %s because %s" % (subdir_, str(msg)))


if __name__ == "__main__":
    main()
