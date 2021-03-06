#!/usr/bin/env python3
from argparse import ArgumentParser, FileType
from csv import DictWriter
import logging
from math import ceil
from os import devnull, remove
from shutil import copyfileobj
from subprocess import check_call

from convert_sam import count_mappings, csv_fields, convert_line
from replace_sam_quals import replace_quals

logging.basicConfig(format='{asctime}|{levelname}|{message}',
    level=logging.INFO, style='{')
info = logging.info

TEMP_FILE_READ_COUNT = 100000
CONCATENATE_BUFFER_SIZE = 2 ** 16

LOQUM_INTERNAL_COMMAND = ('./loqum-internal.R', '{command}', '{csv_input}',
    '{model_filename}', '{csv_output}')

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
                csv_writer.writerow(dict(zip(csv_fields, csv_fields)))
            sam_output.write(line)
            if not line.startswith('@'):
                data = convert_line(line, mapping_counts)
                if data:
                    csv_writer.writerow(data)
        sam_output.close()
        csv_output.close()
        yield sam_output_filename, csv_output_filename

def loqum_run_partial(sam_filename, model_filename, csv_filename):
    """
    Runs LoQuM on a CSV file describing read mappings. Deletes the SAM and
    CSV files afterward.

    Writes a new SAM file with recalibrated mapping qualites to a temporary
    file. Returns the temporary SAM filename.
    """
    sam_temp_filename = '{}.new'.format(sam_filename)
    csv_temp_filename = '{}.predictions'.format(csv_filename)
    loqum_run_data = {
        'command': 'predict',
        'csv_input': csv_filename,
        'model_filename': model_filename,
        'csv_output': csv_temp_filename,
    }
    command = [piece.format(**loqum_run_data) for piece in LOQUM_INTERNAL_COMMAND]
    with open(devnull) as sink:
        check_call(command, stdout=sink, stderr=sink)
    replace_quals(sam_filename, csv_temp_filename, sam_temp_filename)
    remove(sam_filename)
    remove(csv_filename)
    remove(csv_temp_filename)
    return sam_temp_filename

def loqum_run(sam_file_input, model_filename, sam_file_output):
    info('Counting mappings in {}'.format(sam_file_input))
    mapping_counts, total_count = count_mappings(sam_file_input)
    info('Read {} total mappings'.format(total_count))
    if mapping_counts:
        info('Reads with the most mappings:')
        for item, count in mapping_counts.most_common(5):
            info('{}: {}'.format(item, count))
    else:
        info('No reads have more than one mapping')
    progress_output_count = 20
    progress_output_multiple = total_count // progress_output_count
    with open(sam_file_output, 'w') as sam_w:
        for i, (sam_filename_temp, csv_filename_temp) in enumerate(
                divide_sam_file(sam_file_input, mapping_counts)):
            lines_processed = i * TEMP_FILE_READ_COUNT
            info('Processing {}'.format(sam_filename_temp))
            temp_filename = loqum_run_partial(sam_filename_temp,
                model_filename, csv_filename_temp)
            with open(temp_filename) as temp_r:
                copyfileobj(temp_r, sam_w, CONCATENATE_BUFFER_SIZE)
            remove(temp_filename)
            if not i % progress_output_multiple:
                info('Approx. {}% done'.format(ceil(
                    (lines_processed / total_count) * 100)))

if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('sam_file_input', help=('SAM '
        'file with mapping qualities that should be replaced by LoQuM.'))
    p.add_argument('saved_model_file', type=FileType('rb'), help=('RData '
        'file containing a "glm" model that is used to recalibrate mapping'
        'quality scores.'))
    p.add_argument('sam_file_output')
    args = p.parse_args()
    # We don't need the saved model file; we only care that it exists
    args.saved_model_file.close()
    loqum_run(args.sam_file_input, args.saved_model_file.name,
        args.sam_file_output)
