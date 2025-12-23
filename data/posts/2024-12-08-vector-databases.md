---
id: "1234567890005"
author: deaborysov
date: 2024-12-08
url: https://x.com/deaborysov/status/1234567890005
tags: [vector-db, embeddings, infrastructure]
topics: [AI, databases]
importance: medium
notes: Good comparison of options
---

Vector database landscape in 2024:

- Pinecone: Managed, easy, but can get pricey at scale
- Weaviate: Open source, feature-rich, good hybrid search
- Qdrant: Rust-based, very fast, great filtering
- ChromaDB: Simple, embedded, perfect for prototypes and small projects
- pgvector: If you're already on Postgres, just add an extension

For most side projects, ChromaDB is plenty. Don't over-engineer.
