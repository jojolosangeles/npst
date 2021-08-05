from st_cli_args import st_args
from functools import partial

from data_source.fasta import get_fasta_data_str
from suffixtree.location import Location
from suffixtree.suffixtree import SuffixTree, Edge
import pickle

EMIT_DEPTH = 10
"""
Usage:  python visualize.py -suffixtree <suffix tree name> --depth <emit_at_depth> --fasta .. --slice ..

This takes the fasta sequence, and matches it against the suffix tree.
"""
fn_counts = {}


def count_calls(fn):
    fn_counts[fn.__name__] = 0

    def inner(*args, **kwargs):
        fn_counts[fn.__name__] += 1
        return fn(*args, **kwargs)
    return inner


@count_calls
def verification_finder(data_source, s, *, emit_depth):
    if len(s) >= emit_depth:
        start_loc = 0
        while True:
            result = data_source.find(s, start_loc)
            if result != -1:
                yield result
                start_loc = result + len(s)
            else:
                break

@count_calls
def _emit_suffixes(offset, value, data_source, location, st, *, output_file, emit_depth):
    suffixes = st.get_suffixes(location)

    verification_str = data_source[location.offset - emit_depth:location.offset]
    # verification_suffixes = list(verification_finder(data_source, verification_str))
    found_location = offset - len(verification_str)
    pickle.dump((found_location,suffixes), output_file)
    print(f"offset_value_processed=({offset},{value}),"
          f"found_location={found_location},"
          f"slen={len(verification_str)},suffixes={suffixes},"
          f"verification_str='{verification_str}',location_offset={location.offset}")

    #print(f"offset_value_processed=({offset},{value}),found_location={found_location},slen={len(verification_str)},suffixes={suffixes},verification_str='{verification_str}',location_offset={location.offset},{verification_suffixes}")
    return True

@count_calls
def _emit_check(offset, value, data_source, location, st, *, emit_depth):
    # print(f"_emit_check {location.internal_node_id}, depth={emit_depth}")
    if location.on_internal_node:
        return st.depth_exceeds_limit(location.internal_node_id, emit_depth)
    elif location.on_internal_edge:
        return st.depth_exceeds_limit(location.internal_node_id, emit_depth, location.incoming_edge_offset)
    else:
        # not handling leaf edges
        return False

@count_calls
def _goto_root(offset, value, data_source, location, st):
    location.internal_node(st.root_edge)

@count_calls
def _traverse(offset, value, data_source, location, st):
    if location.on_internal_edge or location.on_leaf_edge:
        if data_source[location.offset] == value:
            location.down(st.edge(location.internal_node_id, location.leaf_node_id))
            return True
    else:
        edge = st.find_edge(location.internal_node_id, ord(value))
        if edge is not None:
            location.update(edge)
            return True
    return False


class RuleRunner:
    def __init__(self, rules, data_source, location, st):
        self.rules = rules
        self.data_source = data_source
        self.location = location
        self.st = st

    def process(self, offset, value):
        fn = _traverse
        while True:
            result = fn(offset, value, self.data_source, self.location, self.st)
            if fn in self.rules:
                if result and self.rules[fn].get(TRUTHY, None):
                    fn = self.rules[fn].get(TRUTHY)
                elif not result and self.rules[fn].get(FALSY, None):
                    fn = self.rules[fn].get(FALSY)
                else:
                    break
            else:
                break
        # print(f"{offset},{value} => {self.location}")


TRUTHY = "OK"
FALSY = "FAIL"

args = st_args()
_emit_check = partial(_emit_check, emit_depth=args.emit_depth)

with open(args.output_file, 'wb') as output_file:
    _emit_suffixes = partial(_emit_suffixes, output_file=output_file, emit_depth=args.emit_depth)

    emit_rules = {
        _traverse: {TRUTHY: _emit_check, FALSY: _goto_root},
        _emit_check: {TRUTHY: _emit_suffixes },
        _emit_suffixes: {TRUTHY: _goto_root},
        _goto_root: {}
    }

    # load the suffix tree
    st = SuffixTree.load_from_path(args.suffix_tree_prefix)
    st_location = Location()
    st_location.internal_node(Edge(st.root_node))

    # load the stream to match
    match_seq = get_fasta_data_str(args.fasta_file, args.slice_spec)

    tree_matcher = RuleRunner(emit_rules, st.data_source, st_location, st)

    print(f"len(match_seq)={len(match_seq)}")
    for offset, value in enumerate(match_seq):
        if value != 'N':
            tree_matcher.process(offset, value)
        if offset % 1000 == 0:
            print(f"{offset}...{fn_counts}")
    print(f"done")




