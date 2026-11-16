# Roadmap

Leggere solo i passaggi della fetta in corso (indicata in `docs/status.md`).

Legenda: `[ ]` da fare, `[x]` fatto. Ogni fase termina con un risultato verificabile e si chiude solo quando entrambe le checklist ("Costruire" e "Capire e saper spiegare") sono complete.

Priorità: **[MVP]** va fatto per primo e basta per avere un progetto presentabile; **[Completo]** rende il progetto solido; **[Opzionale]** solo se resta tempo.

## Ordine di lavoro: le fette

Le fasi qui sotto sono l'elenco dei contenuti e delle checklist. L'ordine in cui si affrontano è dato dalle fette: prima una versione sottile ma completa dall'inizio alla fine, poi uno strumento nuovo per volta. Una fetta si chiude quando i suoi passaggi sono fatti e le relative voci "Capire e saper spiegare" sono spuntate.

| Fetta | Cosa contiene | Passaggi |
| --- | --- | --- |
| 1 | Repository e CI. Solo Gutenberg: catalogo e circa 20 testi, puliti con Python semplice e caricati in PostgreSQL con pgvector. Una query SQL sul catalogo e un RAG minimo che risponde citando il libro | Fase 0; 1.4; 2.3; 5.1-5.6 |
| 2 | Open Library: download dei dump di autori e opere, Spark, Parquet, caricamento in PostgreSQL. Object storage | 1.1-1.6; 2.1-2.2; 2.5-2.7 |
| 3 | Entity resolution con precisione e recall misurate. Livello curated e test sui dati (dbt, se scelto) | 2.4; 2.9; parte della fase 4 |
| 4 | Airflow attorno a ciò che già funziona, API, README, demo | Fasi 3, 6 e 8 |
| Dopo, se resta tempo | Streaming, text-to-SQL, Terraform, GCP | 1.7; 5.7; fasi 7 e 9 |

Nella fetta 1 non ci sono Spark, Airflow, object storage né Open Library: gli script si lanciano a mano. È divisa in tre tappe, ognuna con un risultato da mostrare:

1. **Repository e CI:** struttura, pre-commit, GitHub Action verde, prima pull request rivista.
2. **Dati:** catalogo e testi puliti in PostgreSQL, una query con un risultato vero.
3. **RAG minimo:** chunking, embeddings in pgvector, una risposta con la citazione del libro.

**Tempi.** Cronometrare la tappa 1 e usare quel dato per mettere una data alle altre due. Una scadenza serve, ma deve essere realistica.

**Tagliare senza sensi di colpa.** Un progetto piccolo e finito vale più di uno grande a metà.

## Fase 0 - Preparazione [MVP]
Risultato: repository ordinato con CI verde dal primo commit e decisioni iniziali scritte.

**Costruire**
- [x] 0.1 Creare il repository GitHub con README, licenza (per esempio MIT) e `.gitignore` per Python.
- [x] 0.2 Creare la struttura delle cartelle descritta nel `CLAUDE.md`.
- [x] 0.3 Preparare l'ambiente locale: Python 3.11 o superiore, ambiente gestito con uv, Docker.
- [x] 0.4 Configurare pre-commit con ruff (`ruff check` e `ruff format`).
- [x] 0.5 Creare il `Makefile` con i target minimi elencati nel `CLAUDE.md`.
- [x] 0.6 Prima GitHub Action che esegue lint e pytest (anche con un test vuoto).
- [ ] 0.7 Decisioni iniziali, da annotare in `docs/decisions.md`:
  - [ ] 0.7.1 Sottoinsieme di partenza: lingua, generi o periodo da considerare.
  - [ ] 0.7.2 Libri di Gutenberg da usare per il RAG (prima selezione, circa 20).
  - [ ] 0.7.3 LLM locale e modello di embeddings (multilingue se uso testi in italiano). Si può rimandare alla tappa 3 della fetta 1.
  - [ ] 0.7.4 Nome del repository.
  - [ ] 0.7.5 Strumenti della fetta 1: ruff, uv, PostgreSQL con pgvector, con il confronto con le alternative.

