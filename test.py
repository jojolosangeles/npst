import argparse
from suffixtree.builder.tree_builder import TreeBuilder
from time import perf_counter
from data_source.fasta import get_fasta_data

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--str', help="test string", dest="test_string")
parser.add_argument('-f', '--file', help="file containing text", dest="test_file")
parser.add_argument('-r', '--random', help="random text with length provided", dest="random_length")
parser.add_argument('-st', help="file prefix for pickled suffix tree", dest="suffix_tree_prefix")
parser.add_argument('--fasta', help='fasta file to use as data source', dest='fasta_file')
parser.add_argument('--slice', help='slice into data source, 1Mb units', dest='slice')
parser.add_argument("output_file")
parser.add_argument("expected_file")
parser.add_argument("recorded_time")
args = parser.parse_args()

test_string = args.test_string
if test_string is None:
    test_file = args.test_file
    if test_file is not None:
        with open(test_file) as f:
            test_string = f.read()
if test_string is None:
    seq_file = args.fasta_file
    if seq_file:
        test_string = get_fasta_data(seq_file, args.slice)

test_string += "$"
tbuilder = TreeBuilder(test_string)

start_time = perf_counter()
kstart = perf_counter()
total_length = len(test_string)
for o, v in enumerate(test_string):
    start = perf_counter()
    tbuilder.process_value(o, v)
    end = perf_counter()
    if (o % 1000) == 0:
        kend = perf_counter()
        print(f"{o*100/total_length:.2f}% {o}, {v}, {kend - kstart:.2f}")
        kstart = kend

end_time = perf_counter()
if len(test_string) > 30:
    test_string = f"{test_string[:30]}..."

print(test_string, f"{end_time - start_time:.02f}")
if abs((end_time - start_time) - int(args.recorded_time)) > 1:
    print(f"**** FAILED, before duration {args.recorded_time}, this duration {end_time - start_time}")
    # print()
    # tbuilder.show_tree(f"************* After {o}, {v}")
    # print()

if args.suffix_tree_prefix:
    tbuilder.st.internal_nodes.to_pickle(f"{args.suffix_tree_prefix}_internal")
    tbuilder.st.leaf_nodes.to_pickle(f"{args.suffix_tree_prefix}_leaf")
    with open(f'{args.suffix_tree_prefix}.data', 'w') as out_file:
        out_file.write(str(tbuilder.st.data_source))


with open(args.output_file, "w") as out_file:
    out_file.write(tbuilder.context_recorder.history())

with open(args.expected_file) as expected_results, open(args.output_file) as actual_results:
    expected_lines = expected_results.readlines()
    actual_lines = actual_results.readlines()
    if len(expected_lines) != len(actual_lines):
        print(f"*** FAILED, expected {len(expected_lines)} lines, got {len(actual_lines)}")
    print(f"diff {args.expected_file} {args.output_file}")

