import { chromium } from 'playwright';
import fs from 'node:fs';

const BASE = process.env.BASE_URL || 'http://127.0.0.1:4173/knowledge/';
const ORIGIN = new URL(BASE).origin;
const records = JSON.parse(fs.readFileSync('docs/assets/live-search.json','utf8')).records || [];
const sitemapXml = fs.readFileSync('docs/sitemap.xml','utf8');
const en = [...records].reverse().find(r => r.locale === 'en');
const hi = en ? records.find(r => r.article_id === en.article_id && r.locale === 'hi-IN') : null;

assert(sitemapXml.includes('<urlset'),'XML sitemap is missing its urlset root');
assert(!sitemapXml.includes('/knowledge-library/sitemap/'),'Removed human sitemap remains in XML sitemap');
assert(!sitemapXml.includes('/knowledge-library/about/'),'Retired About pages remain in XML sitemap');
assert(sitemapXml.includes('/knowledge-library/library/'),'Knowledge category routes missing from XML sitemap');

function assert(value, message){
  if(!value) throw new Error(message);
}
function articleUrl(record){
  return new URL(String(record.url || '').replace(/^\/+/,''), BASE).href;
}
async function wait(ms=180){ await new Promise(r=>setTimeout(r,ms)); }

async function assertMobileViewportIntegrity(page,label){
  const result=await page.evaluate(()=>{
    const root=document.documentElement;
    const body=document.body;
    const viewportWidth=window.innerWidth;
    const documentWidth=Math.max(root.scrollWidth,body?.scrollWidth||0);
    const header=document.querySelector('.acx-site-header');
    const headerRect=header ? header.getBoundingClientRect() : null;
    return {
      viewportWidth,
      documentWidth,
      header:headerRect ? {left:headerRect.left,right:headerRect.right,width:headerRect.width} : null
    };
  });
  assert(result.documentWidth<=result.viewportWidth+2,
    label+' has horizontal page overflow: '+result.documentWidth+'px document vs '+result.viewportWidth+'px viewport');
  if(result.header){
    assert(result.header.left>=-1,label+' header extends past the left viewport edge');
    assert(result.header.right<=result.viewportWidth+1,label+' header extends past the right viewport edge');
  }
}

