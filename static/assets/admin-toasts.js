(function(){
  function ensureContainer(){
    var c = document.getElementById('toast-container');
    if (!c){
      c = document.createElement('div');
      c.id = 'toast-container';
      document.body.appendChild(c);
    }
    return c;
  }
  function levelClass(tags){
    if (!tags) return 'toast-info';
    if (tags.indexOf('error') !== -1) return 'toast-error';
    if (tags.indexOf('warning') !== -1) return 'toast-warning';
    if (tags.indexOf('success') !== -1) return 'toast-success';
    if (tags.indexOf('info') !== -1) return 'toast-info';
    return 'toast-info';
  }
  function titleFor(cls){
    if (cls === 'toast-error') return 'Error';
    if (cls === 'toast-warning') return 'Warning';
    if (cls === 'toast-success') return 'Success';
    return 'Info';
  }
  function showToast(levelTags, text){
    var container = ensureContainer();
    var cls = levelClass(levelTags);
    var el = document.createElement('div');
    el.className = 'toast ' + cls;
    var strong = document.createElement('span');
    strong.className = 'title';
    strong.textContent = titleFor(cls);
    var span = document.createElement('span');
    span.textContent = ' ' + text;
    var close = document.createElement('button');
    close.className = 'close-btn';
    close.innerHTML = '&times;';
    close.onclick = function(){ if (el.parentNode) el.parentNode.removeChild(el); };
    el.appendChild(strong);
    el.appendChild(span);
    el.appendChild(close);
    container.appendChild(el);
    setTimeout(function(){ if (el.parentNode) el.parentNode.removeChild(el); }, 7000);
  }

  function collectAdminMessages(){
    var msgs = [];
    var list = document.querySelectorAll('.messagelist li');
    if (list && list.length){
      list.forEach(function(li){
        var tags = li.className || '';
        // Get visible text
        var text = li.textContent || '';
        text = text.replace(/\s+/g, ' ').trim();
        if (text){ msgs.push({tags: tags, text: text}); }
      });
      // Hide original list to avoid clutter
      var container = document.querySelector('.messagelist');
      if (container) container.style.display = 'none';
    }
    return msgs;
  }

  function init(){
    try {
      var msgs = collectAdminMessages();
      if (msgs && msgs.length){
        msgs.forEach(function(m){ showToast(m.tags, m.text); });
      }
    } catch (e){ /* no-op */ }
  }

  if (document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();


