#!/Users/nisse/code/pymatgen/python2.7_devSIAs/bin/python

from __future__ import division, print_function, unicode_literals

"""
A script with tools for computing formation energies
of charged point defects, supporting multiple correction
schemes.
"""

__author__ = "Nils E. R. Zimmermann, Bharat Medasani"
__copyright__ = "Copyright 2012, The Materials Project"
__version__ = "1"
__maintainer__ = "Nils E. R. Zimmermann"
__email__ = "nerz@lbl.gov"
__date__ = "May 1, 2015"

import argparse
#import os
#import json
#import glob
import math

import pymatgen
from pymatgen.matproj.rest import MPRester
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.transformations.standard_transformations import SupercellTransformation
from pymatgen.analysis.bond_valence import BVAnalyzer
from pycdcd.core.defectsmaker import ChargedDefectsStructures
from pycdcd.utils.vasp import make_vasp_defect_files, \
        make_vasp_dielectric_files
from pycdcd.utils.parse_calculations import PostProcess


def generate_input_files(args):
    """
    Generates input files for VASP calculations that aim to determine
    formation energies of charged point defects by (possibly) applying
    correction terms (supported so-far: correction due to Freysoldt
    et al., Phys. Rev. Lett., 2009).
    The primitive unit cell is obtained from the MP ID provided during
    script call.  

    Args:
        args (Namespace): contains the parsed command-line arguments for
            this command.
    """

    # initialize variables
    mpid = args.mpid
    mapi_key = args.mapi_key
    nmax = args.nmax
    oxi_range = args.oxi_range

    # error-checking
    if not mpid:
        print ("============\nERROR: Provide an mpid\n============")
        return

    # get primitive unit cell
    if not mapi_key:
        with MPRester() as mp:
            prim_struct = mp.get_structure_by_material_id(mpid)
    else:
        with MPRester(mapi_key) as mp:
            prim_struct = mp.get_structure_by_material_id(mpid)

    # transform to conventional unit cell
    conv_struct = SpacegroupAnalyzer(
        prim_struct).get_conventional_standard_structure()

    make_vasp_dielectric_files(prim_struct)
    if oxi_range:
        oxi_range_dict = {}
        for i in range(len(oxi_range)):
            oxi_range_dict[oxi_range[i][0]] = tuple([int(oxi_range[i][1]),
                int(oxi_range[i][2])])
        def_structs = ChargedDefectsStructures(conv_struct, oxi_range_dict,
            cellmax=nmax)
    else:
        def_structs = ChargedDefectsStructures(conv_struct, cellmax=nmax)
    make_vasp_defect_files(def_structs.defects,
        conv_struct.composition.reduced_formula)


def parse_vasp_output(args):
    """
    Parses output files from VASP calculations that aim to determine
    formation energies of charged point defects by (possibly) applying
    correction terms (supported so-far: correction due to Freysoldt
    et al., Phys. Rev. Lett., 2009).

    Args:
        args (Namespace): contains the parsed command-line arguments for
            this command.
    """

    # initialize variables
    mpid = args.mpid
    mapi_key = args.mapi_key
    root_fldr = args.root_fldr

    # error-checking
    if not mpid:
        print ("============\nERROR: Provide an mpid\n============")
        return

    # get primitive unit cell
    if not mapi_key:
        with MPRester() as mp:
            prim_struct = mp.get_structure_by_material_id(mpid)
    else:
        with MPRester(mapi_key) as mp:
            prim_struct = mp.get_structure_by_material_id(mpid)

    PostProcess(root_fldr, mpid, mapi_key).parse_defect_calculations()


def main():
    parser = argparse.ArgumentParser(description="""
        pycdt is a script that generates vasp input files, parses vasp output
        files, and computes the formation energy of charged defects.
        This script works based on several sub-commands with their own options.
        To see the options for the sub-commands, type
        "pycdt sub-command -h".""",
        epilog="""
        Authors: Nils E. R. Zimmermann, Bharat Medasani
        Version: {}
        Last updated: {}""".format(__version__, __date__))

    subparsers = parser.add_subparsers()
    MPID_string = "Materials Project id of the structure.\nFor more info on " \
        "Materials Project, please, visit www.materialsproject.org"
    MAPI_string = "Your Materials Project REST API key.\nFor more info, " \
        "please, visit www.materialsproject.org/open"
    NMAX_string = "Maximum number of atoms in supercell.\nThe default is" \
        "128.\nKeep in mind the number of atoms in the supercell may vary" \
        "from the provided number including the default."
    OXI_RANGE_string = "Oxidation range for an element.\nThree arguments" \
        " expected: the element type for which the oxidation state range is" \
        " to be specified as well as the lower and the upper limit of the" \
        " range (e.g., --oxi_states As -3 5)."
    ROOT_FLDR_string = "Path (relative or absolute) to directory" \
        " in which data of charged point-defect calculations for" \
        " a particular system are to be found.\n"

    parser_input_files = subparsers.add_parser("generate_input_files",
        help="Generates Vasp input files for charged point defects.")
    parser_input_files.add_argument("--mpid", type=str.lower, dest="mpid",
        help=MPID_string)
    parser_input_files.add_argument("--mapi_key", default = None,
        dest="mapi_key", help=MAPI_string)
    parser_input_files.add_argument("--nmax", type=int, default = 128,
        dest="nmax", help=NMAX_string)
    parser_input_files.add_argument("--oxi_range", action='append', type=str,
        nargs=3, dest="oxi_range", help=OXI_RANGE_string)
    parser_input_files.set_defaults(func=generate_input_files)

    parser_vasp_output = subparsers.add_parser("parse_vasp_output",
        help="Parses VASP output for calculation of formation energies of"
             " charged point defects.")
    parser_vasp_output.add_argument("--mpid", type=str.lower, dest="mpid",
        help=MPID_string)
    parser_vasp_output.add_argument("--mapi_key", default = None,
        dest="mapi_key", help=MAPI_string)
    parser_vasp_output.add_argument("--dir", default = None,
        dest="root_fldr", help=ROOT_FLDR_string)
    parser_vasp_output.set_defaults(func=parse_vasp_output)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()