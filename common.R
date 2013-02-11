library(boot)
library(ROCR)
library(doParallel)

registerDoParallel()

mar.const = c(4, 4, 4, 2) + 0.1
cex.const = 1.4

data_dir = 'data/'
output_dir = 'output/'

mapping_lr = function(raw_data) {
	df = data.frame(raw_data)

	map_lr = glm(formula = correct ~ map_qual + matches +
		insertions + deletions + mismatches + n_count +
		base_qual_slope + base_qual_intercept + base_qual_r_value +
		base_qual_p_value + base_qual_std_err + mapping_count,
		data = df,
		family = binomial("logit"))

	return(map_lr)
}

get_midpoint = function(level) {
	start_pattern = '\\(([0-9.]+)'
	end_pattern = '([0-9.]+)\\]'
	start = regexpr(start_pattern, level, perl=TRUE)
	end = regexpr(end_pattern, level, perl=TRUE)
	low = as.numeric(substr(level, start + 1, attr(start, 'match.length')))
	high = as.numeric(substr(level, end, end + attr(end, 'match.length') - 2))
	return((low + high) / 2.0)
}

accuracy_by_score_df = function(preds, labels) {
	preds_cut = cut(preds, breaks=10)
	df = data.frame(preds_cut, labels)
	accuracies = c()
	qualities = c()
	for (level in levels(preds_cut)) {
		#print(level)
		#print(class(level))
		these_mappings = df[df$preds_cut == level,]
		#print(dim(these_mappings))
		accuracy = mean(these_mappings$labels)
		#print(accuracy)
		accuracies = c(accuracies, accuracy)
		level_midpoint = get_midpoint(level)
		quality = -10 * log10(1 - level_midpoint)
		qualities = c(qualities, quality)
	}
	d = data.frame(qualities, accuracies)
	names(d) = c('Prediction Score (negative log scaled)', 'Average Accuracy')
	return(d)
}

calculate_accuracy_measures = function(training, validation, tool_name,
		output_filename_base, filename_addition, pr_xlim, pr_ylim) {
	cat('Training classifier\n')
	lr = mapping_lr(training)
	print(summary(lr))
	preds = predict(lr, newdata=validation, type="response")
	pred = prediction(preds, validation$correct)
	df = accuracy_by_score_df(preds, validation$correct)

	hist_filename = paste(c(output_dir, output_filename_base,
					filename_addition, '-score-hist.pdf'), collapse='')
	cat('Plotting histogram of predictions in', hist_filename, '\n')
	pdf(hist_filename)
	par(cex=cex.const, mar=mar.const)
	hist(preds)
	dev.off()

	acc_vs_score_filename = paste(c(output_dir, output_filename_base,
					filename_addition, '-acc-vs-score.pdf'), collapse='')
	cat('Plotting accuracy vs. score in', acc_vs_score_filename, '\n')
	pdf(acc_vs_score_filename)
	acc_vs_score_title = paste(c(tool_name, ': Accuracy vs. Prediction, LoQuM'), collapse='')
	par(cex=cex.const, mar=mar.const)
	plot(df, main=acc_vs_score_title, ylim=c(0, 1), type='b', col='blue')
	dev.off()

	pr_perf = performance(pred, 'prec', 'rec')
	pr_filename = paste(c(output_dir, output_filename_base,
					filename_addition, '-pr-loqum.pdf'), collapse='')
	cat('Plotting precision vs. recall in', pr_filename, '\n')
	pdf(pr_filename)
	pr_title = paste(c(tool_name, ': Precision vs. Recall, LoQuM'),
			collapse='')
	par(cex=cex.const, mar=mar.const)
	plot(pr_perf, colorize=TRUE, xlim=pr_xlim, ylim=pr_ylim,
			main=pr_title, downsampling=10000, cex=cex.const)
	dev.off()

	roc_perf = performance(pred, 'tpr', 'fpr')
	roc_filename = paste(c(output_dir, output_filename_base,
					filename_addition, '-roc-loqum.pdf'), collapse='')
	cat('Plotting ROC in', roc_filename, '\n')
	pdf(roc_filename)
	roc_title = paste(c(tool_name, ': ROC, LoQuM'),
			collapse='')
	par(cex=cex.const, mar=mar.const)
	plot(roc_perf, colorize=TRUE, main=roc_title, downsampling=10000, cex=cex.const)
	dev.off()

	score_csv_filename = paste(c(output_dir, output_filename_base,
					filename_addition, '-scores.csv'), collapse='')
	output_df = cbind(id=as.character(validation$read_id), pred=preds)
	write.csv(output_df, score_csv_filename, quote=FALSE, row.names=FALSE)

	return(df)
}

