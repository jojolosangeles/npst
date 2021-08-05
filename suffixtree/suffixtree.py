from suffixtree.tree_nodes import LeafNodes, InternalNodes
import pandas as pd

from suffixtree.location import Location

# TODO: this needs to replace Location or be merged into it
class Edge:
    """API for leaf or internal edge

    If leaf edge, data_row is:     ['parent', 'iESO', 'iESV'], index is suffix
    If internal edge, data_row is: ['parent', 'iESO', 'iESV', 'iEEO', 'sL'], index is node_id, root is 0"""

    def __init__(self, data_row):
        self.data_row = data_row
        self.is_internal = len(data_row) > 3
        self.is_leaf = not self.is_internal

    def suffix_offset(self):
        return self.data_row.name

    @property
    def id(self):
        return self.data_row.name

    @property
    def parent(self):
        return self.data_row.parent

    @property
    def iESO(self):
        return int(self.data_row.iESO)

    @property
    def iESV(self):
        return self.data_row.iESV

    @property
    def iEEO(self):
        return int(self.data_row.iEEO)

    def parent(self):
        return self.data_row.parent

    def __len__(self):
        try:
            return int(self.data_row.iEEO - self.data_row.iESO)
        except AttributeError:
            return 0


class SuffixTree:
    """SuffixTree data structure, either built from a data source, or loaded from a persistent copy"""
    def __init__(self, internal_nodes, leaf_nodes, data_source):
        self.internal_nodes = internal_nodes
        self.leaf_nodes = leaf_nodes
        self.data_source = data_source

    def info(self):
        return f'{len(self.leaf_nodes)} leaf nodes, {len(self.internal_nodes)} internal nodes'

    @classmethod
    def load_from_path(cls, path_prefix):
        """Load a previously built suffix tree, uses path_prefix to get
        internal node DataFrame, leaf node DataFrame,
        and the raw data used to build the suffix tree"""
        data_source_path = f'{path_prefix}.data'
        with open(data_source_path) as in_file:
            data_source = in_file.read()

        leaf_path = f'{path_prefix}_leaf.pickle'
        leaf_df = pd.read_pickle(leaf_path)
        return cls(InternalNodes.load_from_path(path_prefix, data_source), LeafNodes(leaf_df, data_source=data_source), data_source)

    def find_edge(self, parent_node_id, value):
        """Find an outgoing edge with a specific start value, return that Edge or None if not found"""
        df = self.internal_nodes.find_edge(parent_node_id, value)
        if len(df):
            return Edge(df.iloc[0])
        df = self.leaf_nodes.find_edge(parent_node_id, value)
        if len(df):
            return Edge(df.iloc[0])
        return None

    def edges_with_parent(self, internal_node_id):
        """Find all edges with a given internal node parent.

        This is used to get all the outgoing edges.
        See also find_edge, which gets an outgoing edge with a specific start value."""
        return self.internal_nodes.nodes_with_parent(internal_node_id), self.leaf_nodes.nodes_with_parent(
            internal_node_id)

    def depth_exceeds_limit(self, node, limit, offset_on_edge=0):
        edge = Edge(self.internal_nodes.data.iloc[node])
        total_depth = len(edge) if not offset_on_edge else offset_on_edge
        while edge.id != Location.ROOT and total_depth <= limit:
            node = edge.parent()
            edge = Edge(self.internal_nodes.data.iloc[node])
            total_depth += len(edge)
        return total_depth > limit

    def edge(self, internal_node_id, leaf_node_id):
        if internal_node_id:
            return Edge(self.internal_nodes.data.iloc[internal_node_id])
        else:
            return Edge(self.leaf_nodes.data.iloc[leaf_node_id])

    def values_at_location(self, location):
        """returns list of value, node_id, is_leaf_node_flag, incoming_edge_offset"""
        incoming_edge_offset = location.incoming_edge_offset + 1
        if location.on_internal_node:
            return self.internal_nodes.outgoing_values(location.internal_node_id)
        elif location.on_internal_edge:
            if self.internal_nodes.incoming_edge_length(location.internal_node_id) == location.incoming_edge_offset + 1:
                incoming_edge_offset = 0
            return (self.data_source[self.internal_nodes.incoming_edge_offset(location.internal_node_id) +
                                     location.incoming_edge_offset],
                    location.internal_node_id, False, incoming_edge_offset)
        elif location.on_leaf_edge:
            return (self.data_source[self.leaf_nodes.incoming_edge_offset(location.leaf_node_id) +
                                     location.incoming_edge_offset],
                    location.leaf_node_id, True, incoming_edge_offset)
        else:
            raise ValueError(f"Bad location {location}")

    @property
    def root(self):
        return self.internal_nodes.root

    @property
    def root_node(self):
        return self.internal_nodes.root_node

    @property
    def root_edge(self):
        return Edge(self.root_node)

    def __repr__(self):
        prefix = "^" if self.internal_nodes.internal_node_location == 0 else ""
        root_header = f"{prefix}ROOT of {self.data_source}"
        child_rows = []
        nodes_to_process = [(self.internal_nodes.root, 0)]
        while len(nodes_to_process):
            node, indentation = nodes_to_process.pop()
            spacing = '  ' * indentation
            if node != 0:
                child_rows.append(f"{spacing}{self.internal_nodes.to_string(node, self.data_source)}")
            leaf_children = self.leaf_nodes.nodes_with_parent(node)
            child_spacing = spacing + '  '
            for idx, row in leaf_children.iterrows():
                child_rows.append(f"{child_spacing}{self.leaf_nodes.to_string(row.name, self.data_source)}")
            internal_children = self.internal_nodes.nodes_with_parent(node)
            for idx, row in internal_children.iterrows():
                if row.name != 0:
                    nodes_to_process.append((row.name, indentation + 1))
        rows = '\n'.join(child_rows)
        result = f"{root_header}\n{rows}"
        return result

    def get_suffixes(self, location):
        if location.on_leaf_edge:
            #edge = Edge(self.leaf_nodes.data.iloc[location.leaf_node_id])
            return [location.edge.suffix_offset()]
        else:
            suffixes = []
            nodes_to_check = [location.internal_node_id]
            while nodes_to_check:
                internal_node_id = nodes_to_check.pop()
                leafs_below = self.leaf_nodes.nodes_with_parent(internal_node_id)
                internal_below = self.internal_nodes.nodes_with_parent(internal_node_id)
                if len(leafs_below):
                    suffixes.extend(leafs_below.index)
                if len(internal_below):
                    nodes_to_check.extend(internal_below.index)
            return sorted(suffixes)


if __name__ == "__main__":
    import doctest
    doctest.testmod()