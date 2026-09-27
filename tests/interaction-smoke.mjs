import { chromium } from 'playwright';
import fs from 'node:fs';

const BASE = process.env.BASE_URL || 'http://127.0.0.1:4173/knowledge/';
const ORIGIN = new URL(BASE).origin;
const records = JSON.parse(fs.readFileSync('docs/assets/live-search.json','utf8')).records || [];
const en = [...records].reverse().find(r => r.locale === 'en');
const hi = en ? records.find(r => r.article_id === en.article_id && r.locale === 'hi-IN') : null;

function assert(value, message){
  if(!value) throw new Error(message);
}
function articleUrl(record){
  return new URL(String(record.url || '').replace(/^\/+/,''), BASE).href;
}
async function wait(ms=180){ await new Promise(r=>setTimeout(r,ms)); }

const browser = await chromium.launch({headless:true});
try{
  const desktop = await browser.newContext({viewport:{width:1366,height:900}});
  await desktop.grantPermissions(['clipboard-read','clipboard-write'], {origin:ORIGIN});
  const page = await desktop.newPage();
  await page.goto(BASE,{waitUntil:'networkidle'});
  assert(await page.locator('.acx-site-header').isVisible(),'Desktop site header is not visible');
  assert(await page.locator('.acx-search-button').isVisible(),'Desktop Search button is not visible');
  assert(await page.locator('.acx-site-header').count()===1,'Duplicate shared header');
  assert(await page.locator('.acx-menu-button').isVisible(),'Desktop Menu button is missing');
  const installButton=page.locator('.acx-install-app');
  assert(await installButton.isVisible(),'Desktop Install button is not visible');
  await installButton.click();
  assert(await page.locator('.acx-install-note').isVisible(),'Install fallback guidance did not appear');
  assert((await page.locator('.acx-install-note').textContent()).trim().length>0,'Install fallback guidance is empty');
  await page.locator('.acx-menu-button').click();
  assert(await page.locator('#acx-mobile-drawer.is-open').isVisible(),'Desktop menu did not open');
  await page.locator('#acx-mobile-drawer a').last().focus();
  await page.keyboard.press('Tab');
  assert(await page.locator('.acx-menu-button').evaluate(el=>el===document.activeElement),'Menu keyboard loop skipped Close');
  await page.keyboard.press('Escape');
  assert((await page.locator('#acx-mobile-drawer').getAttribute('aria-hidden'))==='true','Desktop menu did not close');

  await page.locator('.acx-search-button').click();
  assert(await page.locator('.acx-search-dialog.is-open').isVisible(),'Search dialog did not open');
  await page.locator('.acx-search-input').fill('stainless');
  await wait(250);
  assert(await page.locator('.acx-search-result').count()>0,'Search produced no results');
  await page.locator('.acx-search-close').click();
  assert(!(await page.locator('.acx-search-dialog').isVisible()),'Search close button did not close the dialog');

  await page.locator('.acx-search-button').click();
  assert(await page.locator('.acx-search-dialog.is-open').isVisible(),'Search dialog did not reopen');
  await page.keyboard.press('Escape');
  assert(!(await page.locator('.acx-search-dialog').isVisible()),'Search dialog did not close with Escape');

  const next=page.locator('[data-slider-next]').first();
  if(await next.count()){
    const targetId=await next.getAttribute('data-slider-next');
    const slider=page.locator('#'+targetId);
    const before=await slider.evaluate(el=>el.scrollLeft);
    if(!(await next.isDisabled())){
      await next.click();
      await wait(350);
      const after=await slider.evaluate(el=>el.scrollLeft);
      assert(after>before,'Homepage slider next control did not move the slider');
      const prev=page.locator('[data-slider-prev="'+targetId+'"]');
      assert(await prev.count()>0,'Homepage slider previous control is missing');
      await prev.click();
      await wait(350);
      const returned=await slider.evaluate(el=>el.scrollLeft);
      assert(returned<after,'Homepage slider previous control did not move the slider back');
    }
  }
  await desktop.close();

  const mobile = await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
  const mp = await mobile.newPage();
  await mp.goto(BASE,{waitUntil:'networkidle'});
  assert(await mp.locator('.acx-menu-button').isVisible(),'Mobile menu button is not visible');
  assert(await mp.locator('.acx-search-button').isVisible(),'Mobile Search button is not visible');
  assert(await mp.locator('.acx-install-app').isVisible(),'Mobile Install button is not visible');
  await mp.locator('.acx-menu-button').click();
  assert(await mp.locator('#acx-mobile-drawer.is-open').isVisible(),'Mobile drawer did not open');
  assert((await mp.locator('.acx-menu-button').getAttribute('aria-expanded'))==='true','Mobile menu aria-expanded did not update');
  await mp.locator('.acx-menu-button').click();
  assert(!(await mp.locator('#acx-mobile-drawer').evaluate(el=>el.classList.contains('is-open'))),'Mobile menu did not remove the open state');
  assert((await mp.locator('#acx-mobile-drawer').getAttribute('aria-hidden'))==='true','Mobile drawer aria-hidden did not reset');
  assert((await mp.locator('.acx-menu-button').getAttribute('aria-expanded'))==='false','Mobile menu aria-expanded did not reset');
  await wait(240);
  assert(!(await mp.locator('#acx-mobile-drawer').isVisible()),'Mobile drawer remained visible after close transition');
  await mp.locator('.acx-menu-button').click();
  await mp.locator('.acx-search-button').click();
  assert(await mp.locator('.acx-search-dialog.is-open').isVisible(),'Mobile search did not open from header');
  assert((await mp.locator('#acx-mobile-drawer').getAttribute('aria-hidden'))==='true','Mobile drawer did not close when search opened');
  await mp.keyboard.press('Escape');
  assert(!(await mp.locator('.acx-search-dialog').isVisible()),'Mobile search did not close with Escape');
  await mobile.close();

  assert(en,'No English live article found for interaction smoke test');

  const articleCtx = await browser.newContext({viewport:{width:1366,height:900}});
  await articleCtx.grantPermissions(['clipboard-read','clipboard-write'], {origin:ORIGIN});
  const ap = await articleCtx.newPage();
  await ap.goto(articleUrl(en),{waitUntil:'networkidle'});
  assert(await ap.locator('.rail .js-share-toggle').isVisible(),'Desktop Share tool is not visible');
  assert(await ap.locator('.rail .js-save-toggle').isVisible(),'Desktop Save tool is not visible');
  assert(await ap.locator('.rail .js-text-toggle').isVisible(),'Desktop Text tool is not visible');

  await ap.locator('.rail .js-share-toggle').click();
  assert(await ap.locator('.rail .js-share-popover').isVisible(),'Share popover did not open');
  const xHref=await ap.locator('.rail .js-share-url[data-share="x"]').getAttribute('href');
  assert(xHref && xHref.includes('twitter.com/intent/tweet'),'X share URL was not generated');

  await ap.locator('.rail .js-copy-link').click();
  await wait(100);
  const copied=await ap.evaluate(()=>navigator.clipboard.readText());
  assert(copied.includes('/knowledge/'),'Copy-link control did not copy the canonical Knowledge URL');

  await ap.locator('.rail .js-save-toggle').click();
  assert(await ap.locator('.rail .js-save-popover').isVisible(),'Save popover did not open');
  await ap.locator('.rail .js-browser-save[data-save-action="bookmark"]').click();
  assert((await ap.locator('.rail .tool-status').textContent()).includes('bookmark'),'Bookmark helper did not provide browser instruction');

  await ap.locator('.rail .js-save-toggle').click();
  await ap.locator('.rail .js-browser-save[data-save-action="save"]').click();
  assert((await ap.locator('.rail .tool-status').textContent()).includes('save'),'Save-page helper did not provide browser instruction');

  await ap.evaluate(()=>{ window.__acxPrinted=false; window.print=()=>{window.__acxPrinted=true;}; });
  await ap.locator('.rail .js-save-toggle').click();
  await ap.locator('.rail .js-browser-save[data-save-action="print"]').click();
  assert(await ap.evaluate(()=>window.__acxPrinted===true),'Print / Save PDF control did not call window.print()');

  await ap.locator('.rail .js-text-toggle').click();
  assert(await ap.locator('.rail .js-text-popover').isVisible(),'Text popover did not open');
  const beforeSize=parseInt(await ap.locator('.rail .js-size-readout').textContent(),10);
  await ap.locator('.rail .js-larger').click();
  const afterSize=parseInt(await ap.locator('.rail .js-size-readout').textContent(),10);
  assert(afterSize===Math.min(21,beforeSize+1),'Increase text-size control did not update size');
  const cssSize=await ap.locator('.page').evaluate(el=>getComputedStyle(el).getPropertyValue('--reading-size').trim());
  assert(cssSize===afterSize+'px','Text-size control did not update --reading-size');
  await ap.locator('.rail .js-smaller').click();
  const reducedSize=parseInt(await ap.locator('.rail .js-size-readout').textContent(),10);
  assert(reducedSize===Math.max(15,afterSize-1),'Decrease text-size control did not update size');

  await ap.reload({waitUntil:'networkidle'});
  const persisted=parseInt(await ap.locator('.rail .js-size-readout').textContent(),10);
  assert(persisted===reducedSize,'Text-size preference did not persist through reload');

  const enTab=ap.locator('.rail-language-switch a[lang="en"]');
  const hiTab=ap.locator('.rail-language-switch a[lang="hi"]');
  assert((await enTab.getAttribute('aria-selected'))==='true','English tab is not selected on English article');
  assert((await hiTab.getAttribute('href')).includes('hi.html'),'Hindi language tab does not target Hindi article');
  await articleCtx.close();

  if(hi){
    const hiCtx=await browser.newContext({viewport:{width:1366,height:900}});
    const hp=await hiCtx.newPage();
    await hp.goto(articleUrl(hi),{waitUntil:'networkidle'});
    assert((await hp.locator('.rail-language-switch a[lang="hi"]').getAttribute('aria-selected'))==='true','Hindi tab is not selected on Hindi article');
    await hiCtx.close();
  }

  const maCtx=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
  const ma=await maCtx.newPage();
  await ma.goto(articleUrl(en),{waitUntil:'networkidle'});
  await ma.locator('.mobile-tools').scrollIntoViewIfNeeded();
  assert(await ma.locator('.mobile-tools .js-share-toggle').isVisible(),'Mobile Share tool is not visible');
  assert(await ma.locator('.mobile-tools .js-save-toggle').isVisible(),'Mobile Save tool is not visible');
  assert(await ma.locator('.mobile-tools .js-text-toggle').isVisible(),'Mobile Text tool is not visible');

  await ma.locator('.mobile-tools .js-share-toggle').click();
  assert(await ma.locator('.mobile-tools .js-share-popover').isVisible(),'Mobile Share bottom sheet did not open');
  await ma.keyboard.press('Escape');
  assert(!(await ma.locator('.mobile-tools .js-share-popover').isVisible()),'Mobile Share bottom sheet did not close');

  await ma.locator('.mobile-tools .js-save-toggle').click();
  assert(await ma.locator('.mobile-tools .js-save-popover').isVisible(),'Mobile Save bottom sheet did not open');
  await ma.locator('.mobile-tools .js-browser-save[data-save-action="bookmark"]').click();
  assert((await ma.locator('.mobile-rail .tool-status').textContent()).includes('browser menu'),'Mobile bookmark helper did not provide touch-friendly guidance');
  await ma.locator('.mobile-tools .js-save-toggle').click();
  await ma.locator('.mobile-tools .js-browser-save[data-save-action="save"]').click();
  assert((await ma.locator('.mobile-rail .tool-status').textContent()).includes('Share or menu'),'Mobile save helper did not provide touch-friendly guidance');
  await ma.locator('.mobile-tools .js-save-toggle').click();
  assert(await ma.locator('.mobile-tools .js-save-popover').isVisible(),'Mobile Save bottom sheet did not reopen');
  await ma.keyboard.press('Escape');
  assert(!(await ma.locator('.mobile-tools .js-save-popover').isVisible()),'Mobile Save bottom sheet did not close');

  await ma.locator('.mobile-tools .js-text-toggle').click();
  assert(await ma.locator('.mobile-tools .js-text-popover').isVisible(),'Mobile Text bottom sheet did not open');
  const mobileBefore=parseFloat(await ma.locator('#article-content').evaluate(el=>getComputedStyle(el).fontSize));
  const mobileReadoutBefore=parseInt(await ma.locator('.mobile-tools .js-size-readout').textContent(),10);
  await ma.locator('.mobile-tools .js-larger').click();
  const mobileReadoutAfter=parseInt(await ma.locator('.mobile-tools .js-size-readout').textContent(),10);
  const mobileAfter=parseFloat(await ma.locator('#article-content').evaluate(el=>getComputedStyle(el).fontSize));
  assert(mobileReadoutAfter===Math.min(21,mobileReadoutBefore+1),'Mobile increase text-size control did not update the readout');
  assert(mobileAfter>mobileBefore,'Mobile text-size control changed the readout but not the rendered article font size');
  await ma.keyboard.press('Escape');
  assert(!(await ma.locator('.mobile-tools .js-text-popover').isVisible()),'Mobile Text bottom sheet did not close');

  const sections=ma.locator('#article-content section[id]');
  assert(await sections.count()>1,'Article has too few sections for scroll navigation test');
  await ma.evaluate(()=>{
    const section=document.querySelectorAll('#article-content section[id]')[1];
    section?.scrollIntoView({behavior:'auto',block:'start'});
    window.dispatchEvent(new Event('scroll'));
  });
  await wait(350);
  const progress=ma.locator('#acx-scroll-progress');
  assert(await progress.isVisible(),'Mobile floating scroll navigation did not become visible');
  await ma.locator('#acx-scroll-progress-toggle').click();
  assert((await ma.locator('#acx-scroll-progress-toggle').getAttribute('aria-expanded'))==='true','Scroll navigation did not expand');
  const items=ma.locator('.scroll-progress-item');
  assert(await items.count()>1,'Scroll navigation has no section items');
  const target=await items.nth(1).getAttribute('data-target');
  await items.nth(1).click();
  await wait(850);
  assert((await ma.locator('#acx-scroll-progress-toggle').getAttribute('aria-expanded'))==='false','Scroll navigation did not close after selecting a section');
  assert((new URL(ma.url())).hash==='#'+target,'Scroll navigation did not update the URL hash');
  await maCtx.close();

  console.log('Interaction smoke test passed: header controls, install guidance, search, mobile menu, sliders, article tools, language tabs, text controls, share/copy/save/print, and mobile section navigation.');
} finally {
  await browser.close();
}
