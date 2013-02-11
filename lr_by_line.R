source('common.R')
library(iterators)

train_filename = '/home/mruffalo/ramdisk/snp/training.csv'
training = read.csv(train_filename)
lr = mapping_lr(training)

filename = '/home/mruffalo/ramdisk/snp/reads.csv'
fh = file(filename, open='rt')
wh = file('output.csv', open='wt')
i = ireadLines(fh)
labels = c(unlist(strsplit(nextElem(i), ',')))
while (TRUE) {
	x = c(as.numeric(unlist(strsplit(nextElem(i), ','))))
	names(x) = labels
	d = data.frame(t(x))
	preds = predict(lr, newdata=d, type="response")
	#print(preds[1])
	lpred = -10 * log10(1 - preds[1])
	write(lpred, file=wh, append=TRUE)
}
close(fh)
close(wh)
