# Music Analytics - Debugging Guide

**Date**: October 16, 2025  
**Status**: Troubleshooting Data Availability

---

## 🔍 Current Situation

**What's Working:**
- ✅ Form loads correctly
- ✅ Artist autocomplete works
- ✅ API calls are being made (no auth errors)
- ✅ No 404 placeholder errors

**What's Not Working:**
- ❌ SoundCharts API returning empty data for September 2025
- ❌ Results page not displaying (because no data)

---

## 🧪 Next Test Steps

### 1. Check Django Logs for API Response

With the latest update, you should now see full API responses logged:

```
INFO API Response for Lady Gaga on Spotify: {full_json_here}
```

**Look for**:
- What does the actual response contain?
- Is there a `plots` key?
- Is `plots` an empty array `[]`?
- Are there other keys we should be parsing?

### 2. Try Different Search Criteria

Test with these variations:

**A. Try September 2024 (not 2025)**
- Date: September 1-30, **2024** (one year ago)
- Reason: Maybe SoundCharts has more complete historical data

**B. Try Just Spotify**
- Uncheck all platforms except Spotify
- Reason: Most reliable platform per docs

**C. Try Different Artist**
- Try "Taylor Swift" or "Billie Eilish" (globally tracked artists)
- Reason: Lady Gaga might not be in the SoundCharts database with audience tracking

**D. Try Last 7 Days**
- Date range: October 9-15, 2025 (last week)
- Reason: Very recent data should be available

---

## 🔧 Platform Compatibility (Updated)

Based on SoundCharts API docs:

### Supported for `/streaming/` endpoint:
- ✅ **Spotify** - Monthly listeners (28-day rolling)
- ✅ **YouTube** - Aggregated views

### Supported for `/social/` endpoint:
- ✅ **Instagram** - Followers
- ✅ **TikTok** - Followers  
- ✅ **Facebook** - Followers
- ✅ **Twitter** - Followers

### NOT supported (will skip):
- ❌ Shazam
- ❌ Apple Music (different endpoint needed)
- ❌ Deezer
- ❌ Amazon
- ❌ Others

**Fix Applied**: System now only tries appropriate endpoints per platform.

---

## 📋 What to Check in Django Console

When you retry the search, look for:

### 1. Platform Endpoint Selection
```
INFO Using STREAMING endpoint for Spotify
INFO Using SOCIAL endpoint for Instagram
WARNING Platform Shazam (shazam) not supported for streaming or social endpoints. Skipping.
```

### 2. API Response Content
```
INFO API Response for Lady Gaga on Spotify: {"plots": [...], "followerCount": 123456, ...}
```

**Copy the full JSON** from the logs and share it - this will tell us exactly what structure SoundCharts is returning.

### 3. Data Points Parsed
```
INFO Fetched 30 streaming data points for Lady Gaga on Spotify
```

If still "0 data points", the issue is:
- API returned empty `plots: []`
- OR plots have a different structure than expected

---

## 🎯 Possible Causes & Solutions

### Cause 1: Artist Not Tracked by SoundCharts

**Symptom**: API returns `200 OK` but empty `plots: []`

**Solution**: 
- Try a different artist (major global star)
- Check artist on soundcharts.com website first
- Some artists aren't tracked for audience data

### Cause 2: Platform Slug Mismatch

**Symptom**: 404 error or empty response

**Solution**:
- SoundCharts might expect different slug format
- Try lowercase without hyphens (e.g., `applemusic` not `apple-music`)
- Check SoundCharts docs for exact slug format

### Cause 3: Response Format Different

**Symptom**: Response contains data but we're not parsing it

**Solution**:
- Check the logged API response structure
- Update parsing logic if format differs
- Maybe it's `{"data": [...]}` not `{"plots": [...]}`

### Cause 4: Date Range Issue

**Symptom**: API says "no data for this period"

**Solution**:
- Try different date ranges
- Start with very recent data (last 7-14 days)
- Try historical data (6 months ago)

---

## 🚀 Immediate Action Items

**Please do this**:

1. **Test again with updated code** (restart Django if needed)

2. **Try this specific search**:
   - Artist: "Billie Eilish" or "Taylor Swift"
   - Platforms: **ONLY Spotify** (uncheck all others)
   - Date: **September 1-30, 2024** (not 2025!)
   - Country: any

3. **Check Django console** for:
   ```
   INFO API Response for [Artist] on Spotify: {COPY THIS FULL JSON}
   ```

4. **Share the full API response JSON** - this is critical for debugging

---

## 🔍 Expected vs Actual

### Expected API Response (from docs):
```json
{
  "plots": [
    {"date": "2024-09-01", "value": 45123456},
    {"date": "2024-09-02", "value": 45234567},
    ...
  ],
  "followerCount": 45234567,
  "topCities": [...]
}
```

### What We Need to Know:
- Is the response actually empty?
- Or is the data in a different structure?
- Are there error messages in the response?

---

## 💡 Quick Test Command

You can also test the API directly:

```bash
curl -H "x-app-id: YOUR_APP_ID" \
     -H "x-api-key: YOUR_API_KEY" \
     "https://customer.api.soundcharts.com/api/v2/artist/ARTIST_UUID/streaming/spotify?startDate=2024-09-01&endDate=2024-09-30"
```

Replace:
- `YOUR_APP_ID` and `YOUR_API_KEY` from your settings
- `ARTIST_UUID` with Lady Gaga's UUID from the logs

This will show exactly what SoundCharts returns.

---

## 📝 What I Updated

**Changes just made:**

1. ✅ Only try `/streaming/` for Spotify and YouTube
2. ✅ Only try `/social/` for Instagram, TikTok, Facebook, Twitter
3. ✅ Skip unsupported platforms (Shazam, etc.)
4. ✅ Log full API responses for debugging
5. ✅ Better error messages with suggestions

**Next**: Once you share the actual API response, I can fix the parsing logic if needed!

