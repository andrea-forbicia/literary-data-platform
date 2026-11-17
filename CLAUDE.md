# CLAUDE.md

Istruzioni per Claude Code in questo repository. Questo file contiene solo ciò che vale in ogni sessione; i dettagli stanno nei documenti elencati in fondo.

## Progetto

**Assistente letterario:** piattaforma dati end-to-end su dati aperti di letteratura (Open Library e Project Gutenberg), con un livello AI che risponde a domande sul catalogo e sui testi dei classici citando le fonti. È un progetto portfolio per colloqui da Data Engineer / Data & AI Engineer.

Flusso: ingestione batch e streaming → data lake → PySpark → collegamento tra le due fonti → warehouse (raw, staging, curated) → Airflow → controlli di qualità → RAG e text-to-SQL → API FastAPI.

## Stato attuale

Lo stato cambia a ogni sessione, quindi sta in un file separato, importato qui sotto. Aggiornare `docs/status.md` alla fine di ogni sessione.

@docs/status.md

## Come lavorare con me

Il progetto serve prima di tutto a **imparare**: a colloquio devo saper spiegare ogni parte e ogni scelta senza guardare il codice.

1. **Chi scrive il codice.** Tutto il codice lo scrivi tu; io non scrivo codice a mano. Il mio lavoro è capire ogni parte e ogni scelta abbastanza bene da spiegarla a colloquio.
2. **Spiegami passo passo quello che fai.** Per ogni pezzo: cosa fa, perché è fatto così, quali alternative c'erano e cosa succede nei casi limite (per esempio "cosa succede se rilanci due volte?", "perché Parquet qui?"). Insisti di più sui pezzi che a colloquio chiedono di disegnare o spiegare alla lavagna: modello dei dati e query SQL, trasformazioni Spark (per esempio la normalizzazione delle date), punteggio e soglia dell'entity resolution, chunking e retrieval del RAG, controlli di qualità. Quando aiuta a capire, rompi qualcosa apposta e mostrami cosa succede.
3. **Domande:** una per volta, mai un elenco.
4. **Una fetta e un passaggio alla volta**, nell'ordine delle fette indicato in `docs/roadmap.md`. Leggi solo i passaggi della fetta in corso.
5. **Prima di ogni fetta o di uno strumento nuovo:** spiegami in poche righe i concetti nuovi, indicami la documentazione ufficiale da leggere (20-30 minuti al massimo) e segnala le scelte aperte.
6. **Scelte tecniche:** proponi due opzioni con pro e contro e aspetta la mia decisione. Il criterio è lo strumento che compare negli annunci a cui voglio rispondere, non lo strumento migliore in assoluto. Dopo la mia decisione, aggiorni tu `docs/decisions.md`; i numeri misurati li annoti tu in `docs/metrics.md`.
7. **Review:** controlla correttezza, leggibilità, test e casi limite, e spiega il perché di ogni osservazione. Il codice che hai scritto tu va rivisto in una sessione nuova, non in quella in cui l'hai scritto.
8. **Dopo ogni passaggio:** test e lint verdi, casella spuntata in `docs/roadmap.md`, commit. La descrizione di ogni pull request la scrivi tu, in inglese: cosa fa il codice, perché è fatto così e le alternative scartate. Deve essere abbastanza chiara da poterla usare per ripassare prima di un colloquio.
9. **A fine fetta, quando te lo chiedo:** fammi 5 domande da colloquio sui passaggi della fetta (almeno una in inglese), valuta le risposte e dimmi cosa approfondire. Le voci "Capire e saper spiegare" si spuntano solo se rispondo bene senza appunti.
10. Non aggiungere funzionalità fuori dalla roadmap e non inventare comandi, risultati o numeri. I numeri reali vanno in `docs/metrics.md`; nel README e nel CV solo valori misurati.

## Vincoli

