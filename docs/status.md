# Stato attuale

Aggiornare questo file alla fine di ogni sessione.

- **Fetta in corso:** 1, tappa 1 - Repository e CI
- **Ultimo passaggio completato:** 0.5 (Makefile con setup, lint, format e test; GNU Make 4.4.1 installato con winget. `up`, `down` e `run-pipeline` arrivano con i file che li richiedono)
- **Prossimo passo:** 0.6
- **Note aperte:**
  - Annotare in `docs/decisions.md` le scelte della fetta 1 (ruff, uv, PostgreSQL con pgvector), il layout `src/` e Python 3.12.
  - Ambiente di sviluppo: deciso WSL2 (Ubuntu) sul PC fisso. Per ora si lavora sul portatile (12 GB di RAM, i7-4702MQ 4 core / 8 thread) con Git Bash, repository in `C:\Users\user\Documents\projects\literary-data-platform`, senza distribuzione Ubuntu. Sul portatile `.wslconfig` limita WSL2 e Docker Desktop a 4 GB e 4 processori. Sul portatile niente Spark né LLM locali: solo i passaggi leggeri della fetta 1.
  - Al passaggio al PC fisso: installare Ubuntu, integrazione con Docker Desktop, `.wslconfig` con il budget del `CLAUDE.md`, clonare il repository in `~/projects/literary-data-platform`.
  - Aggiungere `.gitattributes` (fine riga LF) e `.env.example` nei primi commit.
  - GitHub: aggiungere il revisore come collaborator (ruolo Write), proteggere `main` (pull request obbligatoria e CI verde), attivare secret scanning e push protection.
  - Claude Code: permessi `ask` in `.claude/settings.json` per `terraform apply`/`destroy`, `docker compose down -v`, `docker volume rm`, `docker system prune`, `git push --force`, `gcloud`; skill `/quiz-fase` per il quiz di fine fetta; valutare l'output style "Learning".
  - Rispondere alle domande del revisore: ore a settimana, ruoli e annunci di riferimento, data di inizio candidature, livello con Python, SQL e Docker.
