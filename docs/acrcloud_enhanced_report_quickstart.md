# ACRCloud Enhanced Report - Quick Start Guide

## 🚀 Quick Start (5 minutes)

### Step 1: Start the Server
```bash
cd /Users/tobia/Code/Projects/Customers/Knowmark/MusicCharts/Django/rocket-django-main

# Activate virtual environment
source venv/bin/activate

# Run Django server
python manage.py runserver
```

### Step 2: Access the Application
Open your browser and go to:
```
http://localhost:8000/acrcloud/upload/
```

### Step 3: Upload a Test Song
1. Click "Upload Audio" or navigate to the upload page
2. Select an audio file (MP3, WAV, M4A, etc.)
3. Enter title and artist (optional)
4. Click "Upload"

### Step 4: Wait for Analysis
The song will be processed by ACRCloud. This may take 1-5 minutes depending on:
- File size
- Network speed
- ACRCloud API response time

### Step 5: View Enhanced Report
Once analysis is complete:
1. Click "View Enhanced Report" (blue button)
2. Or navigate directly to:
   ```
   http://localhost:8000/acrcloud/analysis/<analysis-id>/enhanced/
   ```

## 🎯 What to Expect

### If Matches Are Found:
You'll see detailed cards for each match showing:

**Header Section:**
- Track title and artists
- Match type badge (Music/Cover)
- Overall score (large number, color-coded)

**Fingerprint Metrics:**
- Similarity score
- Distance metric
- Pattern matching percentage
- Risk score

**Time Analysis:**
- Match duration in seconds
- Play offset (where match starts)
- Database track time range
- Sample time range

**Distortion Analysis** (if available):
- Time skew (tempo changes)
- Frequency skew (pitch changes)

**Identifiers:**
- ISRC code
- ACRCloud ID
- UPC code (if available)
- Platform links (Spotify, Deezer, YouTube)

### If No Matches Found:
You'll see a message:
> "No Matches Found - This song did not match any tracks in the ACRCloud database."

## 🔍 Testing Recommendations

### Test Files to Use:

1. **Popular Commercial Track** (Expected: High-confidence matches)
   - Use a well-known song
   - Should return multiple matches with high scores (90-100)
   - Will likely have platform links

2. **Cover Version** (Expected: Cover matches)
   - Upload a cover version of a popular song
   - Should show in "cover_songs" category
   - Lower scores than exact match (50-80)

3. **Modified Track** (Expected: Distortion metrics)
   - Speed up or slow down a track slightly
   - Should show time_skew != 1.0
   - Pitch shift should show frequency_skew != 1.0

4. **Original/Unreleased Track** (Expected: No matches)
   - Use your own original recording
   - Should return no matches
   - Good test for "no results" display

5. **Short Snippet** (Expected: Partial matches)
   - Upload a 30-second clip
   - Check time offsets and played_duration
   - Verify sample range matches clip length

### Test Cases Checklist:

#### Basic Functionality:
- [ ] Upload completes successfully
- [ ] Analysis starts automatically
- [ ] Status changes from "Processing" to "Analyzed"
- [ ] Enhanced report link appears
- [ ] Enhanced report page loads

#### Data Display:
- [ ] All matches are shown (not just top 5)
- [ ] Match numbers are sequential (1, 2, 3...)
- [ ] Scores are displayed correctly
- [ ] Color coding works (red for high scores)
- [ ] Time values are formatted correctly

#### Fingerprint Values:
- [ ] Score is displayed
- [ ] Similarity is shown (0-1 format)
- [ ] Distance is shown
- [ ] Pattern matching percentage is visible
- [ ] Risk score is displayed with color

#### Time Offsets:
- [ ] Match duration in seconds
- [ ] Play offset in ms and seconds
- [ ] DB time range is shown
- [ ] Sample time range is shown
- [ ] Values are non-zero for actual matches

#### Identifiers:
- [ ] ISRC code is displayed (if available)
- [ ] ACRCloud ID is shown
- [ ] UPC code appears (if available)
- [ ] Match type is labeled correctly

#### Platform Links:
- [ ] Spotify link works (if data available)
- [ ] Deezer link works (if data available)
- [ ] YouTube link works (if data available)
- [ ] Links open in new tab

#### UI/UX:
- [ ] Layout is responsive on desktop
- [ ] Layout works on mobile
- [ ] Print functionality works
- [ ] Navigation buttons work
- [ ] Page scrolls smoothly with many matches

#### Edge Cases:
- [ ] Song with 0 matches displays correctly
- [ ] Song with 1 match displays correctly
- [ ] Song with 50+ matches loads (performance check)
- [ ] Missing optional fields show "-" instead of error
- [ ] Missing platform data doesn't break layout

## 📊 Expected Results by Track Type

### Commercial Pop Song (e.g., "Shape of You" by Ed Sheeran):
```
Expected Matches: 5-15
Score Range: 95-100
Match Type: Music
Time Skew: ~1.0
Frequency Skew: ~1.0
Platform Links: All (Spotify, Deezer, YouTube)
Risk: High (90-100) - exact duplicate
```

### Cover Version:
```
Expected Matches: 2-10
Score Range: 50-80
Match Type: Cover
Time Skew: ~1.0
Frequency Skew: ~1.0
Platform Links: May be available
Risk: Medium (40-70)
```

