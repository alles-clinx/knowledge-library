import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const baseUrl=process.env.BASE_URL || 'http://127.0.0.1:4173/knowledge/';
const resolve=(path)=>new URL(path,baseUrl).toString();

const manifestResponse=await fetch(resolve('manifest.webmanifest'));
assert.equal(manifestResponse.status,200,'manifest.webmanifest should be served');
const manifest=await manifestResponse.json();
for(const path of ['assets/favicon.svg','assets/app-icon.svg']){
  const svg=await (await fetch(resolve(path))).text();
  assert.match(svg,/Knowledge.*book icon/i,'Knowledge favicon/app icon should have accessible book description');
  assert.match(svg,/M12 6\.5C9\.3 4\.7/,'Site icon should render the same open-book glyph as the header');
  assert.doesNotMatch(svg,/M39\.5 17\.5|M318 142/,'Legacy CX monogram must not remain in icon assets');
}
assert.equal(manifest.name,"Alle's ClinX Knowledge");
assert.equal(manifest.start_url,'./');
assert.equal(manifest.scope,'./');
assert.equal(manifest.display,'standalone');
assert.ok(Array.isArray(manifest.icons) && manifest.icons.length>0,'manifest should include an app icon');
assert.equal(manifest.icons[0].src,'assets/app-icon.svg','manifest should use the shared vector app icon');
assert.ok(manifest.icons.some(icon=>icon.src==='assets/icon-192.png'&&icon.sizes==='192x192'&&icon.type==='image/png'),
  'PWA should include a 192px native PNG icon');
for(const [path,size] of [['assets/apple-touch-icon.png',180],['assets/icon-192.png',192]]){
  const response=await fetch(resolve(path));
  assert.equal(response.status,200,path+' should be available');
  const bytes=Buffer.from(await response.arrayBuffer());
  assert.equal(bytes.subarray(0,8).toString('hex'),'89504e470d0a1a0a',path+' must be a real PNG');
  assert.equal(bytes.readUInt32BE(16),size,path+' PNG width mismatch');
  assert.equal(bytes.readUInt32BE(20),size,path+' PNG height mismatch');
}
const rawHome=await (await fetch(baseUrl)).text();
assert.ok(rawHome.includes('rel="icon" type="image/svg+xml" href='),'Favicon must be declared in the HTML head');
assert.ok(rawHome.includes('apple-touch-icon.png?v=20261018-book'),'Apple touch icon must be declared in the HTML head');

const swResponse=await fetch(resolve('sw.js'));
assert.equal(swResponse.status,200,'sw.js should be served');
const swText=await swResponse.text();
assert.match(swText,/serviceWorker|fetch|PRECACHE|acx-knowledge-pwa-/i);

const browser=await chromium.launch({headless:true});
const context=await browser.newContext({serviceWorkers:'allow'});
const page=await context.newPage();

await page.goto(baseUrl,{waitUntil:'networkidle'});
assert.equal(await page.locator('link[rel="manifest"]').count(),1,'page should expose one manifest link');
assert.equal(await page.locator('link[rel="icon"][type="image/svg+xml"]').count(),1,'page should expose the vector favicon');
assert.match(await page.locator('link[rel="icon"][type="image/svg+xml"]').getAttribute('href'),/favicon\.svg\?v=20261018-book/,'favicon should use the current cache-busted vector mark');
assert.equal(await page.locator('link[rel="alternate icon"]').count(),1,'Browser should have a PNG favicon fallback');
assert.equal(await page.locator('link[rel="apple-touch-icon"]').count(),1,'iOS should have exactly one touch icon');
assert.match(await page.locator('link[rel="apple-touch-icon"]').getAttribute('href'),/apple-touch-icon\.png\?v=20261018-book/);
await page.evaluate(async()=>{await navigator.serviceWorker.ready;});
await page.reload({waitUntil:'networkidle'});
assert.equal(await page.evaluate(()=>Boolean(navigator.serviceWorker.controller)),true,'service worker should control the app after reload');

const articleUrl=resolve('library/cleaning-housekeeping/cleaning-basics/what-is-professional-cleaning/');
await page.goto(articleUrl,{waitUntil:'networkidle'});
assert.equal(await page.locator('link[rel="icon"][type="image/svg+xml"]').count(),1,'Article route should receive site icon');
assert.equal(await page.locator('link[rel="apple-touch-icon"]').count(),1,'Article route should receive exactly one iOS icon');
assert.match(await page.locator('body').innerText(),/Professional Cleaning/i);

await context.setOffline(true);
await page.reload({waitUntil:'domcontentloaded',timeout:15000});
assert.match(await page.locator('body').innerText(),/Professional Cleaning/i,'a previously visited guide should reload offline');

await page.goto(baseUrl,{waitUntil:'domcontentloaded',timeout:15000});
assert.match(await page.locator('body').innerText(),/Alle's ClinX Knowledge/i,'the Knowledge home should load offline');

await context.setOffline(false);
await browser.close();
console.log('PWA smoke test passed');
