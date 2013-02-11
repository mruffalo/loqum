#!/usr/bin/env python3
from argparse import ArgumentParser

from Bio import SeqIO

from sim_log import LazyInitLogger

log = LazyInitLogger()

aln_info_indicator = '>'
def read_aln_positions(aln_filename):
    """
    Reads a .aln file produced by ART and returns a mapping from read IDs to positions
    """
    positions = {}
    with open(aln_filename) as f:
        for line in f:
            if line.startswith(aln_info_indicator):
                chrom, read_id, pos, strand = line.lstrip(aln_info_indicator).split()
                # ART reports 0-offset positions, BWA returns 1-offset
                positions[read_id] = int(pos) + 1
    return positions

def get_read_id(old_id, position):
    """
    As produced by ART, old_id is of the form
    REF_SEQ_NAME-position
    where REF_SEQ_NAME is an arbitrary string, and position is
    an integer.
    """
    read_index = old_id.rsplit('-', 1)[1]
    return '{}:READ_POS={}'.format(read_index, position)

def get_adjusted_seqs(fastq_input, positions):
    with open(fastq_input) as r:
        s = SeqIO.parse(r, 'fastq')
        for seq in s:
            seq.id = seq.description = get_read_id(seq.id, positions[seq.id])
            yield seq

def replace_ids(fastq_input, aln_input, fastq_output):
    positions = read_aln_positions(aln_input)
    with open(fastq_output, 'w') as w:
        SeqIO.write(get_adjusted_seqs(fastq_input, positions), w, 'fastq')

if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('fastq_input')
    p.add_argument('aln_input')
    p.add_argument('fastq_output')
    args = p.parse_args()
    replace_ids(args.fastq_input, args.aln_input, args.fastq_output)
