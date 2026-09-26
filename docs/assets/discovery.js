(function(){const s=document.createElement('script');s.src='/knowledge-library/assets/site.js';s.defer=true;document.head.appendChild(s);})();
(function(){
  const input=document.querySelector('[data-filter-input]');
  const rows=[...document.querySelectorAll('[data-filter-row]')];
  const empty=document.querySelector('[data-empty]');
  if(input){
    input.addEventListener('input',()=>{
      const q=input.value.trim().toLowerCase();
      let shown=0;
      rows.forEach(row=>{
        const hay=(row.textContent+' '+(row.dataset.search||'')).toLowerCase();
        const match=!q||hay.includes(q);
        row.hidden=!match;
        if(match) shown++;
      });
      if(empty) empty.classList.toggle('show',shown===0);
    });
  }
  const liveRows=[...document.querySelectorAll('[data-article-id]')];
  if(liveRows.length){
    fetch('/knowledge-library/assets/live-search.json',{cache:'no-store'})
      .then(r=>r.ok?r.json():Promise.reject())
      .then(data=>{
        const live=new Set((data.records||[]).map(record=>record.article_id));
        liveRows.forEach(row=>{
          const isLive=live.has(row.dataset.articleId);
          row.classList.toggle('is-planned',!isLive);
          if(isLive) row.removeAttribute('aria-disabled');
          else row.setAttribute('aria-disabled','true');
        });
      }).catch(()=>{});
  }
})();