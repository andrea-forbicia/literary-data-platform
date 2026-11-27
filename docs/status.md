# Stato attuale

Aggiornare questo file alla fine di ogni sessione.

- **Fetta in corso:** 1, tappa 1 - Repository e CI
- **Ultimo passaggio completato:** 0.7, tranne 0.7.3 (decisioni D1-D6 in `docs/decisions.md`: narrativa inglese 1800-1930, 20 libri per il RAG, nome del repository, ruff, uv, PostgreSQL con pgvector, layout `src/`, Python 3.12).
- **Passo in corso:** 1.4, diviso in tre pezzi:
  1. Downloader generico (`ingestion/download.py`: streaming, `.part` atomico, idempotenza, retry con backoff e `Retry-After` limitato, SHA-256): fatto (PR #6). Review del 2026-11-27 in una sessione nuova: corretta la corsa tra due download dello stesso file (lock con `flock`, D10), aggiunti `fsync` prima della rinomina e test mancanti. Correzione nel merge su `main` con la PR #8. Decisioni D7-D10.
  2. Catalogo di Gutenberg: codice e test fatti (`ingestion/gutenberg.py`, `make gutenberg-catalog`), solo CSV (D11), percorso con la data del download (D12), dal mirror PGLAF. Fatti verificati in `docs/dataset.md`. Download vero non ancora lanciato: prima leggere *Offline Catalogs* e *Robot Access Policy*, ancora irraggiungibili il 2026-11-27 (sito in manutenzione, `Retry-After: 21600`).
  3. Testi dei 20 libri di D2 da un mirror, con ebook ID verificati sul catalogo: da fare.
- **Prossimo passo:** quando il sito di Gutenberg risponde, leggere le due pagine di regole, poi lanciare `make gutenberg-catalog` e cercare gli ebook ID dei 20 libri di D2; poi il pezzo 3.
- **Quiz fase 0:** completo. Il 2026-11-17 spuntata la voce su Docker, il 2026-11-27 le altre tre (CI, branch e PR, fonti). Tutte le voci "Capire e saper spiegare" della fase 0 sono spuntate; la fase 0 si chiude con la 0.7.3 nella tappa 3. Da allenare: le prime risposte erano parole chiave e sono diventate complete solo con le domande di approfondimento. A colloquio serve la risposta intera, con un esempio concreto:
  - Branch e PR: citare anche la descrizione della PR come documentazione; esempio del revert della PR #8 (squash merge: `git revert <commit>`; con un merge commit serve `-m 1`).
  - Fonti: dire cosa porta ciascuna (Open Library catalogo e dati sporchi, Gutenberg testi per il RAG) e definire precisione e recall sul caso concreto: precisione = quota corretta tra le coppie abbinate, recall = quota trovata tra i libri di Gutenberg che hanno davvero un'opera su Open Library.
- **Note aperte:**
  - 0.7.3 (LLM ed embeddings) rimandata alla tappa 3 della fetta 1: la casella generale 0.7 resta aperta fino ad allora.
  - Ebook ID dei 20 libri di D2 da verificare sul catalogo di Gutenberg nel passo 1.4.
  - Ambiente di sviluppo (2026-11-27): solo il PC fisso, il portatile non c'è più. Fatto: Ubuntu in WSL2, repository in `~/developer/literary-data-platform`, uv, GNU Make 4.4.1, git; la GPU (RTX 4060 Ti, 16 GB di VRAM) è visibile da WSL2. Da fare:
    - installare Docker Engine dentro Ubuntu (serve dalla tappa 2 della fetta 1);
    - installare Ollama dentro Ubuntu (serve dalla tappa 3);
    - creare `.wslconfig` in `C:\Users\<utente>\` con il budget del `CLAUDE.md` (20 GB, 12 processori): ora WSL2 vede 15 GB, il valore predefinito.
  - GitHub: aggiungere il revisore come collaborator (ruolo Write). Fatto il 2026-11-17: ruleset `protect-main` su `main` (PR obbligatoria con 0 approvazioni, check `lint-and-test` richiesto e branch aggiornato, niente force push né cancellazione, bypass vuoto), secret scanning e push protection attivi.
  - Claude Code: permessi `ask` in `.claude/settings.json` per `terraform apply`/`destroy`, `docker compose down -v`, `docker volume rm`, `docker system prune`, `git push --force`, `gcloud`; skill `/quiz-fase` per il quiz di fine fetta; valutare l'output style "Learning".
  - Rispondere alle domande del revisore: ore a settimana, ruoli e annunci di riferimento, data di inizio candidature, livello con Python, SQL e Docker.