const browser = await chromium.launch({headless:true});
try{
  const desktop = await browser.newContext({viewport:{width:1366,height:900}});
  await desktop.grantPermissions(['clipboard-read','clipboard-write'], {origin:ORIGIN});
  // Simulate the media transport without downloading a large external MP3 in CI.
  await desktop.addInitScript(function(){
    window.Audio=class FakeAudio extends EventTarget{
      constructor(){super();this.paused=true;this.ended=false;this.currentTime=0;this.duration=3600;this.src='';this.preload='none';}
      play(){this.paused=false;this.dispatchEvent(new Event('playing'));return Promise.resolve();}
      pause(){this.paused=true;this.dispatchEvent(new Event('pause'));}
    };
  });
  const page = await desktop.newPage();
  await page.goto(BASE,{waitUntil:'networkidle'});
  assert(await page.locator('.acx-site-header').isVisible(),'Desktop site header is not visible');
  assert(await page.locator('.acx-search-button').isVisible(),'Desktop Search button is not visible');
  assert(await page.locator('.acx-site-header').count()===1,'Duplicate shared header');
  assert(await page.locator('.acx-header-library svg').count()===1,'Open-book Library icon missing');
  assert(await page.locator('.acx-header-sitemap').count()===0,'Redundant Sitemap icon returned');
  assert(await page.locator('.acx-header-library .acx-header-label').count()===0,'Library text must not appear in the header');
  assert(await page.locator('.acx-install-app svg').count()===1,'Install must use an SVG icon');
  assert((await page.locator('.acx-install-app').textContent()).trim()==='','Install must be icon-only');
  const headerVisual=await page.locator('.acx-site-header').evaluate(el=>{
    const style=getComputedStyle(el);
    return {top:style.top,shadow:style.boxShadow,radius:style.borderRadius,blur:style.backdropFilter};
  });
  assert(headerVisual.top==='0px','Header is not flush against the top of the viewport');
  assert(headerVisual.shadow==='none','Header must not have a shadow');
  assert(headerVisual.radius==='0px','Header must not have rounded corners');
  assert(headerVisual.blur==='none','Header must not have backdrop blur');
  const searchSvgWidth=await page.locator('.acx-search-button svg').evaluate(el=>parseFloat(getComputedStyle(el).width));
  assert(searchSvgWidth>=23,'Search SVG should be visibly larger');
  assert((await page.locator('.acx-header-library').getAttribute('href'))===new URL('#browse-title',BASE).pathname+'#browse-title','Library icon destination incorrect');
  assert(await page.locator('.acx-site-header').evaluate(el=>getComputedStyle(el).position)==='fixed','Header must remain fixed');
  await page.evaluate(()=>window.scrollTo(0,700));
  await wait(350);
  assert(await page.locator('.acx-site-header').evaluate(el=>el.classList.contains('is-hidden')),'Header did not hide on downward scroll');
  await page.evaluate(()=>window.scrollTo(0,300));
  await wait(350);
  assert(await page.locator('.acx-site-header').evaluate(el=>!el.classList.contains('is-hidden')),'Header did not return on upward scroll');
  await page.evaluate(()=>window.scrollTo(0,0));
  await wait(180);
  // Eleven belongs on the homepage between reading recommendations and categories.
  // Hover treatments add a four-pixel optical inset but never move the entire clickable row.
  async function checkHoverInset(targetPage,rowSelector,childSelector,label){
    const row=targetPage.locator(rowSelector).first();
    assert(await row.count()===1,label+' row missing');
    await row.scrollIntoViewIfNeeded();
    await targetPage.mouse.move(1,1);
    await wait(260);
    const measure=()=>row.evaluate((el,selector)=>{
      const child=el.querySelector(selector);
      if(!child)return null;
      const outer=el.getBoundingClientRect();
      const inner=child.getBoundingClientRect();
      return {left:outer.left,width:outer.width,innerInset:inner.left-outer.left};
    },childSelector);
    const before=await measure();
    assert(before,label+' inset target missing');
    await row.hover();
    await wait(260);
    const after=await measure();
    assert(after.innerInset-before.innerInset>=3.2&&after.innerInset-before.innerInset<=5.1,
      label+' should receive a subtle 4px hover inset: '+(after.innerInset-before.innerInset).toFixed(2));
    assert(Math.abs(after.left-before.left)<1&&Math.abs(after.width-before.width)<1,
      label+' changed its hit target or outer position during hover');
    await targetPage.mouse.move(1,1);
  }
  await checkHoverInset(page,'.editorial-item','div:first-child','Trending article');
  await checkHoverInset(page,'.quick-item','strong','Quick read');
  await checkHoverInset(page,'.category','strong','Homepage category');
  const footerHover=page.locator('.acx-footer-nav a').first();
  await footerHover.scrollIntoViewIfNeeded();
  await page.mouse.move(1,1);
  const footerBase=await footerHover.evaluate(el=>({pad:parseFloat(getComputedStyle(el).paddingLeft),left:el.getBoundingClientRect().left}));
  await footerHover.hover();await wait(260);
  const footerNow=await footerHover.evaluate(el=>({pad:parseFloat(getComputedStyle(el).paddingLeft),left:el.getBoundingClientRect().left}));
  assert(Math.abs((footerNow.pad-footerBase.pad)-4)<=.5,'Footer hover lacks a 4px internal left inset');
  assert(Math.abs(footerNow.left-footerBase.left)<1,'Footer hover moved its click target');
  await page.mouse.move(1,1);
  const podcast=page.locator('#eleven');
  assert(await podcast.count()===1,'Eleven podcast section missing');
  assert((await podcast.locator('h2').textContent()).trim()==='Eleven','Podcast heading incorrect');
  assert(await podcast.locator('.eleven-episode').count()===3,'Latest episodes shelf must show exactly three episodes');
  assert(await podcast.locator('.eleven-play').count()===3,'Every podcast episode needs a Play/Pause control');
  assert(await podcast.locator('.eleven-play > .eleven-play-label').count()===3,'Play/Pause label should be inside its fixed-width control');
  const transportAppearance=await podcast.locator('.eleven-play').first().evaluate(el=>{
    const style=getComputedStyle(el);
    const icon=getComputedStyle(el.querySelector('svg'));
    return {width:el.getBoundingClientRect().width,height:el.getBoundingClientRect().height,
      radius:style.borderRadius,display:style.display,iconWidth:parseFloat(icon.width),
      state:el.dataset.state,label:el.querySelector('.eleven-play-label').textContent};
  });
  assert(transportAppearance.width>=110&&transportAppearance.width<=114,'Player button should have stable 112px width');
  assert(transportAppearance.height===44,'Play/Pause control needs a 44px touch target');
  assert(transportAppearance.iconWidth>=18,'Playback icon should be clearly visible');
  assert(transportAppearance.state==='idle'&&transportAppearance.label==='Play','Player initial state should be Play');
  assert(await podcast.locator('.eleven-progress[hidden]').count()===3,'Episode progress should be hidden until playback starts');
  assert((await podcast.locator('.eleven-play').first().getAttribute('data-audio-src')).startsWith('https://content.rss.com/episodes/'),'Podcast must use verified RSS MP3 audio');
  assert((await podcast.locator('.eleven-source-link').first().getAttribute('href')).startsWith('https://podcasts.apple.com/'),'Apple should remain a secondary episode link');
  assert(await page.locator('.acx-bottom-brand,.legal-bottom-brand').count()===0,'Ghost brand wordmark must be removed');
  assert(await page.locator('.section-head').first().evaluate(el=>getComputedStyle(el).borderBottomWidth)==='0px','Decorative section heading dividers must be removed');
  // Playback must never move a button, its card, or its reserved seek row.
  const episodeGeometry=async targetPage=>targetPage.locator('#eleven .eleven-episode').evaluateAll(cards=>cards.map(card=>{
    const button=card.querySelector('.eleven-play').getBoundingClientRect();
    const rect=card.getBoundingClientRect();
    return {
      playX:button.left,playY:button.top+window.scrollY,
      cardY:rect.top+window.scrollY,cardHeight:rect.height,
      progressHeight:card.querySelector('.eleven-progress').getBoundingClientRect().height
    };
  }));
  const sameEpisodeGeometry=(before,after,label)=>{
    assert(before.length===after.length,label+' changed the number of episode cards');
    for(let i=0;i<before.length;i++){
      for(const property of ['playX','playY','cardY','cardHeight','progressHeight']){
        assert(Math.abs(before[i][property]-after[i][property])<=1,
          label+' shifted an episode control/card: '+property+' of episode '+i+' ('+before[i][property]+' → '+after[i][property]+')');
      }
    }
  };
  const initialEpisodeGeometry=await episodeGeometry(page);
  assert(initialEpisodeGeometry.every(g=>g.progressHeight>=23),'Playback progress must reserve its space while inactive');
  const firstPlay=podcast.locator('.eleven-play').nth(0);
  const secondPlay=podcast.locator('.eleven-play').nth(1);
  await firstPlay.click();
  sameEpisodeGeometry(initialEpisodeGeometry,await episodeGeometry(page),'Play');
  assert(await firstPlay.getAttribute('aria-pressed')==='true','Play did not start in-page audio');
  assert(await firstPlay.getAttribute('data-state')==='playing','Player should expose playing state');
  assert((await firstPlay.locator('.eleven-play-label').textContent())==='Pause','Button label should change to Pause in place');
  assert(await podcast.locator('.eleven-progress:not([hidden])').count()===1,'Active episode progress must be visible');
  await firstPlay.click();
  sameEpisodeGeometry(initialEpisodeGeometry,await episodeGeometry(page),'Pause');
  assert(await firstPlay.getAttribute('aria-pressed')==='false','Pause did not stop in-page audio');
  assert(await firstPlay.getAttribute('data-state')==='paused','Player should retain paused state');
  assert((await firstPlay.locator('.eleven-play-label').textContent())==='Resume','Paused control should offer Resume');
  assert(await podcast.locator('.eleven-progress:not([hidden])').count()===1,'Paused progress should remain available');
  const progressCheck=await podcast.locator('.eleven-progress:not([hidden]) .eleven-seek').first().evaluate(el=>{
    const computed=getComputedStyle(el);
    return {appearance:computed.appearance,aria:el.getAttribute('aria-valuetext'),
      fill:el.style.getPropertyValue('--eleven-seek-fill')};
  });
  assert(progressCheck.appearance==='none','Podcast should use custom minimal progress track');
  assert(progressCheck.aria.includes(' of ')&&progressCheck.fill.endsWith('%'),'Seek bar lacks accessible playback progress');
  await firstPlay.click();
  await secondPlay.click();
  sameEpisodeGeometry(initialEpisodeGeometry,await episodeGeometry(page),'Switch episode');
  assert(await firstPlay.getAttribute('aria-pressed')==='false'&&await secondPlay.getAttribute('aria-pressed')==='true','Starting another episode must pause previous audio');
  await secondPlay.click();
  assert(await podcast.locator('.eleven-show-link').getAttribute('href')==='https://podcasts.apple.com/us/podcast/eleven-by-alles-clinx/id1875218821','Show Apple Podcasts link incorrect');
  assert(await page.locator('script[src*="eleven.js"]').count()===1,'Podcast catalogue refresh script missing');
  const homeSections=await page.locator('main.page > section').evaluateAll(sections=>sections.map(section=>section.id||section.className));
  const podcastIndex=homeSections.indexOf('eleven');
  assert(podcastIndex===2 && homeSections[podcastIndex+1]==='library','Eleven must appear after Quick reads and before categories');
  assert(await page.locator('.acx-menu-button,#acx-mobile-drawer').count()===0,'Menu navigation must be removed on desktop');
  assert(await page.locator('.acx-skip-link').count()===1,'Skip-to-content link is missing');
  assert(await page.locator('#main-content').count()===1,'Main content target is missing');
  assert((await page.locator('#acx-site-footer a').first().getAttribute('aria-current'))==='page','Home footer link is not marked current');
  await page.locator('.acx-skip-link').focus();
  assert(await page.locator('.acx-skip-link').isVisible(),'Skip-to-content link is not visible on focus');
  await page.keyboard.press('Enter');
  await wait(80);
  assert(await page.locator('#main-content').evaluate(el=>el===document.activeElement),'Skip-to-content did not move focus to main content');
  const installButton=page.locator('.acx-install-app');
  assert(await installButton.isVisible(),'Desktop Install button is not visible');
  await installButton.click();
  assert(await page.locator('.acx-install-note').isVisible(),'Install fallback guidance did not appear');
  assert((await page.locator('.acx-install-note').textContent()).trim().length>0,'Install fallback guidance is empty');
  const desktopSearchButton=page.locator('.acx-search-button');
  await desktopSearchButton.click();
  assert(await page.locator('.acx-search-dialog.is-open').isVisible(),'Search dialog did not open');
  await page.locator('.acx-search-input').fill('stainless');
  await wait(250);
  assert(await page.locator('.acx-search-result').count()>0,'Search produced no results');
  await checkHoverInset(page,'.acx-search-result','.acx-search-result-main','Search result');
  const lastSearchResult=page.locator('.acx-search-result').last();
  await lastSearchResult.focus();
  await page.keyboard.press('Tab');
  assert(await page.locator('.acx-search-input').evaluate(el=>el===document.activeElement),'Search dialog keyboard loop did not return to the first control');
  await page.locator('.acx-search-close').click();
  assert(!(await page.locator('.acx-search-dialog').isVisible()),'Search close button did not close the dialog');
  assert(await desktopSearchButton.evaluate(el=>el===document.activeElement),'Search did not restore focus to its trigger');

  await desktopSearchButton.click();
  assert(await page.locator('.acx-search-dialog.is-open').isVisible(),'Search dialog did not reopen');
  await page.keyboard.press('Escape');
  assert(!(await page.locator('.acx-search-dialog').isVisible()),'Search dialog did not close with Escape');
  assert(await desktopSearchButton.evaluate(el=>el===document.activeElement),'Escape did not restore search trigger focus');

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
  const discoveryPage=await desktop.newPage();
  await discoveryPage.goto(new URL('library/cleaning-housekeeping/',BASE).href,{waitUntil:'networkidle'});
  await checkHoverInset(discoveryPage,'.topic','strong','Topic listing');
  await discoveryPage.goto(new URL('library/cleaning-housekeeping/cleaning-basics/',BASE).href,{waitUntil:'networkidle'});
  await checkHoverInset(discoveryPage,'.article-row','strong','Article listing');
  await discoveryPage.goto(new URL('terms-conditions/',BASE).href,{waitUntil:'networkidle'});
  const legalHover=discoveryPage.locator('.legal-accordion summary').first();
  await legalHover.scrollIntoViewIfNeeded();
  await discoveryPage.mouse.move(1,1);
  const legalBefore=await legalHover.evaluate(el=>({left:el.getBoundingClientRect().left,pad:parseFloat(getComputedStyle(el).paddingLeft)}));
  await legalHover.hover();await wait(260);
  const legalAfter=await legalHover.evaluate(el=>({left:el.getBoundingClientRect().left,pad:parseFloat(getComputedStyle(el).paddingLeft)}));
  assert(Math.abs(legalAfter.pad-legalBefore.pad-4)<.7,'Legal summary missing 4px hover inset');
  assert(Math.abs(legalAfter.left-legalBefore.left)<1,'Legal summary shifted its row');
  await discoveryPage.goto(articleUrl(en),{waitUntil:'networkidle'});
  const tocHover=discoveryPage.locator('.toc a:visible').first();
  if(await tocHover.count()){
    await tocHover.scrollIntoViewIfNeeded();
    await discoveryPage.mouse.move(1,1);
    const tocBefore=await tocHover.evaluate(el=>parseFloat(getComputedStyle(el).paddingLeft));
    await tocHover.hover();await wait(260);
    const tocAfter=await tocHover.evaluate(el=>parseFloat(getComputedStyle(el).paddingLeft));
    assert(tocAfter-tocBefore>=3,'Article table-of-contents hover missing its left inset');
  }
  await discoveryPage.close();
  await desktop.close();

  const mobile = await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
  const mp = await mobile.newPage();
  await mp.goto(BASE,{waitUntil:'networkidle'});
  assert(await mp.locator('.acx-menu-button,#acx-mobile-drawer').count()===0,'Menu navigation must be removed on mobile');
  assert(await mp.locator('.acx-search-button').isVisible(),'Mobile Search button is not visible');
  assert(await mp.locator('.acx-header-library svg').count()===1,'Mobile Open-book Library icon missing');
  assert(await mp.locator('.acx-install-app svg').count()===1,'Mobile Install SVG icon is missing');
  assert(await mp.locator('.acx-site-header').evaluate(el=>getComputedStyle(el).top)==='0px','Mobile header must remain at the top');
  await mp.evaluate(()=>window.scrollTo(0,650));
  await wait(350);
  assert(await mp.locator('.acx-site-header').evaluate(el=>el.classList.contains('is-hidden')),'Mobile header did not hide');
  await mp.evaluate(()=>window.scrollTo(0,280));
  await wait(350);
  assert(await mp.locator('.acx-site-header').evaluate(el=>!el.classList.contains('is-hidden')),'Mobile header did not return');
  await mp.evaluate(()=>window.scrollTo(0,0));
  await wait(180);
  assert(await mp.locator('.acx-install-app').isVisible(),'Mobile Install button is not visible');
  const mobileSearchButton=mp.locator('.acx-search-button');
  await mobileSearchButton.click();
  assert(await mp.locator('.acx-search-dialog.is-open').isVisible(),'Mobile search did not open from header');
  await mp.keyboard.press('Escape');
  assert(!(await mp.locator('.acx-search-dialog').isVisible()),'Mobile search did not close with Escape');
  assert(await mobileSearchButton.evaluate(el=>el===document.activeElement),'Mobile search did not restore focus to Search after closing');
  await mobile.close();

  assert(en,'No English live article found for interaction smoke test');

  const mobileAuditRoutes=[
    ['home',BASE],
    ['category',new URL('library/cleaning-housekeeping/',BASE).href],
    ['subcategory',new URL('library/cleaning-housekeeping/cleaning-basics/',BASE).href],
    ['article',articleUrl(en)],
    ['legal terms',new URL('terms-conditions/',BASE).href],
    ['legal privacy',new URL('privacy-policy/',BASE).href],
  ];
  for(const width of [320,360,390,430]){
    const auditCtx=await browser.newContext({viewport:{width,height:844},isMobile:true,hasTouch:true});
    await auditCtx.addInitScript(function(){
      window.Audio=class FakeAudio extends EventTarget{
        constructor(){super();this.paused=true;this.ended=false;this.currentTime=0;this.duration=3600;this.src='';this.preload='none';}
        play(){this.paused=false;this.dispatchEvent(new Event('playing'));return Promise.resolve();}
        pause(){this.paused=true;this.dispatchEvent(new Event('pause'));}
      };
    });
    const auditPage=await auditCtx.newPage();
    for(const [label,url] of mobileAuditRoutes){
      await auditPage.goto(url,{waitUntil:'networkidle'});
      assert((await auditPage.locator('meta[name="viewport"]').getAttribute('content')||'').includes('width=device-width'),
        label+' is missing a mobile viewport declaration');
      assert(await auditPage.locator('.acx-skip-link').count()===1,label+' is missing the shared skip link');
      assert(await auditPage.locator('.acx-bottom-brand,.legal-bottom-brand').count()===0,label+' retains ghost brand text');
      if(label==='category'||label==='subcategory'){
        const visibleRow=auditPage.locator('.category,.topic,.article-row').first();
        if(await visibleRow.count())assert(await visibleRow.evaluate(el=>getComputedStyle(el).borderBottomWidth)==='0px',label+' has distracting row dividers');
      }
      assert(await auditPage.locator('#main-content').count()===1,label+' is missing the shared main target');
      const scrollPadding=parseFloat(await auditPage.locator('html').evaluate(el=>getComputedStyle(el).scrollPaddingTop));
      assert(scrollPadding>0,label+' is missing fixed-header scroll padding');
      await assertMobileViewportIntegrity(auditPage,label+' at '+width+'px');
      assert(await auditPage.locator('.acx-header-library').count()===1,label+' Library shortcut missing');
      if(label==='home'){
        assert(await auditPage.locator('#eleven .eleven-episode').count()===3,'Mobile Eleven episodes missing');
        assert(await auditPage.locator('#eleven .eleven-play').count()===3,'Mobile Play/Pause buttons missing');
        const mobileTransport=await auditPage.locator('#eleven .eleven-play').first().boundingBox();
        assert(mobileTransport.width>=110&&mobileTransport.height>=44,'Mobile Play/Pause touch target is too small at '+width+'px');
        const beforePlayback=await episodeGeometry(auditPage);
        assert(beforePlayback.every(g=>g.progressHeight>=23),'Mobile seek controls did not reserve space at '+width+'px');
        const mobilePlayButton=auditPage.locator('#eleven .eleven-play').first();
        await mobilePlayButton.click();
        sameEpisodeGeometry(beforePlayback,await episodeGeometry(auditPage),'Mobile play at '+width+'px');
        await mobilePlayButton.click();
        sameEpisodeGeometry(beforePlayback,await episodeGeometry(auditPage),'Mobile pause at '+width+'px');
        const shelfFits=await auditPage.locator('#eleven').evaluate(el=>el.getBoundingClientRect().right<=window.innerWidth+1);
        assert(shelfFits,label+' Eleven section exceeds the mobile viewport');
      }
      assert(await auditPage.locator('.acx-install-app svg').count()===1,label+' Install icon missing');
      const hitBoxes=await auditPage.locator('.acx-header-library,.acx-search-button,.acx-install-app').evaluateAll(items=>items.map(item=>({
        width:item.getBoundingClientRect().width,
        height:item.getBoundingClientRect().height
      })));
      assert(hitBoxes.every(box=>box.width>=44&&box.height>=44),label+' icon hit targets are smaller than 44px');
      assert(await auditPage.locator('.acx-site-header').evaluate(el=>getComputedStyle(el).boxShadow)==='none',label+' header shadow regressed');
      assert(await auditPage.locator('.acx-site-actions').evaluate(el=>el.getBoundingClientRect().right<=window.innerWidth+1),label+' icon group overflows viewport');
      assert(await auditPage.locator('.acx-menu-button,#acx-mobile-drawer').count()===0,label+' retains menu navigation');
      const h1=auditPage.locator('h1').first();
      if(await h1.count()){
        const box=await h1.boundingBox();
        assert(!box || box.width<=width+1,label+' H1 exceeds the '+width+'px viewport');
      }
      const footerPalette=await auditPage.locator('#acx-site-footer').evaluate(el=>{
        const footerStyle=getComputedStyle(el);
        const brandStyle=getComputedStyle(el.querySelector('.acx-footer-brand'));
        return {background:footerStyle.backgroundColor,brand:brandStyle.color};
      });
      assert(footerPalette.background==='rgb(249, 249, 249)',label+' footer must use #f9f9f9');
      assert(footerPalette.brand==='rgb(20, 20, 22)',label+' footer brand text must remain readable');
      const footer=auditPage.locator('#acx-site-footer');
      assert(await footer.count()===1,label+' is missing the shared footer');
      const footerBox=await footer.boundingBox();
      assert(!footerBox || footerBox.width<=width+1,label+' footer exceeds the '+width+'px viewport');
      const footerLegalLinks=auditPage.locator('#acx-site-footer .acx-footer-group').nth(1).locator('a');
      assert(await footerLegalLinks.count()===2,label+' footer must have only Privacy and Terms');
      const footerTarget=auditPage.locator('#acx-site-footer .acx-footer-nav a').first();
      const footerTargetBox=await footerTarget.boundingBox();
      assert(!footerTargetBox || footerTargetBox.height>=40,label+' footer link target is too small on mobile');
    }
    await auditCtx.close();
  }

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

  console.log('Interaction smoke test passed: header controls, install guidance, search, open-book Library icon, sliders, article tools, language tabs, text controls, share/copy/save/print, mobile reading navigation, shared footer integrity, and 320–430px viewport coverage across home, discovery, article, and legal pages.');
} finally {
  await browser.close();
}
