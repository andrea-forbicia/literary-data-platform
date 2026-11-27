# Stato attuale

Aggiornare questo file alla fine di ogni sessione.

- **Fetta in corso:** 1, tappa 1 - Repository e CI
- **Ultimo passaggio completato:** 0.7, tranne 0.7.3 (decisioni D1-D6 in `docs/decisions.md`: narrativa inglese 1800-1930, 20 libri per il RAG, nome del repository, ruff, uv, PostgreSQL con pgvector, layout `src/`, Python 3.12).
- **Passo in corso:** 1.4, diviso in tre pezzi:
  1. Downloader generico (`ingestion/download.py`: streaming, `.part` atomico, idempotenza, retry con backoff e `Retry-After` limitato, SHA-256): fatto (PR #6). Review del 2026-11-27 in una sessione nuova: corretta la corsa tra due download dello stesso file (lock con `flock`, D10), aggiunti `fsync` prima della rinomina e test mancanti. PR della correzione aperta. Decisioni D7-D10.
  2. Catalogo di Gutenberg (CSV, RDF da decidere): da fare. Il 2026-11-17 il sito era in manutenzione (503, `Retry-After: 3600`): prima verificare su *Offline Catalogs* e *Robot Access Policy* URL, colonne e regole, e annotarli in `docs/dataset.md`.
  3. Testi dei 20 libri di D2 da un mirror, con ebook ID verificati sul catalogo: da fare.
- **Prossimo passo:** merge della PR di correzione del downloader, poi il pezzo 2 quando il sito di Gutenberg risponde. Nel pezzo 2 il percorso del catalogo deve contenere la data dello snapshot, perché il downloader non riscarica un file che esiste già. In una prossima sessione, nuove domande sulle voci della fase 0 ancora aperte.
- **Quiz fase 0 (2026-11-17):** spuntata solo la voce su Docker. Da approfondire prima della prossima domanda (sezioni 2-4 di `docs/learning/fase-0.md`):
  - CI: la CI controlla, la branch protection impone il merge con CI verde; cosa fa `uv sync --locked` con un lockfile non allineato.
  - Branch e PR: motivi concreti (`main` sempre funzionante, PR come punto della CI, revert e bisect, descrizione come documentazione).
  - Fonti: nessuna chiave comune, matching approssimato su titolo e autore, misurato con precisione e recall.
- **Note aperte:**
  - 0.7.3 (LLM ed embeddings) rimandata alla tappa 3 della fetta 1: la casella generale 0.7 resta aperta fino ad allora.
  - Ebook ID dei 20 libri di D2 da verificare sul catalogo di Gutenberg nel passo 1.4.
  - Ambiente di sviluppo (2026-11-27): solo il PC fisso, il portatile non c'è più. Fatto: Ubuntu in WSL2, repository in `~/developer/literary-data-platform`, uv, GNU Make 4.4.1, git; la GPU (RTX 4060 Ti, 16 GB di VRAM) è visibile da WSL2. Da fare:
    - installare Docker Engine dentro Ubuntu (serve dalla tappa 2 della fetta 1);
    - installare Ollama dentro Ubuntu (serve dalla tappa 3);
    - creare `.wslconfig` in `C:\Users\<utente>\` con il budget del `CLAUDE.md` (20 GB, 12 processori): ora WSL2 vede 15 GB, il valore predefinito.
  - Aggiungere `.env.example` (`.gitattributes` con fine riga LF esiste già).
  - GitHub: aggiungere il revisore come collaborator (ruolo Write). Fatto il 2026-11-17: ruleset `protect-main` su `main` (PR obbligatoria con 0 approvazioni, check `lint-and-test` richiesto e branch aggiornato, niente force push né cancellazione, bypass vuoto), secret scanning e push protection attivi.
  - Claude Code: permessi `ask` in `.claude/settings.json` per `terraform apply`/`destroy`, `docker compose down -v`, `docker volume rm`, `docker system prune`, `git push --force`, `gcloud`; skill `/quiz-fase` per il quiz di fine fetta; valutare l'output style "Learning".
  - Rispondere alle domande del revisore: ore a settimana, ruoli e annunci di riferimento, data di inizio candidature, livello con Python, SQL e Docker.
