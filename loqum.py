#!/usr/bin/env python3
from argparse import ArgumentParser, FileType
from csv import DictWriter
import logging
from math import ceil

from convert_sam import count_mappings, csv_fields, convert_line

logging.basicConfig(format='{asctime}|{levelname}|{message}',
    level=logging.INFO, style='{')
info = logging.info

TEMP_FILE_READ_COUNT = 50000

def divide_sam_file(sam_filename, mapping_counts):
    """
    Processes a SAM file: reads line-by-line and writes lines in groups of
    TEMP_FILE_READ_COUNT to temporary files (both raw and converted).

    Yields 2-tuples:
    [0] SAM output filename
    [1] CSV output filename, suitable for loqum-internal.R

    Header lines aren't treated specially for ease of implementation.
    """
    sam_output = None
    csv_output = None
    csv_writer = None
    sam_output_filename = None
    csv_output_filename = None
    with open(sam_filename) as r:
        for i, line in enumerate(r):
            if not i % TEMP_FILE_READ_COUNT:
                if sam_output:
                    sam_output.close()
                    csv_output.close()
                    yield sam_output_filename, csv_output_filename
                sam_output_filename = '{}.{}'.format(sam_filename, i // TEMP_FILE_READ_COUNT)
                csv_output_filename = '{}.{}.csv'.format(sam_filename, i // TEMP_FILE_READ_COUNT)
                sam_output = open(sam_output_filename, 'w')
                csv_output = open(csv_output_filename, 'w', newline='')
                csv_writer = DictWriter(csv_output, csv_fields)
            sam_output.write(line)
            csv_writer.writerow(convert_line(line, mapping_counts))

def loqum_run(sam_file, csv_output):
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
    p.add_argument('sam_file_input', type=FileType('r'), help=('SAM '
        'file with mapping qualities that should be replaced by LoQuM.'))
    p.add_argument('saved_model_file', type=FileType('rb'), help=('RData '
        'file containing a "glm" model that is used to recalibrate mapping'
        'quality scores.'))
    p.add_argument('sam_file_output')
    args = p.parse_args()
    # We don't need the saved model file; we only care that it exists
    args.saved_model_file.close()
