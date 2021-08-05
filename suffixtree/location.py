attrs = "on_internal_node on_internal_edge on_leaf_edge incoming_edge_start_offset incoming_edge_end_offset incoming_edge_offset internal_node_id leaf_node_id".split()


class Location:
    ROOT = 0

    def __init__(self):
        self.edge = None
        self.on_internal_node = False
        self.on_internal_edge = False
        self.on_leaf_edge = False
        self.incoming_edge_start_offset = 0
        self.incoming_edge_end_offset = 0
        self.incoming_edge_offset = 0   # >0 for edge locations
        self.internal_node_id = None       # internal node id if on_internal_node or on_internal_edge
        self.leaf_node_id = None           # leaf node id if on_leaf_edge

    def internal_node(self, edge):
        self.edge = edge
        node = edge.id
        self.on_internal_node = True
        self.on_internal_edge = False
        self.on_leaf_edge = False
        self.incoming_edge_start_offset = 0
        self.incoming_edge_end_offset = 0
        self.incoming_edge_offset = 0
        self.internal_node_id = node
        self.leaf_node_id = None

    def internal_edge(self, edge, edge_offset=1):
        self.edge = edge
        node = edge.id

        if edge_offset == len(edge):
            self.internal_node(edge)
        else:
            self.on_internal_node = False
            self.on_internal_edge = True
            self.on_leaf_edge = False
            self.incoming_edge_start_offset = int(edge.iESO)
            self.incoming_edge_end_offset = int(edge.iEEO)
            self.incoming_edge_offset = edge_offset
            self.internal_node_id = node
            self.leaf_node_id = None

    def leaf_edge(self, edge, incoming_edge_offset=1):
        self.edge = edge
        node = edge.id
        self.on_internal_node = False
        self.on_internal_edge = False
        self.on_leaf_edge = True
        self.incoming_edge_start_offset = int(edge.iESO)
        self.incoming_edge_end_offset = -1
        self.incoming_edge_offset = int(incoming_edge_offset)
        self.internal_node_id = None
        self.leaf_node_id = node

    def inc_leaf_edge(self):
        self.incoming_edge_offset += 1

    def update(self, edge):
        if edge.is_internal:
            if len(edge) == 1:
                self.internal_node(edge)
            else:
                self.internal_edge(edge)
        else:
            self.leaf_edge(edge, 1)

    def down(self, edge):
        """on an edge, going down one value"""
        self.incoming_edge_offset += 1
        if self.incoming_edge_offset == len(edge):
            self.internal_node(edge)

    @property
    def offset(self):
        return self.incoming_edge_start_offset + self.incoming_edge_offset

    @property
    def on_edge(self):
        return self.on_leaf_edge or self.on_internal_edge

    def __repr__(self):
        if self.on_internal_node:
            return f'Internal i{self.internal_node_id}'
        elif self.on_leaf_edge:
            return f'Leaf s{self.leaf_node_id}, iESO={self.incoming_edge_start_offset}, iEO={self.incoming_edge_offset}'
        elif self.on_internal_edge:
            return f'Internal Edge i{self.internal_node_id}, iESO={self.incoming_edge_start_offset}, iEO={self.incoming_edge_offset}'
        else:
            raise ValueError

    def __eq__(self, other):
        for attr in attrs:
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True

    def __sub__(self, other):
        result = []
        for attr in attrs:
            if getattr(self, attr) != getattr(other, attr):
                result.append(f"{attr}: {getattr(self, attr)} -> {getattr(other,attr)}")
        indentation = "    "
        if result:
            return f"Location:\n{indentation}" + f'\n{indentation}'.join(result)
        else:
            return ""