- **Costo zero e local-first.** Tutto gira in locale con strumenti open source. Il cloud (GCP, free tier) è solo nella fase 9, opzionale.
- **Piccolo e finito prima di grande.** Prima una versione sottile ma completa dall'inizio alla fine (fetta 1), poi uno strumento nuovo per volta. Tagliare è meglio che lasciare a metà.
- **Solo dati pubblici.** Niente dati di clienti, di datori di lavoro o personali.
- **Rispetto delle fonti.** Dump mensili per Open Library, file di catalogo e mirror per Project Gutenberg. Mai scraping dei siti né chiamate massive alle API.
- **Sottoinsieme prima, volume dopo.** Si sviluppa su un campione piccolo e si allarga solo quando la pipeline funziona.
- **Nessun segreto nel repository.** Solo variabili d'ambiente e `.env` ignorato da git, con `.env.example`.
- **Riproducibile.** Chi clona il repository avvia tutto con i comandi del README.

## Azioni che richiedono la mia conferma esplicita

- Cancellare o sovrascrivere dati in `raw/`, bucket dell'object storage o volumi Docker (`docker volume rm`, `docker compose down -v`, `docker system prune`).
- Eseguire `terraform apply` o `destroy`, qualsiasi comando `gcloud`, o creare risorse cloud.
- Usare API a pagamento.
- `git push --force`, riscrittura della cronologia, cancellazione di branch.
- Scaricare più di 5 GB di dati in una volta. Il solo dump delle edizioni di Open Library dovrebbe superare questa soglia (da verificare nel passo 1.1).

## Macchina di sviluppo

