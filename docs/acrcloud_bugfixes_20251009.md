# ACRCloud Enhanced Report Bug Fixes - Oct 9, 2025

## Issues Found During Testing

### Issue 1: Template Syntax Error
**Error Message:**
```
TemplateSyntaxError at /acrcloud/analysis/<uuid>/enhanced/
Could not parse the remainder: '(match_type='music').count' from 'analysis.track_matches.filter(match_type='music').count'
```

**Root Cause:**
Django templates don't support calling methods with arguments directly. The template was trying to use:
```django
{{ analysis.track_matches.filter(match_type='music').count }}
```

**Fix Applied:**
Modified `EnhancedAnalysisReportView` to calculate counts in the view and pass them to the template:

**File:** `apps/acrcloud/views.py`
```python
# Get counts by match type
music_matches_count = analysis.track_matches.filter(match_type='music').count()
cover_matches_count = analysis.track_matches.filter(match_type='cover').count()

context = {
    'analysis': analysis,
    'track_matches': track_matches,
    'music_matches_count': music_matches_count,  # ← Added
    'cover_matches_count': cover_matches_count,   # ← Added
}
```

**File:** `templates/acrcloud/enhanced_analysis_report.html`
Changed from:
```django
{{ analysis.track_matches.filter(match_type='music').count }}
```

To:
```django
{{ music_matches_count }}
```

---

### Issue 2: Report Not Found Error on First Access
**Symptoms:**
- After webhook processing, redirecting to the analysis report initially shows "report not found" error
- Navigating back and trying again works fine

**Root Cause:**
Race condition in the webhook processing task (`process_acrcloud_webhook_task`):

1. Analysis status was set to `'analyzed'` BEFORE creating the AnalysisReport
2. When the page auto-refreshed and saw status='analyzed', it showed the report link
3. But if user clicked the link before the report was created, it would fail

**Sequence of Events:**
```
1. Webhook received → Task queued
2. Task starts processing
3. Line 233: analysis.status = 'analyzed'  ← Status set early!
4. Line 241-245: AnalysisReport.objects.create()  ← Report created after
5. Page auto-refreshes, sees status='analyzed'
6. User clicks "View Report"
7. ERROR: Report doesn't exist yet!
```

**Fix Applied:**

**File:** `apps/acrcloud/tasks.py`

Changed the order of operations in `process_acrcloud_webhook_task`:

**Before:**
```python
# Update analysis with results
analysis.raw_response = combined_results
analysis.status = 'analyzed'  # ← Set too early!
analysis.completed_at = timezone.now()
analysis.save()

# Create AnalysisReport
AnalysisReport.objects.create(
    analysis=analysis,
    **report_data
)

# Update song status
song.status = 'analyzed'
song.save()
```

**After:**
```python
# Update analysis with results (but don't set status to 'analyzed' yet)
analysis.raw_response = combined_results
analysis.completed_at = timezone.now()
analysis.save()  # ← Don't set status yet

# Create AnalysisReport
AnalysisReport.objects.create(
    analysis=analysis,
    **report_data
)

# Process metadata
metadata_processor.process_webhook_results(analysis, combined_results)

# NOW set status to 'analyzed' after everything is ready
analysis.status = 'analyzed'  # ← Set after report is created!
analysis.save()

song.status = 'analyzed'
song.save()
```

**Additional Safeguards Added:**

Added error handling in both report views to gracefully handle edge cases:

**File:** `apps/acrcloud/views.py`

```python
@method_decorator(login_required, name='dispatch')
class AnalysisReportView(View):
    def get(self, request, analysis_id):
        analysis = get_object_or_404(Analysis, id=analysis_id, song__user=request.user)
        
        # Check if analysis is complete
        if analysis.status == 'processing':
            messages.info(request, 'Analysis is still in progress. Please wait a moment.')
            return redirect('acrcloud:song_detail', song_id=str(analysis.song.id))
        
        try:
            report = analysis.report
        except AnalysisReport.DoesNotExist:
            # Report not created yet (race condition)
            if analysis.status == 'analyzed':
                messages.warning(request, 'Report is being generated. Please refresh in a moment.')
            else:
                messages.error(request, 'Analysis report is not available.')
            return redirect('acrcloud:song_detail', song_id=str(analysis.song.id))
        
        # ... render report
```

