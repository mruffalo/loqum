#!/usr/bin/env r
if (is.null(argv) | length(argv) < 4) {
	cat("Usage: loqum.r train_filename validation_filename_base\n")
	cat("               tool_name output_filename_base [filename_addition]\n")
	q()
}

source('common.R')

if (is.na(argv[5])) {
	argv[5] = ''
}

lr_eval_separate(argv[1], argv[2], argv[3], argv[4], argv[5])
