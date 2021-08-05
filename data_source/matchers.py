"""
stream -> words
- min_word_size 5
- max_word_size 10
- mapping { "GC": " ", "XY": " ", "AB": " "

test stream:
xxGCxx7xxxxXYaaabbbccc12dABa4bcXYxxxbbbcc9


for offset,word in yield_mapping(mapping, test_stream):

"""
class Matcher:
    def __init__(self, key, replacement):
        self.key = key
        self.replacement = replacement
        self.itr = iter(key)
        self.current_value = next(self.itr)

    def matches(self, value):
        if self.current_value == value:
            try:
                self.current_value = next(self.itr)
                return False
            except StopIteration:
                self.reset()
                return True
        else:
            self.reset()
            return False

    def reset(self):
        self.itr = iter(self.key)
        self.current_value = next(self.itr)


def yield_mapping(mapping, stream):
    matchers = { key: Matcher(key, mapping[key]) for key in mapping.keys() }
    word = ""
    for offset, value in enumerate(stream):
        word = f"{word}{value}"
        for matcher_key, matcher in matchers.items():
            if matcher.matches(value):
                word = word[:-len(matcher_key)]
                yield offset + 1 - len(matcher_key) - len(word), word, matchers[matcher_key]
                word = ""


def stream_mapper(stream, mappings):
    next_offset_to_process = 0
    for key, (offset, word, matcher) in enumerate(yield_mapping(mappings, test_string)):
        yield f'{word}{matcher.replacement}'
        next_offset_to_process = offset + len(word) + len(matcher.key)
    if next_offset_to_process < len(stream):
        yield stream[next_offset_to_process:]


def map_string(stream, mappings):
    return ''.join(stream_mapper(stream, mappings))


if __name__ == "__main__":
    test_string = "xxGCxx7xxxxXYaaabbbccc12dABa4bcXYxxxbbbcc9"
    mappings = { "GC": " ", "XY": " ", "AB": " "}
    print(test_string)
    for key, (offset, word, matcher) in enumerate(yield_mapping(mappings, test_string)):
        print(f'{key}: {offset}, "{word}", "{matcher.key}" -> "{matcher.replacement}"')

    ms = map_string(test_string, mappings)
    expected_mapped_result = "xx xx7xxxx aaabbbccc12d a4bc xxxbbbcc9"

    print("Expected: ", expected_mapped_result)
    print("Got     : ", ms)
    assert(ms == expected_mapped_result)
