# Text-to-SQL Analytics Agent

Ask ecommerce analytics questions in plain English. The agent writes the SQL, runs it safely against PostgreSQL, and explains the result in plain language. Ambiguous questions get a clarification request instead of a guess, and requests that try to change data never reach the database.

**Live demo:** _add link here_ | **Demo video:** _add link here_

_The demo runs on a free API tier. If a question returns an error, wait a minute and try again._

![App screenshot](docs/screenshot.png)

## What it does

- Turns questions like "Which product has the highest total sales in each category?" into validated, read-only PostgreSQL.
- Detects vague questions ("Which customers are most valuable?") and asks which metric to use.
- Retrieves only the relevant tables for each question using pgvector similarity search, then adds directly joined tables so the model can write joins.
- Retries once with the error message if generation or execution fails.
- Shows the generated SQL, the result rows, and a plain-English answer in a Streamlit UI.

## Architecture

```mermaid
flowchart TD
    Q[User question] --> C{Check question}
    C -->|ambiguous| CL[Ask for clarification]
    C -->|clear| R[Retrieve relevant tables<br/>pgvector + foreign-key neighbours]
    R --> G[Generate SQL<br/>Groq gpt-oss-120b]
    G --> V[Validate<br/>sqlglot + table allowlist]
    V --> E[Execute<br/>read-only role, 5s timeout, 100-row cap]
    V -->|rejected| RT{Attempts left?}
    E -->|error| RT
    RT -->|yes, send error back| G
    RT -->|no| ER[Safe error message]
    E -->|ok| A[Plain-English answer]
```

| Layer | Technology |
|---|---|
| Orchestration | LangGraph, LangChain |
| LLM | Groq `openai/gpt-oss-120b` |
| Database | PostgreSQL 16 with pgvector |
| Embeddings | `all-MiniLM-L6-v2` (384 dimensions, runs locally) |
| SQL validation | sqlglot |
| Backend / UI | FastAPI, Streamlit |
| Packaging | Docker Compose (database, API, frontend) |

## Safety design

The model is not trusted. Several independent layers protect the data:

1. **Read-only database role.** The API connects as `analytics_reader`, which has `SELECT` only.
2. **Read-only transactions.** Every query runs inside `SET TRANSACTION READ ONLY`.
3. **SQL validator.** Exactly one `SELECT`/`UNION` statement. Inserts, updates, deletes, `SELECT INTO`, and writable CTEs are rejected.
4. **Table allowlist.** Only the 15 ecommerce tables can be read. System catalogs, `information_schema`, and the internal embeddings table are blocked.
5. **Resource limits.** 5-second statement timeout, `EXPLAIN` pre-check, and a 100-row cap with a visible truncation notice.
6. **Honest answers.** The answer prompt forbids claiming that data was changed. Error details go to the server log, never to the user.

An adversarial probe (`scripts/probe_attacks.py`) sends hostile prompts such as "Delete all cancelled orders", "DROP TABLE customers", and attempts to read system tables. No data was changed in any run. The probe also found real bugs (a false "prices updated" claim, an unrestricted table list), which are fixed and covered by unit tests.

## Evaluation

The database is synthetic: 15 tables, 200 customers, 1,500 orders, about 3,750 order items, generated with a fixed random seed (`scripts/generate_data.py`).

Metric: **execution accuracy**. The agent's result rows are compared with the result of a hand-verified reference query. Row order is ignored unless the question asks for a ranking, numbers are compared to 2 decimals, and extra columns are allowed. Ambiguous questions are scored correct only if the agent asks for clarification and generates no SQL.

| Split | Cases | Result | Notes |
|---|---|---|---|
| Dev | 20 | 20/20 | Used to tune prompts. Not quoted as a result. |
| Test | 30 | 30/30 | Frozen code, first run. Re-run after the safety changes: 30/30. |
| Challenge | 16 | 16/16 | Messy phrasing, value mismatches, hierarchy rollups, window functions, join fan-out. After the safety changes: 15/16, and the one miss was a Groq rate-limit crash (HTTP 429), not a wrong answer. |

Each case belongs to a tier: single table, joins, aggregation, dates and subqueries, ambiguity, messy phrasing, value traps, hard SQL.

How to read these numbers honestly:

- The 50 core questions and the challenge questions were written with an AI assistant, and every reference query was checked against the database by hand.
- A perfect score on a small set leaves no headroom. It shows the system is reliable on this schema, not that it generalizes to other databases.
- Several issues were found by the evaluation and fixed before the test split was run: the ambiguity checker wrongly asked for clarification on 3 of 18 clear dev questions, one prompt contained hints written for the eval questions (removed), and the model guessed the casing of category values (fixed by listing allowed values automatically from the data).

## Limitations

- **The retry loop has not been shown to improve accuracy.** It is implemented and unit-tested, but across more than 60 evaluation cases it fired once, for an unknown reason, and did not reproduce.
- **Schema retrieval was not ablated.** With 15 tables, most of the schema fits in the prompt anyway, so its benefit is untested. It matters for larger databases.
- **No external benchmark yet.** Spider and BIRD runs are not included.
- **Timeouts are retried.** A query that hits the 5-second timeout is retried once, which costs extra database time.
- **The query role can still read the embeddings table.** The validator blocks it, but a second database role would enforce it at the database level.
- **Shared rate limit on the live demo.** The demo uses a free Groq key limited to 8,000 tokens per minute, shared by all visitors. Each question uses a few thousand tokens, so simultaneous use can return an error. If that happens, wait about a minute and try again. There is no per-visitor request limit.
- **Synthetic data only.** No real customer data, and no personal-data handling.

## Run it locally

Requirements: Docker, Python 3.11, a free [Groq API key](https://console.groq.com).

1. Create `.env` in the project root:

```text
GROQ_API_KEY=your_key
DATABASE_URL=postgresql://postgres:postgres@localhost:5434/ecommerce
READONLY_DB_PASSWORD=choose_a_password
READONLY_DATABASE_URL=postgresql+psycopg2://analytics_reader:choose_a_password@localhost:5434/ecommerce
```

2. Install dependencies and start the database:

```bash
python -m venv .venv
.venv\Scripts\activate        # Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
docker compose up -d db
```

3. Load data, create the read-only role, and build the schema index (in this order):

```bash
python scripts/generate_data.py
python scripts/create_readonly_role.py
python scripts/setup_vector_store.py
python -m app.schema_indexer
```

4. Start everything:

```bash
docker compose up --build
```

API on `http://localhost:8000`, UI on `http://localhost:8501`.

Run the tests and the evaluation:

```bash
python -m unittest discover -s tests
python -m app.evaluator dev          # or: test, challenge
python -m scripts.probe_attacks      # adversarial probe
```

## Project layout

```text
app/        agent graph, SQL generation, validation, execution, retrieval, evaluator, API
frontend/   Streamlit UI
scripts/    schema, data generation, read-only role, vector store setup, probes
data/       evaluation cases and saved reports
tests/      validator, API, and retry tests
```