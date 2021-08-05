"""
Test Basic Building, Saving, Loading a Suffix Tree

   >>> tb = TreeBuilder("mississippi$", size_limit=100)
   >>> st = tb.build_tree()
   >>> print(st.info())
   12 leaf nodes, 7 internal nodes
   >>> print(st)
   ROOT of mississippi$
     mississippi$ p.0 (iESO=0, iESV='m') -0-
     $ p.0 (iESO=11, iESV='$') -11-
     p  p.0 sl.0 (iESO=8, iEEO=9, iESV='p') .6.
       pi$ p.6 (iESO=9, iESV='p') -8-
       i$ p.6 (iESO=10, iESV='i') -9-
     i  p.0 sl.0 (iESO=1, iEEO=2, iESV='i') .5.
       ppi$ p.5 (iESO=8, iESV='p') -7-
       $ p.5 (iESO=11, iESV='$') -10-
       ssi  p.5 sl.3 (iESO=2, iEEO=5, iESV='s') .2.
         ssippi$ p.2 (iESO=5, iESV='s') -1-
         ppi$ p.2 (iESO=8, iESV='p') -4-
     s  p.0 sl.0 (iESO=2, iEEO=3, iESV='s') .1.
       i  p.1 sl.5 (iESO=4, iEEO=5, iESV='i') .4.
         ssippi$ p.4 (iESO=5, iESV='s') -3-
         ppi$ p.4 (iESO=8, iESV='p') -6-
       si  p.1 sl.4 (iESO=3, iEEO=5, iESV='s') .3.
         ssippi$ p.3 (iESO=5, iESV='s') -2-
         ppi$ p.3 (iESO=8, iESV='p') -5-
   >>>

"""
from suffixtree.tree_nodes import LeafNodes, leaf_df, InternalNodes, empty_internal_df
from suffixtree.location import Location
from suffixtree.suffixtree import SuffixTree, Edge
from collections import defaultdict, namedtuple
from collections import deque
from functools import wraps
from copy import copy
from time import perf_counter


def state_recorder(fn):
    @wraps(fn)
    def inner(context):
        if context.builder:
            context.builder.register_before(fn.__name__)
        #print(f'{fn.__name__.upper()}({context.offset}, {context.value}) {context.location}')
        fn(context)
        if context.builder:
            context.builder.register_after(fn.__name__)

    return inner


@state_recorder
def _add_leaf(context):
    context.st.leaf_nodes.add(context.location.internal_node_id, context.offset, ord(context.value))


def fix_suffix_link(context, new_node):
    if context.needs_suffix_link:
        context.st.internal_nodes.set_suffix_link(context.needs_suffix_link, new_node)
        context.needs_suffix_link = None

@state_recorder
def _split_leaf_edge(context):
    location = context.location
    edge = context.st.leaf_nodes.data.iloc[location.leaf_node_id]
    new_internal_node = context.st.internal_nodes.add_node(edge.parent,
                                                           edge.iESO,
                                                           edge.iESV,
                                                           edge.iESO + location.incoming_edge_offset)
    fix_suffix_link(context, new_internal_node)
    new_iESO = edge.iESO + location.incoming_edge_offset
    new_iESV = ord(context.data_source[int(new_iESO)])
    context.st.leaf_nodes.update_leaf_child(location.leaf_node_id, new_internal_node, new_iESO, new_iESV)
    context.location.internal_node(Edge(context.st.internal_nodes[new_internal_node]))


@state_recorder
def _split_internal_edge(context):
    location = context.location
    edge = context.st.internal_nodes.data.iloc[location.internal_node_id]
    new_internal_node = context.st.internal_nodes.add_node(edge.parent,
                                                           edge.iESO,
                                                           edge.iESV,
                                                           edge.iESO + location.incoming_edge_offset)
    fix_suffix_link(context, new_internal_node)
    new_iESO = edge.iESO + location.incoming_edge_offset
    new_iESV = ord(context.data_source[int(new_iESO)])
    context.st.internal_nodes.update_internal_child(location.internal_node_id, new_internal_node, new_iESO, new_iESV)
    context.location.internal_node(Edge(context.st.internal_nodes[new_internal_node]))


