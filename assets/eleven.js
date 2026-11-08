/* Eleven — one unobtrusive, accessible, in-page podcast transport. */
(function(){
  'use strict';
  const section=document.getElementById('eleven');
  if(!section)return;
  const buttons=[...section.querySelectorAll('.eleven-play[data-audio-src]')];
  if(!buttons.length)return;

  const audio=new Audio();
  audio.preload='none';
  let active=null;
  let pending=false;
  let failed=false;
  let playbackRequest=0;

  const validSource=function(url){
    try{
      const parsed=new URL(url);
      return parsed.protocol==='https:' &&
        (parsed.hostname==='rss.com'||parsed.hostname.endsWith('.rss.com')||parsed.hostname.endsWith('.rsscdn.com'));
    }catch(_){return false;}
  };
  const formatTime=function(seconds){
    if(!Number.isFinite(seconds)||seconds<0)return '0:00';
    const rounded=Math.floor(seconds);
    const hours=Math.floor(rounded/3600);
    const minutes=Math.floor((rounded%3600)/60);
    const secs=String(rounded%60).padStart(2,'0');
    return (hours?hours+':'+String(minutes).padStart(2,'0'):String(minutes))+':'+secs;
  };
  const cardFor=function(button){return button.closest('.eleven-episode');};
  const updateProgress=function(){
    if(!active)return;
    const card=cardFor(active);
    const seek=card.querySelector('.eleven-seek');
    const elapsed=card.querySelector('.eleven-play-time');
    const estimated=Number(active.dataset.durationSeconds||0);
    const length=Number.isFinite(audio.duration)&&audio.duration>0?audio.duration:estimated;
    const current=Number.isFinite(audio.currentTime)?Math.max(0,audio.currentTime):0;
    const progress=length?Math.min(1,current/length):0;
    if(seek){
      seek.value=String(Math.round(progress*1000));
      seek.style.setProperty('--eleven-seek-fill',(progress*100).toFixed(2)+'%');
      seek.setAttribute('aria-valuetext',formatTime(current)+' of '+formatTime(length));
    }
    if(elapsed)elapsed.textContent=formatTime(current)+' / '+formatTime(length);
  };
  const syncButtons=function(){
    for(const button of buttons){
      const selected=button===active;
      const playing=selected&&!pending&&!audio.paused&&!audio.ended&&!failed;
      const state=!selected?'idle':failed?'error':pending?'loading':playing?'playing':'paused';
      button.dataset.state=state;
      button.dataset.playing=playing?'true':'false';
      button.setAttribute('aria-pressed',playing?'true':'false');
      button.setAttribute('aria-busy',state==='loading'?'true':'false');
      const title=cardFor(button)?.querySelector('h3')?.textContent?.trim()||'episode';
      const names={
        idle:'Play',paused:'Resume',playing:'Pause',
        loading:'Loading',error:'Retry'
      };
      const label=cardFor(button)?.querySelector('.eleven-play-label');
      if(label)label.textContent=names[state];
      button.setAttribute('aria-label',
        (state==='loading'?'Loading ':state==='error'?'Audio unavailable for ':state==='playing'?'Pause ':state==='paused'?'Resume ':'Play ')+title);
      button.title=state==='error'?'Retry audio playback':names[state];
      const progress=cardFor(button)?.querySelector('.eleven-progress');
      if(progress)progress.hidden=!selected;
    }
    updateProgress();
  };
  const onPlayFailure=function(button,request){
    if(active!==button||request!==playbackRequest)return;
    pending=false;
    failed=true;
    audio.pause();
    syncButtons();
  };

  buttons.forEach(function(button){
    const src=button.getAttribute('data-audio-src');
    if(!validSource(src)){
      button.hidden=true;
      const unavailable=cardFor(button)?.querySelector('.eleven-play-label');
      if(unavailable)unavailable.textContent='Unavailable';
      return;
    }
    button.addEventListener('click',function(){
      if(active===button&&(pending||(!audio.paused&&!audio.ended))){
        playbackRequest++;
        pending=false;
        audio.pause();
        syncButtons();
        return;
      }
      if(active!==button){
        playbackRequest++;
        audio.pause();
        active=button;
        audio.src=src;
        audio.preload='metadata';
      }
      const request=++playbackRequest;
      pending=true;
      failed=false;
      syncButtons();
      try{
        const promise=audio.play();
        if(promise&&typeof promise.then==='function'){
          promise.then(function(){
            if(active===button&&request===playbackRequest){
              pending=false;
              syncButtons();
            }
          }).catch(function(){onPlayFailure(button,request);});
        }else{
          pending=false;
          syncButtons();
        }
      }catch(_){
        onPlayFailure(button,request);
      }
    });
    const seek=cardFor(button)?.querySelector('.eleven-seek');
    seek?.addEventListener('input',function(){
      if(active!==button)return;
      const length=Number.isFinite(audio.duration)&&audio.duration>0?audio.duration:Number(button.dataset.durationSeconds||0);
      if(length>0)audio.currentTime=Math.min(length,length*Number(seek.value)/1000);
      updateProgress();
    });
  });

  for(const event of ['play','playing','pause','loadedmetadata','durationchange','timeupdate','seeking','seeked','ended','waiting']){
    audio.addEventListener(event,function(){
      if(event==='playing')pending=false;
      if(event==='waiting'&&!audio.paused)pending=true;
      if(event==='ended'){
        pending=false;
        audio.currentTime=0;
      }
      syncButtons();
    });
  }
  audio.addEventListener('error',function(){
    if(!active)return;
    playbackRequest++;
    pending=false;
    failed=true;
    audio.pause();
    syncButtons();
  });
  syncButtons();
})();