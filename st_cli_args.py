import argparse


def st_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file',
                        help="file containing text to match against suffix tree",
                        dest="test_file")
    parser.add_argument('-s', '--suffixtree',
                        help="file prefix for pickled suffix tree",
                        dest="suffix_tree_prefix")
    parser.add_argument('--fasta',
                        help='fasta file to use as data source',
                        dest='fasta_file')
    parser.add_argument('--slice',
                        help='slice into data source, 1Mb units',
                        dest='slice_spec')
    parser.add_argument('-o', '--output-file',
                        help='path to output file',
                        dest='output_file')
    parser.add_argument('-d', '--depth',
                        help='emit match data when this depth reached', type=int, default=10,
                        dest='emit_depth')

    return parser.parse_args()