# Radio Airplay Integration - Implementation Discussion

## Overview

This document outlines the proposed integration of SoundCharts radio airplay data into the Music Analytics feature, based on the [SoundCharts Radio API documentation](https://developers.soundcharts.com/documentation/reference/radio/get-radios).

**Date**: October 27, 2025  
**Status**: Discussion Phase

---

## 1. Available SoundCharts Radio APIs

### 1.1 Get Radios List
**Endpoint**: `GET /api/v2.22/radio`  
**Documentation**: https://developers.soundcharts.com/documentation/reference/radio/get-radios

**Purpose**: Get list of all available radio stations on SoundCharts

**Response Data**:
```json
{
  "items": [
    {
      "uuid": "...",
      "name": "BBC Radio 1",
      "slug": "bbc-radio-1",
      "cityName": "London",
      "countryCode": "GB",
      "countryName": "United Kingdom",
      "timeZone": "Europe/London",
      "reach": 1500000,
      "firstAiredAt": "2020-01-01T00:00:00Z",
      "imageUrl": "..."
    }
  ]
}
```

**Notes**:
- "reach" = sum of followers across TuneIn, Instagram, Facebook, X, YouTube
- For national radios, cityName = headquarters location
- We **already have** the `Radio` model ✅

---

### 1.2 Get Artist Radio Spins (Detailed)
**Endpoint**: `GET /api/v2/artist/{uuid}/broadcasts`  
**Documentation**: https://developers.soundcharts.com/documentation/reference/artist/get-radio-spins

**Purpose**: Get individual broadcast events for all tracks by an artist

**Query Parameters**:
- `radioSlugs`: Filter by specific radios (comma-separated)
- `countryCode`: Filter by country (ISO 3166-2)
- `startDate`: Period start (YYYY-MM-DD)
- `endDate`: Period end (YYYY-MM-DD)
- **Max period**: 90 days
- `offset`, `limit`: Pagination (max 100 per page)

**Response Data**:
```json
{
  "items": [
    {
      "uuid": "broadcast-uuid",
      "airedAt": "2025-09-15T14:23:00Z",
      "radio": {
        "uuid": "radio-uuid",
        "name": "BBC Radio 1",
        "slug": "bbc-radio-1",
        "countryCode": "GB"
      },
      "song": {
        "uuid": "song-uuid",
        "name": "Track Name",
        "artists": [...]
      }
    }
  ]
}
```

**Use Cases**:
- See every time a track was played on radio
- Identify which radios play the artist most
- Analyze broadcast timing patterns

---

### 1.3 Get Artist Radio Spin Count (Aggregated)
**Endpoint**: `GET /api/v2/artist/{uuid}/broadcasts/count`  
**Documentation**: https://developers.soundcharts.com/documentation/reference/artist/get-radio-spin-count

**Purpose**: Get aggregated spin counts (daily totals)

**Query Parameters**: Same as detailed spins

**Response Data**:
```json
{
  "items": [
    {
      "date": "2025-09-15",
      "count": 45,
      "radio": {
        "uuid": "...",
        "name": "BBC Radio 1",
        "slug": "bbc-radio-1"
      }
    }
  ]
}
```

**Use Cases**:
- Daily spin count trends
- Compare radio exposure across stations
- More efficient than individual broadcasts

---

### 1.4 Get Song Radio Spins
**Endpoint**: `GET /api/v2/song/{uuid}/broadcasts`  
**Documentation**: https://developers.soundcharts.com/documentation/reference/song/get-radio-spins

**Similar to artist spins, but for a single track**

---

### 1.5 Get Song Radio Spin Count
**Endpoint**: `GET /api/v2/song/{uuid}/broadcasts/count`  
**Documentation**: https://developers.soundcharts.com/documentation/reference/song/get-radio-spin-count

**Aggregated counts for a single track**

---

## 2. Current Database Schema

### ✅ Already Exists: Radio Model
```python
class Radio(models.Model):
    name = models.CharField(max_length=255)
    uuid = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    city_name = models.CharField(max_length=255)
    country_code = models.CharField(max_length=255)
    country_name = models.CharField(max_length=255)
    time_zone = models.CharField(max_length=255)
    reach = models.IntegerField()
    first_aired_at = models.DateTimeField()
    image_url = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### ✅ Already Exists: Platform with 'airplay' support
- Platform type: `'radio'`
- Platform slug: `'airplay'` (already added to analytics)

---

## 3. Implementation Options

### Option A: **Lightweight Approach** (Recommended for MVP)
**Focus**: Real-time aggregation, no persistent storage of broadcasts

**What to implement**:
1. ✅ **Sync Radio List** (one-time or periodic):
   - Fetch `/api/v2.22/radio`
   - Populate/update `Radio` table
   - Allows radio filtering in UI

2. ✅ **Artist Radio Spin Count API** (on-demand):
   - Call `/api/v2/artist/{uuid}/broadcasts/count` when analytics is run
   - Aggregate totals for the period
   - Display in analytics UI alongside streaming data

3. ✅ **Track Radio Spin Count** (on-demand for Phase 2):
   - Call `/api/v2/song/{uuid}/broadcasts/count` for track breakdown
   - Show per-track radio exposure

**Pros**:
- ✅ Fast to implement
- ✅ Always up-to-date data (no caching issues)
- ✅ Minimal database complexity
- ✅ No storage of individual broadcasts (saves space)

**Cons**:
- ❌ API calls on every analytics query (could be slow)
- ❌ Can't do historical trend analysis beyond 90 days
- ❌ No correlation analysis with streaming data over time

**Best For**:
- Quick implementation
- "How many radio spins in September?" type questions
- Simple radio exposure metrics

---

### Option B: **Full Storage Approach** (For Advanced Analytics)
**Focus**: Store all broadcast data for deep analysis

**What to implement**:
1. **New Models**:
   ```python
   class RadioBroadcast(models.Model):
       """Individual broadcast event"""
       uuid = models.CharField(max_length=255, unique=True)
       radio = models.ForeignKey(Radio, on_delete=models.CASCADE)
       track = models.ForeignKey(Track, on_delete=models.CASCADE)
       artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
       aired_at = models.DateTimeField()
       api_data = models.JSONField(default=dict)
       created_at = models.DateTimeField(auto_now_add=True)
   
   class RadioSpinCount(models.Model):
       """Aggregated daily counts (pre-computed)"""
       artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
       track = models.ForeignKey(Track, on_delete=models.CASCADE, null=True, blank=True)
       radio = models.ForeignKey(Radio, on_delete=models.CASCADE)
       date = models.DateField()
       spin_count = models.IntegerField()
       api_data = models.JSONField(default=dict)
       
       class Meta:
           unique_together = ['artist', 'track', 'radio', 'date']
   ```

2. **Periodic Sync Tasks**:
   - Celery task to fetch broadcasts for tracked artists
   - Store in database for historical analysis

3. **Analytics Integration**:
   - Query local database for radio data
   - Combine with streaming metrics

**Pros**:
- ✅ Historical data beyond 90 days
- ✅ Fast analytics queries (local data)
- ✅ Correlation analysis possible
- ✅ Can identify trends over time

**Cons**:
- ❌ Complex implementation
- ❌ Requires periodic sync tasks
- ❌ Large database storage needs
- ❌ Data staleness (not real-time)

**Best For**:
- Long-term trend analysis
- Radio ↔ streaming correlation studies
- Research and deep insights

---

### Option C: **Hybrid Approach** (Balanced)
**Focus**: Store aggregated counts, fetch details on-demand

**What to implement**:
1. ✅ **Sync Radio List** (periodic)
2. ✅ **Store Aggregated Spin Counts** (daily sync):
   - Fetch `/api/v2/artist/{uuid}/broadcasts/count` daily
   - Store in `RadioSpinCount` model (lightweight)
   - Build historical database incrementally

3. ✅ **Fetch Details On-Demand**:
   - For recent data (< 90 days): call API directly
   - For historical data: query local `RadioSpinCount` table

**Pros**:
- ✅ Reasonable implementation complexity
- ✅ Historical trends available
- ✅ Smaller storage footprint (aggregates only)
- ✅ Flexible: real-time + historical

**Cons**:
- ⚠️ Still requires sync tasks
- ⚠️ Individual broadcast details not stored

**Best For**:
- Balanced approach for most use cases
- Trend analysis with manageable complexity

---

## 4. Proposed Analytics UI Integration

### 4.1 Add Radio Data to Artist Summary Cards

**Current Structure**:
```
Spotify:  Start | End | Diff | Avg | Peak | Track Streams
YouTube:  Start | End | Diff | Avg | Peak | Track Streams
```

**Proposed Addition**:
```
Airplay:  Total Spins | Avg Daily Spins | Peak Day | Stations Count
```

**Example**:
```
┌─────────────────────────────────────────────────────┐
│ 📻 AIRPLAY (September 2024)                        │
├─────────────────────────────────────────────────────┤
│ Total Spins:        1,245                          │
│ Avg Daily:          41.5                           │
│ Peak Day:           89 (Sep 15)                    │
│ Stations:           12 radios                      │
│ Top Station:        BBC Radio 1 (345 spins)       │
└─────────────────────────────────────────────────────┘
```

---

### 4.2 Track Breakdown Enhancement

**Current Track Table**:
| Track | Streams | Avg | Peak | Best Pos | Weeks | Entry | Last Seen |

**Add Radio Column**:
| Track | Streams | **Radio Spins** | Avg | Peak | Best Pos | Weeks | Entry | Last Seen |

**Example**:
```
Hit Song A    12.5M    🎵 845 spins
Hit Song B    8.2M     🎵 532 spins
Deep Cut      1.1M     🎵 12 spins
```

---

### 4.3 Radio Breakdown (Expandable Detail)

**Click to expand track row → Show radio details**:

```
📻 Radio Airplay Details: "Hit Song A"
┌──────────────────────────────────────────────────────┐
│ Radio Station      Country  Spins  Last Aired        │
├──────────────────────────────────────────────────────┤
│ BBC Radio 1        🇬🇧 GB    145    Sep 28, 2024     │
│ NRJ France         🇫🇷 FR     98    Sep 27, 2024     │
│ RTL Germany        🇩🇪 DE     67    Sep 26, 2024     │
│ ...                                                   │
└──────────────────────────────────────────────────────┘
Total: 845 spins across 12 stations
```

---

### 4.4 Radio Filter in Search Form

**Add to existing filters**:
```html
☐ Include Radio Airplay Data
   ↳ Country: [Select...] or [All]
   ↳ Radios:  [Select stations...] or [All]
```

---

## 5. Correlation Analysis Possibilities

### If we store historical data:

#### 5.1 Radio Impact on Streaming
**Question**: "Does radio airplay drive streaming numbers?"

**Analysis**:
- Plot radio spins vs. streaming listeners over time
- Calculate correlation coefficient
- Identify lag (e.g., radio spike → streaming increase 2-3 days later)

**Visual**:
```
Chart: Dual-axis line graph
  Y1: Radio Spins (bars)
  Y2: Spotify Monthly Listeners (line)
  X:  Date
```

#### 5.2 Regional Analysis
**Question**: "Which countries show strongest radio-streaming correlation?"

**Analysis**:
- Group by country
- Compare radio spins to local audience data
- Identify markets where radio still drives discovery

#### 5.3 Track Lifecycle
**Question**: "Did radio help a track enter charts?"

**Analysis**:
- Compare track entry date with first radio airplay
- Identify if radio preceded or followed chart success

---

## 6. Recommended Implementation Plan

### Phase 1: MVP (Quick Win) - **Option A**

**Week 1: Backend**
1. Add service methods to `SoundchartsService`:
   - `get_radios()` - fetch radio list
   - `get_artist_radio_spin_count(artist_uuid, start_date, end_date, country=None)`
   - `get_track_radio_spin_count(track_uuid, start_date, end_date, country=None)`

2. Integrate into `MusicAnalyticsService`:
   - Add radio spin aggregation to `fetch_and_aggregate_artist_metrics()`
   - Add to `get_track_breakdown_for_artist()`

3. Update views to pass radio data to frontend

**Week 1-2: Frontend**
1. Add "Airplay" summary card to per-platform groups
2. Add "Radio Spins" column to track breakdown table
3. Add optional "Include Radio Data" checkbox to search form

**Week 2: Polish**
- Excel export with radio data
- Documentation
- Testing

**Estimated Effort**: 3-5 days

---

### Phase 2: Historical Tracking (Future Enhancement) - **Option C**

**Requirements**:
1. Create `RadioSpinCount` model
2. Celery periodic task to sync spin counts daily
3. Update analytics service to use local data for historical queries
4. Admin interface for managing radio sync

**Estimated Effort**: 5-7 days

---

### Phase 3: Advanced Analytics (Future) - **Option B Features**

**Requirements**:
1. Correlation analysis UI
2. Advanced visualizations (charts)
3. Regional insights dashboard
4. Radio impact reports

**Estimated Effort**: 10+ days

---

## 7. Data Examples and Use Cases

### Use Case 1: Artist Manager Question
**Q**: "How much radio exposure did we get in Italy last month?"

**Answer with Option A**:
```
Artist: Achille Lauro
Period: September 2024
Country: Italy (IT)

📻 Radio Airplay Summary:
- Total Spins: 234
- Avg Daily: 7.8
- Stations: 5 (RTL, Virgin Radio IT, ...)
- Top Track: "Che Sarà" (145 spins)
```

---

### Use Case 2: A&R Question
**Q**: "Is this track getting radio play before it charted?"

**Answer with Option C** (requires historical data):
```
Track: "New Hit Song"
Chart Entry: Sep 15, 2024
First Radio Airplay: Sep 8, 2024

📻 Timeline:
Sep 8:  First radio spin (BBC Radio 1)
Sep 10: 5 stations playing
Sep 15: Entered Spotify UK Top 200 (#87)
Sep 20: 15 stations playing, chart position #42

✅ Radio preceded chart success by 7 days
```

---

### Use Case 3: Label Strategy
**Q**: "Which markets should we focus radio promotion?"

**Answer with Option C**:
```
Artist: Example Artist
Comparison: Radio Spins vs. Streaming Growth

🇬🇧 UK:
  Radio: 450 spins → Streaming: +15% 📈 Strong correlation
  
🇩🇪 Germany:
  Radio: 120 spins → Streaming: +2% 📉 Weak correlation
  
🇮🇹 Italy:
  Radio: 890 spins → Streaming: +42% 📈🔥 Very strong!

💡 Recommendation: Increase radio promotion in Italy and UK
```

---

## 8. Technical Considerations

### 8.1 API Rate Limits
- SoundCharts API has rate limits (unspecified in docs)
- For Option A: Cache results client-side for duration of analytics session
- For Option B/C: Spread API calls across time with Celery tasks

### 8.2 Data Volume
**Rough Estimates**:
- Individual broadcasts: ~50 bytes per record
- 1 artist with 10 tracks, 1000 spins/month = 50 KB/month
- 100 artists tracked = 5 MB/month = 60 MB/year
- Aggregated counts: ~10 KB/month/artist = 12 MB/year for 100 artists

**Conclusion**: Storage is not a concern for aggregated data (Option C)

### 8.3 Query Performance
- Option A: API latency (1-2 seconds per call)
- Option B/C: Database query (< 100ms)
- Recommendation: Implement client-side loading states for Option A

---

## 9. Questions for Discussion

### Priority Questions:

1. **Which implementation option do you prefer?**
   - Option A (Quick, on-demand API calls)
   - Option C (Hybrid with historical data)
   - Option B (Full storage)

2. **What questions do you want to answer with radio data?**
   - Simple: "How many spins this month?"
   - Advanced: "How does radio affect streaming?"

3. **Do you need historical radio data beyond 90 days?**
   - If yes → Need Option B or C
   - If no → Option A is sufficient

4. **UI Preferences**:
   - Separate "Airplay" card in summary?
   - Integrate into existing track table?
   - Both?

5. **Radio filtering**:
   - Important to filter by specific stations?
   - Or just country-level filtering is enough?

### Technical Questions:

6. **Correlation analysis priority?**
   - High: Implement in Phase 1-2
   - Low: Defer to Phase 3

7. **Excel export requirements?**
   - Include radio data in existing sheets?
   - Separate sheet for radio breakdown?

---

## 10. My Recommendation

### Start with **Option A (Lightweight)** for immediate value:

**Why**:
- ✅ Can be implemented in 3-5 days
- ✅ Answers 80% of user questions
- ✅ No complex sync infrastructure
- ✅ Easy to test and iterate

**Then evaluate** if Option C (historical tracking) is needed based on:
- User feedback
- Performance concerns
- Demand for trend analysis

**Reserve Option B** for when you have specific correlation analysis requirements

---

## 11. Next Steps

**If you agree with Option A:**

1. ✅ I'll implement the service methods to call radio APIs
2. ✅ Integrate into analytics service alongside streaming data
3. ✅ Add UI components to display radio metrics
4. ✅ Update Excel export
5. ✅ Document the feature

**Timeline**: 3-5 days

**Ready to proceed when you are!** 🚀

---

*Last Updated: October 27, 2025*
*Author: AI Assistant (Cursor)*

