import argparse
import sys
from subprocess import call
import os
import pkg_resources
from tools.pvacview import *

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    subparsers = parser.add_subparsers()

    #add subcommands
    run_main_program_parser = subparsers.add_parser(
        "run",
        help="Run the pVACview R shiny application",
        add_help=False
    )
    run_main_program_parser.set_defaults(func=run)

    args = parser.parse_known_args()
    try:
        args[0].func.main(args[1])
    except AttributeError as e:
        parser.print_help()
        print("Error: No command specified")
        raise


if __name__ == '__main__':
    main()