# Reads training and validation data from separate files
lr_eval_separate = function(train_filename, validation_filename_base, tool_name,
		output_filename_base, filename_addition='',
		pr_xlim=c(0, 1), pr_ylim=c(0, 1)) {
	if (substr(train_filename, 1, 1) == '/') {
		train_file = train_filename
	} else {
		train_file = paste(c(data_dir, train_filename), collapse='')
	}
	if (substr(validation_filename_base, 1, 1) == '/') {
		validation_file = paste(c(validation_filename_base, '.csv'),
				collapse='')
	} else {
		validation_file = paste(c(data_dir, validation_filename_base, '.csv'),
				collapse='')
	}
	cat('Reading training data from', train_file, '\n')
	training = read.csv(train_file)
	cat('Reading validation data from', validation_file, '\n')
	validation = read.csv(validation_file)

	df = calculate_accuracy_measures(training, validation, tool_name,
			output_filename_base, filename_addition, pr_xlim, pr_ylim)
	return(df)
}

# Reads training and validation data from the same data set
# and performs 5-fold cross validation
lr_eval_cross = function(filename_base, tool_name, output_filename_base,
		filename_addition='',
		pr_xlim=c(0, 1), pr_ylim=c(0, 1), training_proportion=0.8) {
	if (substr(filename_base, 1, 1) == '/') {
		csv_file = paste(c(filename_base, '.csv'), collapse='')
	} else {
		csv_file = paste(c(data_dir, filename_base, '.csv'), collapse='')
	}
	csv_filename = paste(c(data_dir, filename_base, '.csv'), collapse='')
	cat('Reading data from', csv_file, '\n')
	raw_data = read.csv(csv_file)
	print(dim(raw_data))
	training_count = floor(dim(raw_data)[1] * training_proportion)
	validation_count = dim(raw_data)[1] - training_count
	assignments = sample(c(rep(1, training_count), rep(0, validation_count)))
	training = raw_data[which(assignments == 1),]
	validation = raw_data[which(assignments == 0),]

	df = calculate_accuracy_measures(training, validation, tool_name,
			output_filename_base, filename_addition, pr_xlim, pr_ylim)
	return(df)
}

plot_acc_by_score = function(tools, dfs, desc,
		filename_addition='') {
	colors = rainbow(length(tools), start=0, end=4/6, v=0.9)

	thr_cutoff = 15
	cropped_thr = 0:thr_cutoff
	theoretical = 1 - (10 ^ -(cropped_thr / 10))

	filename = paste(c(output_dir, 'accuracy-vs-score', filename_addition,
					'.pdf'), collapse='')
	pdf(filename)
	par(xpd=NA, mar=mar.const, cex=cex.const)
	plot.new()
	plot.window(range(cropped_thr), range(0, 1))
	acc_vs_score_title = paste(c(desc, ', LoQuM'), collapse='')
	title(main=acc_vs_score_title,
			xlab="Prediction (negative log-scaled)", ylab="Mean Accuracy")
	axis(1, at=cropped_thr)
	axis(2, at=seq(0, 1, 0.2))

	theoretical_pch = 15
	points(theoretical ~ cropped_thr, type="b", col="black",
			pch=theoretical_pch)
	for (i in 1:length(tools)) {
		points(dfs[[i]], type="b", col=colors[i], pch=i)
	}

	tool_names = c("<Theoretical>", tools)
	tool_icons = c(theoretical_pch, 1:length(tools))
	tool_colors = c("black", colors)
	legend("bottomright", xjust=1, yjust=0.5, legend=tool_names, title="Tool",
			col=tool_colors, pch=tool_icons)
	dev.off()
}
