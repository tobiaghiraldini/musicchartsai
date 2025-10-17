Data aggregation views
## 🎯 IL PROBLEMA IN UNA FRASE

La dashboard attuale mostra le classifiche musicali e dettaglio brano.  
Quello che serve: poter rispondere a domande tipo "quanto ha fatto l'artista X in Italia a settembre?"

---

## 💡 ESEMPIO CONCRETO

### Domanda che devo fare spesso:

> "Achille Lauro quanto ha fatto in totale in Italia a settembre 2024?"

### Con la dashboard attuale:

❌ Impossibile rispondere perché:
- Vedo solo le chart del giorno
- Devo aprire ogni brano uno per uno (ne ha 50+)
- Non c'è "somma automatica"
- Non posso selezionare "settembre" (solo "ultimi 30 giorni")

### Con quello che devi costruire:

✅ Filtro:
Artista: Achille Lauro
Paese: Italia
Periodo: 1-30 settembre 2024
Piattaforma: Tutte
✅ Click su "Cerca"

✅ Risultato immediato:
Spotify:  12.5M stream
YouTube:   3.2M views
Shazam:    89K tags
──────────────────────
TOTALE:   15.8M plays
Questo è quello che manca e che devi aggiungere.

---
## 🔄 COME LA POPOLI

### Script che gira ogni notte (alle 3:00):
# Pseudo-codice semplificato

def sync_daily():
    # Prendi data di ieri
    yesterday = today - 1
    
    # Per ogni chart italiana
    for chart in ['spotify-top-200-it', 'youtube-top-100-it', 'shazam-top-200-it']:
        
        # Scarica i brani della chart
        tracks = soundcharts_api.get_chart(chart, date=yesterday)
        
        # Per ogni brano, prendi i dettagli
        for track in tracks:
            
            metrics = soundcharts_api.get_track_metrics(
                track_id=track.id,
                country='IT',
                date=yesterday
            )
            
            # Salva nel database
            db.insert({
                'song_title': metrics.title,
                'artist_name': metrics.artist,
                'isrc': metrics.isrc,
                'platform': 'spotify',  # o 'youtube', 'shazam'
                'country': 'IT',
                'date': yesterday,
                'streams_or_views': metrics.streams,
                'listeners': metrics.listeners,
                'playlist_count': metrics.playlists,
                'snapshot_date': today,
                'source_api': 'soundcharts'
            })
Questo script gira automaticamente ogni notte.

---

## 🎨 UI CHE DEVI FARE

### Pagina 1: "Ricerca Dati"

Form con filtri (vedi sopra) + bottone "Cerca"

### Pagina 2: "Risultati"

Tabella con dati aggregati + bottone "Scarica Excel"

### Pagina 3: "Report Salvati" (opzionale)

Lista di ricerche salvate che l'utente può rieseguire con un click

---

## 📋 ESEMPI DI QUERY SQL

### Esempio 1: Totale stream artista in Italia a settembre
SELECT 
    platform,
    SUM(streams_or_views) as total
FROM unified_music_data
WHERE 
    artist_name = 'Achille Lauro'
    AND country = 'IT'
    AND date BETWEEN '2024-09-01' AND '2024-09-30'
GROUP BY platform;
Risultato:
spotify: 12.500.000
youtube:  3.200.000
shazam:     89.000
---

### Esempio 2: Confronto paesi per un brano
SELECT 
    country,
    SUM(streams_or_views) as total_streams
FROM unified_music_data
WHERE 
    isrc = 'ITUM71234567'
    AND platform = 'spotify'
    AND date BETWEEN '2024-09-01' AND '2024-09-30'
GROUP BY country
ORDER BY total_streams DESC;
Risultato:
IT: 12.500.000
DE:  3.800.000
FR:  2.100.000
ES:  1.600.000
---

### Esempio 3: Trend mensile
SELECT 
    DATE_TRUNC('month', date) as month,
    SUM(streams_or_views) as monthly_total
