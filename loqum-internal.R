#!/usr/bin/env r
if (is.null(argv)) {
	cat('loqum-internal.R should not be called directly\n')
	q()
}

source('common.R')

train = function(csv.input, model.filename, csv.output) {
	load(model.filename)
	data = read.csv(csv.input)
	preds = predict(lr, newdata=validation, type='response')
	write.csv(preds, file='csv.output')
}
