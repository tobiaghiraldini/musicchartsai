# Music Analytics - Metric Explanations

**Date**: October 16, 2025  
**Status**: ✅ UI Enhanced with Clear Metrics

---

## 🎯 Understanding the Data

### **The Core Question**
> "How much did Achille Lauro do in Italy in September 2024?"

### **The Answer Format**

**Search Parameters**:
- Artist: Achille Lauro
- Platform: Spotify
- Date: September 1-30, 2024
- Country: IT (Italy)

**Results Shown**:
```
┌─────────────────────────────────────────────────┐
│ Achille Lauro                                   │
│ Sept 1-30, 2024 | Spotify | IT                  │
└─────────────────────────────────────────────────┘

Period Average: 8.5M     ← ANSWER: "8.5M monthly listeners in September"
Latest Value:   9.2M     ← Current state at month end
Growth:        +700K     ← Grew by 700K during September
Peak:          9.5M      ← Best day was 9.5M
```

---

## 📊 Metric Definitions

### **1. Period Average** ⭐ (PRIMARY METRIC)

**What it is**: Average of all daily monthly listener counts across the selected period

**Formula**: `SUM(all values) / number of days`

**Example**: 
- Sept 1: 8.2M
- Sept 2: 8.3M
- ...
- Sept 30: 9.2M
- **Average**: 8.5M

**Use for**: **"How much did artist X do in month Y?"**

**Answer**: "Achille Lauro had an average of 8.5M monthly listeners in September 2024"

---

### **2. Latest Value** (CURRENT STATE)

**What it is**: The most recent audience count (as of end date)

**Example**: 9.2M (as of September 30, 2024)

**Use for**: "What's the current audience?"

**Answer**: "As of September 30, Achille Lauro has 9.2M monthly listeners"

**Note**: This is a SNAPSHOT, not cumulative

---

### **3. Difference** (GROWTH INDICATOR)

**What it is**: Change from first day to last day of period

**Formula**: `Latest Value - First Value`

**Example**: 
- Sept 1: 8.5M
- Sept 30: 9.2M
- **Difference**: +700K (growth)

**Colors**:
- 🟢 Green = Positive (growing)
- 🔴 Red = Negative (declining)

**Use for**: "Did the artist grow during this period?"

**Answer**: "Achille Lauro grew by 700K monthly listeners during September"

---

### **4. Peak** (BEST PERFORMANCE)

**What it is**: Highest audience count in the period

**Example**: 9.5M (on September 25, 2024)

**Use for**: "What was the best day?"

**Answer**: "Peak performance was 9.5M monthly listeners"

---

## 🔍 What "Monthly Listeners" Actually Means

### **Spotify Monthly Listeners**

**Definition**: Unique listeners over a **28-day rolling window**

**Example for September 2**:
- "107.9M monthly listeners" = 107.9M unique people listened between August 5 - September 2 (28 days)

