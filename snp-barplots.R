load('~/data/loqum-snp/snp-df.RData')

# Don't need to do this; the axis labels are enough
#nf = layout(t(c(1, 2, 3, 4)), widths=c(2, 2, 2, 1))
#layout.show(nf)

colors = c("red", "blue")
ylim.const = c(0, 1)

pdf('output/snp-barplots.pdf', width=10, height=5)
par(mfrow=c(1, 3))
boxplot(Precision ~ Type, data=d, col=colors, main='Precision', ylab='Precision', ylim=ylim.const)
boxplot(Recall ~ Type, data=d, col=colors, main='Recall', ylab='Recall', ylim=ylim.const)
boxplot(F ~ Type, data=d, col=colors, main='F', ylab='F', ylim=ylim.const)
dev.off()
