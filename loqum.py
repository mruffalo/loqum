#!/usr/bin/env python3
from argparse import ArgumentParser, FileType
from csv import DictWriter
import logging
from math import ceil
from os.path import isfile

from .convert_sam import count_mappings, csv_fields, convert_line

logging.basicConfig(format='{asctime}|{levelname}|{message}',
    level=logging.INFO, style='{')
info = logging.info

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
    with open(csv_output, 'w', newline='') as w:
        cw = DictWriter(w, csv_fields)
        cw.writerow(dict(zip(csv_fields, csv_fields)))
        for i, line in enumerate(sam_file):
            if line.startswith('@'):
                continue
            data = convert_line(line, mapping_counts)
            if data:
                cw.writerow(data)
            if not i % progress_output_multiple:
                info('Approx. {}% done'.format(ceil((i / total_count) * 100)))

if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('sam_file_input', type=FileType('r'))
    p.add_argument('saved_model_file', type=FileType('rb'))
    p.add_argument('sam_file_output')
    args = p.parse_args()
    # We don't need the saved model file; we only care that it exists
    args.saved_model_file.close()
