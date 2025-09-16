README - Workflow File Scanning ACRCloud (RAW + Enrichment + Analisi)
=====================================================================

Questo pacchetto contiene 3 script Python per lavorare con i risultati di File Scanning (FS) di ACRCloud.

STRUTTURA:
1. dump_acrcloud_fs_raw.py
   - Scarica tutti i risultati grezzi di File Scanning (inclusi "no match" e falsi positivi)
   - Output: CSV con i file, CSV con i candidati, JSONL raw

2. enrich_identify_windows.py
   - Richiama la Identification API su file locali o frammenti per ottenere score multipli
   - Utile per analisi su finestre temporali
   - Output: CSV con candidati arricchiti

3. analyze_fs_candidates.py
   - Analizza e visualizza distribuzioni di score e similarità
   - Output: PNG con grafici

---------------------------------------------------------------------
COME USARE
---------------------------------------------------------------------

*** FASE 1 - Dump File Scanning ***
Impostare variabili d'ambiente:
export ACR_BASE_URL="https://api-<region>.acrcloud.com"
export ACR_BEARER="TOKEN_CONSOLE_API"
export ACR_CONTAINER_ID="ID_CONTAINER_FS"

Eseguire:
python dump_acrcloud_fs_raw.py --limit 0

*** FASE 2 - Enrichment (opzionale) ***
export ACR_ID_HOST="identify-eu-west-1.acrcloud.com"
export ACR_ID_ACCESS_KEY="CHIAVE_ID"
export ACR_ID_ACCESS_SECRET="SEGRETO_ID"

python enrich_identify_windows.py   --audio_dir ./audio_locali   --candidates acr_fs_dump/fs_candidates.csv   --out enr_candidates.csv   --top_n 5 --win 12 --hop 6

*** FASE 3 - Analisi ***
python analyze_fs_candidates.py

I risultati saranno nella cartella acr_fs_dump/.