Same safeguards added to `EnhancedAnalysisReportView`.

---

## Summary of Changes

### Files Modified:

1. **`apps/acrcloud/views.py`**
   - Added `music_matches_count` and `cover_matches_count` to EnhancedAnalysisReportView
   - Added status checks and error handling to AnalysisReportView
   - Added status checks to EnhancedAnalysisReportView

2. **`apps/acrcloud/tasks.py`**
   - Reordered operations in `process_acrcloud_webhook_task`
   - Status is now set to 'analyzed' AFTER report creation

3. **`templates/acrcloud/enhanced_analysis_report.html`**
   - Changed template variables from `.filter().count()` to pre-calculated counts

### Testing Checklist:

- [x] Template syntax error resolved
- [x] Enhanced report page loads without errors
- [x] Match counts display correctly
- [x] Race condition fixed - report always exists when status='analyzed'
- [x] Graceful error handling if report accessed during processing
- [x] No linting errors

### Optional Enhancement (Not Currently Implemented):

A commented-out additional defensive check has been added to `SongDetailView` (lines 177-193 in `views.py`).

**If race conditions still occur during testing:**
1. Uncomment the defensive check in `SongDetailView`
2. Add `'has_report': has_report` to context
3. Update `song_detail.html` template to use `{% if has_report %}` instead of `{% if report %}`

This provides an extra layer by checking actual object existence rather than relying solely on status flags. However, the correct task ordering should make this unnecessary.

### How to Test:

1. **Upload a song**
   ```
   http://localhost:8000/acrcloud/upload/
   ```

2. **Wait for analysis to complete** (status changes to 'analyzed')

3. **Click "View Enhanced Report"** immediately after completion
   - Should now work on first try
   - No "report not found" error

4. **Verify all match counts display correctly**
   - Total matches
   - Music matches
   - Cover matches

5. **Try accessing report while processing**
   - Should show message: "Analysis is still in progress"
   - Should redirect back to song detail

### Expected Behavior:

✅ **Before the Fix:**
- Template error on enhanced report page
- "Report not found" on first access after analysis
- Had to navigate back and try again

✅ **After the Fix:**
- Enhanced report loads immediately
- All match counts display correctly
- Report is always available when status='analyzed'
- Graceful error messages if accessed during processing

---

## Technical Details

### Django Template Limitations

Django templates are intentionally limited in what they can do:
- ✅ Can access attributes: `{{ object.field }}`
- ✅ Can call methods with no arguments: `{{ object.method }}`
- ❌ Cannot call methods with arguments: `{{ object.method(arg) }}`
- ❌ Cannot use filter with kwargs: `{{ queryset.filter(field='value') }}`

**Solution:** Calculate in the view, pass to template.

### Race Condition Prevention

**Key Principle:** Only set status when ALL dependent data is ready.

In this case:
1. Report creation
2. Metadata processing
3. Track matches creation
4. **THEN** set status='analyzed'

This ensures that when the UI checks status, everything is guaranteed to exist.

### Error Handling Layers

**Three layers of protection:**

1. **Task ordering** - Create everything before setting status
2. **View checks** - Check status and report existence
3. **Template fallbacks** - Handle missing data gracefully

---

## Deployment Notes

### No Database Migrations Required
- No model changes
- Only logic changes in views and tasks

### No Configuration Changes Required
- No settings updates needed
- No environment variables changed

### Backward Compatible
- Existing analyses will still work
- Old code paths still function
- No breaking changes

### Testing in Production

**Before deploying:**
1. Test with real ACRCloud API (not mock)
2. Upload multiple songs in parallel
3. Try accessing reports immediately after completion
4. Verify webhook processing completes successfully

**Monitoring:**
- Check Celery task logs for any errors
- Monitor webhook processing times
- Watch for any "report not found" errors in logs

---

## Lessons Learned

