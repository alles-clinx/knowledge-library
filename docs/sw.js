const VERSION='acx-knowledge-pwa-20260927-v2-header';
const STATIC_CACHE=VERSION+'-static';
const RUNTIME_CACHE=VERSION+'-runtime';
const SCOPE=new URL(self.registration.scope);
const asset=function(path){return new URL(path,SCOPE).toString();};
const PRECACHE=[
  asset('./'),
  asset('offline.html'),
  asset('manifest.webmanifest'),
  asset('assets/site.css'),
  asset('assets/site.js'),
  asset('assets/live-search.json'),
  asset('assets/favicon.png'),
  asset('assets/favicon.svg'),
  asset('assets/app-icon.svg')
];

self.addEventListener('install',function(event){
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(function(cache){return cache.addAll(PRECACHE);})
      .then(function(){return self.skipWaiting();})
  );
});

self.addEventListener('activate',function(event){
  event.waitUntil(
    Promise.all([
      caches.keys().then(function(keys){
        return Promise.all(keys.filter(function(key){
          return key!==STATIC_CACHE && key!==RUNTIME_CACHE && key.startsWith('acx-knowledge-pwa-');
        }).map(function(key){return caches.delete(key);}));
      }),
      self.clients.claim()
    ])
  );
});

self.addEventListener('message',function(event){
  if(event.data && event.data.type==='SKIP_WAITING') self.skipWaiting();
});

async function cacheResponse(cacheName,request,response){
  if(response && response.ok){
    const cache=await caches.open(cacheName);
    await cache.put(request,response.clone());
  }
  return response;
}

async function networkFirst(request){
  try{
    const response=await fetch(request);
    return cacheResponse(RUNTIME_CACHE,request,response);
  }catch(error){
    return (await caches.match(request,{ignoreSearch:true})) ||
      (await caches.match(asset('offline.html'))) ||
      (await caches.match(asset('./')));
  }
}

async function staleWhileRevalidate(request){
  const cached=await caches.match(request,{ignoreSearch:false});
  const fresh=fetch(request)
    .then(function(response){return cacheResponse(RUNTIME_CACHE,request,response);})
    .catch(function(){return null;});
  return cached || fresh || caches.match(asset('offline.html'));
}

self.addEventListener('fetch',function(event){
  const request=event.request;
  if(request.method!=='GET') return;
  const url=new URL(request.url);
  if(url.origin!==self.location.origin) return;

  if(request.mode==='navigate'){
    event.respondWith(networkFirst(request));
    return;
  }

  if(url.pathname.endsWith('/assets/live-search.json')){
    event.respondWith(networkFirst(request));
    return;
  }

  if(['style','script','image','font','manifest'].includes(request.destination)){
    event.respondWith(staleWhileRevalidate(request));
  }
});