**Capire e saper spiegare**
- [ ] Cos'è un container e perché Docker rende il progetto riproducibile.
- [ ] Cos'è la CI e cosa controlla la mia GitHub Action.
- [ ] Perché uso branch, pull request e commit piccoli anche lavorando da solo.
- [ ] Perché ho scelto Open Library e Gutenberg, e cosa rende interessante combinarli.
- [ ] Nota `docs/learning/fase-0.md` scritta.

## Fase 1 - Ingestione e data lake [MVP]
Risultato: i dati grezzi delle due fonti arrivano nel data lake, sia in batch sia in streaming.

**Costruire**
- [ ] 1.1 Documentare le fonti: schema dei dump di Open Library, colonne del catalogo di Gutenberg, licenze, frequenze di aggiornamento, regole d'uso. Verificare i punti aperti di `docs/dataset.md`: formato TSV dei dump, presenza dell'ora in valutazioni e reading log, dimensione del dump delle edizioni.
- [ ] 1.2 Avviare l'object storage con API S3 (SeaweedFS o Garage, da decidere) con Docker Compose e creare il bucket del data lake.
- [ ] 1.3 Download dei dump di Open Library (autori e opere per primi, poi edizioni, valutazioni, reading log):
  - [ ] 1.3.1 Download in streaming dei file grandi, senza caricarli tutti in memoria.
  - [ ] 1.3.2 Retry, logging e verifica dell'integrità del file.
  - [ ] 1.3.3 Ripresa del download se si interrompe a metà.
- [ ] 1.4 Download del catalogo CSV e dei metadati RDF di Gutenberg, e dei testi del sottoinsieme scelto da un mirror.
- [ ] 1.5 Salvare tutto in `raw/` così com'è, partizionato per fonte e data dello snapshot (per esempio `raw/openlibrary/2026-11/`, `raw/gutenberg/2026-11-15/`).
- [ ] 1.6 Gestire i casi di errore:
  - [ ] 1.6.1 Sorgente non disponibile.
  - [ ] 1.6.2 Snapshot già scaricato (rilanciare non deve duplicare i dati).
  - [ ] 1.6.3 File corrotto o incompleto.
  - [ ] 1.6.4 Schema cambiato.
- [ ] 1.7 Streaming [Opzionale: dopo la fetta 4, se resta tempo]:
  - [ ] 1.7.1 Avviare Redpanda/Kafka in Docker Compose.
  - [ ] 1.7.2 Producer che riproduce reading log e valutazioni come eventi, in ordine temporale. Se i dati hanno solo la data, dichiarare nel README che il replay è una simulazione.
  - [ ] 1.7.3 Consumer che scrive gli eventi a piccoli blocchi in `raw/events/`.
- [ ] 1.8 Test con pytest sulle funzioni di parsing e di download.

**Capire e saper spiegare**
- [ ] Differenza tra object storage, file system e database, e perché il data lake usa l'object storage.
- [ ] Perché salvo i dati grezzi senza modificarli.
- [ ] Cos'è l'idempotenza e come la garantisco nell'ingestione.
- [ ] Differenza tra batch e streaming, e quando ha senso ciascuno.
- [ ] Concetti di Kafka: topic, partizione, offset, consumer group; cosa significa "at least once".
- [ ] Rispondere a: "Cosa succede se il download si interrompe a metà?"
- [ ] Nota `docs/learning/fase-1.md` scritta.

## Fase 2 - Trasformazione e data warehouse [MVP]
Risultato: tabelle curate e collegate tra le due fonti, pronte per l'analisi e per il livello AI.

