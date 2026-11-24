# Week 5 Cheatsheet: Classic ML Essentials

## Learning types
Supervised (X,y) | Unsupervised (X) | Self-supervised (labels from data; LLMs) | Semi | Reinforcement (reward; RLHF).

## Bias-variance
Error = bias^2 + variance + noise. High bias: train and test both bad -> more capacity. High variance: big train-test gap -> data, regularize, simplify, ensemble, early stop.
L2 shrinks, L1 sparsifies, elastic net both. loss = data_loss + lambda * penalty.

## Splits
Train fit | Val tune | Test once. k-fold (stratified, grouped). Time series: split by time.
Leakage: target/future features, preprocessing before split, duplicates, same entity across splits, tuning on test, benchmark contamination. Too-good score = suspect.

## Metrics
Precision = TP/(TP+FP). Recall = TP/(TP+FN). Specificity = TN/(TN+FP). FPR = 1 - spec. F1 = 2PR/(P+R). Accuracy = (TP+TN)/N.
Worked: TP40 FP10 FN20 TN930 -> P .80, R .667, F1 .727, Acc .97 (baseline always-negative .94).
ROC-AUC = P(random pos scores > random neg). Rare positives: use PR-AUC. Threshold: lower = more recall, less precision.
Regression: MAE, RMSE, R^2. Ranking: nDCG, MRR, recall@k. Macro vs micro vs weighted averages.

## Models
Linear: y=w.x+b, squared loss. Logistic: sigmoid(w.x+b), log loss, gradient (p-y)*x.
Tree: split to reduce Gini/entropy; Gini = 1 - sum p^2. Forest = bagging (variance down). GBM = sequential residual fitting (bias down), tune lr/depth/trees, early stop. Tabular: boosted trees strong baseline.

## Clustering / embeddings
k-means: assign, recompute, repeat; pick k via silhouette/elbow; scale features. DBSCAN for shapes/noise. PCA for variance directions. Embeddings: dense similarity vectors; eval on downstream task. Curse of dimensionality.

## Neural nets
neuron = act(w.x+b); nonlinearity essential. Forward -> loss -> backprop (chain rule) -> w -= lr*grad. Adam/SGD, mini-batch, epoch. LR most sensitive. Vanishing gradients: ReLU, residuals, norm. Overfit: dropout, weight decay, early stop. Softmax + cross-entropy classify.

## Workflow
Metric + baseline -> split -> EDA -> simple model -> boosted trees -> tune on val -> test once -> error analysis by segment -> monitor drift.

## Red flags to say aloud
"99 percent accuracy" on imbalance; "random split" on time data; "scaled before splitting"; "tuned on test".
