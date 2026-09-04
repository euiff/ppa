(()=>{
  const ua=navigator.userAgent||'';
  const isNative=/Escala(?:De|Com)PropositoAndroid/i.test(ua);
  if(!isNative) return;

  const BRAND='Escala de Propósito';

  function cleanupNativeStyles(){
    const ids=[
      'native-app-style-v1317',
      'native-app-style-v1318',
      'native-app-recovery-v106',
      'native-app-style-v1319'
    ];
    for(const id of ids){
      const el=document.getElementById(id);
      if(el) el.remove();
    }

    document.documentElement.classList.remove('native-app-mode');
    if(document.body) document.body.classList.remove('native-app-mode','native-login-page');

    const styled=document.querySelectorAll('.native-bottom-nav,.native-top-header,.native-stat-card,.native-content-card,.native-login-card');
    styled.forEach(el=>el.classList.remove('native-bottom-nav','native-top-header','native-stat-card','native-content-card','native-login-card'));
  }

  function norm(s){return (s||'').replace(/\s+/g,' ').trim().toLowerCase();}

  function hideInstall(){
    const els=document.querySelectorAll('a,button,[role="button"]');
    for(const el of els){
      const t=norm(el.textContent);
      if(t==='instalar aplicativo'||t==='instalar app'||t==='instalar o aplicativo'){
        el.style.setProperty('display','none','important');
      }
    }
  }

  function replaceBrand(){
    if(!document.body) return;
    const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
    let n;
    while((n=w.nextNode())){
      const v=n.nodeValue||'';
      const nv=v
        .replace(/Escala com Propósito/g,BRAND)
        .replace(/EscalaFacil/g,BRAND)
        .replace(/Escala Fácil/g,BRAND)
        .replace(/Escalas Top/g,BRAND);
      if(nv!==v) n.nodeValue=nv;
    }
    if(document.title){
      document.title=document.title.replace(/Escala com Propósito|EscalaFacil|Escala Fácil|Escalas Top/g,BRAND);
    }
  }

  function sync(){
    try{
      cleanupNativeStyles();
      hideInstall();
      replaceBrand();
    }catch(e){console.warn('native parity sync',e);}
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',sync,{once:true});
  else sync();

  let timer=null;
  const obs=new MutationObserver(()=>{
    clearTimeout(timer);
    timer=setTimeout(sync,80);
  });
  if(document.documentElement) obs.observe(document.documentElement,{subtree:true,childList:true});
  setTimeout(sync,300);
  setTimeout(sync,1000);
})();