**Key Points**:
- ✅ It's **unique listeners**, not total streams
- ✅ It's a **28-day window**, not calendar month
- ✅ Updates **daily** (new 28-day window each day)
- ❌ NOT cumulative (doesn't add up month to month)
- ❌ NOT total streams (one person = 1 listener, regardless of how many times they played)

---

## 🌍 Country Filtering

### **How It Works**

**SoundCharts API Response** includes:
```json
{
  "items": [{
    "date": "2024-09-02",
    "value": 107906557,  // Global total
    "countryPlots": [
      {"countryCode": "IT", "value": 559152},   // Italy: 559K
      {"countryCode": "US", "value": 8761382},  // USA: 8.7M
      ...
    ]
  }]
}
```

**When Country Selected**:
- System extracts values from `countryPlots` array
- Only shows data for that specific country
- **Italy (IT)**: 559K monthly listeners
- **Global (no filter)**: 107.9M monthly listeners

**Supported Platforms**:
- ✅ Spotify (has countryPlots)
- ✅ YouTube (likely has countryPlots)
- ❌ Social platforms (Instagram, TikTok) - no country breakdown

---

## 📋 Answering Common Questions

### Q1: "How much did Artist X do in Italy in September?"

**Search**:
- Artist: X
- Platform: Spotify
- Date: Sept 1-30, 2024
- Country: IT

**Answer**: Look at **Period Average** = "X.XM average monthly listeners in Italy during September"

---

### Q2: "Is the artist growing?"

**Answer**: Look at **Difference** column
- Green (+) = Growing
- Red (-) = Declining
- Magnitude shows how much

---

### Q3: "What's the current audience?"

**Answer**: Look at **Latest Value** = "As of [end date], X.XM monthly listeners"

---

### Q4: "What was the best performance?"

**Answer**: Look at **Peak** = "Peak of X.XM monthly listeners"

---

## 🎨 UI Enhancements Implemented

### **1. Period Context Header**

Shows search criteria clearly:
```
Achille Lauro
📅 Sept 1-30, 2024 | Spotify, YouTube | IT
```

### **2. Tooltip Icons on Summary Cards**

Each card has an (ℹ️) icon that shows explanation on hover

### **3. Collapsible Explanation Panel**

"What do these metrics mean?" button reveals:
- Detailed explanation of each metric
- Important note about Spotify's 28-day window
- Guidance on which metric to use
- Country filter status

### **4. Table Header Tooltips**

Column headers show (ℹ️) icons with explanations:
- Current: "Latest audience count as of end date"
- Period Avg: "Average audience across period"
- Difference: "Change from start to end (growth)"
- Peak: "Highest value in period"

### **5. Period Context in Table**

Table subtitle shows:
```
Sept 1-30, 2024 | Spotify, YouTube | Italy
```

---

## 📊 Example Output Interpretation

### **Search**: Achille Lauro, Spotify, September 2024, Italy

**Results**:
```
┌─────────────────────────────────────┐
│ Period Average: 2.1M  ℹ️             │  ← "In September, Achille had avg 2.1M monthly listeners in Italy"
│ Latest Value:   2.3M  ℹ️             │  ← "As of Sept 30, he has 2.3M"
│ Growth:        +200K  ℹ️             │  ← "Grew by 200K during September"
│ Peak:          2.5M   ℹ️             │  ← "Best day was 2.5M"
└─────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Artist × Platform Metrics                           │
│ Sept 1-30, 2024 | Spotify | Italy                   │
├───────────┬──────────┬─────────┬──────────┬─────────┤
│ Artist    │ Platform │ Current │ Period   │ Diff    │
│           │          │         │ Avg      │         │
├───────────┼──────────┼─────────┼──────────┼─────────┤
│ Achille   │ Spotify  │ 2.3M    │ 2.1M     │ +200K 🟢│
│ Lauro     │          │         │          │         │
└───────────┴──────────┴─────────┴──────────┴─────────┘
```

**Client's Question Answered**: 
> "Achille Lauro had an average of **2.1M monthly listeners** in Italy during September 2024, 
> growing by 200K to reach 2.3M by month end."

---

## ⚠️ Important Clarifications

### **What This Data IS**:
- ✅ Monthly listeners (unique people who listened in 28-day window)
- ✅ Daily snapshots of that 28-day rolling count
- ✅ Average across the month = typical monthly listener count
- ✅ Country-specific (when country selected)

### **What This Data is NOT**:
- ❌ NOT total streams (one listener ≠ one stream)
- ❌ NOT calendar month exact (it's 28-day rolling)
- ❌ NOT cumulative (doesn't add up month-to-month)
- ❌ NOT all-time total

### **For "Total Streams in September"**:

**You would need a different SoundCharts endpoint** (if available):
- `/api/v2/song/{uuid}/streaming-stats` or similar
- That would give actual stream counts per track
- Then sum across all artist's tracks

**Current endpoint** gives **monthly listeners**, not **total streams**.

---

## 🔧 Future Enhancements

### **Phase 1.5: Country Breakdown Table**

Show top countries in results:
```
Top Countries for Achille Lauro on Spotify (Sept 2024):
┌──────────┬────────────┐
│ Country  │ Listeners  │
├──────────┼────────────┤
│ Italy    │ 2.3M       │
│ Germany  │ 850K       │
│ France   │ 620K       │
└──────────┴────────────┘
```

### **Phase 2: Track Breakdown**

Add "View Tracks" button showing:
```
Which tracks contributed to these 2.1M listeners?
┌─────────────────┬──────────────┐
│ Track           │ Monthly Plays│
├─────────────────┼──────────────┤
│ AMOR            │ 1.2M         │
│ Rolls Royce     │ 900K         │
└─────────────────┴──────────────┘
```

---

## ✅ Summary

**UI Now Provides**:
- ✅ Clear period context (dates, platforms, country)
- ✅ Tooltips on every metric
- ✅ Collapsible explanation panel
- ✅ Guidance on which metric to use
- ✅ Note about Spotify's 28-day window
- ✅ Country filter status indicator

**Users Can Now**:
- Understand what each number means
- Know which metric answers their question
- See country-specific data (when filter works)
- Export to Excel with labeled columns

**Next**: Debug country filter, then proceed to Phase 2 (track breakdown) when ready!

