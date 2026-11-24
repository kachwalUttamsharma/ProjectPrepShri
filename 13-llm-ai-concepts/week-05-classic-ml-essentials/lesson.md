# Week 5: Classic ML Essentials for Interviews

Goal: answer the "ML basics" round fluently. AI-engineering interviews still ask these because they reveal whether you can reason about data, error and evaluation, which LLM work depends on. Pure Python snippets below run with no libraries.

---

## 1. Supervised vs unsupervised (and friends)

| Type | Data | Goal | Examples |
|---|---|---|---|
| Supervised | inputs X with labels y | learn f(X) to predict y | spam classifier (classification), price prediction (regression) |
| Unsupervised | X only | find structure | clustering customers, dimensionality reduction, anomaly detection |
| Self-supervised | labels derived from the data itself | learn representations | next-token prediction in LLMs, masked language modeling |
| Semi-supervised | few labels, many unlabeled | use both | pseudo-labeling |
| Reinforcement | actions and rewards | learn a policy | RLHF stage, game agents |

Classification: discrete labels. Regression: continuous values. Ranking: order items. Always ask first: what is the target, what is the cost of each error type, and what is the baseline (majority class, rule, human)?

## 2. Overfitting, underfitting, regularization, bias-variance

- Underfitting (high bias): model too simple; poor on train and test.
- Overfitting (high variance): memorizes noise; great on train, poor on test.
- Total expected error = bias^2 + variance + irreducible noise.

```
 error
  |  \                      test error
  |   \_                  _/
  |     \__           __/       <- overfitting side: variance dominates
  |        \_______/
  |   train error keeps falling
  +-------------------------------> model complexity
   underfit (bias)          overfit (variance)
```

Diagnose with learning curves: both errors high and close = high bias (need a richer model/features). Big train-test gap = high variance (more data, regularize, simpler model).

Remedies for variance: more data, regularization (L2/ridge shrinks weights smoothly; L1/lasso drives some to zero, feature selection; elastic net mixes), early stopping, dropout (neural nets), pruning or depth limits (trees), bagging/ensembles, data augmentation, fewer features. Remedies for bias: more features, more complex model, less regularization, train longer.

Regularized loss: loss = data_loss + lambda * penalty(weights). Larger lambda means simpler model.

## 3. Splits, validation, leakage

- Train: fit parameters. Validation: tune hyperparameters and choose models. Test: touched once at the end for an unbiased estimate. Typical 60/20/20 or 70/15/15 or cross-validation when data is small.
- k-fold CV: split into k parts, train on k-1, validate on 1, rotate, average. Stratified for imbalanced classes. Time series: split by time (walk-forward), never shuffle across time. Grouped CV when rows from the same user/patient/document must stay together.
- Data leakage: information in training that would not exist at prediction time, inflating scores. Examples: (1) target leakage: a feature computed from the label or from future info (e.g. "refund_issued" when predicting churn), (2) preprocessing leakage: fitting scaler/imputer/vocabulary/embeddings on all data before splitting, (3) duplicates or near-duplicates across train and test, (4) same user/entity in both splits, (5) random split on time-ordered data, (6) tuning many times on the test set, (7) LLM evals where test items appear in prompts or pretraining data.
- Red flag: a suspiciously high metric. Investigate before celebrating.
- Distribution shift: production data differs from training (covariate shift, label shift, concept drift). Monitor and retrain.

```python
import random

def train_val_test(rows, seed=0, fracs=(0.7, 0.15, 0.15)):
    rows = rows[:]
    random.Random(seed).shuffle(rows)
    n = len(rows)
    a = int(n * fracs[0]); b = a + int(n * fracs[1])
    return rows[:a], rows[a:b], rows[b:]

tr, va, te = train_val_test(list(range(100)))
print(len(tr), len(va), len(te))
assert not (set(tr) & set(te))         # no overlap
```

## 4. Metrics with worked examples

Confusion matrix for a binary problem (positive = "fraud"):

```
                 Predicted +   Predicted -
 Actual +           TP            FN
 Actual -           FP            TN
```

Worked example: 1,000 transactions; 60 are fraud. Model flags 50; 40 of those are truly fraud.
TP=40, FP=10, FN=20, TN=930.
- Accuracy = (TP+TN)/N = 970/1000 = 0.97 (misleading: always predicting "not fraud" gives 0.94).
- Precision = TP/(TP+FP) = 40/50 = 0.80 (of flagged, how many are real).
- Recall (sensitivity, TPR) = TP/(TP+FN) = 40/60 = 0.667 (of real, how many caught).
- Specificity = TN/(TN+FP) = 930/940 = 0.989. FPR = 1 - specificity = 0.0106.
- F1 = 2PR/(P+R) = 2*0.8*0.667/1.467 = 0.727 (harmonic mean). F-beta weights recall more if beta > 1.

