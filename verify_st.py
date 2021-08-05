import argparse
import random
from suffixtree.location import Location
from suffixtree.suffixtree import SuffixTree, Edge
from suffixtree.builder.tree_builder import ValueProcessor
from time import perf_counter

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--str', help="test string", dest="test_string")
parser.add_argument('-st', '--suffix-tree', help="file prefix for pickled suffix tree", dest="suffix_tree_prefix")
parser.add_argument('-sd', '--seed', help="seed for random repeatability", dest="seed", default=0, type=int)
parser.add_argument('-f', '--file', help="file containing text", dest="test_file")
parser.add_argument('-n', help="number of tests to run", default=1000, type=int)
args = parser.parse_args()

start = perf_counter()

random.seed(args.seed)
print(args)
print(type(args.seed))

st = SuffixTree.load_from_path(args.suffix_tree_prefix)
data_source = st.data_source


class TreeSearcher:
    def __init__(self, st):
        self.st = st

    def find(self, s):
        location = Location()
        location.internal_node(Edge(self.st.root_node))
        vp = ValueProcessor(self.st, location, data_source)
        for offset, value in enumerate(s):
            vp.process(offset, value)
            if not vp.succeeded:
                print(f"Failed at {offset}, {value}")
                return False, None
        return True, location


def random_bounds(n):
    """excluding $ terminator (last value in n)
    returns lower,upper where lower is min 0, max (n-2), and upper is min 1, max n-1, and lower < upper"""
    if n < 40:
        upper = random.randint(1, n - 1)
        lower = random.randint(0, upper - 1)
    else:
        lower = random.randint(0, n - n // 10)
        upper = lower + random.randint(1, n // 10)
    return lower, upper


tree_searcher = TreeSearcher(st)
for i in range(args.n):
    lower, upper = random_bounds(len(data_source))
    test_string = data_source[lower:upper]
    result, location = tree_searcher.find(test_string)
    if result:
        suffixes = st.get_suffixes(location)
        for offset in suffixes:
            xtract = data_source[offset:offset + len(test_string)]
            assert (xtract == test_string)
        # print(f"found at {len(suffixes)} locations")
    else:
        print("..NOT FOUND")
    if i % 10 == 0:
        print('.', flush=True, end='')

end = perf_counter()
print(f"done, {end - start:.2f}")
