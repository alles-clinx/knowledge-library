import assert from 'node:assert/strict';
import { chromium } from 'playwright';

const baseUrl=process.env.BASE_URL || 'http://127.0.0.1:4173/knowledge/';
const resolve=(path)=>new URL(path,baseUrl).toString();

const manifestResponse=await fetch(resolve('manifest.webmanifest'));
assert.equal(manifestResponse.status,200,'manifest.webmanifest should be served');
const manifest=await manifestResponse.json();
assert.equal(manifest.name,"Alle's ClinX Knowledge");
assert.equal(manifest.start_url,'./');
assert.equal(manifest.scope,'./');
assert.equal(manifest.display,'standalone');
assert.ok(Array.isArray(manifest.icons) && manifest.icons.length>0,'manifest should include an app icon');

const swResponse=await fetch(resolve('sw.js'));
assert.equal(swResponse.status,200,'sw.js should be served');
const swText=await swResponse.text();
assert.match(swText,/serviceWorker|fetch|PRECACHE|acx-knowledge-pwa-/i);

const browser=await chromium.launch({headless:true});
const context=await browser.newContext({serviceWorkers:'allow'});
const page=await context.newPage();

await page.goto(baseUrl,{waitUntil:'networkidle'});
assert.equal(await page.locator('link[rel="manifest"]').count(),1,'page should expose one manifest link');
await page.evaluate(async()=>{await navigator.serviceWorker.ready;});
await page.reload({waitUntil:'networkidle'});
assert.equal(await page.evaluate(()=>Boolean(navigator.serviceWorker.controller)),true,'service worker should control the app after reload');

const articleUrl=resolve('library/cleaning-housekeeping/cleaning-basics/what-is-professional-cleaning/');
await page.goto(articleUrl,{waitUntil:'networkidle'});
assert.match(await page.locator('body').innerText(),/Professional Cleaning/i);

await context.setOffline(true);
await page.reload({waitUntil:'domcontentloaded',timeout:15000});
assert.match(await page.locator('body').innerText(),/Professional Cleaning/i,'a previously visited guide should reload offline');

await page.goto(baseUrl,{waitUntil:'domcontentloaded',timeout:15000});
assert.match(await page.locator('body').innerText(),/Alle's ClinX Knowledge/i,'the Knowledge home should load offline');

await context.setOffline(false);
await browser.close();
console.log('PWA smoke test passed');