### Modified Track (sped up 10%):
```
Expected Matches: 1-5
Score Range: 70-90
Match Type: Music
Time Skew: ~1.1 (10% faster)
Frequency Skew: ~1.0
Platform Links: May be available
Risk: High (70-90)
```

### Original Track:
```
Expected Matches: 0
Score Range: N/A
Match Type: N/A
Platform Links: None
Risk: Low (no matches)
```

## 🐛 Troubleshooting

### Issue: "No Enhanced Report Button"
**Solution:** 
- Check song status is "Analyzed"
- Refresh the song detail page
- Verify analysis completed (check analysis table in admin)

### Issue: "Page Shows No Matches" but there should be
**Solution:**
- Check Analysis.track_matches in Django admin
- Verify webhook processing completed
- Check Analysis.raw_response for match data
- May need to re-run analysis

### Issue: "Missing Fingerprint Values (showing as -)"
**Solution:**
- This is normal - ACRCloud doesn't always provide all fields
- Check raw_data JSONField to verify what was returned
- Optional fields: time_skew, frequency_skew, UPC

### Issue: "No Platform Links"
**Solution:**
- Not all tracks have platform metadata
- Check track_info.external_metadata in raw_data
- Try with a different (more popular) song

### Issue: "Time Offsets All Zero"
**Solution:**
- May indicate match at the beginning of both tracks
- Check if played_duration is also zero (might be data issue)
- Verify in raw_data that ACRCloud provided the values

### Issue: "Page Load Very Slow"
**Solution:**
- If song has 50+ matches, consider pagination
- Check database query performance
- Add select_related/prefetch_related to view
- Consider limiting matches displayed

### Issue: "Colors Look Wrong (Dark Mode)"
**Solution:**
- Check if dark mode classes are applying
- Verify Tailwind CSS dark: variants
- May need to adjust color thresholds

## 🔗 Useful URLs

### Development:
```
Upload Page:              http://localhost:8000/acrcloud/upload/
View Songs:               http://localhost:8000/acrcloud/songs/
Song Detail:              http://localhost:8000/acrcloud/song/<song-id>/
Enhanced Report:          http://localhost:8000/acrcloud/analysis/<analysis-id>/enhanced/
Pattern Matching Table:   http://localhost:8000/acrcloud/analysis/<analysis-id>/pattern-matching/
Simple Report:            http://localhost:8000/acrcloud/analysis/<analysis-id>/
```

### Admin:
```
Django Admin:             http://localhost:8000/admin/
Songs:                    http://localhost:8000/admin/acrcloud/song/
Analyses:                 http://localhost:8000/admin/acrcloud/analysis/
Track Matches:            http://localhost:8000/admin/acrcloud/acrcloudtrackmatch/
Webhook Logs:             http://localhost:8000/admin/acrcloud/webhooklog/
```

## 📸 Screenshot Locations

When taking screenshots for comparison with PDF:

1. **Overview**: Full page showing all matches
2. **Single Match Card**: One complete match with all details
3. **Fingerprint Metrics**: The 4-box grid with scores
4. **Time Offsets**: The time analysis section
5. **Platform Links**: The platform buttons at bottom

## 🎓 Training Tips

### For New Users:
1. Start with a known commercial song
2. Compare results with Spotify/Shazam to verify accuracy
3. Upload the same song twice to see consistency
4. Try different audio formats (MP3, WAV, M4A)
5. Test with different quality levels (128kbps vs 320kbps)

### For Developers:
1. Check Django admin for raw_data structure
2. Use pattern_matching_report.html for debugging
3. Monitor webhook logs for processing issues
4. Review ACRCloud documentation for field meanings
5. Test with mock_service.py for offline development

## 📚 Related Documentation

- `acrcloud_detailed_analysis_enhancement.md` - Full enhancement proposal
- `acrcloud_enhanced_report_implementation.md` - Implementation details
- `acrcloud_pdf_field_mapping.md` - PDF field mapping
- `acrcloud_integration.md` - ACRCloud integration guide
- `acrcloud_setup.md` - Initial setup instructions

## ✅ Success Criteria

You've successfully implemented and tested when:

1. ✅ Can upload and analyze a song
2. ✅ Enhanced report displays all matches
3. ✅ All fingerprint values are visible
4. ✅ Time offsets are formatted correctly
5. ✅ Platform links work (when available)
6. ✅ Color coding makes sense
7. ✅ Layout is responsive
8. ✅ Print functionality works
9. ✅ No console errors
10. ✅ Matches PDF field coverage

## 🆘 Getting Help

If you encounter issues:

1. **Check logs**: `python manage.py runserver` output
2. **Check admin**: Django admin to see raw data
3. **Check webhook logs**: ACRCloud webhook processing
4. **Review docs**: Implementation and mapping docs
5. **Contact support**: Provide song ID and screenshots

## 🎉 Next Steps

After successful testing:

1. Deploy to staging/production environment
2. Train users on new enhanced report
3. Collect feedback on additional features needed
4. Implement export functionality (CSV/JSON)
5. Add visualizations (timeline, charts)
6. Integrate lyrics analysis
7. Add batch analysis features

---

**Last Updated**: October 8, 2025
**Version**: 1.0
**Status**: ✅ Ready for Testing
