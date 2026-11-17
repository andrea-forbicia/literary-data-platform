# Fase 0 - Preparazione

Note di ripasso per il colloquio. Per ogni argomento: il concetto, come è fatto nel progetto, le alternative e i casi limite. In fondo, le domande probabili.

Risultato della fase: repository ordinato, CI verde dal primo commit, decisioni iniziali scritte in `docs/decisions.md`.

---

## 1. Container e Docker

### Il concetto

- **Immagine:** un pacchetto in sola lettura con tutto quello che serve per far girare un programma: file di sistema, librerie, runtime (per esempio Python 3.12), codice e configurazione. Si costruisce da un `Dockerfile`, a strati (*layer*). Ogni istruzione crea uno strato, e gli strati invariati restano in cache.
- **Container:** un'istanza in esecuzione di un'immagine, cioè un processo isolato (filesystem, rete e processi suoi) che però usa il kernel del sistema ospite. L'immagine è la "classe", il container è l'"oggetto".
- **Volume:** spazio su disco gestito da Docker che sopravvive al container. Il container è usa e getta; i dati che devono restare (per esempio il database PostgreSQL) stanno nei volumi.
- **Docker Compose:** un file YAML che descrive più servizi insieme (PostgreSQL, Airflow, l'API), con reti, volumi e variabili d'ambiente. `docker compose up` avvia tutto, `docker compose down` lo ferma.

### Container contro macchina virtuale

| | Container | Macchina virtuale |
| --- | --- | --- |
| Kernel | condiviso con l'host | ne ha uno suo |
| Avvio | secondi | minuti |
| Peso | decine o centinaia di MB | GB |
| Isolamento | buono, ma meno forte | più forte |

Su Windows i container Linux non possono usare il kernel di Windows: Docker Desktop li fa girare dentro la macchina virtuale leggera di WSL2, che ha un kernel Linux. Per questo `.wslconfig` limita la RAM e i processori di Docker.

### Perché rende il progetto riproducibile

Il classico problema è "sul mio PC funziona": versioni diverse di Python, di PostgreSQL o delle librerie di sistema, o un sistema operativo diverso. Con Docker:
- la versione di ogni servizio è scritta nel file (per esempio un tag preciso dell'immagine di PostgreSQL), quindi chi clona il repository ottiene la stessa versione;
- non serve installare PostgreSQL o Airflow sulla macchina: basta Docker;
- l'ambiente è lo stesso in locale, in CI e nel cloud.

### Nel progetto

Nella fase 0 Docker è solo installato (passo 0.3); il primo `docker-compose.yml`, con PostgreSQL e pgvector, arriva nella tappa 2 della fetta 1. Regole già fissate nel `CLAUDE.md`:
- immagini leggere e con versione fissata (mai `latest`, che cambia nel tempo e rompe la riproducibilità);
- nessun segreto nelle immagini: password e chiavi solo da variabili d'ambiente e `.env`, che è ignorato da git;
- dati e volumi nel filesystem di WSL2, mai sotto `/mnt/c`, che è molto più lento.

### Casi limite

- **`docker compose down` contro `docker compose down -v`:** il primo ferma e rimuove i container, ma i volumi restano, quindi al prossimo `up` i dati ci sono ancora. Il secondo cancella anche i volumi, cioè i dati. Per questo `-v`, `docker volume rm` e `docker system prune` richiedono conferma esplicita.
- **Rilanciare `docker compose up` due volte:** se i container sono già avviati e la configurazione non è cambiata, non succede niente; se è cambiata, Compose ricrea solo i servizi modificati.
- **Container contro immagine con lo stesso nome:** modificare un file dentro un container in esecuzione non cambia l'immagine; quando il container viene ricreato, la modifica è persa.

---

## 2. La CI e la GitHub Action del progetto

### Il concetto

**CI (Continuous Integration):** a ogni modifica proposta, un server pulito scarica il codice ed esegue controlli automatici (lint, test). Se un controllo fallisce, la modifica non entra in `main`. Serve a scoprire i problemi subito, quando sono piccoli e si sa quale commit li ha causati, e a non dipendere dalla memoria di chi sviluppa ("ho lanciato i test?").

CD (Continuous Delivery/Deployment) è il passo dopo: rilasciare automaticamente ciò che ha passato la CI. Nel progetto per ora c'è solo la CI.

### Cosa fa `.github/workflows/ci.yml`

| Parte | Cosa fa | Perché |
| --- | --- | --- |
| `on: push` su `main` e `pull_request` | parte su ogni pull request e su ogni push in `main` | la PR viene controllata prima del merge, `main` dopo |
| `permissions: contents: read` | il token del workflow può solo leggere il repository | principio del privilegio minimo: se un'azione esterna fosse compromessa, non potrebbe scrivere |
| `concurrency` con `cancel-in-progress` | un nuovo push sullo stesso branch annulla il run precedente ancora in corso | non si spreca tempo su codice già superato |
| `timeout-minutes: 10` | ferma un run bloccato | senza timeout, un test appeso consumerebbe minuti fino al limite di GitHub |
| `actions/checkout`, `astral-sh/setup-uv` con versione fissata | scarica il codice e installa uv in una versione precisa | riproducibilità: un aggiornamento delle azioni non cambia la CI all'improvviso |
| `enable-cache: true` | conserva la cache dei pacchetti tra un run e l'altro | installazioni più veloci |
| `uv sync --locked` | installa Python 3.12 (da `.python-version`) e le versioni esatte di `uv.lock` | se `uv.lock` non è allineato con `pyproject.toml`, **fallisce** invece di aggiornarlo in silenzio |
| `make lint` | `ruff check .` e `ruff format --check .` | stessi comandi che uso in locale: niente differenze tra CI e PC |
| `make test` | tutta la suite pytest | |

### I livelli di controllo

1. **pre-commit** (in locale, prima di ogni commit): ruff con `--fix`, ruff format, blocco dei file sopra 1 MB, rilevamento di chiavi private, marcatori di conflitto rimasti, YAML e TOML validi, fine file e spazi finali.
2. **CI** (sul server, a ogni PR): lint e test su una macchina pulita.

Perché tutti e due: il pre-commit dà un riscontro immediato, ma si può saltare (`git commit --no-verify`) o non essere installato su un altro PC. La CI non si può saltare, soprattutto se `main` è protetto e richiede la CI verde per il merge.

### Casi limite

- **Il pre-commit corregge un file:** il commit fallisce, i file sono stati modificati; basta rifare `git add` e il commit.
- **Ho aggiunto una dipendenza con `pip install` e non con `uv add`:** in locale funziona, ma `uv.lock` non la contiene e la CI fallisce all'import. È proprio il tipo di errore che la CI deve trovare.
- **Un test passa in locale e fallisce in CI:** di solito dipende da qualcosa che esiste solo sul mio PC (un file non committato, una variabile d'ambiente, un percorso Windows). La macchina pulita della CI lo mette in evidenza.
- **Il test "vuoto":** `tests/test_package.py` controlla che ogni sottopacchetto (`ingestion`, `transform`, `quality`, `ai`, `api`) si importi. È piccolo, ma verifica che il pacchetto sia installato correttamente e che la pipeline della CI funzioni dall'inizio alla fine. È parametrizzato (`pytest.mark.parametrize`): un caso per sottopacchetto, così se ne fallisce uno si vede subito quale.

---

## 3. Branch, pull request e commit piccoli lavorando da solo

### Il flusso

1. `main` contiene solo codice funzionante.
2. Per ogni passaggio si crea un branch (`chore/project-structure`, `docs/initial-decisions`).
3. Commit piccoli nel formato `tipo: descrizione` (`feat`, `fix`, `docs`, `test`, `chore`, `refactor`).
4. Si apre una pull request: la CI la controlla, si rilegge il diff, si fa il merge.

### Perché anche da solo

- **`main` sempre funzionante:** un esperimento a metà resta sul suo branch.
- **La CI ha un punto in cui intervenire:** la PR è il momento in cui i controlli bloccano il codice rotto prima che entri in `main`.
- **Rileggere il diff:** nella PR si vede la modifica intera, ed è lì che si trovano gli errori.
- **Documentazione:** la descrizione della PR spiega cosa, perché e quali alternative. Tra sei mesi (o a colloquio) è la storia del progetto.
- **È il flusso dei team:** a colloquio posso dire che lo uso già.

### Perché commit piccoli

- **Revert facile:** se un commit rompe qualcosa, `git revert` toglie solo quello.
- **`git bisect`:** trova il commit che ha introdotto un bug con una ricerca binaria; funziona bene solo se ogni commit è piccolo e lascia il codice funzionante.
- **Review più semplice:** un commit con una sola idea si capisce in un minuto.
- **Messaggi utili:** il prefisso dice subito il tipo di modifica, e la cronologia si legge come un elenco di cambiamenti.

### Casi limite

- **Merge commit contro squash:** le PR del progetto sono entrate con un merge commit (`Merge pull request #1 ...`), che conserva i commit piccoli del branch. Lo squash li fonde in uno solo: cronologia più pulita, ma si perde il dettaglio.
- **Branch rimasto indietro rispetto a `main`:** si aggiorna con un merge o un rebase di `main` prima del merge della PR; la CI riparte sul codice aggiornato.
- **`git push --force`:** riscrive la cronologia sul server; su un branch condiviso fa perdere lavoro agli altri. Nel progetto richiede conferma esplicita.

---

## 4. Le fonti: Open Library e Project Gutenberg

### Cosa offrono

| | Open Library | Project Gutenberg |
| --- | --- | --- |
| Cosa | catalogo bibliografico: autori, opere, edizioni, valutazioni, reading log | ebook di pubblico dominio: catalogo e testi completi |
| Forza | metadati ricchi e tantissimi titoli | testo integrale dei libri |
| Formato | dump mensili in gzip, TSV con un record JSON nell'ultima colonna | catalogo CSV, metadati RDF, file `.txt` da mirror |
| Licenza | CC0 (pubblico dominio) | testi di pubblico dominio, con le condizioni d'uso di Gutenberg |

### Perché proprio queste

- **Dati aperti e legali:** niente dati personali, di clienti o di datori di lavoro; posso mostrare tutto.
- **Accesso rispettoso:** dump e mirror pensati per lo scaricamento in blocco, quindi nessuno scraping e nessuna chiamata massiva alle API.
- **Volume vero:** decine di milioni di record in Open Library giustificano Spark, Parquet e un warehouse, senza essere ingestibili su un PC.
- **Dati sporchi in modo realistico:** date in formati diversi, duplicati, campi mancanti: c'è lavoro vero di pulizia e di controlli di qualità.

### Cosa rende interessante combinarle

Le due fonti si completano: Open Library sa *di cosa parla* un libro (autore, edizioni, soggetti, valutazioni), Gutenberg ha *il testo*. Collegarle permette, per esempio, di rispondere a una domanda sul catalogo e poi citare un passaggio del testo.

Il collegamento però non è dato: non c'è una chiave comune affidabile. Va costruito con l'**entity resolution** (fetta 3): abbinare titolo e autore con un matching approssimato, gestendo varianti ("Twain, Mark" contro "Mark Twain"), sottotitoli e i molti duplicati di Open Library. Si misura con due numeri:
- **precisione:** quanti abbinamenti trovati sono giusti;
- **recall:** quanti libri di Gutenberg restano senza abbinamento pur avendone uno in Open Library.

È la parte più difficile e la più interessante da raccontare a colloquio, perché è un problema reale di data engineering: integrare fonti che non sono state pensate per stare insieme.

### Sottoinsieme (decisioni D1 e D2)

Si parte piccoli: narrativa in inglese, circa 1800-1930, e circa 20 libri di Gutenberg scelti per mettere alla prova il RAG (gruppi per autore e titoli poco noti). Il volume cresce solo quando la pipeline funziona.

---

## 5. Gli altri strumenti della fase 0

Dettagli e alternative in `docs/decisions.md` (D5 e D6). In breve:

- **uv:** gestisce versione di Python, `.venv`, dipendenze e lockfile `uv.lock`. `uv run` esegue un comando nell'ambiente del progetto senza bisogno di attivarlo, e prima lo allinea al lockfile.
- **ruff:** lint (`ruff check`) e formato (`ruff format`) in un solo strumento. Regole attive: pycodestyle (E, W), pyflakes (F), ordine degli import (I), bugbear (B), pyupgrade (UP), semplificazioni (SIM).
- **Makefile:** comandi brevi e uguali per tutti (`make setup`, `make lint`, `make format`, `make test`). La CI usa gli stessi target, quindi locale e CI non possono divergere. `make setup` si può rilanciare senza danni: `uv sync` non cambia nulla se l'ambiente è già allineato.
- **Layout `src/`:** i test importano il pacchetto installato, non la cartella corrente, quindi un errore di packaging fa fallire i test invece di restare nascosto.
- **`.gitattributes` con `eol=lf`:** fine riga LF su ogni sistema. Su Windows git potrebbe convertire in CRLF, e uno script shell con CRLF fallisce dentro un container Linux.

---

## Domande probabili

1. **Qual è la differenza tra immagine e container? E tra container e macchina virtuale?**
2. **Perché Docker rende un progetto riproducibile? Cosa non risolve?** (Non risolve, per esempio, le differenze di hardware come la GPU, o i dati che stanno fuori dal repository.)
3. **Cosa succede ai dati di PostgreSQL con `docker compose down`? E con `down -v`?**
4. **Cosa controlla la tua CI e cosa succede se `uv.lock` non è allineato?**
5. **Perché hai sia pre-commit sia la CI?**
6. **Lavori da solo: perché usi branch e pull request?**
7. **What is the difference between a merge commit and a squash merge, and which one do you use?**
8. **Perché Open Library e Gutenberg, e cosa c'è di difficile nel collegarle?**
9. **Come misuri la qualità del collegamento tra le due fonti?**
10. **Perché uv e non pip o Poetry? Perché ruff?**

## Documentazione ufficiale

- Docker, *Get started* (concetti di immagine, container, volume): https://docs.docker.com/get-started/
- GitHub Actions, *Understanding GitHub Actions*: https://docs.github.com/en/actions/about-github-actions/understanding-github-actions
- uv, *Projects*: https://docs.astral.sh/uv/concepts/projects/
- pre-commit: https://pre-commit.com/