FROM unified_music_data
WHERE 
    song_title = 'AMOR'
    AND country = 'IT'
    AND platform = 'spotify'
    AND date >= '2024-06-01'
GROUP BY month
ORDER BY month;
Risultato:
2024-06: 8.500.000
2024-07: 12.300.000
2024-08: 15.700.000
2024-09: 18.200.000
---

## ⚙️ COSA FARE - STEP BY STEP

### Week 1: Database
- [ ] Crea la tabella unified_music_data
- [ ] Aggiungi gli indici
- [ ] Test con 100 righe di esempio

### Week 2: Sync Script
- [ ] Script Python che chiama Sound Charts API
- [ ] Salva dati nella tabella
- [ ] Test manuale per 1 giorno

### Week 3: Automazione
- [ ] Cron job per esecuzione notturna
- [ ] Log per monitorare errori
- [ ] Email alert se fallisce

### Week 4: API Backend
- [ ] Endpoint /api/search che accetta filtri
- [ ] Ritorna dati aggregati in JSON
- [ ] Test con Postman

### Week 5: UI Form
- [ ] Pagina con filtri (artista, paese, date, platform)
- [ ] Bottone "Cerca"
- [ ] Mostra loading durante ricerca

### Week 6: UI Risultati
- [ ] Tabella con risultati
- [ ] Bottone "Scarica Excel"
- [ ] Grafici (opzionale)

TOTALE: 6 settimane

---

## ✅ TEST FINALE

Il sistema funziona se posso fare questo:

1. Apro la dashboard
2. Scrivo "Achille Lauro" nel campo artista
3. Seleziono "Italia"
4. Seleziono periodo "1-30 settembre 2024"
5. Click su "Cerca"
6. Vedo risultato: "12.5M stream Spotify, 3.2M view YouTube"
7. Click su "Scarica Excel"
8. Ottengo file con tutti i dettagli

Tempo totale: 30 secondi

Attualmente: Impossibile fare questa cosa

---

## 🎯 DIFFERENZA CHIAVE

### Dashboard ATTUALE (quella che hai fatto):
Utente → Seleziona Chart → Vede Top 100 del giorno
Uso: Vedere classifiche

### Dashboard NUOVA (quella da fare):
Utente → Filtra (artista/paese/periodo) → Vede dati aggregati
Uso: Analizzare performance

---

## 💬 DOMANDE FREQUENTI

### "Ma le chart che ho fatto le butto via?"
No! Le tieni. Aggiungi questa nuova parte accanto.

### "Devo salvare TUTTI i brani di Spotify?"
No! Solo:
- Brani in Top 200 Italia
- Brani con >5.000 stream/giorno in Italia
- Brani del repertorio collecting (lista fornita)

### "Quanti dati saranno?"
Circa 25.000 righe al giorno = 9 milioni/anno = 2-3 GB
Gestibilissimo

### "Come faccio a popolare i dati storici?"
Non serve per MVP. Inizi da oggi, accumuli dati nel tempo.
Opzionale: se Sound Charts ha API per storico, puoi fare backfill.

### "Le posizioni in classifica non servono?"
Sono secondarie. Il focus è su stream/view assoluti, non posizioni.
Se vuoi, puoi salvarle come campo aggiuntivo.

---

## 📖 RICAPITOLANDO

### Cosa devi costruire:

1. Una tabella che unisce dati di tutte le piattaforme
2. Uno script che la popola ogni notte da Sound Charts
3. Un form dove filtro per artista/brano/paese/periodo
4. Una tabella che mostra risultati aggregati
5. Un bottone per scaricare Excel

### Cosa NON devi fare:

❌ Sistema complesso con 20 tabelle
❌ Dashboard real-time con grafici interattivi
❌ Machine learning o predizioni
❌ Salvare tutto Spotify (solo Italia rilevante)

### In pratica:

È come aggiungere una funzione "Cerca nel database" alla dashboard esistente.

---

## 🚀 PROSSIMI PASSI

1. Leggi questo documento
2. Fai domande su tutto quello che non è chiaro