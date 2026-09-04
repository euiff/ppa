(()=>{
  const ua=navigator.userAgent||'';
  const isNative=/Escala(?:De|Com)PropositoAndroid/i.test(ua);
  if(!isNative) return;

  const BRAND='Escala de Propósito';

  function norm(s){return (s||'').replace(/\s+/g,' ').trim();}

  function addSafeStyle(){
    if(document.getElementById('native-app-style-v1318')) return;
    const s=document.createElement('style');
    s.id='native-app-style-v1318';
    s.textContent=`
      html.native-app-mode,html.native-app-mode body{
        background:#f6f8fc!important;
        -webkit-tap-highlight-color:transparent;
      }
      html.native-app-mode *{box-sizing:border-box}
      html.native-app-mode button,
      html.native-app-mode a,
      html.native-app-mode [role="button"]{touch-action:manipulation}
      html.native-app-mode input,
      html.native-app-mode select,
      html.native-app-mode textarea{
        font-size:16px!important;
        border-radius:12px!important;
      }
      html.native-app-mode button{
        border-radius:12px!important;
      }
      html.native-app-mode .dashboard-hero{
        padding-left:14px!important;
        padding-right:14px!important;
      }
      html.native-app-mode .adaptive-grid{
        gap:12px!important;
        padding-left:12px!important;
        padding-right:12px!important;
      }
      html.native-app-mode .stat-card,
      html.native-app-mode .stat-card>div{
        border-radius:18px!important;
        box-shadow:0 6px 20px rgba(15,23,42,.055)!important;
        border-color:rgba(148,163,184,.16)!important;
      }
      @media(max-width:430px){
        html.native-app-mode .adaptive-grid{
          grid-template-columns:minmax(0,1fr)!important;
        }
        html.native-app-mode .dashboard-hero{
          padding-top:12px!important;
          padding-bottom:12px!important;
        }
      }
    `;
    document.head.appendChild(s);
  }

  function replaceBrand(root){
    root=root||document.body;
    if(!root) return;
    const w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
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

  function hideInstall(root){
    root=root||document;
    const els=root.querySelectorAll?root.querySelectorAll('a,button,[role="button"]'):[];
    for(const el of els){
      const t=norm(el.textContent).toLowerCase();
      if(t==='instalar aplicativo'||t==='instalar app'||t==='instalar o aplicativo'){
        el.style.setProperty('display','none','important');
      }
    }
  }

  function enhance(root){
    try{
      document.documentElement.classList.add('native-app-mode');
      if(document.body) document.body.classList.add('native-app-mode');
      addSafeStyle();
      replaceBrand(root||document.body);
      hideInstall(root||document);
    }catch(e){console.warn('native safe enhance',e);}
  }

  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded',()=>enhance(document.body),{once:true});
  }else{
    enhance(document.body);
  }

  let timer=null;
  const obs=new MutationObserver(mutations=>{
    clearTimeout(timer);
    timer=setTimeout(()=>{
      for(const m of mutations){
        for(const n of m.addedNodes){
          if(n.nodeType===1){
            replaceBrand(n);
            hideInstall(n);
          }else if(n.nodeType===3){
            const v=n.nodeValue||'';
            const nv=v.replace(/Escala com Propósito/g,BRAND).replace(/EscalaFacil/g,BRAND).replace(/Escala Fácil/g,BRAND).replace(/Escalas Top/g,BRAND);
            if(nv!==v)n.nodeValue=nv;
          }
        }
      }
    },120);
  });
  if(document.documentElement) obs.observe(document.documentElement,{subtree:true,childList:true});
})();
