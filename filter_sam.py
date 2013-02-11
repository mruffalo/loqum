#!/usr/bin/env python3
import argparse

p = argparse.ArgumentParser()
p.add_argument('orig_sam_file')
p.add_argument('output_sam_file')
args = p.parse_args()

with open(args.orig_sam_file) as r, open(args.output_sam_file, 'w') as w:
    for line in r:
        pieces = line.split()
        if len(pieces) < 10 or 'N' not in pieces[9]:
            w.write(line)
