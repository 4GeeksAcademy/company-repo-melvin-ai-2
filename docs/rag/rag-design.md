# Brasaland knowledge assistant

Location managers ask a question in English. The answer is written by a generation model from the official manuals. A raw Qdrant hit is never the reply.

## Flow

1. `docs/company-knowledge-base/` holds the four English manuals: loyalty, waste, allergens, and supplier ordering.
2. `setup()` in `data/process/rag.py` splits each manual on headings and section labels, then on blank lines, so a sentence stays inside one chunk. Each file produces at least three chunks.
3. `embed()` sends that text to the embeddings model and stores the vector in the Qdrant collection `brasaland_knowledge`. Distance is cosine. Running `setup()` again deletes and recreates the collection, then upserts the same chunk ids.
4. At question time, `retrieve()` in `data/pipelines/rag.py` embeds the question with the same `embed()` function, asks Qdrant for the top 5 neighbors, and drops any hit below `RAG_MIN_SCORE` (default 0.35). It can return fewer than five chunks, including none.
5. `generate_answer()` sends the surviving excerpts and the question to the generation model. `query()` is only those two steps. `POST /knowledge/query` returns `{ "answer": "..." }`.

```text
manuals -> setup -> embed -> Qdrant
question -> retrieve -> embed -> Qdrant -> min_score
         -> generate_answer -> answer
```

## Chunking

The manuals are short procedures, tier lists, and allergen lines. Splitting on a heading or a label such as "Program tiers:" keeps the rule and its numbers together. A further split happens only at a blank line, which is a paragraph boundary, so a sentence is not cut in half. One chunk per document would mix unrelated rules. One chunk per line would separate a discount from the tier it belongs to.

## Embeddings

`RAG_EMBEDDING_MODEL` and `RAG_GENERATION_MODEL` are two ids from the 4Geeks student LLM access, sent to `RAG_BASE_URL`. For this key those ids are `downtown-miami/openrouter/perplexity/pplx-embed-v1-0.6b` and `downtown-miami/openrouter/openai/gpt-6-luna`. `embed()` calls `/embeddings`. `chat_complete()` calls `/chat/completions`. The code refuses to start if those ids are equal. A 429 waits until the gateway reset time and retries, because the student key allows 15 requests in a window and indexing sends one request per chunk. The same `embed()` function is used when a chunk is indexed and when a question is searched, so both sides of the cosine comparison use one vector space.

Text is not lowercased, stemmed, or otherwise normalized before `embed()`. The only preparation is the chunk split: headings and labels become the section title, and a blank line starts a new chunk. The indexed collection uses 1024-dimensional vectors and cosine distance, which is the size this embeddings model returned. `RAG_MIN_SCORE` stays 0.35. That floor was kept after the live Recall@3 measurement scored 100% on the eight questions, so weak neighbors from another manual are still dropped without hiding a correct chunk.

## Similarity floor

Cosine similarity near 1 is the same meaning. A neighbor at 0.35 or below is usually a different manual, and putting it in the prompt invites the model to invent a policy. Hits under `RAG_MIN_SCORE` are discarded. If none remain, the generation model is still called and is instructed to say the manuals do not contain enough information.

The audience is a location manager. The voice is a trained salesperson: confident, limited to the excerpt, with peso and dollar amounts copied as written, and with no promise of zero cross-contamination risk.

## Recall@3

`data/eval/test-queries.json` has eight questions, two for each manual. `recall_at_3` counts a hit when the expected phrase is inside one of the top three payloads from the expected source. The briefing requires at least 80 percent. The live index scored 100 percent. Measure it again with:

```bash
uv run python scripts/index_knowledge.py
uv run python scripts/evaluate_knowledge_recall.py
```
