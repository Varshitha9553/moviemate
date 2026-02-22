import numpy as np


# hit rate: “Does the recommended list contain a relevant movie?”
def evaluate_hit_rate_at_k(similarity, k=5, sample_size=200):
    hits = 0
    total = 0

    n = min(sample_size, similarity.shape[0])

    for i in range(n):
        scores = list(enumerate(similarity[i]))
        scores = sorted(scores, key=lambda x: x[1], reverse=True)

        # ignore self (index 0)
        recommended = [idx for idx, _ in scores[1:k+1]]

        # assume top-1 similar movie is relevant
        relevant = scores[1][0]

        if relevant in recommended:
            hits += 1
        total += 1

    return hits / total


#precision: “Out of the recommended movies, how many are actually relevant?”
def evaluate_precision_at_k(similarity, k=5, sample_size=200):
    precision_sum = 0
    n = min(sample_size, similarity.shape[0])

    for i in range(n):
        scores = list(enumerate(similarity[i]))
        scores = sorted(scores, key=lambda x: x[1], reverse=True)

        recommended = [idx for idx, _ in scores[1:k+1]]
        relevant = scores[1][0]

        if relevant in recommended:
            precision_sum += 1 / k

    return precision_sum / n


#Mean Reciprocal Rank (MRR): “How early does the relevant movie appear in recommendations?”
def evaluate_mrr(similarity, sample_size=200):
    rr_sum = 0
    n = min(sample_size, similarity.shape[0])

    for i in range(n):
        scores = list(enumerate(similarity[i]))
        scores = sorted(scores, key=lambda x: x[1], reverse=True)

        relevant = scores[1][0]

        for rank, (idx, _) in enumerate(scores[1:], start=1):
            if idx == relevant:
                rr_sum += 1 / rank
                break

    return rr_sum / n

print("Evaluating recommendation model...\n")

hit_rate = evaluate_hit_rate_at_k(similarity, k=5, sample_size=200)
precision = evaluate_precision_at_k(similarity, k=5, sample_size=200)
mrr = evaluate_mrr(similarity, sample_size=200)

print(f"Hit Rate@5      : {hit_rate:.4f}")
print(f"Precision@5     : {precision:.4f}")
print(f"MRR             : {mrr:.4f}")