@state_recorder
def _skip_count_down(context):
    while context.edge_value:
        first_value = ord(context.edge_value[0])
        edge = context.st.find_edge(context.location.internal_node_id, first_value)
        if edge is None:
            raise ValueError(f"{context.location}, cannot find {context.edge_value[0]}")
        if edge.is_internal:
            if len(edge) <= len(context.edge_value):
                context.location.internal_node(edge)
                context.edge_value = context.edge_value[len(edge):]
                if not context.edge_value:
                    if context.needs_suffix_link:
                        context.st.internal_nodes.set_suffix_link(context.needs_suffix_link, edge.id)
                        context.needs_suffix_link = None
            else:
                context.location.internal_edge(edge, len(context.edge_value))
                context.edge_value = ""
        else:
            context.location.leaf_edge(edge, len(context.edge_value))
            context.edge_value = ""

    context.q.append(_traverse_value)

@state_recorder
def _goto_suffix(context):
    location = context.location
    if location.on_internal_node:
        if location.internal_node_id != context.st.internal_nodes.root:
            internal_row = context.st.internal_nodes[location.internal_node_id]
            if internal_row.sL != -1:
                location.internal_node(Edge(context.st.internal_nodes[internal_row.sL]))
                context.q.appendleft(_traverse_value)
            else:
                context.needs_suffix_link = location.internal_node_id
                edge_value = context.data_source[internal_row.iESO:internal_row.iEEO]
                parent_row = context.st.internal_nodes[internal_row.parent]
                if internal_row.parent == context.st.internal_nodes.root:
                    edge_value = edge_value[1:]
                if edge_value:
                    context.edge_value = edge_value
                    context.location.internal_node(Edge(context.st.internal_nodes[parent_row.sL]))
                    context.q.appendleft(_skip_count_down)
                else:
                    context.st.internal_nodes.set_suffix_link(location.internal_node_id, context.st.internal_nodes.root)
                    context.needs_suffix_link = None
                    location.internal_node(Edge(context.st.root_node))
                    context.q.appendleft(_traverse_value)


@state_recorder
def _traverse_value(context):
    location = context.location
    if location.on_edge:
        if context.data_source[location.offset] == context.value:
            location.down(context.st.edge(location.internal_node_id, location.leaf_node_id))
            context.succeeded = True
        elif context.building:
            if location.on_internal_edge:
                context.q.append(_split_internal_edge)
            else:
                context.q.append(_split_leaf_edge)
            context.q.append(_add_leaf)
            context.q.append(_goto_suffix)
    else:
        edge = context.st.find_edge(location.internal_node_id, ord(context.value))
        if edge is not None:
            location.update(edge)
            context.succeeded = True
        elif context.building:
            context.q.append(_add_leaf)
            context.q.append(_goto_suffix)


class ValueProcessor:
    def __init__(self, st, location, data_source, builder=None):
        self.st = st
        self.location = location
        self.data_source = data_source
        self.offset = None
        self.value = None
        self.needs_suffix_link = None
        self.q = deque()
        self.building = (builder is not None)
        self.builder = builder
        self.succeeded = False

    def process(self, offset, value):
        self.offset = offset
        self.value = value
        self.q.append(_traverse_value)
        while self.q:
            fnstart = perf_counter()
            fn = self.q.popleft()
            self.succeeded = False
            fn(self)
            fnend = perf_counter()
            # print(f"    {fn.__name__}: {fnend - fnstart:.2f}")
            # self.builder.show_tree(f"After {fn.__name__}({offset}, {value})", indent=True)






TreeState = namedtuple('TreeState', 'fn offset value loc n_internal n_leaf')


def ndiff(title, before, after):
    if before != after:
        return f"{after - before} {title} added"
    else:
        return f""


class ContextRecorder:
    def __init__(self):
        self.before_steps = []
        self.after_steps = []
        self.current_offset = None
        self.current_value = None

    def step_processing(self, offset, value):
        self.current_offset = offset
        self.current_value = value

    def before(self, fn_name, location, number_internal_nodes, number_leaf_nodes):
        self.before_steps.append(TreeState(fn_name, self.current_offset, self.current_value, location,
                                           number_internal_nodes, number_leaf_nodes))

    def after(self, fn_name, location, number_internal_nodes, number_leaf_nodes):
        self.after_steps.append(TreeState(fn_name, self.current_offset, self.current_value, location,
                                          number_internal_nodes, number_leaf_nodes))

    def __repr__(self):
        MAX_RESULTS = 1
        result = [
            f"{before.fn}({before.offset}, {before.value}): {ndiff('Internal', before.n_internal, after.n_internal)}{ndiff('Leaf', before.n_leaf, after.n_leaf)}{before.loc - after.loc}"
            for before, after in zip(self.before_steps, self.after_steps)]
        if len(result) > MAX_RESULTS:
            result = result[-MAX_RESULTS:]
        return "\n".join(result)

    def history(self):
        result = [
            f"{before.fn}({before.offset}, {before.value}): {ndiff('Internal', before.n_internal, after.n_internal)}.{ndiff('Leaf', before.n_leaf, after.n_leaf)}.{'' if after.loc == before.loc else after.loc}"
            for before, after in zip(self.before_steps, self.after_steps)]
        return "\n".join(result)


