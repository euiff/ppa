(()=>{
  'use strict';
  const TOKEN_KEY='escala-facil.auth-token';
  const POLL_MS=20000;
  const SEEN_PREFIX='escala-app-native-seen:';
  let lastCount=-1;
  let timer=null;
  function token(){try{return localStorage.getItem(TOKEN_KEY)||'';}catch{return '';}}
  function nativeBridge(){return window.EscalaNative||null;}
  function setBadge(count){
    count=Math.max(0,Number(count)||0);
    try{
      const n=nativeBridge();
      if(n&&typeof n.setBadge==='function'){n.setBadge(count);}
      else if(count>0&&navigator.setAppBadge){navigator.setAppBadge(count).catch(()=>{});}
      else if(count===0&&navigator.clearAppBadge){navigator.clearAppBadge().catch(()=>{});}
    }catch(e){console.warn('[EscalaApp] badge falhou',e);}
    let el=document.getElementById('escala-app-pending-badge');
    if(count<=0){if(el)el.remove();return;}
    if(!el){
      el=document.createElement('div');
      el.id='escala-app-pending-badge';
      el.style.cssText='position:fixed;right:16px;bottom:92px;z-index:2147483640;background:#dc2626;color:#fff;border-radius:999px;min-width:28px;height:28px;padding:0 8px;display:flex;align-items:center;justify-content:center;font:800 13px system-ui;box-shadow:0 8px 24px rgba(220,38,38,.35);border:2px solid #fff;pointer-events:none';
      document.body.appendChild(el);
    }
    el.textContent=count>99?'99+':String(count);
    el.title=count+' pendência(s) no aplicativo';
  }
  function stripSupabaseMigration(){
    try{
      document.querySelectorAll('a[href*="migracao-supabase"],a[href*="migration-supabase"]').forEach(a=>{
        const item=a.closest('li,div,[role="menuitem"]');
        if(item&&item!==document.body)item.remove();else a.remove();
      });
      document.querySelectorAll('a,button,span,div').forEach(el=>{
        if(el.children.length===0&&/migra[cç][aã]o\s+supabase/i.test((el.textContent||'').trim())){
          const clickable=el.closest('a,button');if(clickable)clickable.remove();
        }
      });
    }catch(e){}
  }
  async function browserNotify(title,body,url,count){
    try{
      const n=nativeBridge();
      if(n&&typeof n.notify==='function'){n.notify(String(title||'Escala de Propósito'),String(body||''),String(url||'/'),Number(count)||1);return;}
      if(!('Notification' in window))return;
      if(Notification.permission==='granted'){
        const reg=await navigator.serviceWorker?.getRegistration?.();
        if(reg?.showNotification){
          await reg.showNotification(title,{body,icon:'/icon-192.png',badge:'/icon-192.png',tag:'escala-pendente-'+String(url||''),renotify:true,data:{url:url||'/'}});
        }else{
          const nt=new Notification(title,{body,icon:'/icon-192.png',tag:'escala-pendente'});
          nt.onclick=()=>{window.focus();location.href=url||'/';};
        }
      }
    }catch(e){console.warn('[EscalaApp] notify falhou',e);}
  }
  function seenKey(){const t=token();return SEEN_PREFIX+(t?t.slice(-12):'anon');}
  function getSeen(){try{const v=JSON.parse(localStorage.getItem(seenKey())||'[]');return Array.isArray(v)?v:[];}catch{return [];}}
  function saveSeen(v){try{localStorage.setItem(seenKey(),JSON.stringify(v.slice(-300)));}catch{}}
  async function fetchPending(){
    const t=token();
    if(!t){setBadge(0);return;}
    try{
      const res=await fetch('/api/app-pending.php',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Bearer '+t},body:'{}',cache:'no-store'});
      const json=await res.json().catch(()=>null);
      if(!res.ok||!json||json.error)throw new Error(json?.error?.message||('HTTP '+res.status));
      const data=json.data||{},items=Array.isArray(data.items)?data.items:[],count=Number(data.count)||0;
      setBadge(count);
      if(count!==lastCount){window.dispatchEvent(new CustomEvent('escala-pending-count',{detail:{count,items}}));lastCount=count;}
      const seen=getSeen(),seenSet=new Set(seen),fresh=items.filter(i=>i&&i.id&&!seenSet.has(i.id));
      for(const item of fresh){
        await browserNotify(item.title||'Nova pendência',item.message||'Você possui uma nova pendência no Escala de Propósito.',item.url||'/',count);
        seen.push(item.id);seenSet.add(item.id);
      }
      if(fresh.length)saveSeen(seen);
      const active=new Set(items.map(i=>i.id));
      saveSeen(seen.filter(id=>active.has(id)||!String(id).startsWith('escala:')));
    }catch(e){console.warn('[EscalaApp] falha ao consultar pendências',e);}
  }
  function start(){stripSupabaseMigration();if(timer)clearInterval(timer);fetchPending();timer=setInterval(fetchPending,POLL_MS);}
  document.addEventListener('DOMContentLoaded',()=>{start();const mo=new MutationObserver(stripSupabaseMigration);mo.observe(document.documentElement,{subtree:true,childList:true});});
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)fetchPending();});
  window.addEventListener('focus',fetchPending);
  window.addEventListener('online',fetchPending);
  window.addEventListener('escala-app-refresh-pending',fetchPending);
  window.EscalaAppNotifications={refresh:fetchPending,setBadge};
})();