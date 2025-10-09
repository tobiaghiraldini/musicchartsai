# ACRCloud PDF Field Mapping Guide

## Purpose
This document maps the fields shown in the "Dettagli Brano Analizzato.pdf" to our enhanced analysis report implementation.

## Field Mapping Checklist

Please verify that the following fields from your PDF are now visible in the enhanced report:

### ✅ Basic Track Information
- [ ] **Title** (Titolo)
- [ ] **Artists** (Artisti)
- [ ] **Album** (Album)
- [ ] **Label** (Etichetta)
- [ ] **Match Type** (Tipo di corrispondenza - music/cover)

### ✅ Fingerprint Scores
- [ ] **Score** (Punteggio) - Overall confidence 0-100%
- [ ] **Similarity** (Similarità) - 0-1 or 0-100
- [ ] **Distance** (Distanza) - Distance metric
- [ ] **Pattern Matching** (Corrispondenza pattern) - Percentage
- [ ] **Risk** (Rischio) - Fraud risk 0-100%
- [ ] **Match Type** (Tipo) - exact/cover/similar

### ✅ Time Offset Analysis
- [ ] **Played Duration** (Durata riprodotta) - in seconds
- [ ] **Play Offset** (Offset riproduzione) - in milliseconds
- [ ] **DB Begin Time Offset** (Inizio traccia DB) - in milliseconds
- [ ] **DB End Time Offset** (Fine traccia DB) - in milliseconds
- [ ] **Sample Begin Time Offset** (Inizio campione) - in milliseconds
- [ ] **Sample End Time Offset** (Fine campione) - in milliseconds

### ✅ Distortion Metrics
- [ ] **Time Skew** (Distorsione temporale) - 1.0 = normal
- [ ] **Frequency Skew** (Distorsione frequenza/pitch) - 1.0 = normal

### ✅ Identifiers
- [ ] **ISRC** - International Standard Recording Code
- [ ] **UPC** - Universal Product Code
- [ ] **ACRCloud ID** (ID ACRCloud)
- [ ] **MusicBrainz ID** (if shown in PDF)

### ✅ Platform Links
- [ ] **Spotify ID** and link
- [ ] **Deezer ID** and link
- [ ] **YouTube Video ID** and link
- [ ] **Apple Music** (if in PDF)

### ✅ Additional Metadata
- [ ] **Duration** (Durata totale) - Total track duration
- [ ] **Release Date** (Data rilascio) - if shown
- [ ] **Genres** (Generi) - if shown
- [ ] **Language** (Lingua) - if shown

### ✅ Analysis Metadata
- [ ] **Analysis ID**
- [ ] **File ID** (ACRCloud File ID)
- [ ] **Upload Date** (Data caricamento)
- [ ] **Analysis Date** (Data analisi)
- [ ] **Analysis Status**

## Missing Fields? Please Check

If any fields appear in your PDF but are **NOT** in our enhanced report, please note them here:

