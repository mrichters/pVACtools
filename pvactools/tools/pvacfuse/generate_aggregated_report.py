import sys
import argparse
import tempfile

from pvactools.lib.aggregate_all_epitopes import UnmatchedSequenceAggregateAllEpitopes

def define_parser():
    parser = argparse.ArgumentParser(
        "pvacfuse generate_aggregated_report",
        description="Generate an aggregated report from a pVACfuse .all_epitopes.tsv report file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "input_file",
        help="A pVACfuse .all_epitopes.tsv report file"
    )
    parser.add_argument(
        "output_file",
        help="The file path to write the aggregated report tsv to"
    )
    parser.add_argument(
        '-b', '--binding-threshold', type=int,
        help="Tier epitopes in the \"Pass\" tier when the mutant allele "
             + "has ic50 binding scores below this value and in the \"Relaxed\" tier when the mutant allele has ic50 binding scores below double this value.",
        default=500
    )
    parser.add_argument(
        '--allele-specific-binding-thresholds',
        help="Use allele-specific binding thresholds. To print the allele-specific binding thresholds run `pvacfuse allele_specific_cutoffs`. "
             + "If an allele does not have a special threshold value, the `--binding-threshold` value will be used.",
        default=False,
        action='store_true',
    )
    parser.add_argument(
        '--percentile-threshold', type=float,
        help="When set, tier epitopes in the \"Pass\" tier when the mutant allele "
             + "has percentile scores below this value and in the \"Relaxed\" tier "
             + "when the mutant allele has percentile scores below double this value.",
    )

    return parser

def main(args_input = sys.argv[1:]):
    parser = define_parser()
    args = parser.parse_args(args_input)

    tmp_fh = tempfile.NamedTemporaryFile()

    print("Creating Aggreggated Report")
    UnmatchedSequenceAggregateAllEpitopes(
        args.input_file,
        args.output_file,
        binding_threshold=args.binding_threshold,
        allele_specific_binding_thresholds=args.allele_specific_binding_thresholds,
        percentile_threshold=args.percentile_threshold
    ).execute()
    print("Completed")

if __name__ == '__main__':
    main()
