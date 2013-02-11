#!/usr/bin/env python3
import argparse
from binascii import unhexlify
from collections import Counter
from functools import lru_cache
from math import ceil
import csv
import re
import logging

import numpy as np
from scipy import stats

logging.basicConfig(format='%(asctime)s|%(levelname)s|%(message)s', level=logging.INFO)
info = logging.info

cigar = re.compile(r'(\d+)([MIDS=X])')
csv_fields = [
    'read_id',
    'map_qual',
    'matches',
    'insertions',
    'deletions',
    'mismatches',
    'n_count',
    'base_qual_slope',
    'base_qual_intercept',
    'base_qual_r_value',
    'base_qual_p_value',
    'base_qual_std_err',
    'mapping_count',
    'correct',
]

# Field names come from the SAM description
sam_fields = [
    ('qname', str),
    ('flag', int),
    ('rname', str),
    ('pos', int),
    ('mapq', int),
    ('cigar', str),
    ('rnext', str),
    ('pnext', int),
    ('tlen', int),
    ('seq', str),
    ('qual', str)
]

def hex_str_to_bytes(hex_str):
    return unhexlify(hex_str.encode())

def csv_to_int_array(csv_str):
    return np.array([int(x) for x in csv_str[1:].split(',')])

flag_types = {
    'A': str,
    'i': int,
    'f': float,
    'Z': str,
    'H': hex_str_to_bytes,
    'B': csv_to_int_array,
}

def process_sam(line):
    """
    Converts a SAM line into a dict which maps each element of sam_fields
    to the appropriate data. Types are handled as the second field of each
    element of sam_fields.
    """
    pieces = line.rstrip('\n').split('\t')
    if len(pieces) < len(sam_fields):
        raise ValueError('malformed SAM line, possibly header?')
    data = {}
    for piece, (name, type_func) in zip(pieces, sam_fields):
        data[name] = type_func(piece)
    flags = {}
    for flag in pieces[len(sam_fields):]:
        name, type_code, value = flag.split(':')
        flags[name] = flag_types[type_code](value)
    data['flags'] = flags
    return data

def convert_qual(quality_char, offset=33):
    return ord(quality_char) - offset

def get_read_pos(identifier):
    pos_slash_zero = identifier.split('=')
    return int(pos_slash_zero[1].split('/')[0])

def linreg_qual(quality_string):
    """
    Returns slope, intercept, r_value, p_value, std_err
    from the output of scipy.stats.linregress
    """
    positions = np.arange(len(quality_string))
    qualities = np.array([convert_qual(char) for char in quality_string])
    return stats.linregress(positions, qualities)

def count_mappings(sam_filename):
    """
    Returns a dict mapping read IDs to the number of times the read appears in the file
    """
    # If the file has no lines, correctly return 0
    i = -1
    c = Counter()
    with open(sam_filename) as f:
        # This was so elegant:
        #   return Counter(line.split()[0] for line in f)
        # Too bad I kind of need a total mapping count also
        for i, line in enumerate(f):
            c[line.split()[0]] += 1
    return c, i + 1

# There aren't many distinct CIGAR strings in a SAM file
@lru_cache(maxsize=50)
def get_cigar_counts(cigar_str):
    cigar_pieces = list(filter(lambda s: s, cigar.split(cigar_str)))
    cigar_counts = Counter()
    for count, operation in zip(cigar_pieces[::2], cigar_pieces[1::2]):
        cigar_counts[operation] += int(count)
    return cigar_counts

def convert_line(line, mapping_counts):
    """
    Process a SAM line into a dict of features.
    """
    data = process_sam(line)
    if data['flag'] & 0x4:
        # If this read wasn't mapped, ignore it completely
        return None
    char_counts = Counter(data['seq'])
    cigar_counts = get_cigar_counts(data['cigar'])
    position = get_read_pos(data['qname'])
    correct_aln = int(position == data['pos'])
    slope, intercept, r_value, p_value, std_err = linreg_qual(data['qual'])
    return {
        'read_id': data['qname'],
        'map_qual': data['mapq'],
        # TODO un-hardcode these
        'matches': cigar_counts['M'],
        'insertions': cigar_counts['I'],
        'deletions': cigar_counts['D'],
        'mismatches': cigar_counts['X'],
        'n_count': char_counts['N'],
        'base_qual_slope': slope,
        'base_qual_intercept': intercept,
        'base_qual_r_value': r_value,
        'base_qual_p_value': p_value,
        'base_qual_std_err': std_err,
        'mapping_count': mapping_counts[data['qname']],
        'correct': correct_aln,
    }

def convert_sam(sam_file, csv_output):
    info('Counting mappings in {}'.format(sam_file))
    mapping_counts, total_count = count_mappings(sam_file)
    info('Read {} distinct mappings'.format(len(mapping_counts)))
    info('Reads with the most mappings:')
    for item, count in mapping_counts.most_common(5):
        info('{}: {}'.format(item, count))
    info('Writing CSV output to {}'.format(csv_output))
    progress_output_count = 10
    progress_output_multiple = total_count // progress_output_count
    with open(sam_file) as r, open(csv_output, 'w') as w:
        cw = csv.DictWriter(w, csv_fields)
        cw.writerow(dict(zip(csv_fields, csv_fields)))
        for i, line in enumerate(r):
            if line.startswith('@'):
                continue
            data = convert_line(line, mapping_counts)
            if data:
                cw.writerow(data)
            if not i % progress_output_multiple:
                info('Approx. {}% done'.format(ceil((i / total_count) * 100)))

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('sam_file')
    p.add_argument('csv_output')
    p.add_argument('--cache-linreg', action='store_true')
    args = p.parse_args()
    if args.cache_linreg:
        linreg_qual = lru_cache(maxsize=None)(linreg_qual)
    convert_sam(args.sam_file, args.csv_output)