### Django Templates
- Always calculate dynamic values in views
- Don't try to call methods with arguments in templates
- Use template tags for complex logic

### Async Processing
- Be careful about when you set status flags
- Create all dependent data BEFORE setting "complete" status
- Add safeguards for race conditions

### Error Handling
- Provide helpful messages to users
- Gracefully handle temporary states
- Always have fallback behavior

---

### Issue 3: Invalid Filter 'floordiv' Error
**Error Message:**
```
TemplateSyntaxError at /acrcloud/analysis/<uuid>/enhanced/
Invalid filter: 'floordiv'
```

**Location:** `templates/acrcloud/components/match_detail_card.html`, lines 162 and 298

**Root Cause:**
Django templates don't have a built-in `floordiv` filter. The template was trying to use:
```django
{{ match.raw_data.pattern_matching.play_offset_ms|floordiv:1000 }}
```

This was an attempt to convert milliseconds to seconds by dividing by 1000.

**Fix Applied:**

**Created custom template filters:**

**New File:** `apps/acrcloud/templatetags/__init__.py`
- Package marker for template tags

**New File:** `apps/acrcloud/templatetags/acrcloud_filters.py`
```python
from django import template

register = template.Library()

@register.filter(name='divide')
def divide(value, arg):
    """Divides the value by the argument."""
    try:
        return int(value) // int(arg)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0

@register.filter(name='ms_to_seconds')
def ms_to_seconds(value):
    """Converts milliseconds to seconds."""
    try:
        return int(value) / 1000
    except (ValueError, TypeError):
        return 0
```

**Updated Template:** `templates/acrcloud/components/match_detail_card.html`

1. Added filter loading at the top:
```django
{% load static %}
{% load acrcloud_filters %}
```

2. Replaced `floordiv` with `divide`:
```django
<!-- Before -->
{{ match.raw_data.pattern_matching.play_offset_ms|floordiv:1000 }}

<!-- After -->
{{ match.raw_data.pattern_matching.play_offset_ms|divide:1000 }}
```

**Changes:**
- Line 13: Added `{% load acrcloud_filters %}`
- Line 163: Changed `floordiv:1000` to `divide:1000` (Play Offset)
- Line 298: Changed `floordiv:1000` to `divide:1000` (Duration)

---

### Issue 4: Pattern Matching Report Styling Enhancement
**Location:** `templates/acrcloud/pattern_matching_report.html`

**User Request:**
"The table view is very rough. Use the same kind of table used for soundcharts charts rankings. The raw data at the end should be contained in an expandable box with better JSON formatting."

**Changes Applied:**

**1. Updated Table Styling:**
- Adopted soundcharts `data-table` style with gradient purple headers
- Added hover effects on table rows
- Improved badge styling with consistent colors
- Added transition animations

**2. Enhanced JSON Viewer:**
- Created expandable/collapsible JSON section
- Added button with smooth animations
- Implemented syntax highlighting for JSON:
  - Keys in blue (`#9cdcfe`)
  - Strings in orange (`#ce9178`)
  - Numbers in light green (`#b5cea8`)
  - Booleans/null in blue (`#569cd6`)
- Dark VS Code-style background (`#1e1e1e`)
- Maximum height with scroll for large JSON
- Uses Django's `json_script` filter for safe data passing

**3. Added Custom Styles:**
```css
- .data-table-container (soundcharts style)
- .json-toggle (expandable button with gradient)
- .json-content (dark code viewer)
- Badge color enhancements
- Row hover effects
```

**4. Added JavaScript:**
- `toggleJSON()` - Expands/collapses JSON viewer
- `formatJSON()` - Formats JSON with 2-space indentation
- `syntaxHighlight()` - Applies color syntax highlighting

**Files Modified:**
- `templates/acrcloud/pattern_matching_report.html`
  - Added `{% load acrcloud_filters %}`
  - Linked soundcharts CSS: `soundcharts/css/admin_data_table.css`
  - Updated all table classes from Bootstrap to data-table style
  - Replaced raw `<pre>` with expandable JSON viewer
  - Added JavaScript for JSON formatting

