source('common.R')

pr_plot = function(filename_base, tool_name) {
	data_filename = paste(c(data_dir, filename_base, '-raw.csv'), collapse='')
	cat('Reading ', data_filename, '\n')
	data = read.csv(data_filename)
	pred = prediction(data$predictions, data$labels)

	pr_perf = performance(pred, 'prec', 'rec')
	pr_filename = paste(c(output_dir, filename_base, '-pr-raw.pdf'), collapse='')
	cat('Plotting precision vs. recall in', pr_filename, '\n')
	pdf(pr_filename)
	pr_title = paste(c(tool_name, ': Precision vs. Recall, Raw Map. Qual.'),
			collapse='')
	par(cex=cex.const, mar=mar.const)
	plot(pr_perf, colorize=TRUE, xlim=c(0, 1), ylim=c(0, 1),
			main=pr_title)
	dev.off()

	roc_perf = performance(pred, 'tpr', 'fpr')
	roc_filename = paste(c(output_dir, filename_base, '-roc-raw.pdf'), collapse='')
	cat('Plotting ROC in', roc_filename, '\n')
	pdf(roc_filename)
	roc_title = paste(c(tool_name, ': ROC, Raw Map. Qual.'),
			collapse='')
	par(cex=cex.const, mar=mar.const)
	plot(roc_perf, colorize=TRUE, main=roc_title)
	dev.off()
}

pr_plot('bwa-art', 'BWA')
pr_plot('nva-art', 'Novoalign')
pr_plot('soap-art', 'SOAP2')
