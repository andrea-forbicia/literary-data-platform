# Decisions

Technical and scope decisions, one record per decision, in the style of an
Architecture Decision Record: context, decision, alternatives considered, consequences.
New decisions are appended at the end; a decision that changes is marked as superseded,
not deleted.

## D1. Starting subset: English-language fiction, about 1800-1930

- **Status:** accepted (step 0.7.1)
- **Context:** both sources are far too large to work on in full, and the project
  develops on a small sample first. The subset has to give enough overlap between
  Project Gutenberg and Open Library for the entity resolution (slice 3), and texts
  that a RAG pipeline can index and be evaluated on.
- **Decision:** start with English-language fiction published roughly between 1800
  and 1930.
- **Alternatives considered:**
  - *Italian literature, same period.* More distinctive, but Gutenberg has far fewer
    Italian texts and Open Library covers Italian titles less well, so matching recall
    would be lower and harder to evaluate. It would also require a multilingual
    embedding model, with fewer and generally weaker options.
- **Consequences:**
  - The largest and best-covered part of both catalogues, so the entity resolution
    has many candidate matches to measure.
  - English-only embedding and language models are acceptable (see D3).
  - Any reviewer can judge the demo answers.
  - Less original dataset; Italian texts can be added in a later slice if time allows.

## D2. Books for the RAG: a mix designed to test the system

- **Status:** accepted (step 0.7.2)
- **Context:** an LLM already knows famous classics from its training data, so a
  correct answer about a well-known novel does not prove that retrieval works. Only an
  answer that cites the right passage, or a question the model cannot answer from
  memory, does.
- **Decision:** about 20 books, chosen to test the system rather than to be the most
  popular:
  - **Same-author groups**, where similar books make retrieval harder:
    - Jane Austen: *Pride and Prejudice*, *Emma*, *Persuasion*, *Northanger Abbey*
      (same setting and vocabulary).
    - Charles Dickens: *Great Expectations*, *A Tale of Two Cities*, *Oliver Twist*,
      *Hard Times* (long texts, many chunks).
    - Arthur Conan Doyle: *A Study in Scarlet*, *The Sign of the Four*,
      *The Hound of the Baskervilles* (same characters across books).
    - H. G. Wells: *The Time Machine*, *The War of the Worlds*, *The Invisible Man*
      (short novels, a different genre).
    - Mark Twain: *The Adventures of Tom Sawyer*, *Adventures of Huckleberry Finn*,
      *The Prince and the Pauper* (shared characters, dialect).
  - **Lesser-known titles**, which a model is unlikely to answer from memory:
    George Gissing, *The Odd Women*; Margaret Oliphant, *Miss Marjoribanks*;
    Charlotte Riddell, *The Uninhabited House*; Mary Elizabeth Braddon,
    *Lady Audley's Secret* (a middle case).
- **Alternatives considered:**
  - *The 20 most downloaded novels.* Familiar to everyone and easy to match to Open
    Library, but it is hard to show that answers come from retrieval and not from the
    model's memory, and one book per author gives few hard cases.
- **Consequences:**
  - The RAG evaluation can compare famous and lesser-known titles: if the model
    answers the famous ones without context but not the lesser-known ones, retrieval
    is shown to matter.
  - Austen, Dickens and Twain have many editions in Open Library, which exercises the
    duplicate-handling rule of the entity resolution early.
  - Choosing the books took more effort, and answers on lesser-known titles are
    harder to check by hand.
  - Ebook IDs and availability are not fixed yet: they are verified against the
    Gutenberg catalogue in step 1.4.

## D3. Local LLM and embedding model: postponed

- **Status:** postponed to stage 3 of slice 1 (step 0.7.3)
- **Context:** the development laptop cannot run local LLMs; the choice depends on
  the desktop PC's GPU memory and on the language of the texts.
- **Decision:** decide in stage 3 of slice 1. Because of D1, an English-only
  embedding model is acceptable.
- **Update (2026-11-27):** the laptop is no longer used. Development runs only on
  the desktop PC, whose RTX 4060 Ti has 16 GB of VRAM (checked with `nvidia-smi`).

## D4. Repository name: `literary-data-platform`

- **Status:** accepted (step 0.7.4)
- **Context:** the repository is the first thing a recruiter sees, and the target
  role is Data Engineer / Data & AI Engineer.
- **Decision:** keep `literary-data-platform` (Python package `literary_data_platform`).
- **Alternatives considered:**
  - *A product-like name such as `literary-assistant`.* It matches the user-facing
    product, but sounds like a chatbot app and hides the data engineering work (lake,
    Spark, warehouse, Airflow) that is the core of the project. Renaming would also
    mean changing the package, imports, `pyproject.toml` and docs.
