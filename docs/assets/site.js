(function(){
  document.querySelectorAll('link[rel~="icon"],link[rel="shortcut icon"],link[rel="apple-touch-icon"],link[rel="mask-icon"]').forEach(function(el){el.remove();});
  const blankIcon=document.createElement('link');
  blankIcon.rel='icon';
  blankIcon.href='data:,';
  document.head.appendChild(blankIcon);

  if(window.__ACX_SITE_SHELL__) return;
  window.__ACX_SITE_SHELL__=true;

  const BASE='/knowledge-library/';
  const preferredLocale=document.documentElement.lang==='hi'?'hi-IN':'en';
  const searchIcon='<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5"></circle><path d="m16 16 4.25 4.25"></path></svg>';
  const nav=[
    ['Solutions','https://allesclinx.com/solutions/'],
    ['ClinXAi','https://allesclinx.com/clinxai/'],
    ['Shop','https://allesclinx.com/shop/'],
    ['Plus','https://allesclinx.com/plus/'],
    ['Support','https://allesclinx.com/support/']
  ];

  function navLinks(){
    return nav.map(([label,href])=>'<a href="'+href+'">'+label+'</a>').join('');
  }

  const header=document.createElement('div');
  header.innerHTML='<header class="acx-site-header"><div class="acx-site-bar">'+
    '<div class="acx-brand-cluster"><a class="acx-wordmark" href="https://allesclinx.com/" aria-label="Alle\'s ClinX main website">Alle\'s ClinX</a><span class="acx-brand-divider" aria-hidden="true"></span><a class="acx-context-link" href="'+BASE+'" aria-label="Alle\'s ClinX Knowledge home">Knowledge</a></div>'+
    '<nav class="acx-primary-nav" aria-label="Primary">'+navLinks()+'</nav>'+
    '<div class="acx-site-actions"><button class="acx-search-button" type="button" aria-label="Search Knowledge">'+searchIcon+'<span class="acx-search-label">Search</span><kbd>⌘K</kbd></button>'+
    '<button class="acx-menu-button" type="button" aria-label="Open menu" aria-expanded="false"><span></span></button></div></div>'+
    '<div class="acx-mobile-drawer" id="acx-mobile-drawer"><div class="acx-mobile-drawer-inner"><div class="acx-mobile-context"><strong>Knowledge</strong><a href="'+BASE+'">Knowledge home</a></div><nav class="acx-mobile-nav" aria-label="Mobile primary">'+navLinks()+'</nav></div></div></header>';
  document.body.insertAdjacentElement('afterbegin',header.firstElementChild);

  const siteHeader=document.querySelector('.acx-site-header');
  function syncHeaderState(){
    siteHeader.classList.toggle('is-scrolled',window.scrollY>10);
  }
  window.addEventListener('scroll',syncHeaderState,{passive:true});
  syncHeaderState();

  const footer=document.createElement('footer');
  footer.className='acx-site-footer';
  footer.innerHTML='<div class="acx-footer-inner"><div class="acx-footer-top">'+
    '<div class="acx-footer-brand"><a class="acx-wordmark" href="https://allesclinx.com/">Alle\'s ClinX</a><p>Institutional hygiene systems, technical knowledge and practical tools for cleaner, safer facility operations.</p></div>'+
    '<div class="acx-footer-col"><strong>Explore</strong><a href="'+BASE+'">Knowledge</a><a href="https://allesclinx.com/shop/">Products</a><a href="https://allesclinx.com/solutions/">Solutions</a></div>'+
    '<div class="acx-footer-col"><strong>Tools</strong><a href="https://allesclinx.com/clinxai/">ClinXAi</a><a href="https://allesclinx.com/metricon/">Metricon</a><a href="https://allesclinx.com/support/media-documents/">Document Center</a></div>'+
    '<div class="acx-footer-col"><strong>Company</strong><a href="https://allesclinx.com/company/">Company</a><a href="https://allesclinx.com/sustainability/">Sustainability</a><a href="https://allesclinx.com/support/contact/">Contact</a></div>'+
    '</div><div class="acx-footer-bottom"><div>© 2026 Alle\'s ClinX. Open Knowledge content is available under CC BY 4.0.</div><span><a href="https://allesclinx.com/privacy-legal/">Privacy & Legal</a> · <a href="https://allesclinx.com/terms-conditions/">Terms</a></span></div></div>';
  document.body.appendChild(footer);

  const dialog=document.createElement('div');
  dialog.className='acx-search-dialog';
  dialog.setAttribute('role','dialog');
  dialog.setAttribute('aria-modal','true');
  dialog.setAttribute('aria-label','Search Alle\'s ClinX Knowledge');
  dialog.innerHTML='<div class="acx-search-panel">'+
    '<div class="acx-search-top">'+searchIcon+
      '<input class="acx-search-input" type="search" autocomplete="off" autocapitalize="none" spellcheck="false" placeholder="Search cleaning, deep cleaning, schedules…" aria-label="Search live Knowledge guides" aria-controls="acx-search-results">'+
      '<button class="acx-search-close" type="button" aria-label="Close search">×</button>'+
    '</div>'+
    '<div class="acx-search-status"><span class="acx-search-status-label">Search all live Knowledge guides</span><span class="acx-search-keys"><kbd>↑</kbd><kbd>↓</kbd> navigate <kbd>Enter</kbd> open</span></div>'+
    '<div class="acx-search-results" id="acx-search-results" role="listbox" aria-label="Search results"><div class="acx-search-empty">Loading Knowledge index…</div></div>'+
    '<div class="acx-search-hint"><span>Tip: search by topic, title, category, or article ID.</span><span class="acx-search-count"></span></div>'+
  '</div>';
  document.body.appendChild(dialog);

  const menuBtn=document.querySelector('.acx-menu-button');
  const drawer=document.getElementById('acx-mobile-drawer');
  const searchBtns=[...document.querySelectorAll('.acx-search-button')];
  const closeBtn=dialog.querySelector('.acx-search-close');
  const input=dialog.querySelector('.acx-search-input');
  const results=dialog.querySelector('.acx-search-results');
  const statusLabel=dialog.querySelector('.acx-search-status-label');
  const countLabel=dialog.querySelector('.acx-search-count');
  let records=null;
  let activeIndex=-1;
  let visibleResults=[];

  function setMenu(open){
    menuBtn.setAttribute('aria-expanded',open?'true':'false');
    menuBtn.setAttribute('aria-label',open?'Close menu':'Open menu');
    drawer.classList.toggle('is-open',open);
    document.body.classList.toggle('acx-menu-open',open);
  }
  menuBtn.addEventListener('click',()=>setMenu(menuBtn.getAttribute('aria-expanded')!=='true'));

  function esc(value){
    return String(value||'').replace(/[&<>"']/g,function(m){
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m];
    });
  }

  function normalize(value){
    return String(value||'')
      .normalize('NFD').replace(/[\u0300-\u036f]/g,'')
      .toLowerCase()
      .replace(/sanitizing/g,'sanitising')
      .replace(/sanitize/g,'sanitise')
      .replace(/[^\p{L}\p{N}]+/gu,' ')
      .trim();
  }

  function queryTokens(value){
    return normalize(value).split(/\s+/).filter(Boolean);
  }

  function editDistance(a,b){
    if(a===b) return 0;
    if(!a.length) return b.length;
    if(!b.length) return a.length;
    const row=Array.from({length:b.length+1},(_,i)=>i);
    for(let i=1;i<=a.length;i++){
      let prev=row[0];
      row[0]=i;
      for(let j=1;j<=b.length;j++){
        const old=row[j];
        row[j]=Math.min(row[j]+1,row[j-1]+1,prev+(a[i-1]===b[j-1]?0:1));
        prev=old;
      }
    }
    return row[b.length];
  }

  function tokenMatches(token,field){
    if(!token||!field) return false;
    if(field.includes(token)) return true;
    if(token.length<4) return false;
    const maxDistance=token.length>=8?2:1;
    return field.split(' ').some(function(word){
      return Math.abs(word.length-token.length)<=maxDistance && editDistance(token,word)<=maxDistance;
    });
  }

  function scoreRecord(record,rawQuery){
    const q=normalize(rawQuery);
    const tokens=queryTokens(rawQuery);
    if(!q||!tokens.length) return 0;

    const title=normalize(record.title);
    const category=normalize(record.category);
    const subcategory=normalize(record.subcategory);
    const excerpt=normalize(record.excerpt);
    const id=normalize(record.article_id);
    const all=[title,subcategory,category,excerpt,id].join(' ');
    let score=0;

    if(id===q) score+=220;
    if(title===q) score+=180;
    if(title.startsWith(q)) score+=115;
    if(title.includes(q)) score+=90;
    if(subcategory===q) score+=65;
    if(subcategory.includes(q)) score+=34;
    if(category.includes(q)) score+=18;
    if(excerpt.includes(q)) score+=14;
    if(record.locale===preferredLocale) score+=12;

    let matched=0;
    tokens.forEach(function(token){
      if(tokenMatches(token,title)){score+=32;matched++;return;}
      if(tokenMatches(token,subcategory)){score+=18;matched++;return;}
      if(tokenMatches(token,category)){score+=10;matched++;return;}
      if(tokenMatches(token,id)){score+=24;matched++;return;}
      if(tokenMatches(token,excerpt)){score+=6;matched++;}
    });

    if(matched===tokens.length) score+=28;
    if(!all.includes(q) && matched===0) return 0;
    return score;
  }

  function highlight(value,rawQuery){
    const source=esc(value);
    const terms=String(rawQuery||'').trim().split(/\s+/).filter(function(x){return x.length>1;});
    if(!terms.length) return source;
    const pattern=terms.map(function(term){
      return term.replace(/[.*+?^$()|[\]\\{}]/g,'\\$&');
    }).join('|');
    if(!pattern) return source;
    return source.replace(new RegExp('('+pattern+')','ig'),'<mark>$1</mark>');
  }

  function resultUrl(record){
    let path=String(record.url||'').replace(/^\/+/, '');
    path=path.replace(/^knowledge-library\//,'');
    return BASE+path;
  }

  async function loadRecords(){
    if(records) return records;
    statusLabel.textContent='Loading Knowledge index…';
    try{
      const response=await fetch(BASE+'assets/live-search.json',{cache:'no-store'});
      if(!response.ok) throw new Error('Search index unavailable');
      const data=await response.json();
      records=(data.records||[]).map(function(record,index){return Object.assign({_order:index},record);});
      const articleCount=new Set(records.map(function(record){return record.article_id;})).size;
      countLabel.textContent=articleCount+' live guides · English + हिन्दी';
      statusLabel.textContent='Search all live Knowledge guides';
    }catch(error){
      records=[];
      countLabel.textContent='';
      statusLabel.textContent='Search temporarily unavailable';
    }
    return records;
  }

  function renderResult(record,index,query){
    return '<a class="acx-search-result" id="acx-search-result-'+index+'" role="option" aria-selected="false" data-index="'+index+'" href="'+esc(resultUrl(record))+'">'+
      '<span class="acx-search-result-main"><strong>'+highlight(record.title,query)+'</strong>'+
      '<span class="acx-search-result-meta">'+esc(record.subcategory)+' <b>·</b> '+esc(record.article_id)+' <b>·</b> '+(record.locale==='hi-IN'?'हिन्दी':'English')+'</span>'+
      (record.excerpt?'<span class="acx-search-result-excerpt">'+highlight(record.excerpt,query)+'</span>':'')+
      '</span><span class="acx-search-result-arrow" aria-hidden="true">→</span></a>';
  }

  function defaultResults(){
    if(!records||!records.length){
      results.innerHTML='<div class="acx-search-empty">Search index is temporarily unavailable.</div>';
      visibleResults=[];
      return;
    }
    const preferred=records.filter(function(record){return record.locale===preferredLocale;});
    visibleResults=(preferred.length?preferred:records).slice(-6).reverse();
    statusLabel.textContent='Recently published';
    results.innerHTML=visibleResults.map(function(record,index){
      return renderResult(record,index,'');
    }).join('');
    activeIndex=-1;
  }

  function setActive(index){
    const items=[...results.querySelectorAll('.acx-search-result')];
    if(!items.length){activeIndex=-1;input.removeAttribute('aria-activedescendant');return;}
    activeIndex=Math.max(0,Math.min(index,items.length-1));
    items.forEach(function(item,i){
      const active=i===activeIndex;
      item.classList.toggle('is-active',active);
      item.setAttribute('aria-selected',active?'true':'false');
      if(active){
        input.setAttribute('aria-activedescendant',item.id);
        item.scrollIntoView({block:'nearest'});
      }
    });
  }

  function renderSearch(){
    const raw=input.value.trim();
    if(!raw){
      defaultResults();
      return;
    }

    const ranked=(records||[])
      .map(function(record){return {record:record,score:scoreRecord(record,raw)};})
      .filter(function(item){return item.score>0;})
      .sort(function(a,b){return b.score-a.score || a.record._order-b.record._order;})
      .slice(0,10)
      .map(function(item){return item.record;});

    visibleResults=ranked;
    activeIndex=-1;
    input.removeAttribute('aria-activedescendant');
    statusLabel.textContent=ranked.length?(ranked.length+' best match'+(ranked.length===1?'':'es')):'No matches';

    if(!ranked.length){
      results.innerHTML='<div class="acx-search-empty"><strong>No matching guide found.</strong><span>Try fewer words, a broader topic, or an article ID such as ACX-KB-0011.</span></div>';
      return;
    }

    results.innerHTML=ranked.map(function(record,index){
      return renderResult(record,index,raw);
    }).join('');
  }

  async function openSearch(){
    setMenu(false);
    dialog.classList.add('is-open');
    document.body.classList.add('acx-search-open');
    input.value='';
    results.innerHTML='<div class="acx-search-empty">Loading Knowledge index…</div>';
    await loadRecords();
    renderSearch();
    requestAnimationFrame(function(){input.focus();});
  }

  function closeSearch(){
    dialog.classList.remove('is-open');
    document.body.classList.remove('acx-search-open');
    activeIndex=-1;
    input.removeAttribute('aria-activedescendant');
  }

  searchBtns.forEach(function(button){button.addEventListener('click',openSearch);});
  closeBtn.addEventListener('click',closeSearch);
  dialog.addEventListener('pointerdown',function(event){if(event.target===dialog)closeSearch();});
  input.addEventListener('input',renderSearch);
  input.addEventListener('keydown',function(event){
    const items=[...results.querySelectorAll('.acx-search-result')];
    if(event.key==='ArrowDown'&&items.length){
      event.preventDefault();
      setActive(activeIndex<0?0:(activeIndex+1)%items.length);
    }else if(event.key==='ArrowUp'&&items.length){
      event.preventDefault();
      setActive(activeIndex<0?items.length-1:(activeIndex-1+items.length)%items.length);
    }else if(event.key==='Enter'&&activeIndex>=0&&items[activeIndex]){
      event.preventDefault();
      items[activeIndex].click();
    }
  });
  results.addEventListener('mousemove',function(event){
    const item=event.target.closest('.acx-search-result');
    if(!item) return;
    setActive(Number(item.dataset.index));
  });

  document.addEventListener('keydown',function(event){
    if((event.metaKey||event.ctrlKey)&&event.key.toLowerCase()==='k'){
      event.preventDefault();
      dialog.classList.contains('is-open')?closeSearch():openSearch();
    }
    if(event.key==='Escape'){
      if(dialog.classList.contains('is-open')) closeSearch();
      else setMenu(false);
    }
  });
})();
