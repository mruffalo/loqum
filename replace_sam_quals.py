#!/usr/bin/env python3
from argparse import ArgumentParser
from csv import reader
import logging
from math import floor, log10

from sim_log import LazyInitLogger

log = LazyInitLogger(level=logging.INFO)

def get_quals(f):
    r = reader(f)
    # Skip header line:
    next(r)
    for items in r:
        yield items[0], items[1]

def replace_qual(sam_line, new_qual_str):
    pieces = sam_line.strip().split('\t')
    qual = floor(0.5 + -10 * log10(1 - float(new_qual_str)))
    pieces[4] = qual
    return '\t'.join(str(piece) for piece in pieces)

def is_unmapped(sam_line):
    return int(sam_line.split()[1]) & 0x4

def replace_quals(sam_file, qual_file, sam_output):
    with open(sam_file) as s, open(qual_file) as c:
        with open(sam_output, 'w') as w:
            qual_values = get_quals(c)
            for sam_line in s:
                if sam_line.startswith('@') or is_unmapped(sam_line):
                    log.debug('Writing raw SAM line: {}'.format(sam_line))
                    w.write(sam_line)
                    continue
                read_id, new_qual_str = next(qual_values)
                assert read_id == sam_line.split()[0]
                new_sam_line = replace_qual(sam_line, new_qual_str)
                log.debug('Writing adjusted SAM line: {}'.format(new_sam_line))
                print(new_sam_line, file=w)

if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('sam_file')
    p.add_argument('qual_file')
    p.add_argument('sam_output')
    args = p.parse_args()
    replace_quals(args.sam_file, args.qual_file, args.sam_output)
