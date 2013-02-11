#!/usr/bin/env python3
import argparse

from convert_sam import process_sam
from replace_art_read_ids import read_aln_positions

p = argparse.ArgumentParser()
p.add_argument('sam_input')
p.add_argument('aln_input')
p.add_argument('csv_output')
args = p.parse_args()

positions = read_aln_positions(args.aln_input)

with open(args.sam_input) as r, open(args.csv_output, 'w') as w:
    # TODO maybe use the CSV module for this
    w.write('predictions,labels\n')
    for line in r:
        if line.startswith('@'):
            continue
        data = process_sam(line)
        correct_aln = int(positions[data['qname']] == data['pos'])
        w.write('{},{}\n'.format(data['mapq'], correct_aln))