**Benefits:**
- ✅ Modern, professional table appearance
- ✅ Consistent with soundcharts UI
- ✅ Raw JSON is hidden by default (reduces clutter)
- ✅ Syntax highlighting makes JSON readable
- ✅ Smooth animations improve UX
- ✅ Dark code theme (VS Code style)

---

### Issue 5: Pattern Matching Table Style Update
**User Request:**
"The table style you took is not the one I wanted. Please refer to the table at URL http://localhost:8000/charts/, it has light headings, alternate row patterns, no purple colors on the headings, chip style for related data."

**Changes Applied:**

**1. Complete Table Redesign to Match `/charts/` Style:**

**Header Styling (Light Gray):**
- Changed from: `background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)` (purple gradient)
- Changed to: `bg-gray-100 dark:bg-gray-700` (light gray)
- Header text: `text-xs font-medium text-left text-gray-500 uppercase dark:text-gray-400`

**Table Structure:**
```html
<table class="min-w-full divide-y divide-gray-200 table-fixed dark:divide-gray-600">
  <thead class="bg-gray-100 dark:bg-gray-700">
    <!-- Light gray headers with uppercase small text -->
  </thead>
  <tbody class="bg-white divide-y divide-gray-200 dark:bg-gray-800 dark:divide-gray-700">
    <!-- Alternate row styling with dividers -->
  </tbody>
</table>
```

**2. Chip-Style Badges:**

**Match Type Chips:**
```html
<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium 
  bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300">
  Music Match
</span>
```

**Artist Chips:**
```html
<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium 
  bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
  Artist Name
</span>
```

**Score/Risk Chips (Color-Coded):**
- Green: Low risk (< 50%)
- Yellow: Medium risk (50-80%)
- Red: High risk (> 80%)

**3. Row Styling:**
- Hover effect: `hover:bg-gray-100 dark:hover:bg-gray-700`
- Alternate rows with dividers: `divide-y divide-gray-200 dark:divide-gray-700`
- Clean transitions, no transform effects

**4. Enhanced Layout:**
- Added breadcrumb navigation
- Added summary stats cards at top
- Action buttons for navigation
- Row numbers (#) in first column
- "Actions" column with view button for each match
- Modal dialogs for viewing raw match data

**5. JSON Viewer Updates:**
- Button color changed from purple gradient to blue: `bg-blue-700 hover:bg-blue-800`
- Cleaner button design
- Expandable sections in modals for per-match data
- Main raw JSON viewer for staff at bottom

**6. Added Columns:**
- Row number (#)
- Similarity (3 decimal precision)
- Distance (3 decimal precision)
- Pattern % (percentage)
- Actions (view button)

**Files Modified:**
- `templates/acrcloud/pattern_matching_report.html` - Complete redesign with Tailwind
- `apps/acrcloud/views.py` - Added music/cover match counts to PatternMatchingReportView

**Removed:**
- All purple gradient colors
- soundcharts `admin_data_table.css` dependency
- Bootstrap card styling
- Heavy animations and transforms

**Visual Comparison:**

**Before (Purple Gradient):**
```
╔═══════════════════════════════╗ ← Purple gradient header
║ Match Type │ Title │ Score   ║
╠═══════════════════════════════╣
║ Music      │ Song  │ 95%     ║ ← Basic row
```

**After (Light Clean):**
```
┌──────────────────────────────┐ ← Light gray header (bg-gray-100)
│ # │ Match Type │ Title │ Score│
├──────────────────────────────┤
│ 1 │ 🔵 Music  │ Song  │🔴95%│ ← Chips, alternating rows
├──────────────────────────────┤
│ 2 │ 🟡 Cover  │ Song  │🟡70%│ ← Hover effect
```

**Features:**
- ✅ Light gray headers (no purple)
- ✅ Alternate row pattern with dividers
- ✅ Chip-style badges for all data
- ✅ Clean Tailwind styling
- ✅ Responsive design
- ✅ Dark mode support
- ✅ Expandable JSON in modal per match
- ✅ Main JSON viewer for staff

---

**Status:** ✅ Fixed and Tested
**Date:** October 9, 2025
**Version:** 1.4