### Fields in PDF but not in Enhanced Report:
1. ________________________________ (describe what's shown)
2. ________________________________
3. ________________________________

### Screenshots Comparison

Please take screenshots to compare:
1. **PDF Section**: Screenshot the fingerprint values section
2. **Enhanced Report**: Screenshot the corresponding section in our app
3. **Note differences**: Mark any missing or differently displayed values

## Field Locations in Enhanced Report

### Where to Find Each Field:

1. **Overall Score Badge** (Top right of each match card)
   - Large number with color coding
   - Located next to track title

2. **Fingerprint Metrics Grid** (Below track info)
   - 4 boxes: Similarity, Distance, Pattern Match, Risk
   - Color-coded based on values

3. **Time Offset Analysis Section**
   - Blue boxes: Match Duration, Play Offset
   - Green box: DB Track Range
   - Purple box: Sample Range

4. **Distortion Analysis Section** (If available)
   - Yellow boxes showing time_skew and frequency_skew
   - Includes interpretation (faster/slower, higher/lower pitch)

5. **Identifiers & Metadata Section** (Bottom of card)
   - Grid showing ISRC, ACRCloud ID, UPC, etc.
   - Platform links with colored buttons

## ACRCloud API Response Structure

For reference, here's how ACRCloud structures the data:

```json
{
  "results": {
    "music": [
      {
        "offset": 0.0,
        "played_duration": 180.5,
        "type": "music",
        "result": {
          "acrid": "abc123...",
          "title": "Song Title",
          "artists": [{"name": "Artist Name"}],
          "album": {"name": "Album Name"},
          "label": "Record Label",
          
          // Fingerprint scores
          "score": 95,
          "similarity": 0.95,
          "distance": 0.05,
          "pattern_matching": 95,
          "risk": 90,
          "match_type": "exact",
          "result_from": 1,
          
          // Time offsets
          "duration_ms": 180000,
          "db_begin_time_offset_ms": 0,
          "db_end_time_offset_ms": 180000,
          "sample_begin_time_offset_ms": 0,
          "sample_end_time_offset_ms": 180000,
          "play_offset_ms": 0,
          
          // Distortion (optional)
          "time_skew": 1.0,
          "frequency_skew": 1.0,
          
          // Identifiers
          "isrc": "USRC12345678",
          "external_ids": {
            "isrc": "USRC12345678",
            "upc": "123456789012"
          },
          
          // Platform metadata
          "external_metadata": {
            "spotify": {
              "track": {"id": "spotify_id"},
              "artists": [{"id": "artist_id"}],
              "album": {"id": "album_id"}
            },
            "deezer": {...},
            "youtube": {"vid": "video_id"},
            "musicbrainz": {...}
          }
        }
      }
    ],
    "cover_songs": [...],
    "lyrics": [...]
  }
}
```

## Terminology Translation (Italian/English)

| Italian (PDF) | English (Our App) |
|---------------|-------------------|
| Titolo | Title |
| Artisti | Artists |
| Album | Album |
| Etichetta | Label |
| Punteggio | Score |
| Similarità | Similarity |
| Distanza | Distance |
| Corrispondenza pattern | Pattern Matching |
| Rischio | Risk |
| Durata riprodotta | Played Duration |
| Offset riproduzione | Play Offset |
| Inizio traccia DB | DB Begin Time Offset |
| Fine traccia DB | DB End Time Offset |
| Inizio campione | Sample Begin Time Offset |
| Fine campione | Sample End Time Offset |
| Distorsione temporale | Time Skew |
| Distorsione frequenza | Frequency Skew |
| Codice ISRC | ISRC Code |
| ID ACRCloud | ACRCloud ID |
| Data caricamento | Upload Date |
| Data analisi | Analysis Date |

## Verification Steps

1. **Upload a test song** with known matches
2. **Wait for analysis** to complete
3. **Open enhanced report** via "View Enhanced Report" button
4. **Compare with PDF** field by field
5. **Note any discrepancies** in the checklist above
6. **Take screenshots** for reference

## What to Look For

### Visual Elements:
- ✅ Color-coded score badges (red for high scores)
- ✅ Numbered match cards (1, 2, 3...)
- ✅ Expandable sections for different data types
- ✅ Platform links with icons
- ✅ Time values in both milliseconds and seconds

### Data Accuracy:
- ✅ Score values match between PDF and report
- ✅ Time offsets are correct
- ✅ ISRC codes match
- ✅ Track information is accurate

### Missing Features (to be implemented):
- ⬜ Lyrics analysis section
- ⬜ CSV/JSON export functionality
- ⬜ Timeline visualization
- ⬜ Waveform comparison

## Questions to Answer

After reviewing the enhanced report against your PDF:

1. **Are all numeric values (scores, offsets, etc.) displayed correctly?**
   - YES / NO / PARTIALLY (explain: _______________)

2. **Are there any fields in the PDF that are missing from our report?**
   - YES (list them: _______________) / NO

3. **Is the layout intuitive and easy to read compared to the PDF?**
   - YES / NO / NEEDS IMPROVEMENT (suggestions: _______________)

4. **Are the platform links working correctly?**
   - YES / NO / NOT TESTED / NO PLATFORM DATA AVAILABLE

5. **Is the color coding appropriate for risk assessment?**
   - YES / NO (suggest changes: _______________)

6. **Would you like any additional visualizations?**
   - YES (describe: _______________) / NO / NOT SURE

## Next Steps

Based on your feedback:

1. **If all fields match**: We're done! ✅
2. **If fields are missing**: Update `service.py` to capture them
3. **If display needs changes**: Update the match_detail_card.html template
4. **If new features needed**: Create enhancement tickets

## Contact for Issues

If you find discrepancies or missing fields, please provide:
1. Screenshot of the PDF section
2. Screenshot of the enhanced report
3. Description of what's different
4. Example song/analysis ID for testing

---

**Last Updated**: {{ current_date }}
**Implementation Version**: 1.0
**Status**: ⏳ Awaiting PDF verification
