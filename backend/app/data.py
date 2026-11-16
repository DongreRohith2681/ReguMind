import random
from sklearn.model_selection import train_test_split
from .automata import accepts

def generate(a, n, max_length, seed=42):
    rng = random.Random(seed); words = []; labels = []
    for _ in range(n):
        word = [rng.choice(a.alphabet) for _ in range(rng.randint(0, max_length))] if a.alphabet else []
        words.append(word); labels.append(int(accepts(a, word)))
    return words, labels

def balanced_generate(a, n, max_length, seed=42):
    rng = random.Random(seed); positives = []; negatives = []; attempts = 0
    while (len(positives) < n // 2 or len(negatives) < n - n // 2) and attempts < n * 100:
        word = [rng.choice(a.alphabet) for _ in range(rng.randint(0, max_length))] if a.alphabet else []
        (positives if accepts(a, word) else negatives).append(word); attempts += 1
    words = positives[:n // 2] + negatives[:n - n // 2]
    rng.shuffle(words)
    return words, [int(accepts(a, word)) for word in words]

def split(words, labels, test_size=.2, seed=42):
    return train_test_split(words, labels, test_size=test_size, random_state=seed, stratify=labels if len(set(labels)) > 1 else None)

def features(words, vocabulary=None):
    vocab = sorted(vocabulary or {symbol for word in words for symbol in word})
    return [[word.count(symbol) for symbol in vocab] + [len(word)] for word in words], vocab
