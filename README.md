# Warframe RAG Assistant

A local-first Retrieval-Augmented Generation (RAG) assistant built on top of the Warframe Wiki.

The project looks to combine multilingual embeddings, vector search  and an LLM to answer Warframe questions using information retrieved from the Wiki rather than relying exclusively on the model's internal knowledge.

The goal is to build a fast, lightweight and reliable conversational assistant for Warframe while experimenting with modern RAG architectures.

## Features
- Retrieval-Augmented Generation using the Warframe Wiki
- Local vector database with ChromaDB
- Multilingual embeddings for English Wiki content and Spanish user queries
- LLM-based answer generation
- Designed to reduce hallucinations by restricting answers to retrieved Wiki context
- Conversational desktop interface
- Local document processing and indexing
- Configurable models and database paths through environment variables
- Jev integration for document relevance scoring and reranking (PENDING)

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd warframe-rag
```
### 2. Create a Python environment

Using Conda:

```bash
conda create -n warframe-rag python=3.13
conda activate warframe-rag
```

Or using `venv`:

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---
## 4. Setup environment variables

The following section details the purpose of each variable defined in the project configuration:

---

### File and Data Paths

* **`RUTA_XML`**  
  Specifies the file system path to the XML file that the application will read or process. Typically used to load structured data, configurations, or logs. [Download link](https://warframe.fandom.com/wiki/Special:Statistics)

* **`RUTA_DB`**  
  Defines the location of the local database file (e.g., SQLite or a `.db` file). Allows the application to establish a connection to store or query information persistently.

---

### AI Models

* **`MODELO_GPT`** (`"gpt-4.1-nano"`)  
  Name of the OpenAI model to be invoked via the API. The `nano` variants are typically designed for high speed and cost efficiency in lightweight or low-latency tasks.

* **`MODELO_HF`** (`"paraphrase-multilingual-MiniLM-L12-v2"`)  
  Name of the Hugging Face model to be used. This specific model (*Sentence Transformers*) specializes in generating multilingual text embeddings for semantic search or similarity calculations.

---

### Credentials

* **`OPENAI_API_KEY`**  
  Private API key required to authenticate and make requests to OpenAI services.

* **`HF_TOKEN`**  
  Personal access token for Hugging Face. Required to authenticate requests to their inference APIs or to download models that require user permissions.

---

## Roadmap

### Retrieval

- [x] Chroma vector database
- [x] Semantic retrieval
- [x] Multilingual embeddings
- [ ] Jev reranking
- [ ] Hybrid BM25 + vector retrieval
- [ ] Metadata filtering
- [ ] Parent-child retrieval
- [ ] Context compression

### RAG

- [x] Basic RAG pipeline
- [x] Context-based generation
- [ ] Evidence validation
- [ ] Source citations
- [ ] Query rewriting
- [ ] Conversational retrieval
- [ ] Confidence estimation

### Interface

- [x] Desktop chat interface
- [x] Movable window
- [x] Resizable chat area
- [ ] Streaming responses
- [ ] Source/document panel

### Evaluation

- [ ] Retrieval Recall\@K
- [ ] MRR / NDCG
- [ ] Answer relevance
- [ ] Faithfulness evaluation
- [ ] Latency benchmarks
- [ ] Token usage comparison
- [ ] RAG architecture comparison

---

## Evaluation

One of the project's goals is to measure whether each retrieval component actually improves the system.

Potential experiments:

```text
Baseline
Chroma
   ↓
LLM
```

versus:

```text
Multilingual Chroma
   ↓
Jev
   ↓
LLM
```

versus:

```text
BM25 + Vector Search
   ↓
Jev
   ↓
Context Compression
   ↓
LLM
```

Metrics include:

- Recall\@K
- MRR
- NDCG
- Context relevance
- Answer faithfulness
- Response latency
- Token consumption
- API cost

---

## Design Principles

### Retrieval before generation

The LLM should primarily reason over information retrieved from the Wiki instead of relying on its parametric knowledge.

### Local-first processing

Wiki processing, embeddings and vector storage are performed locally whenever practical.

### Language independence

Users should be able to ask questions in languages different from the language of the source documents.

### Measurable improvements

New components should be evaluated quantitatively rather than added only because they appear to improve responses subjectively.

### Modular architecture

Retrieval, reranking, generation and UI components should remain separable so individual components can be replaced or benchmarked.

---

## Disclaimer

This project is an independent technical project and is not affiliated with or endorsed by Digital Extremes or the Warframe Wiki.

Warframe and related trademarks belong to their respective owners.