- **Consequences:** the name signals the main role; the AI part is stated in the
  first line of the README and in the GitHub repository description.

## D5. Slice 1 tools: ruff, uv, PostgreSQL with pgvector

- **Status:** accepted (step 0.7.5)

### ruff for linting and formatting

- **Context:** code style and common bugs should be checked automatically, on every
  commit (pre-commit) and in CI.
- **Decision:** ruff, both `ruff check` and `ruff format`, configured in
  `pyproject.toml`. No black.
- **Alternatives considered:**
  - *black + flake8 + isort.* The classic combination, still common in existing
    projects, but three tools with three configurations and versions to keep aligned,
    and slower.
  - *pylint.* Deeper checks, but slow, noisy and heavy to configure.
- **Consequences:** one fast tool that covers the flake8 and isort rules, with a
  formatter largely compatible with black. It does not do pylint's deeper analysis,
  and type checking would need a separate tool (not used for now).

### uv for the Python environment and dependencies

- **Context:** the project must be reproducible: anyone cloning it, and the CI, must
  get exactly the same environment.
- **Decision:** uv manages the Python version (`.python-version`), the `.venv`, the
  dependencies and the lockfile `uv.lock`. CI runs `uv sync --locked`.
- **Alternatives considered:**
  - *pip + venv + requirements.txt.* Universal, but no real lockfile (transitive
    dependencies are not pinned without pip-tools) and the Python version is managed
    separately.
  - *Poetry.* Mature, with a lockfile and common in job postings, but slower, does not
    manage Python versions and uses partly its own `pyproject.toml` format.
- **Consequences:** identical environments locally and in CI, fast installs, and a
  standard `pyproject.toml` (PEP 621). uv is younger than pip and Poetry; the concepts
  (lockfile, dependency resolution) transfer to Poetry if a team uses it.

### PostgreSQL with pgvector as warehouse and vector store

- **Context:** slice 1 needs a warehouse (raw, staging, curated) and a vector index
  for the RAG, running locally at zero cost.
- **Decision:** PostgreSQL with the pgvector extension, which adds the `vector` type,
  vector distance operators and approximate indexes (HNSW, IVFFlat). The PostgreSQL
  version is pinned in stage 2 of slice 1.
- **Alternatives considered:**
  - *DuckDB as warehouse.* Columnar, embedded and very fast on aggregations and
    Parquet, but it runs inside a single process, so concurrent writers and readers
    (Airflow, Spark, the API) are harder to handle.
  - *A dedicated vector database (Qdrant, Chroma, Weaviate).* More vector-specific
    features, but one more service to run, and metadata lives apart from the vectors.
- **Consequences:**
  - One service is both the warehouse and the vector index.
  - Retrieval can filter on metadata with plain SQL (`JOIN`, `WHERE`, for example
    "only Austen's books").
  - PostgreSQL is common in job postings and supported by dbt.
  - It is row-oriented, so large analytical queries are slower than on a columnar
    warehouse. Fine at this project's scale; at real scale BigQuery or Snowflake would
    fit better.

## D6. Repository layout and Python version

- **Status:** accepted (phase 0)
- **Decision:** `src/` layout, with the code as an installed package
  (`literary_data_platform`); Python 3.12 (`requires-python = ">=3.12"`).
- **Why the `src/` layout:** tests import the installed package, not the current
  folder, so packaging mistakes show up in the tests instead of being hidden.
- **Alternatives considered:** *flat layout* (package at the repository root):
  simpler, but tests can pass by importing local files even when the installed
  package is broken.
- **Why Python 3.12:** a recent, stable version supported by the libraries planned
  for the project (to be rechecked when PySpark and Airflow are added).

## D7. HTTP client for downloads: `requests`

- **Status:** accepted (step 1.4)
- **Context:** ingestion downloads the Gutenberg catalogue and a few text files, later
  the Open Library dumps. Downloads are sequential and deliberately slow (polite
  access), and large files must be streamed to disk.
- **Decision:** `requests`, with `stream=True` and `iter_content` for streaming.
- **Alternatives considered:**
  - *`httpx`.* Almost the same API, with async support and default timeouts, and it is
    already used under the hood by FastAPI's test client. Async brings nothing to a
    sequential, rate-limited download, and `httpx` appears less often in job postings.
- **Consequences:**
  - `requests` has no default timeout: every call must pass an explicit `timeout`,
    otherwise a stalled connection can hang forever.
  - Retry with backoff is not built in and has to be added (see the retry decision).

## D8. Retry with backoff: our own loop around the whole download

- **Status:** accepted (step 1.4)
- **Context:** a streamed download can fail in two places: when the request is made
  (timeout, 429, 5xx) or halfway through, while the body is being read in chunks.
  Sources can also ask the client to wait: on 2026-11-17 every Gutenberg page answered
  `503` with `Retry-After: 3600`.
