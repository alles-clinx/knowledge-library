/* Eleven by Alle's ClinX — one in-page player, three independent controls. */
(function(){
  'use strict';
  const section=document.getElementById('eleven');
  if(!section) return;
  const buttons=[...section.querySelectorAll('.eleven-play[data-audio-src]')];
  if(!buttons.length) return;
  const audio=new Audio();
  audio.preload='none';
  let active=null;
  const validSource=function(url){
    try{
      const parsed=new URL(url);
      return parsed.protocol==='https:' && (parsed.hostname==='rss.com'||parsed.hostname.endsWith('.rss.com')||parsed.hostname.endsWith('.rsscdn.com'));
    }catch(_){return false;}
  };
  const formatTime=function(seconds){
    if(!Number.isFinite(seconds)||seconds<0) return '0:00';
    const rounded=Math.floor(seconds);
    const hours=Math.floor(rounded/3600);
    const minutes=Math.floor((rounded%3600)/60);
    const secs=String(rounded%60).padStart(2,'0');
    return (hours?hours+':'+String(minutes).padStart(2,'0'):String(minutes))+':'+secs;
  };
  const parent=function(button){return button.closest('.eleven-episode');};
  const updateProgress=function(){
    if(!active)return;
    const root=parent(active);
    const seek=root.querySelector('.eleven-seek');
    const elapsed=root.querySelector('.eleven-play-time');
    const estimate=Number(active.dataset.durationSeconds||0);
    const length=Number.isFinite(audio.duration)&&audio.duration>0?audio.duration:estimate;
    const current=Number.isFinite(audio.currentTime)?audio.currentTime:0;
    if(seek)seek.value=length?String(Math.min(1000,Math.round(current/length*1000))):'0';
    if(elapsed)elapsed.textContent=formatTime(current)+' / '+formatTime(length);
  };
  const syncButtons=function(){
    for(const button of buttons){
      const isActive=button===active;
      const isPlaying=isActive&&!audio.paused&&!audio.ended;
      button.dataset.playing=isPlaying?'true':'false';
      button.setAttribute('aria-pressed',isPlaying?'true':'false');
      const title=parent(button)?.querySelector('h3')?.textContent?.trim()||'episode';
      button.setAttribute('aria-label',(isPlaying?'Pause ':'Play ')+title);
      button.title=isPlaying?'Pause episode':'Play episode';
      const label=parent(button)?.querySelector('.eleven-play-label');
      if(label)label.textContent=isPlaying?'Pause':'Play episode';
      const progress=parent(button)?.querySelector('.eleven-progress');
      if(progress)progress.hidden=!isActive;
    }
    updateProgress();
  };
  buttons.forEach(function(button){
    const url=button.getAttribute('data-audio-src');
    if(!validSource(url)){
      button.hidden=true;
      return;
    }
    button.addEventListener('click',function(){
      if(active===button&&!audio.paused){
        audio.pause();
        syncButtons();
        return;
      }
      if(active!==button){
        audio.pause();
        active=button;
        audio.src=url;
        audio.preload='metadata';
      }
      syncButtons();
      const started=audio.play();
      if(started&&typeof started.catch==='function'){
        started.catch(function(){
          if(active!==button)return;
          audio.pause();
          syncButtons();
          const label=parent(button)?.querySelector('.eleven-play-label');
          if(label)label.textContent='Audio unavailable here';
        });
      }
    });
    const seek=parent(button)?.querySelector('.eleven-seek');
    seek?.addEventListener('input',function(){
      if(active!==button)return;
      const length=Number.isFinite(audio.duration)&&audio.duration>0?audio.duration:Number(button.dataset.durationSeconds||0);
      if(length>0)audio.currentTime=Math.min(length,length*Number(seek.value)/1000);
      updateProgress();
    });
  });
  for(const event of ['playing','play','pause','ended','loadedmetadata','durationchange','timeupdate','seeking','seeked']){
    audio.addEventListener(event,function(){
      if(event==='ended'&&active){
        audio.currentTime=0;
      }
      syncButtons();
    });
  }
  audio.addEventListener('error',function(){
    audio.pause();
    syncButtons();
    if(active){
      const label=parent(active)?.querySelector('.eleven-play-label');
      if(label)label.textContent='Audio unavailable here';
    }
  });
  syncButtons();
})();