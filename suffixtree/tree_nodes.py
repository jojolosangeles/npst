import numpy as np
import pandas as pd


def empty_internal_df(n):
    return pd.DataFrame(np.zeros((n, 5), dtype=int), columns=['parent', 'iESO', 'iESV', 'iEEO', 'sL'])


class NodeList:
    def __init__(self, df, next_idx=None, data_source=None):
        self.data = df
        self.data_source = data_source
        if next_idx is None:
            x = self.data[self.data.iESO != 0]
            idx = 0 if not len(x) else max(x.index)
            self.next_idx = idx + 1
        else:
            self.next_idx = next_idx

    def to_pickle(self, filepath):
        df = self.data[:self.next_idx]
        df.to_pickle(f'{filepath}.pickle')

    def nodes_with_parent(self, parent):
        df = self.data.iloc[:self.next_idx]
        return df[df.parent == parent]

    def find_edge(self, parent_id, value):
        df = self.data.iloc[:self.next_idx]
        return df[(df.parent == parent_id) & (df.iESV == value)]

    def __len__(self):
        return self.next_idx

    def __getitem__(self, item):
        return self.data.iloc[item]


class InternalNodes(NodeList):
    def __init__(self, df, next_idx=None, data_source=None):
        """Root is at offset 0, all values 0"""
        super().__init__(df, next_idx, data_source)
        self.root = 0
        # self.data.at[0, 'parent'] = -1

        # just for repr
        self.internal_node_location = None

    @classmethod
    def load_from_path(cls, path_prefix, data_source):
        internal_path = f'{path_prefix}_internal.pickle'
        internal_df = pd.read_pickle(internal_path)
        return InternalNodes(internal_df, next_idx=None, data_source=data_source)

    @property
    def root_node(self):
        return self.data.iloc[0]

    def __getitem__(self, item):
        return self.data.iloc[item]

    def __repr__(self):
        nodes = [self.to_string(i, self.data_source) for i in range(self.next_idx)]
        return "\n".join(nodes)

    def add_node(self, parent, iESO, iESV, iEEO, sL=-1):
        """parent, incoming_edge_start_offset, incoming_edge_start_value, incoming_edge_end_offset, suffix_link"""
        self.data.iloc[self.next_idx] = (parent, iESO, iESV, iEEO, sL)
        self.next_idx += 1
        return self.next_idx - 1

    def update_internal_child(self, original_child, new_parent, new_iESO, new_iESV):
        """When an internal node is added, an internal edge is split,
        'add_node' adds the new internal node, this method updates the
        original child node with its new parent, iESO, iESV"""
        self.data.at[original_child, 'parent'] = new_parent
        self.data.at[original_child, 'iESO'] = new_iESO
        self.data.at[original_child, 'iESV'] = new_iESV

    def set_suffix_link(self, node, link_value):
        self.data.at[node, 'sL'] = link_value

    def to_string(self, row_idx, data_source):
        if row_idx >= self.next_idx:
            return ''
        else:
            row = self.data.iloc[row_idx]
            prefix = "^" if row_idx == self.internal_node_location else ""
            data_str = data_source[row.iESO:row.iEEO]
            return f"{data_str} {prefix} p.{row.parent} sl.{row.sL} (iESO={row.iESO}, iEEO={row.iEEO}, iESV='{chr(row.iESV)}') .{row_idx}."


def leaf_df(n):
    return pd.DataFrame(np.zeros((n, 3), dtype=int), columns=['parent', 'iESO', 'iESV'])


class LeafNodes(NodeList):
    def __init__(self, df, next_idx=None, data_source=None, next_offset_to_process=None):
        super().__init__(df, next_idx, data_source)
        # these are only for __repr__
        self.next_offset_to_process = next_offset_to_process
        self.leaf_node_with_edge = None
        self.incoming_edge_offset = None

    def __repr__(self):
        nodes = [self.to_string(i, self.data_source) for i in range(self.next_idx)]
        return "\n".join(nodes)

    def add(self, parent_node, iESO, iESV):
        self.data.iloc[self.next_idx] = (parent_node, iESO, iESV)
        self.next_idx += 1

    def update_leaf_child(self, original_child, new_parent, new_iESO, new_iESV):
        """When an internal node is added, an internal edge is split,
        'add_node' adds the new internal node, this method updates the
        original child node with its new parent, iESO, iESV"""
        self.data.iloc[original_child] = (new_parent, new_iESO, new_iESV)

    def to_string(self, row_idx, data_source):
        if row_idx >= len(self):
            return ''
        else:
            row = self.data.iloc[row_idx]
            data_str = data_source[row.iESO:]
            if self.next_offset_to_process and self.leaf_node_with_edge==row.name and self.incoming_edge_offset:
                boundary = row.iESO + self.incoming_edge_offset
                data_str = f'{data_source[row.iESO:boundary]}^{data_source[boundary:]}'
            return f"{data_str} p.{row.parent} (iESO={row.iESO}, iESV='{chr(row.iESV)}') -{row_idx}-"


