(function(){
  document.querySelectorAll('link[rel~="icon"],link[rel="shortcut icon"],link[rel="apple-touch-icon"],link[rel="mask-icon"]').forEach(function(el){el.remove();});
  const siteIcon=document.createElement('link');
  siteIcon.rel='icon';
  siteIcon.type='image/png';
  siteIcon.href='/knowledge-library/assets/favicon.png?v=20260927-3';
  document.head.appendChild(siteIcon);

  const shortcutIcon=document.createElement('link');
  shortcutIcon.rel='shortcut icon';
  shortcutIcon.href='/knowledge-library/assets/favicon.png?v=20260927-3';
  document.head.appendChild(shortcutIcon);

  if(window.__ACX_SITE_SHELL__) return;
  window.__ACX_SITE_SHELL__=true;

  const BASE='/knowledge-library/';

  function ensurePwaHead(){
    if(!document.querySelector('link[rel="manifest"]')){
      const manifest=document.createElement('link');
      manifest.rel='manifest';
      manifest.href=BASE+'manifest.webmanifest';
      document.head.appendChild(manifest);
    }
    if(!document.querySelector('link[rel="apple-touch-icon"]')){
      const touchIcon=document.createElement('link');
      touchIcon.rel='apple-touch-icon';
      touchIcon.href=BASE+'assets/favicon.png?v=20260927-3';
      document.head.appendChild(touchIcon);
    }
    [
      ['theme-color','#ffffff'],
      ['mobile-web-app-capable','yes'],
      ['apple-mobile-web-app-capable','yes'],
      ['apple-mobile-web-app-status-bar-style','default'],
      ['apple-mobile-web-app-title',"ClinX Knowledge"]
    ].forEach(function(pair){
      if(document.querySelector('meta[name="'+pair[0]+'"]')) return;
      const meta=document.createElement('meta');
      meta.name=pair[0];
      meta.content=pair[1];
      document.head.appendChild(meta);
    });
  }
  ensurePwaHead();

  const pwaStyle=document.createElement('style');
  pwaStyle.textContent=[
    '.acx-install-app{height:36px;padding:0 12px;border:1px solid #dedee1;border-radius:8px;background:#fff;color:#111;font:600 13px/1 -apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;cursor:pointer;white-space:nowrap}',
    '.acx-install-app:hover,.acx-install-app:focus-visible{border-color:#bcbcc1;background:#fafafa;outline:0}',
    '.acx-install-app[hidden],.acx-pwa-status[hidden]{display:none!important}',
    '.acx-pwa-status{position:fixed;left:50%;bottom:max(18px,env(safe-area-inset-bottom));z-index:9999;transform:translateX(-50%);max-width:calc(100% - 32px);padding:9px 12px;border:1px solid #dedee1;border-radius:999px;background:rgba(255,255,255,.96);color:#303034;font:600 12px/1.25 -apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;box-shadow:0 5px 22px rgba(0,0,0,.08);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px)}',
    '@media(max-width:640px){.acx-install-app{height:34px;padding:0 9px;font-size:12px}.acx-pwa-status{bottom:max(12px,env(safe-area-inset-bottom))}}'
  ].join('');
  document.head.appendChild(pwaStyle);

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
    '<div class="acx-brand-cluster"><a class="acx-wordmark" href="'+BASE+'" aria-label="Alle\'s ClinX Knowledge home">Alle\'s ClinX</a></div>'+
    '<div class="acx-site-actions"><button class="acx-search-button" type="button" aria-label="Search Knowledge">'+searchIcon+'</button><button class="acx-install-app" type="button" aria-label="Install Alle\'s ClinX Knowledge app">Install</button>'+
    '<button class="acx-menu-button" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="acx-mobile-drawer">Menu</button></div></div>'+
    '<div class="acx-mobile-drawer" id="acx-mobile-drawer" role="dialog" aria-modal="true" aria-label="Explore Alle\'s ClinX Knowledge" aria-hidden="true"><div class="acx-mobile-drawer-inner">'+
      '<section class="acx-mobile-section" aria-labelledby="acx-mobile-knowledge-label">'+
        '<div class="acx-mobile-section-head"><span id="acx-mobile-knowledge-label">Knowledge</span><span class="acx-mobile-guide-count" aria-live="polite"></span></div>'+
        '<nav class="acx-mobile-knowledge-nav" aria-label="Knowledge navigation"><a href="'+BASE+'" data-internal="true"><span>Knowledge home</span></a></nav>'+
      '</section>'+
      '<section class="acx-mobile-section acx-mobile-company-section" aria-labelledby="acx-mobile-company-label">'+
        '<div class="acx-mobile-section-head"><span id="acx-mobile-company-label">Alle\'s ClinX</span></div>'+
        '<nav class="acx-mobile-nav" aria-label="Alle\'s ClinX navigation">'+navLinks()+'</nav>'+
      '</section>'+
      '<div class="acx-mobile-drawer-foot"><a href="https://allesclinx.com/">Alle\'s ClinX</a><span>Open Knowledge</span></div>'+
    '</div></div></header>';
  const injectedHeader=header.firstElementChild;
  document.body.insertAdjacentElement('afterbegin',injectedHeader);
  const injectedDrawer=injectedHeader.querySelector('#acx-mobile-drawer');
  if(injectedDrawer) injectedHeader.insertAdjacentElement('afterend',injectedDrawer);

  if(!document.getElementById('acx-site-footer')){
    const footer=document.createElement('footer');
    footer.className='acx-site-footer';
    footer.id='acx-site-footer';
    footer.setAttribute('aria-label',"Alle's ClinX Knowledge footer");
    footer.innerHTML=
      '<div class="acx-footer-shell">'+
        '<div class="acx-footer-main">'+
          '<div class="acx-footer-intro">'+
            '<a class="acx-footer-brand" href="'+BASE+'">Alle\'s ClinX</a>'+
            '<p>Open Knowledge for professional cleaning, hygiene, safety and facility operations.</p>'+
          '</div>'+
          '<div class="acx-footer-groups">'+
            '<section class="acx-footer-group" aria-labelledby="acx-footer-knowledge">'+
              '<h2 id="acx-footer-knowledge">Knowledge</h2>'+
              '<nav class="acx-footer-nav" aria-label="Knowledge footer navigation">'+
                '<a href="'+BASE+'">Knowledge home</a>'+
                '<a href="'+BASE+'about/knowledge/">About Knowledge</a>'+
                '<a href="'+BASE+'library/cleaning-housekeeping/">Cleaning &amp; Housekeeping</a>'+
                '<a href="'+BASE+'library/safety-compliance/">Safety &amp; Compliance</a>'+
                '<a href="'+BASE+'library/alles-clinx/">Tools &amp; Support</a>'+
                '<a href="'+BASE+'about/tools/">About digital tools</a>'+
              '</nav>'+
            '</section>'+
            '<section class="acx-footer-group" aria-labelledby="acx-footer-legal">'+
              '<h2 id="acx-footer-legal">Legal</h2>'+
              '<nav class="acx-footer-nav" aria-label="Legal footer navigation">'+
                '<a href="'+BASE+'privacy-policy/">Privacy</a>'+
                '<a href="'+BASE+'terms-conditions/">Terms</a>'+
                '<a href="'+BASE+'cookie-policy/">Cookies</a>'+
                '<a href="'+BASE+'ai-data-use/">AI &amp; Data Use</a>'+
                '<a href="'+BASE+'accessibility/">Accessibility</a>'+
                '<a href="'+BASE+'trust-security/">Trust &amp; Security</a>'+
              '</nav>'+
            '</section>'+
          '</div>'+
        '</div>'+
        '<div class="acx-footer-bottom">'+
          '<div class="acx-footer-meta"><span>Open Knowledge</span><span>© <span data-acx-footer-year></span> Alle\'s ClinX</span></div>'+
          '<div class="acx-footer-actions">'+
            '<a href="mailto:care@allesclinx.com">care@allesclinx.com</a>'+
            '<a href="https://allesclinx.com/">allesclinx.com <span aria-hidden="true">↗</span></a>'+
            '<button class="acx-footer-top" type="button" aria-label="Back to top">Top <span aria-hidden="true">↑</span></button>'+
          '</div>'+
        '</div>'+
      '</div>';
    const decorativeBrand=document.querySelector('.acx-bottom-brand,.legal-bottom-brand');
    if(decorativeBrand) decorativeBrand.insertAdjacentElement('afterend',footer);
    else document.body.appendChild(footer);
    const year=footer.querySelector('[data-acx-footer-year]');
    if(year) year.textContent=String(new Date().getFullYear());
    const topButton=footer.querySelector('.acx-footer-top');
    if(topButton) topButton.addEventListener('click',function(){
      window.scrollTo({top:0,behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
    });
  }

  const installBtn=document.querySelector('.acx-install-app');
  let deferredInstallPrompt=null;
  const installNote=document.createElement('div');
  installNote.className='acx-install-note';
  installNote.setAttribute('role','status');
  installNote.hidden=true;
  document.body.appendChild(installNote);
  let installNoteTimer;
  function isStandalone(){
    return window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone===true;
  }
  function syncInstallButton(){
    if(!installBtn) return;
    installBtn.hidden=isStandalone();
  }
  window.addEventListener('beforeinstallprompt',function(event){
    event.preventDefault();
    deferredInstallPrompt=event;
    syncInstallButton();
  });
  if(installBtn){
    installBtn.addEventListener('click',async function(){
      if(!deferredInstallPrompt){
        installNote.textContent=/iPhone|iPad|iPod/i.test(navigator.userAgent)
          ? 'In Safari, tap Share, then Add to Home Screen.'
          : 'Use your browser menu to install this app or add it to your home screen.';
        installNote.hidden=false;
        clearTimeout(installNoteTimer);
        installNoteTimer=setTimeout(function(){installNote.hidden=true;},6000);
        return;
      }
      deferredInstallPrompt.prompt();
      try{await deferredInstallPrompt.userChoice;}catch(error){}
      deferredInstallPrompt=null;
      syncInstallButton();
    });
  }
  window.addEventListener('appinstalled',function(){
    deferredInstallPrompt=null;
    syncInstallButton();
  });
  window.matchMedia('(display-mode: standalone)').addEventListener?.('change',syncInstallButton);
  syncInstallButton();

  const pwaStatus=document.createElement('div');
  pwaStatus.className='acx-pwa-status';
  pwaStatus.setAttribute('role','status');
  pwaStatus.setAttribute('aria-live','polite');
  pwaStatus.hidden=true;
  pwaStatus.textContent='Offline mode · visited guides remain available';
  document.body.appendChild(pwaStatus);
  function syncConnectivity(){
    pwaStatus.hidden=navigator.onLine;
  }
  window.addEventListener('online',syncConnectivity);
  window.addEventListener('offline',syncConnectivity);
  syncConnectivity();

  if('serviceWorker' in navigator && location.protocol!=='file:'){
    window.addEventListener('load',async function(){
      try{
        const registration=await navigator.serviceWorker.register(BASE+'sw.js',{scope:BASE});
        if(registration.waiting && navigator.serviceWorker.controller){
          registration.waiting.postMessage({type:'SKIP_WAITING'});
        }
        registration.addEventListener('updatefound',function(){
          const worker=registration.installing;
          if(!worker) return;
          worker.addEventListener('statechange',function(){
            if(worker.state==='installed' && registration.waiting && navigator.serviceWorker.controller){
              registration.waiting.postMessage({type:'SKIP_WAITING'});
            }
          });
        });
      }catch(error){
        console.warn('Alle\'s ClinX Knowledge service worker registration failed.',error);
      }
    });
  }

  const siteHeader=document.querySelector('.acx-site-header');
  function syncHeaderState(){
    siteHeader.classList.toggle('is-scrolled',window.scrollY>10);
  }
  window.addEventListener('scroll',syncHeaderState,{passive:true});
  syncHeaderState();

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
  const mobileKnowledgeNav=document.querySelector('.acx-mobile-knowledge-nav');
  const mobileGuideCount=document.querySelector('.acx-mobile-guide-count');
  const searchBtns=[...document.querySelectorAll('.acx-search-button,.acx-mobile-search')];
  const closeBtn=dialog.querySelector('.acx-search-close');
  const input=dialog.querySelector('.acx-search-input');
  const results=dialog.querySelector('.acx-search-results');
  const statusLabel=dialog.querySelector('.acx-search-status-label');
  const countLabel=dialog.querySelector('.acx-search-count');
  let records=null;
  let activeIndex=-1;
  let visibleResults=[];

  let menuReturnFocus=null;
  const hookStates=new WeakMap();

  function syncHookRails(){
    drawer.querySelectorAll('.acx-mobile-knowledge-nav,.acx-mobile-nav').forEach(function(nav){
      let rail=nav.querySelector(':scope > .acx-hover-rail');
      if(!rail){
        rail=document.createElement('span');
        rail.className='acx-hover-rail';
        rail.setAttribute('aria-hidden','true');
        nav.appendChild(rail);
      }
      let state=hookStates.get(nav);
      if(!state){
        state={rail:null,hovered:null};
        hookStates.set(nav,state);
      }
      state.rail=rail;
      state.hovered=null;
      function move(link,hover){
        if(!link || !nav.contains(link)){
          state.rail.className='acx-hover-rail';
          return;
        }
        state.rail.style.height=(link.offsetTop+link.offsetHeight/2)+'px';
        state.rail.className='acx-hover-rail is-visible '+(hover?'is-hover':'is-active');
      }
      function restore(){move(nav.querySelector('a.is-current'),false);}
      if(!nav.dataset.hookReady){
        nav.dataset.hookReady='true';
        nav.addEventListener('mouseover',function(event){
          const link=event.target.closest('a');
          if(link && nav.contains(link)){state.hovered=link;move(link,true);}
        });
        nav.addEventListener('focusin',function(event){
          const link=event.target.closest('a');
          if(link && nav.contains(link)){state.hovered=link;move(link,true);}
        });
        nav.addEventListener('mouseleave',function(){state.hovered=null;restore();});
        nav.addEventListener('focusout',function(event){if(!nav.contains(event.relatedTarget)){state.hovered=null;restore();}});
        if(window.ResizeObserver) new ResizeObserver(function(){move(state.hovered||nav.querySelector('a.is-current'),!!state.hovered);}).observe(nav);
      }
      restore();
    });
  }

  function syncMobileActiveLinks(){
    const current=window.location.pathname.replace(/\/+$/,'/') || '/';
    drawer.querySelectorAll('a[href]').forEach(function(link){
      const href=link.getAttribute('href')||'';
      const internal=href.startsWith(BASE);
      if(!internal) return;
      const normalized=href.replace(/\/+$/,'/') || '/';
      const exact=current===normalized;
      const section=!exact && normalized!==BASE && current.startsWith(normalized);
      link.classList.toggle('is-current',exact||section);
      if(exact) link.setAttribute('aria-current','page');
      else link.removeAttribute('aria-current');
    });
  }

  function setMenu(open,restoreFocus){
    if(open){
      menuReturnFocus=document.activeElement;
      if(dialog.classList.contains('is-open')) closeSearch();
    }
    menuBtn.setAttribute('aria-expanded',open?'true':'false');
    menuBtn.setAttribute('aria-label',open?'Close menu':'Open menu');
    menuBtn.textContent=open?'Close':'Menu';
    drawer.setAttribute('aria-hidden',open?'false':'true');
    drawer.classList.toggle('is-open',open);
    document.body.classList.toggle('acx-menu-open',open);
    if(open){
      syncMobileActiveLinks();
      syncHookRails();
      const first=drawer.querySelector('.acx-mobile-search');
      if(first) first.focus({preventScroll:true});
    }else if(restoreFocus!==false && menuReturnFocus && typeof menuReturnFocus.focus==='function'){
      menuReturnFocus.focus({preventScroll:true});
      menuReturnFocus=null;
    }
  }
  menuBtn.addEventListener('click',function(){setMenu(menuBtn.getAttribute('aria-expanded')!=='true');});
  drawer.addEventListener('click',function(event){
    if(event.target.closest('a[href]')) setMenu(false,false);
  });

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

  function hydrateMobileKnowledge(records){
    if(!mobileKnowledgeNav||!Array.isArray(records)) return;
    const categories=new Map();
    records.forEach(function(record){
      if(!record.category_slug||!record.category||!record.article_id) return;
      const key=record.category_slug;
      if(!categories.has(key)) categories.set(key,{name:record.category,ids:new Set()});
      categories.get(key).ids.add(record.article_id);
    });
    const home=mobileKnowledgeNav.querySelector('a[href="'+BASE+'"]');
    mobileKnowledgeNav.innerHTML='';
    if(home) mobileKnowledgeNav.appendChild(home);
    categories.forEach(function(info,slug){
      const link=document.createElement('a');
      link.href=BASE+'library/'+slug+'/';
      link.setAttribute('data-internal','true');
      link.innerHTML='<span>'+esc(info.name)+'</span><small>'+info.ids.size+'</small>';
      mobileKnowledgeNav.appendChild(link);
    });
    const total=new Set(records.map(function(record){return record.article_id;})).size;
    if(mobileGuideCount) mobileGuideCount.textContent=total+' live guides';
    syncMobileActiveLinks();
    syncHookRails();
  }

  async function loadRecords(){
    if(records) return records;
    statusLabel.textContent='Loading Knowledge index…';
    try{
      const response=await fetch(BASE+'assets/live-search.json',{cache:'no-store'});
      if(!response.ok) throw new Error('Search index unavailable');
      const data=await response.json();
      records=(data.records||[]).map(function(record,index){return Object.assign({_order:index},record);});
      hydrateMobileKnowledge(records);
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

  loadRecords();

  function closeSearch(){
    dialog.classList.remove('is-open');
    document.body.classList.remove('acx-search-open');
    activeIndex=-1;
    input.removeAttribute('aria-activedescendant');
  }

  const homeSearch=document.getElementById('knowledge-search');
  if(homeSearch){
    homeSearch.placeholder='Search all Knowledge guides';
    homeSearch.setAttribute('aria-label','Search all Knowledge guides');
    homeSearch.addEventListener('focus',function(){openSearch();});
    homeSearch.addEventListener('click',function(){openSearch();});
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
      else if(drawer.classList.contains('is-open')) setMenu(false);
    }
    if(event.key==='Tab'&&drawer.classList.contains('is-open')){
      const focusable=[menuBtn,...drawer.querySelectorAll('a[href],button:not([disabled])')].filter(function(el){
        return el.offsetParent!==null;
      });
      if(focusable.length){
        const first=focusable[0];
        const last=focusable[focusable.length-1];
        if(event.shiftKey&&document.activeElement===first){
          event.preventDefault();last.focus();
        }else if(!event.shiftKey&&document.activeElement===last){
          event.preventDefault();first.focus();
        }
      }
    }
  });
})();