- **Decision:** a small retry loop written in the project that retries the whole
  download (request and body) on transient errors only, with exponential backoff. It
  honours `Retry-After` up to a configurable maximum; above it, it stops with a
  "source unavailable" error instead of waiting.
- **Alternatives considered:**
  - *`urllib3.Retry` mounted on a `requests` `HTTPAdapter`.* Declarative and standard,
    and it honours `Retry-After` on its own, but it only covers the request: a
    connection dropped while reading the body is not retried. It would also wait out a
    one-hour `Retry-After` silently unless that behaviour is turned off.
  - *A retry library such as `tenacity`.* One more dependency for about 30 lines of
    logic.
- **Consequences:** one mechanism covers both failure points, every attempt is logged,
  and waiting time is bounded. The loop is project code, so it needs its own tests.

## D9. Mocking HTTP in tests: `responses`

- **Status:** accepted (step 1.4)
- **Context:** download code must be tested without real network calls, which would
  be slow, flaky and would hit the real sources on every CI run.
- **Decision:** the `responses` library (development dependency), with its ordered
  registry so that a sequence such as "503, 503, then 200" is served in order.
- **Alternatives considered:**
  - *A fake session written in the tests.* No dependency and full control, but the
    tests would not go through the real `requests` and `urllib3` code, so a fake that
    behaves differently from the real thing (decompression, truncated bodies) would let
    bugs through.
- **Consequences:** the tests exercise the real transport stack. For example, a body
  shorter than its `Content-Length` makes `urllib3` raise `ChunkedEncodingError`, exactly
  as in production.

## D10. Concurrent downloads of the same file: exclusive `flock` on a lock file

- **Status:** accepted (step 1.4, review of the downloader)
- **Context:** the `.part` name is fixed, so two runs downloading the same file at the
  same time (an Airflow retry started while the first try is still alive, or two
  backfills) write into the same file. The review reproduced it with a slow local
  server and a source that changed between the two requests: the final file mixed
  both versions, while the run that renamed it reported the SHA-256 of the bytes it
  had received, not of the bytes on disk.
- **Decision:** each download holds an exclusive `fcntl.flock` on `<name>.lock` next to
  the final file. A second run waits, then checks again whether the final file exists
  and skips it. The lock file is never deleted.
- **Alternatives considered:**
  - *A unique `.part` name per run (`tempfile.mkstemp`).* The usual pattern and no
    locking, but both runs download the file, so the source gets a duplicate request,
    and a run killed with `kill -9` leaves orphan `.part` files with random names.
  - *Creating the lock with `O_CREAT | O_EXCL`.* Portable, but a crashed run leaves a
    stale lock that blocks every later run until someone removes it by hand.
- **Consequences:**
  - The kernel releases a `flock` when the file is closed, also when the process is
    killed, so there are no stale locks.
  - `flock` is Unix-only: fine, because everything runs in WSL2 or in containers.
  - An empty `.lock` file stays next to each downloaded file. Deleting it would let a
    third run lock a new file with the same name while a second one still waits on
    the old one, and two downloads would run at once again.
  - The same review added `fsync` before the rename, so that after a power cut a file
    with its final name is still a whole file.

## D11. Gutenberg metadata for slice 1: the CSV catalogue only

- **Status:** accepted (step 1.4, piece 2)
- **Context:** Project Gutenberg publishes its catalogue in several bulk files. On the
  PGLAF mirror (`https://gutenberg.pglaf.org/cache/epub/feeds/`, 2026-11-27) the CSV
  `pg_catalog.csv.gz` is 5.6 MB (21 MB uncompressed, dated 2026-11-08), and the RDF
  archive `rdf-files.tar.bz2` is 127 MB (dated 2026-11-15). Slice 1 needs the catalogue
  to find the ebook IDs of the 20 books of D2 and for one SQL query in stage 2.
- **Decision:** download only `pg_catalog.csv.gz` in slice 1.
- **Alternatives considered:**
  - *CSV plus RDF.* Richer metadata (expected, to be checked on the files: agents
    with IDs, separate birth and death years, file formats with URLs, download
    counts), useful later for entity resolution. But it is 20 times larger, holds one
    RDF/XML file per book (over 75,000), and needs an XML parser with namespaces:
    work that slice 1 does not need.
- **Consequences:**
  - Authors are free text with life dates (`"Jefferson, Thomas, 1743-1826"`), with no
    author ID; multi-valued fields are separated by `"; "`.
  - `Issued` is the date a book entered Project Gutenberg, not its publication year,
    so the 1800-1930 period of D1 can only be estimated from the authors' life dates.
  - The RDF can be added in slice 3 if entity resolution needs it.