**Costruire**
- [ ] 2.1 Definire i tre livelli: `raw` (dati come arrivano), `staging` (puliti e tipizzati), `curated` (pronti per l'analisi).
- [ ] 2.2 Staging di Open Library con PySpark:
  - [ ] 2.2.0 Leggere i `.gz` (non divisibili: una sola partizione), ripartizionare esplicitamente e convertire subito in Parquet.
  - [ ] 2.2.1 Estrarre e appiattire il JSON dei dump (ultima colonna del TSV).
  - [ ] 2.2.2 Normalizzare le date di pubblicazione (spesso testo libero) in un anno.
  - [ ] 2.2.3 Normalizzare codici lingua e ISBN (10 e 13 cifre).
  - [ ] 2.2.4 Deduplicare autori ed edizioni.
  - [ ] 2.2.5 Applicare il filtro del sottoinsieme.
- [ ] 2.3 Staging di Gutenberg:
  - [ ] 2.3.1 Pulire il catalogo (autori, lingue, soggetti).
  - [ ] 2.3.2 Separare il testo del libro da intestazione e piè di pagina di Project Gutenberg.
- [ ] 2.4 Entity resolution tra Gutenberg e Open Library:
  - [ ] 2.4.1 Normalizzare titoli e nomi degli autori (maiuscole, accenti, punteggiatura, ordine nome-cognome).
  - [ ] 2.4.2 Ridurre i confronti con un blocking (per esempio per iniziale dell'autore o lingua).
  - [ ] 2.4.3 Calcolare un punteggio di somiglianza e scegliere una soglia.
  - [ ] 2.4.4 Definire una regola per i libri che corrispondono a più opere (Open Library ha molti duplicati).
  - [ ] 2.4.5 Precisione: controllare a mano un campione di almeno 50 abbinamenti.
  - [ ] 2.4.6 Recall: misurare quanti libri di Gutenberg restano senza abbinamento e controllare a mano un campione dei non abbinati.
  - [ ] 2.4.7 Annotare precisione e recall in `docs/metrics.md`.
- [ ] 2.5 Livello curated, per esempio: autori, opere, edizioni, valutazioni aggregate, attività di lettura, libri di Gutenberg collegati alle opere. Output in Parquet.
- [ ] 2.6 Caricare il curated in PostgreSQL con tabelle indicizzate o partizionate.
- [ ] 2.7 Scrivere tre query analitiche di esempio (per esempio autori più letti, valutazioni per decennio di pubblicazione, quota di opere con testo disponibile su Gutenberg).
- [ ] 2.8 Annotare nel README le scelte fatte: partizioni, formato, modello dei dati.
- [ ] 2.9 [Fetta 3, se si sceglie dbt] Spark porta i dump fino allo staging; dbt costruisce in SQL le tabelle curated dentro PostgreSQL, con i propri test sui dati.
- [ ] 2.10 Test sulle trasformazioni con un piccolo campione di esempio.

**Capire e saper spiegare**
- [ ] Architettura di Spark: driver, executor, partizioni.
- [ ] Lazy evaluation: differenza tra trasformazioni e azioni.
- [ ] Cos'è uno shuffle e perché rallenta i job; cos'è un broadcast join.
- [ ] Perché un file gzip non è divisibile e cosa comporta per Spark.
- [ ] Perché uso Spark anche se su questi volumi non è indispensabile, e quali strumenti più semplici basterebbero.
- [ ] Perché Parquet e non CSV o JSON per i livelli staging e curated.
- [ ] Modello dei dati curated: tabelle, chiavi e relazioni (saperlo disegnare alla lavagna).
- [ ] Come funziona la mia entity resolution, cosa misurano precisione e recall, i miei valori e come li migliorerei.
- [ ] Rispondere a: "Come gestisci date e dati sporchi inseriti dagli utenti?"
- [ ] Nota `docs/learning/fase-2.md` scritta.

## Fase 3 - Orchestrazione [MVP]
Risultato: pipeline che partono da sole, ognuna con la cadenza della sua fonte, e si possono rilanciare per qualsiasi periodo.

**Costruire**
- [ ] 3.1 Airflow in Docker Compose.
- [ ] 3.2 DAG mensile per Open Library: download, staging, entity resolution, curated, controlli.
- [ ] 3.3 DAG settimanale per Gutenberg: catalogo, nuovi testi, aggiornamento del collegamento con Open Library.
- [ ] 3.4 Retry, timeout, alert in caso di errore e schedulazione.
- [ ] 3.5 Parametrizzare i DAG per snapshot e fare il backfill di qualche periodo passato.
- [ ] 3.6 Documentare perché il consumer dello streaming gira come servizio continuo e non come DAG.
- [ ] 3.7 Test nella CI che verifica che i DAG si importino senza errori.
- [ ] 3.8 Nel README, sezione "Come girerebbe su Cloud Composer" (stessi DAG, ambiente gestito), senza deployarlo.

**Capire e saper spiegare**
- [ ] Concetti di Airflow: DAG, task, operator, scheduler, executor.
- [ ] Perché i task devono essere idempotenti.
- [ ] Cos'è il backfill e cosa fa il parametro `catchup`.
- [ ] Come passano informazioni tra i task e perché non si passano dati grandi con XCom.
- [ ] Rispondere a: "Come rilanci la pipeline per lo snapshot di tre mesi fa?"
- [ ] Nota `docs/learning/fase-3.md` scritta.

## Fase 4 - Qualità del dato e test [Completo]
Risultato: la pipeline si ferma o segnala quando i dati non sono affidabili.

**Costruire**
- [ ] 4.1 Definire i controlli:
  - [ ] 4.1.1 Validità degli ISBN (cifra di controllo).
  - [ ] 4.1.2 Anni di pubblicazione plausibili (né nel futuro né assurdamente antichi).
  - [ ] 4.1.3 Codici lingua validi.
  - [ ] 4.1.4 Duplicati di autori ed edizioni.
  - [ ] 4.1.5 Valutazioni nell'intervallo consentito.
  - [ ] 4.1.6 Opere senza autore o edizioni senza opera.
  - [ ] 4.1.7 Variazione del numero di righe rispetto allo snapshot precedente.
  - [ ] 4.1.8 Freschezza: lo snapshot più recente è stato caricato?
- [ ] 4.2 Implementarli con pytest e i test di dbt, oppure con Great Expectations (decisione nella fetta 3).
- [ ] 4.3 Distinguere controlli bloccanti e controlli di avviso, e fermare la pipeline sui primi.
- [ ] 4.4 Salvare un report sintetico dei controlli in una tabella del warehouse.
- [ ] 4.5 Misurare la copertura dei test con pytest-cov e annotare il valore reale in `docs/metrics.md`.
- [ ] 4.6 Sicurezza e privacy:
  - [ ] 4.6.1 Verificare se reading log e valutazioni contengono identificativi di utenti; se sì, scartarli o renderli anonimi.
  - [ ] 4.6.2 Segreti solo in variabili d'ambiente.
  - [ ] 4.6.3 Permessi minimi su ogni servizio.
  - [ ] 4.6.4 Descrivere queste scelte nel README.

**Capire e saper spiegare**
- [ ] Dimensioni della qualità del dato: completezza, validità, unicità, coerenza, freschezza.
- [ ] Differenza tra test sul codice (unit test) e test sui dati.
- [ ] Dove mettere i controlli nella pipeline e perché.
- [ ] Rispondere a: "Come ti accorgi che lo snapshot di questo mese è sbagliato prima che arrivi agli utenti?"
- [ ] Nota `docs/learning/fase-4.md` scritta.

## Fase 5 - Livello AI (RAG e text-to-SQL) [MVP: 5.1-5.6 | Completo: 5.7-5.9 | Opzionale: 5.10]
Risultato: un assistente che risponde su catalogo e testi citando le fonti, con una metrica di qualità.

**Costruire**
- [ ] 5.1 Decidere cosa indicizzare: testi dei libri di Gutenberg (con autore, titolo e capitolo come metadati) ed eventuali descrizioni delle opere di Open Library.
- [ ] 5.2 Chunking: dividere i testi in frammenti, provando almeno due strategie (per esempio lunghezza fissa e per paragrafo o capitolo).
- [ ] 5.3 Generare gli embeddings con sentence-transformers.
- [ ] 5.4 Salvarli in PostgreSQL con pgvector, insieme ai metadati.
- [ ] 5.5 Retrieval dei frammenti più simili alla domanda, con filtri sui metadati (autore, lingua, libro).
- [ ] 5.6 Prompt per l'LLM locale che usa solo i frammenti recuperati e cita libro e capitolo.
- [ ] 5.7 Text-to-SQL sul catalogo curated:
  - [ ] 5.7.1 Connessione in sola lettura.
  - [ ] 5.7.2 Validazione della query prima dell'esecuzione.
  - [ ] 5.7.3 Scelta automatica tra RAG e text-to-SQL in base alla domanda.
- [ ] 5.8 Indicizzazione incrementale: un task Airflow aggiunge al vector database solo i libri nuovi.
- [ ] 5.9 Valutazione:
  - [ ] 5.9.1 Preparare un set di domande con risposta attesa, metà sul catalogo e metà sui testi. Partire da 15-20 e ampliarlo: con così poche domande i risultati sono fragili.
  - [ ] 5.9.2 Metrica sul retrieval: per ogni domanda sui testi, il frammento giusto è tra i primi k recuperati? Calcolarla per ogni strategia di chunking.
  - [ ] 5.9.3 Metrica sulle risposte: scrivere il criterio di punteggio prima di calcolarlo, poi applicarlo.
  - [ ] 5.9.4 Annotare i risultati in `docs/metrics.md`.
- [ ] 5.10 [Opzionale] riscrivere il retrieval con LangChain o LlamaIndex dopo aver fatto la versione senza framework, per capire cosa fanno.

**Capire e saper spiegare**
- [ ] Cos'è un embedding e cosa misura la similarità del coseno.
- [ ] Come funziona il RAG passo per passo, e perché si usa invece del fine-tuning.
- [ ] Pro e contro delle strategie di chunking che ho provato, con i miei risultati.
- [ ] Cosa sono le allucinazioni e come le riduco (grounding, citazioni, risposta "non lo so").
- [ ] Rischi del text-to-SQL e come li ho mitigati.
- [ ] Rispondere a: "Come misuri se l'assistente risponde correttamente?"
- [ ] Nota `docs/learning/fase-5.md` scritta.

## Fase 6 - API e container [Completo]
Risultato: un servizio che si avvia con un comando e si può mostrare dal vivo.

**Costruire**
- [ ] 6.1 API FastAPI con gli endpoint:
  - [ ] 6.1.1 `/health`.
  - [ ] 6.1.2 `/ask`: domanda in linguaggio naturale (RAG o text-to-SQL).
  - [ ] 6.1.3 Ricerca di autori e opere sul catalogo curated.
- [ ] 6.2 Validazione degli input con Pydantic, gestione degli errori e logging.
- [ ] 6.3 Dockerfile multi-stage e `docker-compose.yml` che avvia l'intero stack in locale.
- [ ] 6.4 Interfaccia minima (Streamlit o una pagina semplice) per la demo.
- [ ] 6.5 Test dell'API con pytest e TestClient.

**Capire e saper spiegare**
- [ ] Principi REST, metodi HTTP e codici di stato che uso.
- [ ] Cosa fa Pydantic e cosa succede con un input non valido.
- [ ] Come comunicano i container nella rete di Docker Compose.
- [ ] Rispondere a: "Come avvio tutto da zero su un'altra macchina?"
- [ ] Nota `docs/learning/fase-6.md` scritta.

## Fase 7 - CI/CD e infrastruttura come codice [Completo]
Risultato: pipeline di integrazione completa e infrastruttura descritta in codice, senza spese.

**Costruire**
- [ ] 7.1 GitHub Actions: lint, test, build delle immagini Docker.
- [ ] 7.2 [Opzionale: dopo la fetta 4, se resta tempo] Terraform per le risorse GCP della fase 9 (bucket, dataset BigQuery, topic Pub/Sub, service account, ruoli):
  - [ ] 7.2.1 Scrivere i file in `infra/`.
  - [ ] 7.2.2 Validare con `terraform validate`, senza applicare. `terraform plan` con il provider Google può richiedere credenziali: nella CI solo `validate`.
  - [ ] 7.2.3 Eseguire il controllo nella CI.
- [ ] 7.3 Documentare nel README come si userebbe (`apply`) e come si spegnerebbe tutto (`destroy`).

**Capire e saper spiegare**
- [ ] Differenza tra CI e CD.
- [ ] Vantaggi dell'infrastruttura come codice rispetto alla console.
- [ ] Ciclo di Terraform: `init`, `plan`, `apply`, `destroy`; cos'è lo state e perché va custodito.
- [ ] Rispondere a: "Perché usi Terraform se il progetto gira in locale?"
- [ ] Nota `docs/learning/fase-7.md` scritta.

## Fase 8 - Documentazione e colloquio [Completo]
Risultato: un repository che si capisce in due minuti e una storia che so raccontare con sicurezza.

**Costruire**
- [ ] 8.1 README con obiettivo, diagramma dell'architettura, avvio in pochi comandi, scelte, limiti e costi.
- [ ] 8.2 Diagramma dell'architettura (draw.io o Mermaid nel README).
- [ ] 8.3 GIF o breve video della demo.
- [ ] 8.4 Controllare la cronologia: commit piccoli con messaggi chiari, issue e pull request.
- [ ] 8.5 Aggiornare il CV (file LaTeX `PlushCV.tex`):
  - [ ] 8.5.1 Riattivare la riga GitHub nella sezione Contact (già pronta, commentata).
  - [ ] 8.5.2 Aggiungere un bullet sul progetto con numeri reali, presi da `docs/metrics.md`.
  - [ ] 8.5.3 Aggiungere alle skills solo gli strumenti usati davvero.

**Capire e saper spiegare**
- [ ] Racconto di 3 minuti: il problema, l'architettura, una scelta difficile, un errore e cosa ho imparato, cosa migliorerei.
- [ ] Approfondimento di 10 minuti, fase per fase, senza guardare il codice.
- [ ] Disegnare l'architettura alla lavagna a memoria.
- [ ] `docs/interview.md` con almeno 20 domande probabili e le mie risposte.
- [ ] Simulazione di colloquio con Claude Code, una in italiano e una in inglese, con valutazione delle risposte.
- [ ] Saper dire cosa farei con più tempo o in produzione (scalabilità, monitoraggio, costi, sicurezza).

## Fase 9 - Estensione GCP [Opzionale]
Risultato: almeno un pezzo del progetto gira davvero su GCP, nei limiti del free tier.
Da fare solo dopo la fase 8 e con la mia conferma esplicita prima di creare qualsiasi risorsa.

**Costruire**
- [ ] 9.1 Creare un progetto GCP dedicato e impostare un budget alert. L'alert avvisa soltanto: non blocca la spesa.
- [ ] 9.2 Creare un service account con permessi minimi.
- [ ] 9.3 Cloud Storage al posto dell'object storage locale, in una regione US (il free tier vale solo lì).
- [ ] 9.4 BigQuery al posto del warehouse locale, restando nei limiti gratuiti (1 TiB di query e 10 GiB di storage al mese). Nel sandbox senza carta non sono supportati streaming e DML e le tabelle scadono dopo 60 giorni: tenerne conto.
- [ ] 9.5 Facoltativo: Pub/Sub al posto del broker locale.
- [ ] 9.6 Facoltativo: deploy dell'API su Cloud Run.
- [ ] 9.7 Autenticazione da GitHub a GCP con Workload Identity Federation, senza chiavi.
- [ ] 9.8 Applicare Terraform e, a fine prova, eseguire `terraform destroy` per non lasciare risorse accese.
- [ ] 9.9 Aggiornare README e CV con ciò che gira davvero su GCP.

**Capire e saper spiegare**
- [ ] Differenze tra la versione locale e quella su GCP, e cosa ho dovuto cambiare nel codice.
- [ ] Come ho tenuto sotto controllo i costi.
- [ ] Principio del privilegio minimo applicato ai service account.
- [ ] Nota `docs/learning/fase-9.md` scritta.
