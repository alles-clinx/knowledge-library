(function(){
  document.querySelectorAll('link[rel~="icon"],link[rel="shortcut icon"],link[rel="apple-touch-icon"],link[rel="mask-icon"]').forEach(function(el){el.remove();});
  const blankIcon=document.createElement('link');
  blankIcon.rel='icon';
  blankIcon.href='data:,';
  document.head.appendChild(blankIcon);
  if(window.__ACX_SITE_SHELL__) return;
  window.__ACX_SITE_SHELL__=true;
  const BASE='/knowledge-library/';
  const isKnowledge=true;
  const searchIcon='<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6.5"></circle><path d="m16 16 4.25 4.25"></path></svg>';
  const wordmark='<span class="acx-wordmark">Alle\'s ClinX</span>';
  const nav=[
    ['Solutions','https://allesclinx.com/solutions/'],
    ['ClinXAi','https://allesclinx.com/clinxai/'],
    ['Shop','https://allesclinx.com/shop/'],
    ['Plus','https://allesclinx.com/plus/'],
    ['Support','https://allesclinx.com/support/']
  ];
  function links(){
    return nav.map(([label,href])=>'<a href="'+href+'">'+label+'</a>').join('');
  }
  const header=document.createElement('div');
  header.innerHTML='<header class="acx-site-header"><div class="acx-site-bar">'+
    '<div class="acx-brand-cluster"><a class="acx-wordmark" href="https://allesclinx.com/" aria-label="Alle\'s ClinX main website">Alle\'s ClinX</a><span class="acx-brand-divider" aria-hidden="true"></span><a class="acx-context-link" href="'+BASE+'" aria-label="Alle\'s ClinX Knowledge home">Knowledge</a></div>'+
    '<nav class="acx-primary-nav" aria-label="Primary">'+links()+'</nav>'+
    '<div class="acx-site-actions"><button class="acx-search-button" type="button" aria-label="Search Knowledge">'+searchIcon+'<span class="acx-search-label">Search</span><kbd>⌘K</kbd></button>'+
    '<button class="acx-menu-button" type="button" aria-label="Open menu" aria-expanded="false"><span></span></button></div></div>'+
    '<div class="acx-mobile-drawer" id="acx-mobile-drawer"><div class="acx-mobile-drawer-inner"><div class="acx-mobile-context"><strong>Knowledge</strong><a href="'+BASE+'">Knowledge home</a></div><nav class="acx-mobile-nav" aria-label="Mobile primary">'+links()+'</nav></div></div></header>';
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
  dialog.innerHTML='<div class="acx-search-panel"><div class="acx-search-top">'+searchIcon+
    '<input class="acx-search-input" type="search" autocomplete="off" placeholder="Search live Knowledge guides" aria-label="Search live Knowledge guides">'+
    '<button class="acx-search-close" type="button" aria-label="Close search">×</button></div>'+
    '<div class="acx-search-results"><div class="acx-search-empty">Start typing to search live guides.</div></div>'+
    '<div class="acx-search-hint">Search covers currently live Knowledge articles.</div></div>';
  document.body.appendChild(dialog);

  const menuBtn=document.querySelector('.acx-menu-button');
  const drawer=document.getElementById('acx-mobile-drawer');
  const searchBtns=[...document.querySelectorAll('.acx-search-button')];
  const closeBtn=dialog.querySelector('.acx-search-close');
  const input=dialog.querySelector('.acx-search-input');
  const results=dialog.querySelector('.acx-search-results');
  let records=null;

  function setMenu(open){
    menuBtn.setAttribute('aria-expanded',open?'true':'false');
    menuBtn.setAttribute('aria-label',open?'Close menu':'Open menu');
    drawer.classList.toggle('is-open',open);
    document.body.classList.toggle('acx-menu-open',open);
  }
  menuBtn.addEventListener('click',()=>setMenu(menuBtn.getAttribute('aria-expanded')!=='true'));

  async function loadRecords(){
    if(records) return records;
    try{
      const r=await fetch(BASE+'assets/live-search.json',{cache:'no-store'});
      if(!r.ok) throw new Error('search');
      const data=await r.json();
      records=data.records||[];
    }catch(e){ records=[]; }
    return records;
  }
  function esc(s){return String(s||'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));}
  function renderSearch(){
    const q=input.value.trim().toLowerCase();
    if(!q){results.innerHTML='<div class="acx-search-empty">Start typing to search live guides.</div>';return;}
    const found=(records||[]).filter(r=>(r.title+' '+r.category+' '+r.subcategory+' '+r.article_id).toLowerCase().includes(q)).slice(0,8);
    results.innerHTML=found.length?found.map(r=>'<a class="acx-search-result" href="'+BASE+r.url.replace(/^\//,'')+'"><strong>'+esc(r.title)+'</strong><span>'+esc(r.subcategory)+' · '+esc(r.article_id)+'</span></a>').join(''):'<div class="acx-search-empty">No live guide matches “'+esc(input.value.trim())+'”.</div>';
  }
  async function openSearch(){
    setMenu(false);
    dialog.classList.add('is-open');
    document.body.classList.add('acx-search-open');
    await loadRecords();
    input.focus();
    renderSearch();
  }
  function closeSearch(){
    dialog.classList.remove('is-open');
    document.body.classList.remove('acx-search-open');
    input.value='';
    renderSearch();
  }
  searchBtns.forEach(b=>b.addEventListener('click',openSearch));
  closeBtn.addEventListener('click',closeSearch);
  dialog.addEventListener('pointerdown',e=>{if(e.target===dialog)closeSearch();});
  input.addEventListener('input',renderSearch);
  document.addEventListener('keydown',e=>{
    if((e.metaKey||e.ctrlKey)&&e.key.toLowerCase()==='k'){e.preventDefault();dialog.classList.contains('is-open')?closeSearch():openSearch();}
    if(e.key==='Escape'){if(dialog.classList.contains('is-open'))closeSearch();else setMenu(false);}
  });
})();
