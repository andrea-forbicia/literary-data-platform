# Stato attuale

Aggiornare questo file alla fine di ogni sessione.

- **Fetta in corso:** 1, tappa 1 - Repository e CI
- **Ultimo passaggio completato:** 0.1 (repository GitHub con README, licenza MIT e `.gitignore` per Python)
- **Prossimo passo:** 0.2
- **Note aperte:**
  - Annotare in `docs/decisions.md` le scelte della fetta 1 (ruff, uv, PostgreSQL con pgvector).
  - Decidere l'ambiente di sviluppo: tutto dentro WSL2 (repository, `.venv`, `make`, con Ollama su Windows raggiunto via `host.docker.internal`) oppure Git Bash su Windows. Oggi il repository è sotto `C:\`.
  - Aggiungere `.gitattributes` (fine riga LF) e `.env.example` nei primi commit.
  - GitHub: aggiungere il revisore come collaborator (ruolo Write), proteggere `main` (pull request obbligatoria e CI verde), attivare secret scanning e push protection.
  - Claude Code: permessi `ask` in `.claude/settings.json` per `terraform apply`/`destroy`, `docker compose down -v`, `docker volume rm`, `docker system prune`, `git push --force`, `gcloud`; skill `/quiz-fase` per il quiz di fine fetta; valutare l'output style "Learning".
  - Rispondere alle domande del revisore: ore a settimana, ruoli e annunci di riferimento, data di inizio candidature, livello con Python, SQL e Docker.
