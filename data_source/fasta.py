from Bio import SeqIO


def get_fasta_data(seq_file, slice_spec):
    SEGMENT_SIZE = 100_000
    print(f"seq_file={seq_file}, slice_spec={slice_spec}")
    seq_object = SeqIO.read(seq_file, "fasta")
    sequence = seq_object.seq
    if slice_spec:
        data = slice_spec.split(':')
        min_bound = int(data[0])
        max_bound = int(data[1])
        sequence = sequence[(min_bound*SEGMENT_SIZE):(max_bound*SEGMENT_SIZE)]
    return sequence


def get_fasta_data_str(seq_file, slice_spec):
    SEGMENT_SIZE = 100_000
    print(f"seq_file={seq_file}, slice_spec={slice_spec}")
    seq_object = SeqIO.read(seq_file, "fasta")
    sequence = seq_object.seq
    if slice_spec:
        data = slice_spec.split(':')
        min_bound = int(data[0])
        max_bound = int(data[1])
        sequence = sequence[(min_bound*SEGMENT_SIZE):(max_bound*SEGMENT_SIZE)]
    return str(sequence)