source('common.R')

tools = list(
		c('bwa-art', 'BWA', 'bwa-art'),
		c('nva-art', 'Novoalign', 'nva-art'),
		c('soap-art', 'SOAP2', 'soap-art'),
		c('mrf-art', 'mrFAST', 'mrf-art')
)

bwa = lr_eval_cross('bwa-art', 'BWA', 'bwa-art')
nva = lr_eval_cross('nva-art', 'Novoalign', 'nva-art')
soap = lr_eval_cross('soap-art', 'SOAP2', 'soap-art')
mrfast = lr_eval_cross('mrf-art', 'mrFAST', 'mrf-art')

tool_names = c('BWA', 'Novoalign', 'SOAP', 'mrFAST')
acc_by_score_dfs = foreach(tool=tools) %dopar% lr_eval_cross(tool[1], tool[2], tool[3])

plot_acc_by_score(tool_names, acc_by_score_dfs, 'Accuracy vs. Prediction')
