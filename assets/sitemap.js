(function(){
  const BASE='/knowledge/';
  const liveRoot=document.getElementById('acx-sitemap-live');
  const count=document.getElementById('acx-sitemap-count');
  const filter=document.getElementById('acx-sitemap-filter');
  if(!liveRoot) return;

  function escapeHtml(value){
    return String(value||'').replace(/[&<>"']/g,function(ch){
      return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch];
    });
  }
  function route(value){
    return BASE+String(value||'').replace(/^\/+/, '');
  }
  function render(records){
    const groups=new Map();
    records.filter(function(record){return record.locale==='en';}).forEach(function(record){
      const catKey=record.category_slug||record.category;
      if(!groups.has(catKey)){
        groups.set(catKey,{name:record.category,slug:record.category_slug,topics:new Map(),count:0});
      }
      const category=groups.get(catKey);
      const topicKey=record.subcategory_slug||record.subcategory;
      if(!category.topics.has(topicKey)){
        category.topics.set(topicKey,{name:record.subcategory,slug:record.subcategory_slug,articles:[]});
      }
      category.topics.get(topicKey).articles.push(record);
      category.count++;
    });
    if(!groups.size){
      liveRoot.innerHTML='<p class="acx-sitemap-error">No live English Knowledge articles are available in the current index.</p>';
      if(count) count.textContent='0 live articles';
      return;
    }
    let total=0;
    liveRoot.innerHTML=Array.from(groups.values()).map(function(category){
      total+=category.count;
      const topics=Array.from(category.topics.values()).map(function(topic){
        const articles=topic.articles.map(function(article){
          return '<a class="acx-sitemap-live-link" href="'+route(article.url)+'">'+escapeHtml(article.title)+'</a>';
        }).join('');
        return '<section class="acx-sitemap-topic">'+
          '<a href="'+BASE+'library/'+encodeURIComponent(category.slug)+'/'+encodeURIComponent(topic.slug)+'/">'+escapeHtml(topic.name)+'</a>'+
          '<div class="acx-sitemap-articles">'+articles+'</div>'+
        '</section>';
      }).join('');
      return '<section class="acx-sitemap-category-block" data-sitemap-category>'+
        '<div class="acx-sitemap-category-head">'+
          '<a href="'+BASE+'library/'+encodeURIComponent(category.slug)+'/">'+escapeHtml(category.name)+'</a>'+
          '<span>'+category.count+' article'+(category.count===1?'':'s')+'</span>'+
        '</div>'+
        '<div class="acx-sitemap-topic-grid">'+topics+'</div>'+
      '</section>';
    }).join('');
    if(count) count.textContent=total+' live English article'+(total===1?'':'s');
    applyFilter();
  }
  function applyFilter(){
    const q=filter ? filter.value.trim().toLowerCase() : '';
    document.querySelectorAll('[data-sitemap-static]').forEach(function(section){
      section.hidden=!!q && !section.textContent.toLowerCase().includes(q);
    });
    document.querySelectorAll('[data-sitemap-category]').forEach(function(section){
      section.hidden=!!q && !section.textContent.toLowerCase().includes(q);
    });
  }
  if(filter) filter.addEventListener('input',applyFilter);
  fetch(BASE+'assets/live-search.json',{cache:'no-store'})
    .then(function(response){if(!response.ok) throw new Error('index'); return response.json();})
    .then(function(data){render(data.records||[]);})
    .catch(function(){
      liveRoot.innerHTML='<p class="acx-sitemap-error">The live article index could not be loaded. Use the site search or category pages to continue browsing.</p>';
      if(count) count.textContent='Live index unavailable';
    });
})();