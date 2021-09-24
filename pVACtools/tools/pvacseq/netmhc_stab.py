import sys

from pvactools.lib.netmhc_stab import NetMHCStab

def define_parser():
    return NetMHCStab.parser('pvacseq')

def main(args_input = sys.argv[1:]):
    parser = define_parser()
    args = parser.parse_args(args_input)

    NetMHCStab(args.input_file, args.output_file, file_type='pVACseq').execute()

if __name__ == "__main__":
    main()