- **PC fisso:** Intel Core i7-12700K (12 core, 20 thread), 32 GB di RAM, SSD NVMe da 1 TB con circa 465 GB liberi, NVIDIA RTX 4060 Ti.
- **Portatile (temporaneo):** 12 GB di RAM, i7-4702MQ 4 core / 8 thread. Git Bash su Windows, repository sotto `C:\`, WSL2 limitato a 4 GB da `.wslconfig`. Adatto solo a lavori leggeri: niente Spark né LLM locali. Lo stato del passaggio al PC fisso è in `docs/status.md`.
- **Sistema (PC fisso):** Windows con WSL2 (Ubuntu). Repository, ambiente Python gestito con uv (`.venv`) e `make` stanno dentro WSL2, in `~/projects/literary-data-platform`. Docker Desktop con backend WSL2 e integrazione attiva per la distribuzione Ubuntu. Ollama resta su Windows per usare la GPU e i container lo raggiungono tramite `host.docker.internal`.
- **Budget di risorse, valori di partenza da ritoccare misurando:**
  - Docker/WSL2: al massimo 20 GB di RAM e 12 thread, per lasciare margine a IDE e browser.
  - Spark: modalità `local[8]`, 8 GB di memoria per il driver.
  - Ollama: usare la GPU. Verificare la VRAM con `nvidia-smi` (8 o 16 GB) e scegliere un modello che ci stia interamente.
  - Data lake locale: al massimo 100 GB su disco.
- **Attenzioni per Windows:** fine riga LF (`.gitattributes`), comandi eseguiti da WSL2 o nei container, dati e volumi nel filesystem di WSL2 e mai sotto `/mnt/c` (è molto più lento).

## Stack

Quando una scelta è fatta, sostituire le alternative con la sola scelta e la versione.

| Livello | Strumento | Stato |
| --- | --- | --- |
| Linguaggi | Python 3.11+, SQL | deciso |
| Ambiente Python | uv, versione da fissare | deciso (fetta 1) |
| Lint e formato | ruff (`ruff check` e `ruff format`, senza black), versione da fissare | deciso (fetta 1) |
| Warehouse | PostgreSQL, versione da fissare | deciso (fetta 1) |
| Vector database | pgvector dentro PostgreSQL | deciso (fetta 1) |
| Embeddings | sentence-transformers, modello da scegliere | da decidere (fetta 1, tappa 3) |
| LLM | Ollama, modello da scegliere | da decidere (fetta 1, tappa 3) |
| Data lake | Object storage con API S3. MinIO community non è più mantenuto: alternative SeaweedFS o Garage. Il codice usa l'API S3, così il backend si cambia solo da configurazione | da decidere (fetta 2) |
| Trasformazione | PySpark in Docker | deciso |
| Livello curated | dbt in PostgreSQL oppure solo Spark e SQL | da decidere (fetta 3) |
| Qualità del dato | pytest e test di dbt, oppure Great Expectations | da decidere (fetta 3) |
| Orchestrazione | Airflow in Docker Compose | deciso |
| API | FastAPI, Pydantic | deciso |
| CI/CD | GitHub Actions | deciso |
| Streaming | Redpanda oppure Kafka | da decidere (dopo la fetta 4, se resta tempo) |
| Infrastruttura | Terraform, solo `validate` fino alla fase 9 | dopo la fetta 4, se resta tempo |

## Convenzioni

- **Lingua:** codice, commenti, commit, README e documentazione tecnica in inglese. Le note in `docs/learning/` e `docs/interview.md` possono essere in italiano. Con me comunica in italiano.
- **Python:** ruff per lint e formato, type hints sulle funzioni pubbliche, `logging` al posto di `print`.
- **Test:** pytest; ogni modulo nuovo ha almeno un test; suite verde prima di ogni commit.
- **Commit:** piccoli, nel formato `tipo: descrizione` (`feat`, `fix`, `docs`, `test`, `chore`, `refactor`).
- **Branch e PR:** un branch per funzionalità e una pull request con descrizione, anche lavorando da solo.
- **Configurazione:** nessun valore fisso nel codice; dipendenze con versioni fissate.
- **Docker:** immagini leggere, nessun segreto nelle immagini.

## Comandi

Target del `Makefile` (GNU Make; sul portatile installato con winget). Tutti usano `uv run`, quindi le versioni fissate in `uv.lock`:

- `make setup`: crea `.venv` da `uv.lock` (`uv sync --locked`) e installa il hook di pre-commit
- `make lint`: `ruff check .` e `ruff format --check .`, senza modificare i file (è quello che esegue la CI)
- `make format`: corregge con `ruff check --fix .` e riformatta con `ruff format .`
- `make test`: esegue tutta la suite pytest
- Singolo test: `uv run pytest tests/test_file.py::nome_test`

Da aggiungere quando esisteranno i file che servono: `make up` / `make down` (stack Docker Compose, fetta 1 tappa 2) e `make run-pipeline` (pipeline completa).

## Struttura del repository

Layout `src/`: il codice Python è un pacchetto installato (`literary_data_platform`) e i test lo importano da lì, non dalla cartella corrente.

```
src/literary_data_platform/
  ingestion/   download dump e catalogo, producer e consumer dello streaming
  transform/   job PySpark e SQL, entity resolution
  quality/     controlli sulla qualità del dato
  ai/          chunking, embeddings, retrieval, RAG, text-to-SQL, valutazione
  api/         FastAPI
dags/          DAG Airflow (sottili: chiamano il codice del pacchetto)
infra/         Terraform
tests/
docs/          documenti di riferimento (vedi sotto)
```

## Documenti di riferimento

Da leggere solo quando servono, non a ogni sessione.

- `docs/status.md`: stato attuale (importato in questo file).
- `docs/roadmap.md`: ordine delle fette, fasi, passaggi, priorità e checklist. Leggere solo i passaggi della fetta in corso.
- `docs/dataset.md`: fonti, licenze, uso nel progetto e strategia di sottoinsieme.
- `docs/decisions.md`: scelte tecniche con motivazioni e alternative scartate.
- `docs/metrics.md`: numeri reali misurati.
- `docs/learning/fase-N.md`: le mie note per fase.
- `docs/interview.md`: domande da colloquio e risposte preparate.
