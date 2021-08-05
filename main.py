import sys
from suffixtree.builder.tree_builder import TreeBuilder
from collections import defaultdict, namedtuple

CheckLine = namedtuple('CheckLine',
                       'alg_location offset_processed internal_node_count leaf_node_count location_on_node location_on_leaf_edge location_on_internal_edge')


def offset(line):
    data = line.split()
    return int(data[0])


def checks(data):
    return CheckLine(data[0], int(data[1]), int(data[2]), int(data[3]), data[4] == 'True', data[5] == 'True', data[6] == 'True')


class BuildChecker:
    def __init__(self, lines):
        self.checklines = defaultdict(list)
        for line in lines:
            if len(line) and line[0] != '#':
                line_data = line.strip().split()
                key = int(line_data[1])
                self.checklines[key].append(checks(line_data))

    def verify_value(self, expected, actual, check_type):
        if expected != actual:
            print(f"*** FAIL {check_type} ***, expected {expected}, actual {actual}")

    def check(self, offset, tb, st, location):
        checklines = self.checklines.get(offset, [])
        print(f"checklines={checklines}")
        for check in checklines:
            # alg_location offset_processed internal_node_count leaf_node_count location_on_node location_on_leaf_edge location_on_internal_edge
            if check.alg_location == "processed":
                self.verify_value(check.internal_node_count, len(st.internal_nodes), "Internal Node Count")
                self.verify_value(check.leaf_node_count, len(st.leaf_nodes), "Leaf Node Count")
                self.verify_value(check.location_on_node, location.on_internal_node, "On Internal Node")
                self.verify_value(check.location_on_leaf_edge, location.on_leaf_edge, "On Leaf Edge")
                self.verify_value(check.location_on_internal_edge, location.on_internal_edge, "On Internal Edge")
            else:
                print(check)
                recorded_data = tb.create_node_data[offset]
                print("recorded_data")
                print(recorded_data)
                print("that was it")
                for record in recorded_data:
                    if record.alg_location == check.alg_location:
                        print(f"Found check, comparing {record} to {check}")
                        if record != check:
                            print("*** MASSIVE FAIL ***")



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python main.py test_str check_file_name_in_tests_folder")
        exit(0)
    test_str = sys.argv[1]
    with open(f'tests/{sys.argv[2]}') as in_file:
        bc = BuildChecker(in_file.readlines())
    tb = TreeBuilder(test_str)
    data_source_iter = enumerate(iter(test_str))
    while True:
        line = input('>>> ')
        if not len(line):
            offset, value = next(data_source_iter)
            tb.process_value(offset, value)
            bc.check(offset, tb, tb.st, tb.location)
        elif line[0] == 't':
            tb.show_tree()
        else:
            try:
                skips = int(line)
                for _ in range(skips):
                    offset, value = next(data_source_iter)
                    tb.process_value(offset, value)
                    bc.check(offset, tb, tb.st, tb.location)
            except ValueError:
                print(f"..ignoring: {line}")

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
