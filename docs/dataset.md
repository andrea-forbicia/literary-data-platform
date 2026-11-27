# Dataset

Fonti di dati del progetto. Da leggere quando si lavora su ingestione, trasformazione o indicizzazione.

| Fonte | Contenuto | Formato | Aggiornamento | Licenza |
| --- | --- | --- | --- | --- |
| Open Library (Internet Archive) | Autori (~15 M), opere (~41 M), edizioni (~56 M), valutazioni (~1 M), reading log (~12 M) | Dump compressi in gzip. Autori, opere ed edizioni: TSV a cinque colonne (tipo, chiave, revisione, data di ultima modifica, record JSON), con il JSON nell'ultima colonna | Mensile | CC0 (pubblico dominio) |
| Project Gutenberg | Oltre 75.000 ebook di pubblico dominio: catalogo e testi completi | Catalogo CSV (settimanale), metadati RDF (giornalieri), testi `.txt` da mirror | Settimanale / giornaliero | Testi di pubblico dominio; rispettare le condizioni d'uso di Project Gutenberg |

I numeri sono indicativi (snapshot 2026): misurare e annotare i valori reali in `docs/metrics.md`.

**Da verificare sulla documentazione delle fonti (passo 1.1)**
- Formato dei dump: TSV a cinque colonne, non "un record JSON per riga". Verificare anche il formato dei dump di valutazioni e reading log, che è diverso.
- Valutazioni e reading log: dovrebbero avere solo la data, senza l'ora. In quel caso un replay "in ordine temporale" è poco realistico: lo streaming va dichiarato nel README come simulazione, oppure tagliato.
- Dimensioni: il solo dump delle edizioni dovrebbe superare la soglia di 5 GB che richiede conferma (vedi `CLAUDE.md`).

**Catalogo di Project Gutenberg (verificato il 2026-11-27)**
- Il sito `www.gutenberg.org` è in manutenzione almeno dal 2026-11-17: ogni pagina risponde `503` con `Retry-After` (3600 il 2026-11-17, 21600 il 2026-11-27). Le pagine *Offline Catalogs* e *Robot Access Policy* non sono ancora state lette: vanno lette prima di lanciare il download vero.
- Il mirror PGLAF risponde: `https://gutenberg.pglaf.org/cache/epub/feeds/`. Contiene `pg_catalog.csv.gz` (5.602.458 byte, `Last-Modified` 2026-11-08), `pg_catalog.csv` (21 MB), `rdf-files.tar.bz2` (127 MB, 2026-11-15), i file MARC e `txt-files.tar.zip` (11 GB). Supporta le richieste parziali (`Accept-Ranges: bytes`) e restituisce un `ETag`.
- Nella fetta 1 si usa solo il CSV (D11).
- Colonne del CSV: `Text#`, `Type`, `Issued`, `Title`, `Language`, `Authors`, `Subjects`, `LoCC`, `Bookshelves`.
- Particolarità viste nelle prime righe:
  - alcuni campi tra virgolette contengono un a capo (il titolo del libro 2 è su due righe), quindi il file va letto con un parser CSV e mai riga per riga;
  - `Authors`, `Subjects`, `LoCC` e `Bookshelves` contengono più valori separati da `"; "`;
  - l'autore è testo libero con le date di vita (`"Jefferson, Thomas, 1743-1826"`);
  - `Issued` è la data di ingresso in Project Gutenberg (1971-12-01 per il libro 1), non l'anno di pubblicazione.

**Conseguenze per la trasformazione**
- Un file `.gz` non è divisibile: Spark lo legge in una sola partizione. Subito dopo la lettura servono una ripartizione esplicita e la conversione in Parquet.

**Uso nel progetto**
- **Project Gutenberg:** testi completi per il RAG e metadati per collegare i libri al catalogo di Open Library. È la prima fonte (fetta 1).
- **Open Library:** dati tabellari per il catalogo (autori, opere, edizioni) e per analisi su valutazioni e letture (fetta 2). Il reading log e le valutazioni possono alimentare uno streaming simulato, solo se resta tempo dopo la fetta 4.
- **Collegamento tra le fonti:** associare ogni libro di Gutenberg all'opera corrispondente in Open Library per titolo e autore (entity resolution con matching approssimato, fetta 3). È la parte più impegnativa e la più interessante da raccontare. Va misurata con due numeri:
  - **Precisione:** quanti abbinamenti trovati sono giusti (controllo a mano di un campione).
  - **Recall:** quanti libri di Gutenberg restano senza abbinamento, pur avendo un'opera corrispondente in Open Library.
  - Serve anche una regola per quando un libro corrisponde a più opere, perché Open Library contiene molti duplicati.

**Strategia di sottoinsieme**
1. Fetta 1: solo Gutenberg, il catalogo e circa 20 testi.
2. Fetta 2: autori e opere di Open Library, filtrati per lingua o genere.
3. Poi: edizioni, valutazioni e reading log, e qualche centinaio di libri di Gutenberg.
4. Infine: volume maggiore tramite backfill, solo se il PC lo regge (vedi il budget di risorse nel `CLAUDE.md`).