def indent_lines(indent_flag, text):
    if not indent_flag:
        return text
    else:
        lines = text.split("\n")
        return "\n".join("    " + line for line in lines)


class TreeBuilder:
    SIZE_LIMIT = 10_000_000

    def __init__(self, data_source, size_limit=SIZE_LIMIT):
        internal_nodes = InternalNodes(empty_internal_df(size_limit), next_idx=1, data_source=data_source)
        leaf_nodes = LeafNodes(leaf_df(size_limit), next_idx=0, data_source=data_source, next_offset_to_process=0)
        self.st = SuffixTree(internal_nodes, leaf_nodes, data_source)
        self.data_source = data_source
        self.location = Location()
        self.location.internal_node(Edge(self.st.root_node))
        self.next_offset_to_process = 0
        self.create_node_data = defaultdict(list)
        self.node_needing_suffix_link = None
        self.context_recorder = ContextRecorder()
        self.value_processor = ValueProcessor(self.st, self.location, self.data_source, self)

    def register_before(self, fn_name):
        self.context_recorder.before(fn_name, copy(self.location), len(self.st.internal_nodes), len(self.st.leaf_nodes))

    def register_after(self, fn_name):
        self.context_recorder.after(fn_name, copy(self.location), len(self.st.internal_nodes), len(self.st.leaf_nodes))

    def build_tree(self):
        for offset, value in enumerate(self.data_source):
            self.process_value(offset, value)
        return self.st

    def process_value(self, offset, value):
        #self.show_tree(f"About to process: ({offset}, {value})")
        self.next_offset_to_process = offset + 1
        self.context_recorder.step_processing(offset, value)
        self.value_processor.process(offset, value)

    def show_tree(self, title=None, indent=False):
        self.st.leaf_nodes.next_offset_to_process = self.next_offset_to_process
        self.st.leaf_nodes.leaf_node_with_edge = self.location.leaf_node_id if self.location.on_leaf_edge else None
        self.st.leaf_nodes.incoming_edge_offset = self.location.incoming_edge_offset
        self.st.internal_nodes.internal_node_location = self.location.internal_node_id if self.location.on_internal_node else None
        self.st.internal_nodes.data_source = self.data_source
        if title:
            print(f"{title}")
        print(indent_lines(indent, f"{self.st}"))
        print(indent_lines(indent,
                           f"{self.data_source[:self.next_offset_to_process]}^{self.data_source[self.next_offset_to_process:]}"))
        print(indent_lines(indent, f"{self.location}"))
        print(indent_lines(indent, f"{self.context_recorder}"))

#
# if __name__ == "__main__":
#     parser = argparse.ArgumentParser()
#     parser.add_argument("test_string")
#     parser.add_argument("output_file")
#     parser.add_argument("expected_file")
#     args = parser.parse_args()
#
#     tbuilder = TreeBuilder(args.test_string)
#     #tbuilder.show_tree()
#     for o, v in enumerate(args.test_string):
#         #print(f".................................. process {o}, {v}")
#         tbuilder.process_value2(o, v)
#         #tbuilder.show_tree(f"Done processing {o}, {v}")
#         #print("stop here")
#     with open(args.output_file, "w") as out_file:
#         out_file.write(tbuilder.context_recorder.history())
#     with open(args.expected_file) as expected_results, open(args.output_file) as actual_results:
#         expected_lines = expected_results.readlines()
#         actual_lines = actual_results.readlines()
#         if len(expected_lines) != len(actual_lines):
#             print(f"*** FAILED, expected {len(expected_lines)} lines, got {len(actual_lines)}")
#         print(f"diff {args.expected_file} {args.output_file}")


if __name__ == "__main__":
    import doctest
    doctest.testmod()