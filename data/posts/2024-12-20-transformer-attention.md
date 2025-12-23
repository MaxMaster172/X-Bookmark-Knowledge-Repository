---
id: "1234567890001"
author: karpathy
date: 2024-12-20
url: https://x.com/karpathy/status/1234567890001
tags: [machine-learning, transformers, attention]
topics: [AI, deep-learning]
importance: high
---

The key insight of the transformer architecture is that attention is all you need. Self-attention allows the model to weigh the importance of different parts of the input when producing each output element.

The attention mechanism computes queries, keys, and values from input embeddings, then uses dot products to determine how much each position should attend to every other position.

This parallelizes beautifully compared to RNNs, which must process sequences step by step.
