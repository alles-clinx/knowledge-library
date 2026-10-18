/* Eleven's three newest publicly released episodes, with static HTML fallback. */
(function(){
  'use strict';
  const cards=[...document.querySelectorAll('.eleven-episode')].slice(0,3);
  if(cards.length!==3) return;
  const api='https://itunes.apple.com/lookup?id=1875218821&entity=podcastEpisode&limit=30&country=us';
  const controller=new AbortController();
  const timeout=setTimeout(function(){controller.abort();},5500);
  fetch(api,{signal:controller.signal,mode:'cors',credentials:'omit'})
    .then(function(response){if(!response.ok)throw new Error('Catalogue unavailable');return response.json();})
    .then(function(payload){
      if(!payload||!Array.isArray(payload.results))return;
      const episodes=payload.results.filter(function(record){
        return Number(record.collectionId)===1875218821 &&
          (record.kind==='podcast-episode'||record.wrapperType==='podcastEpisode') &&
          record.trackName && record.releaseDate &&
          Date.parse(record.releaseDate)<=Date.now() &&
          /^https:\/\/podcasts\.apple\.com\//.test(String(record.trackViewUrl||''));
      }).sort(function(a,b){return Date.parse(b.releaseDate)-Date.parse(a.releaseDate);}).slice(0,3);
      if(episodes.length<3)return;
      episodes.forEach(function(ep,index){
        const card=cards[index];
        const title=String(ep.trackName).trim();
        const date=new Date(ep.releaseDate);
        if(!title||!Number.isFinite(date.getTime()))return;
        card.href=ep.trackViewUrl;
        card.setAttribute('aria-label','Listen to '+title);
        const heading=card.querySelector('h3');
        if(heading)heading.textContent=title;
        const num=Number(ep.episodeNumber||0);
        const minutes=Math.round(Number(ep.trackTimeMillis||0)/60000);
        const meta=card.querySelector('.eleven-episode-meta');
        if(meta)meta.textContent=(num?'Episode '+String(num).padStart(2,'0'):'Latest episode')+(minutes?' · '+minutes+' min':'');
        const desc=card.querySelector('.eleven-episode-body p');
        if(desc){
          const summary=String(ep.shortDescription||ep.description||'').replace(/<[^>]*>/g,' ').replace(/\s+/g,' ').trim();
          if(summary)desc.textContent=summary.length>195?summary.slice(0,192).trimEnd()+'…':summary;
        }
        const time=card.querySelector('time');
        if(time){
          time.dateTime=date.toISOString().slice(0,10);
          time.textContent=date.toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'});
        }
        const artwork=String(ep.artworkUrl600||ep.artworkUrl160||'');
        if(/^https:\/\/[^/]+\.mzstatic\.com\//.test(artwork)){
          const cover=card.querySelector('.eleven-cover');
          if(cover){
            const img=document.createElement('img');
            img.alt='';
            img.loading='lazy';
            img.decoding='async';
            img.referrerPolicy='no-referrer';
            img.src=artwork;
            cover.replaceChildren(img);
          }
        }
      });
    })
    .catch(function(){/* Verified static episode links remain visible. */})
    .finally(function(){clearTimeout(timeout);});
})();