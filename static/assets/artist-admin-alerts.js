/* Artist Admin Alerts - mirror of track admin behavior */

function showArtistAlert(message, type) {
  const existing = document.querySelectorAll('.alert');
  existing.forEach(a => a.remove());
  const cls = type === 'error' ? 'alert-danger' : type === 'success' ? 'alert-success' : type === 'warning' ? 'alert-warning' : 'alert-info';
  const html = '<div class="alert ' + cls + ' alert-dismissible">' +
    '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">×</button>' +
    message +
    '</div>';
  const content = document.querySelector('#content');
  if (content) content.insertAdjacentHTML('afterbegin', html);
  setTimeout(() => {
    const a = document.querySelector('.alert');
    if (a) a.remove();
  }, 5000);
}

async function postJson(url, body) {
  // get CSRF token
  let csrf = null;
  const inpt = document.querySelector('[name=csrfmiddlewaretoken]');
  if (inpt) csrf = inpt.value;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
    body: body ? JSON.stringify(body) : null
  });
  if (!res.ok) throw new Error('HTTP ' + res.status);
  return await res.json();
}

function getArtistIdFromPath() {
  const m = window.location.pathname.match(/\/artist\/(\d+)\//);
  return m ? m[1] : null;
}

function fetchArtistMetadata(btn) {
  const id = getArtistIdFromPath();
  if (!id) { showArtistAlert('Could not determine artist ID from URL', 'error'); return; }
  const orig = btn.value; btn.value = 'Fetching...'; btn.disabled = true;
  postJson(`/admin/soundcharts/artist/${id}/fetch-metadata/`)
    .then(data => {
      if (data.success) {
        showArtistAlert(data.message, 'success');
        setTimeout(() => location.reload(), 800);
      } else {
        showArtistAlert(data.error || 'Failed to fetch metadata', 'error');
        btn.value = orig; btn.disabled = false;
      }
    })
    .catch(e => { showArtistAlert('Error: ' + e.message, 'error'); btn.value = orig; btn.disabled = false; });
}

function fetchArtistAudienceDefaults(btn) {
  const id = getArtistIdFromPath();
  if (!id) { showArtistAlert('Could not determine artist ID from URL', 'error'); return; }
  const orig = btn.value; btn.value = 'Fetching...'; btn.disabled = true;
  const platforms = ['spotify','youtube','tiktok','airplay','shazam'];
  let ok = 0, fail = 0, details = [];
  const run = platforms.reduce((p, plat) => p.then(() =>
    postJson(`/admin/soundcharts/artist/${id}/fetch-audience/`, { platform: plat })
      .then(d => { if (d.success) { ok++; details.push(`${plat}: OK`); } else { fail++; details.push(`${plat}: FAIL`); } })
      .catch(() => { fail++; details.push(`${plat}: ERROR`); })
  ), Promise.resolve());
  run.then(() => {
    const summary = `Fetched audience: ${ok} ok, ${fail} failed. ${details.join('; ')}`;
    showArtistAlert(summary, ok ? 'success' : 'warning');
    setTimeout(() => location.reload(), 1000);
  }).catch(() => {
    showArtistAlert('Unexpected error during audience fetch', 'error');
    btn.value = orig; btn.disabled = false;
  });
}

function fetchArtistAudienceSelected(btn) {
  const id = getArtistIdFromPath();
  if (!id) { showArtistAlert('Could not determine artist ID from URL', 'error'); return; }
  const plat = document.getElementById('platform_select')?.value || 'spotify';
  const orig = btn.value; btn.value = 'Fetching...'; btn.disabled = true;
  postJson(`/admin/soundcharts/artist/${id}/fetch-audience/`, { platform: plat })
    .then(d => {
      if (d.success) { showArtistAlert(d.message || `Fetched audience for ${plat}`, 'success'); setTimeout(() => location.reload(), 800); }
      else { showArtistAlert(d.error || `Failed to fetch audience for ${plat}`, 'error'); btn.value = orig; btn.disabled = false; }
    }).catch(e => { showArtistAlert('Error: ' + e.message, 'error'); btn.value = orig; btn.disabled = false; });
}

document.addEventListener('DOMContentLoaded', function(){
  const metaBtn = document.querySelector('input[name="_fetch_metadata"]');
  if (metaBtn) metaBtn.addEventListener('click', function(e){ e.preventDefault(); fetchArtistMetadata(this); });
  const audBtn = document.querySelector('input[name="_fetch_audience"]');
  if (audBtn) audBtn.addEventListener('click', function(e){ e.preventDefault(); fetchArtistAudienceDefaults(this); });
  const audSelBtn = document.querySelector('input[name="_fetch_audience_selected"]');
  if (audSelBtn) audSelBtn.addEventListener('click', function(e){ e.preventDefault(); fetchArtistAudienceSelected(this); });
});


