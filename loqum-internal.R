#!/usr/bin/env r
if (is.null(argv)) {
	cat('loqum-internal.R should not be called directly\n')
	q()
}

source('common.R')

predict.quals = function(csv.input, model.filename, csv.output) {
	load(model.filename)
	data = read.csv(csv.input)
	preds = data.frame(predict(lr, newdata=data, type='response'))
	row.names(preds) = data$read_id
	write.csv(preds, file=csv.output)
}

if (argv[1] == 'predict') {
	predict.quals(argv[2], argv[3], argv[4])
}