```python
def metrics(tp, fp, fn, tn):
    acc = (tp + tn) / (tp + fp + fn + tn)
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return {"acc": round(acc, 3), "precision": round(p, 3), "recall": round(r, 3), "f1": round(f1, 3)}

print(metrics(40, 10, 20, 930))
```

Choosing: missing cancer or fraud costs more than a false alarm: favor recall. Spam folder losing real email, or auto-banning users: favor precision. Imbalanced data: use precision/recall/PR-AUC, not accuracy. Multi-class: macro average (each class equal) vs micro (each sample equal) vs weighted.

Thresholds: classifiers output scores; the threshold trades precision vs recall. Lower threshold: more positives, higher recall, lower precision.

ROC-AUC: ROC plots TPR vs FPR across all thresholds; AUC = probability a random positive is scored above a random negative (0.5 random, 1.0 perfect). Threshold-independent and insensitive to class balance, which can look rosy when positives are rare; PR-AUC is more informative then. Calibration: do predicted probabilities match frequencies?

```python
def auc(scores, labels):
    """Probability a random positive outranks a random negative (ties count 0.5)."""
    pos = [s for s, y in zip(scores, labels) if y == 1]
    neg = [s for s, y in zip(scores, labels) if y == 0]
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))

print(auc([0.9, 0.8, 0.4, 0.3, 0.2], [1, 1, 0, 1, 0]))   # 5/6 = 0.833
```

Regression metrics: MAE (robust, interpretable), MSE/RMSE (punishes large errors), R^2 (variance explained), MAPE (careful near zero). Ranking: nDCG, MRR, recall@k. Generation: see Week 4.

## 5. Linear and logistic regression

Linear regression: y_hat = w.x + b. Fit by minimizing squared error (closed form or gradient descent). Assumptions: linearity, independent errors, constant variance, little multicollinearity. Interpretable coefficients; sensitive to outliers and feature scale (when regularized). Ridge/lasso add penalties.

Logistic regression: p = sigmoid(w.x + b), sigmoid(z) = 1/(1+e^-z). Despite the name it is a classifier. Trained by minimizing log loss (cross-entropy): -[y log p + (1-y) log(1-p)]. Outputs probabilities; coefficients are changes in log-odds. Strong, fast baseline; linear decision boundary unless you add feature interactions. Multi-class: softmax.

Gradient descent in pure Python:

```python
import math

def sigmoid(z): return 1 / (1 + math.exp(-z))

# toy 1-D data: x small -> 0, x large -> 1
X = [0.5, 1.0, 1.5, 3.0, 3.5, 4.0]
Y = [0, 0, 0, 1, 1, 1]
w, b, lr = 0.0, 0.0, 0.5
for _ in range(2000):
    gw = gb = 0.0
    for x, y in zip(X, Y):
        p = sigmoid(w * x + b)
        gw += (p - y) * x
        gb += (p - y)
    w -= lr * gw / len(X)
    b -= lr * gb / len(X)
print(round(w, 2), round(b, 2), [round(sigmoid(w * x + b), 2) for x in X])
```

## 6. Trees and boosting (intuition)

- Decision tree: repeatedly split data on the feature/threshold that most reduces impurity (Gini or entropy for classification, variance for regression). Interpretable, handles mixed features and nonlinearity, no scaling needed. Overfits easily when deep: limit depth, min samples per leaf, prune.
- Random forest (bagging): train many deep trees on bootstrap samples with random feature subsets, average votes. Reduces variance; robust default; parallel; less interpretable; gives feature importances.
- Gradient boosting (e.g. XGBoost/LightGBM-style): build trees sequentially, each fitting the residual errors (negative gradients) of the ensemble so far, scaled by a learning rate. Reduces bias (and variance with shrinkage/regularization); often the best on tabular data; needs tuning (learning rate, depth, number of trees, subsampling); can overfit without early stopping.
- Bagging reduces variance by averaging independent-ish models; boosting reduces bias by sequentially correcting.
- For tabular data, boosted trees often beat deep learning; for text, images, audio, neural nets dominate.

Gini impurity for a node with class proportions p_i: 1 - sum p_i^2. A 50/50 node has 0.5; a pure node 0.

```python
def gini(counts):
    n = sum(counts)
    return 1 - sum((c / n) ** 2 for c in counts)

print(gini([50, 50]), gini([100, 0]), gini([80, 20]))
```

## 7. Embeddings and clustering

