# Stato attuale

Aggiornare questo file alla fine di ogni sessione.

- **Fetta in corso:** 1, tappa 1 - Repository e CI
- **Ultimo passaggio completato:** 0.7, tranne 0.7.3 (decisioni D1-D6 in `docs/decisions.md`: narrativa inglese 1800-1930, 20 libri per il RAG, nome del repository, ruff, uv, PostgreSQL con pgvector, layout `src/`, Python 3.12).
- **Prossimo passo:** merge della PR con la nota `docs/learning/fase-0.md`, poi domande sulla fase 0 (una alla volta) per spuntare le voci "Capire e saper spiegare", poi 1.4 (download del catalogo e dei testi di Gutenberg).
- **Note aperte:**
  - 0.7.3 (LLM ed embeddings) rimandata alla tappa 3 della fetta 1: la casella generale 0.7 resta aperta fino ad allora.
  - Ebook ID dei 20 libri di D2 da verificare sul catalogo di Gutenberg nel passo 1.4.
  - Ambiente di sviluppo: deciso WSL2 (Ubuntu) sul PC fisso. Per ora si lavora sul portatile (12 GB di RAM, i7-4702MQ 4 core / 8 thread) con Git Bash, repository in `C:\Users\user\Documents\projects\literary-data-platform`, senza distribuzione Ubuntu. Sul portatile `.wslconfig` limita WSL2 e Docker Desktop a 4 GB e 4 processori. Sul portatile niente Spark né LLM locali: solo i passaggi leggeri della fetta 1.
  - Al passaggio al PC fisso: installare Ubuntu, integrazione con Docker Desktop, `.wslconfig` con il budget del `CLAUDE.md`, clonare il repository in `~/projects/literary-data-platform`.
  - Aggiungere `.env.example` (`.gitattributes` con fine riga LF esiste già).
  - GitHub: aggiungere il revisore come collaborator (ruolo Write), proteggere `main` (pull request obbligatoria e CI verde), attivare secret scanning e push protection.
  - Claude Code: permessi `ask` in `.claude/settings.json` per `terraform apply`/`destroy`, `docker compose down -v`, `docker volume rm`, `docker system prune`, `git push --force`, `gcloud`; skill `/quiz-fase` per il quiz di fine fetta; valutare l'output style "Learning".
  - Rispondere alle domande del revisore: ore a settimana, ruoli e annunci di riferimento, data di inizio candidature, livello con Python, SQL e Docker.