- Embeddings: learned dense representations (words, sentences, users, items) where distance means similarity. Used for search, recommendation, clustering, features for downstream models. Evaluate by downstream task.
- k-means: choose k; init centroids; assign each point to the nearest; recompute centroids; repeat until stable. Minimizes within-cluster variance. Needs k, assumes roughly spherical equal-size clusters, sensitive to init (use k-means++) and scale, uses Euclidean distance. Choose k with elbow, silhouette score, or domain need.
- Hierarchical clustering: build a dendrogram. DBSCAN: density-based, finds arbitrary shapes and noise, no k needed but needs eps/min_samples. Gaussian mixtures: soft assignments.
- PCA: project onto directions of maximum variance; used for compression, visualization, denoising. t-SNE/UMAP: nonlinear visualization (distances between far clusters not meaningful).
- Curse of dimensionality: in high dimensions distances concentrate and data is sparse; hence dimensionality reduction and ANN.
- Evaluation without labels: silhouette, stability across seeds, manual inspection, downstream value.

```python
import random

def kmeans(points, k, iters=20, seed=0):
    rnd = random.Random(seed)
    cents = rnd.sample(points, k)
    for _ in range(iters):
        groups = [[] for _ in range(k)]
        for p in points:
            j = min(range(k), key=lambda i: (p[0] - cents[i][0]) ** 2 + (p[1] - cents[i][1]) ** 2)
            groups[j].append(p)
        cents = [
            (sum(x for x, _ in g) / len(g), sum(y for _, y in g) / len(g)) if g else cents[i]
            for i, g in enumerate(groups)
        ]
    return cents, groups

pts = [(1, 1), (1.2, 0.8), (0.8, 1.1), (5, 5), (5.2, 4.9), (4.8, 5.1)]
cents, groups = kmeans(pts, 2)
print([tuple(round(c, 2) for c in cc) for cc in cents], [len(g) for g in groups])
```

## 8. Neural nets and backprop (intuition)

- A neuron: output = activation(w.x + b). A layer is many neurons; a network stacks layers. Nonlinear activations (ReLU, GELU, sigmoid, tanh) are what let networks model nonlinear functions; without them stacked layers collapse into one linear map.
- Training: forward pass computes predictions and loss; backpropagation applies the chain rule to compute the gradient of loss with respect to every weight; an optimizer (SGD, Adam) steps weights opposite the gradient: w <- w - lr * grad. Mini-batches approximate the full gradient cheaply. An epoch is one pass over the data.
- Hyperparameters: learning rate (most important: too high diverges, too low crawls), batch size, depth/width, regularization (weight decay, dropout), epochs with early stopping.
- Problems: vanishing/exploding gradients (fixes: ReLU-family activations, residual connections, normalization, good initialization, gradient clipping), overfitting, local minima/saddles (less of an issue in practice), need for lots of data and compute.
- Architectures by data: MLP (tabular), CNN (images), RNN/LSTM (sequences, mostly replaced), transformer (text, now multimodal).
- Softmax plus cross-entropy for classification; MSE for regression. LLM training is this same loop with next-token cross-entropy at huge scale.

Tiny backprop by hand (single neuron, squared loss):

```python
# y_hat = w*x + b ; L = (y_hat - y)^2 ; dL/dw = 2(y_hat - y)*x ; dL/db = 2(y_hat - y)
x, y = 2.0, 10.0
w, b, lr = 0.0, 0.0, 0.05
for step in range(50):
    y_hat = w * x + b
    grad_w = 2 * (y_hat - y) * x
    grad_b = 2 * (y_hat - y)
    w -= lr * grad_w
    b -= lr * grad_b
print(round(w * x + b, 3))      # approaches 10
```

## 9. Feature engineering and practical workflow
1. Define the problem, metric, baseline, and costs of errors.
2. Explore data: missingness, outliers, class balance, leakage suspects.
3. Split correctly before any fitting.
4. Baseline (majority/rule/logistic regression), then try boosted trees; compare on validation.
5. Handle imbalance: class weights, resampling, threshold tuning, appropriate metrics.
6. Categorical encoding (one-hot, target encoding with care for leakage), scaling for distance- or gradient-based models, imputation inside the pipeline.
7. Tune, then evaluate once on test; examine errors by segment.
8. Deploy, monitor drift and performance, retrain.
Use sklearn-style Pipelines so preprocessing is fit only on training folds.

## 10. How interviewers probe
- "Accuracy is 99 percent. Is it good?" (Class imbalance; show confusion matrix.)
- "Precision vs recall: which for X?" (Cost of each error.)
- "Train 98, test 70?" (Overfit/leakage; learning curves; remedies.)
- "How does boosting differ from bagging?"
- "Explain regularization L1 vs L2."
- "How do you split time-series data?" 
- "Explain backprop to a non-technical person."
- "How would you cluster customers and know if it is good?"
- Link to LLMs: "How is evaluating an LLM classifier like evaluating classic ML?" (Same metrics, splits, leakage rules.)

## Self-check
1. Recompute the fraud example with threshold changes (e.g. TP=50, FP=30, FN=10).
2. Explain AUC as a probability in one sentence.
3. List five leakage sources.
4. Write the logistic regression gradient update.
