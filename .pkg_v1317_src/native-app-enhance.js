(()=>{
  const ua=navigator.userAgent||'';
  const isNative=/Escala(?:De|Com)PropositoAndroid/i.test(ua);
  if(!isNative) return;

  const ROOT=document.documentElement;
  ROOT.classList.add('native-app-mode');
  const BRAND='Escala de Propósito';

  function norm(s){return (s||'').replace(/\s+/g,' ').trim();}
  function replaceTextNode(node){
    if(!node||node.nodeType!==3) return;
    const v=node.nodeValue||'';
    const n=v.replace(/Escala com Propósito/g,BRAND).replace(/EscalaFacil/g,BRAND).replace(/Escala Fácil/g,BRAND).replace(/Escalas Top/g,BRAND);
    if(n!==v) node.nodeValue=n;
  }
  function replaceBrand(root=document.body){
    if(!root) return;
    const w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
    let n; while((n=w.nextNode())) replaceTextNode(n);
    if(document.title) document.title=document.title.replace(/Escala com Propósito|EscalaFacil|Escala Fácil|Escalas Top/g,BRAND);
  }

  function hideInstall(){
    const els=[...document.querySelectorAll('a,button,[role="button"],div,span,p')];
    for(const el of els){
      const t=norm(el.textContent).toLowerCase();
      if(t==='instalar aplicativo' || t==='instalar app' || t==='instalar o aplicativo'){
        const target=el.closest('a,button,[role="button"]')||el;
        target.style.setProperty('display','none','important');
        const wrap=target.parentElement;
        if(wrap && norm(wrap.textContent).toLowerCase().includes('instalar aplicativo') && wrap.children.length<=2){
          wrap.style.setProperty('display','none','important');
        }
      }
    }
  }

  function commonAncestor(nodes){
    if(nodes.length<2) return null;
    let a=nodes[0];
    while(a && a!==document.body){
      if(nodes.every(n=>a.contains(n))) return a;
      a=a.parentElement;
    }
    return null;
  }

  function markBottomNav(){
    const wanted=['Home','Escalas','Louvor','Avisos'];
    const found=[];
    for(const label of wanted){
      const el=[...document.querySelectorAll('a,button')].find(x=>norm(x.textContent)===label);
      if(el) found.push(el);
    }
    if(found.length>=3){
      let nav=commonAncestor(found);
      if(nav){
        while(nav.parentElement && nav.parentElement!==document.body && nav.clientHeight<52) nav=nav.parentElement;
        nav.classList.add('native-bottom-nav');
      }
    }
  }

  function markHeader(){
    const role=[...document.querySelectorAll('body *')].find(el=>['PASTOR','MASTER','ADMIN','LÍDER','LIDER','VOLUNTÁRIO','VOLUNTARIO'].includes(norm(el.textContent)));
    if(!role) return;
    let p=role.parentElement;
    for(let i=0;i<5 && p && p!==document.body;i++,p=p.parentElement){
      const r=p.getBoundingClientRect();
      if(r.width>innerWidth*.75 && r.height>=55 && r.height<190){p.classList.add('native-top-header');break;}
    }
  }

  function markStatCards(){
    document.querySelectorAll('.stat-card').forEach(x=>x.classList.add('native-stat-card'));
    const labels=['VOLUNTÁRIOS','VOLUNTARIOS','ESCALAS (MÊS)','ESCALAS (MES)','CONFIRMADOS','PENDENTES','IGREJAS','DEPARTAMENTOS'];
    for(const label of labels){
      const textEl=[...document.querySelectorAll('body *')].find(el=>norm(el.textContent)===label);
      if(!textEl) continue;
      let p=textEl.parentElement;
      for(let i=0;i<5 && p && p!==document.body;i++,p=p.parentElement){
        const r=p.getBoundingClientRect();
        if(r.width>innerWidth*.65 && r.height>=75 && r.height<340){p.classList.add('native-stat-card');break;}
      }
    }
  }

  function markContentCards(){
    const labels=['Minha Frequência','Relatório de Frequência','Status de Presença','Como funciona o Check-in?','Próxima escala','Minha próxima escala'];
    for(const label of labels){
      const h=[...document.querySelectorAll('h1,h2,h3,h4,div,p')].find(el=>norm(el.textContent)===label);
      if(!h) continue;
      let p=h.parentElement;
      for(let i=0;i<4 && p && p!==document.body;i++,p=p.parentElement){
        const r=p.getBoundingClientRect();
        if(r.width>innerWidth*.72 && r.height>80){p.classList.add('native-content-card');break;}
      }
    }
  }

  function markLogin(){
    const email=document.querySelector('input[type="email"]');
    if(!email) return;
    document.body.classList.add('native-login-page');
    let p=email.parentElement;
    for(let i=0;i<6 && p && p!==document.body;i++,p=p.parentElement){
      const t=norm(p.textContent);
      if(/Seja bem-vindo/i.test(t) && p.getBoundingClientRect().width>innerWidth*.7){p.classList.add('native-login-card');break;}
    }
  }

  function addStyle(){
    if(document.getElementById('native-app-style-v1317')) return;
    const s=document.createElement('style');
    s.id='native-app-style-v1317';
    s.textContent=`
      html.native-app-mode{background:#f7f9fc!important;-webkit-tap-highlight-color:transparent}
      html.native-app-mode body{background:linear-gradient(180deg,#f8faff 0%,#f4f7fb 100%)!important;color:#172033!important;overscroll-behavior-y:none}
      html.native-app-mode *{box-sizing:border-box}
      html.native-app-mode button,html.native-app-mode a,html.native-app-mode [role="button"]{touch-action:manipulation}
      html.native-app-mode button:active,html.native-app-mode a:active,html.native-app-mode [role="button"]:active{transform:scale(.985);transition:transform .08s ease}
      html.native-app-mode input,html.native-app-mode select,html.native-app-mode textarea{font-size:16px!important;border-radius:14px!important;min-height:46px}
      html.native-app-mode button{border-radius:14px!important;min-height:44px}

      html.native-app-mode .native-top-header{min-height:86px!important;max-height:112px!important;padding-top:10px!important;padding-bottom:10px!important;background:rgba(255,255,255,.96)!important;border-bottom:1px solid rgba(148,163,184,.18)!important;box-shadow:0 4px 18px rgba(15,23,42,.04)!important;backdrop-filter:blur(14px)}
      html.native-app-mode .native-top-header h1,html.native-app-mode .native-top-header h2{font-size:20px!important;line-height:1.2!important}

      html.native-app-mode .native-stat-card,html.native-app-mode .stat-card>div{min-height:98px!important;height:auto!important;padding:14px 16px!important;border-radius:20px!important;margin:0!important;box-shadow:0 8px 24px rgba(15,23,42,.065)!important;border:1px solid rgba(148,163,184,.14)!important;overflow:hidden!important}
      html.native-app-mode .stat-card>div{display:grid!important;grid-template-columns:60px minmax(0,1fr)!important;grid-template-rows:auto auto!important;column-gap:14px!important;row-gap:2px!important;align-items:center!important;text-align:left!important}
      html.native-app-mode .stat-card>div>div:first-child{grid-column:1!important;grid-row:1/3!important;width:56px!important;height:56px!important;margin:0!important;padding:12px!important;border-radius:17px!important;display:flex!important;align-items:center!important;justify-content:center!important}
      html.native-app-mode .stat-card>div>div:first-child svg{width:27px!important;height:27px!important}
      html.native-app-mode .stat-card>div>p:nth-child(2){grid-column:2!important;grid-row:1!important;font-size:30px!important;line-height:1!important;margin:0!important;align-self:end!important}
      html.native-app-mode .stat-card>div>p:nth-child(3){grid-column:2!important;grid-row:2!important;font-size:11px!important;line-height:1.2!important;margin:5px 0 0!important;align-self:start!important;letter-spacing:.04em!important}
      html.native-app-mode .adaptive-grid{gap:12px!important;padding-left:14px!important;padding-right:14px!important}
      html.native-app-mode .dashboard-hero{padding:18px 16px!important;min-height:0!important}

      html.native-app-mode .native-content-card{border-radius:20px!important;box-shadow:0 8px 24px rgba(15,23,42,.06)!important;border:1px solid rgba(148,163,184,.13)!important;padding:18px!important;margin-left:14px!important;margin-right:14px!important}
      html.native-app-mode .native-content-card h2,html.native-app-mode .native-content-card h3{font-size:19px!important;line-height:1.25!important}

      html.native-app-mode .native-bottom-nav{background:rgba(255,255,255,.96)!important;border-top:1px solid rgba(148,163,184,.2)!important;box-shadow:0 -8px 24px rgba(15,23,42,.07)!important;backdrop-filter:blur(16px)!important;padding:8px 10px!important;min-height:74px!important;max-height:82px!important;z-index:9999!important}
      html.native-app-mode .native-bottom-nav a,html.native-app-mode .native-bottom-nav button{min-height:56px!important;border-radius:16px!important;padding:7px 10px!important;font-size:12px!important;transition:background .15s ease,color .15s ease,transform .08s ease!important}
      html.native-app-mode .native-bottom-nav svg{width:24px!important;height:24px!important}
      html.native-app-mode .native-bottom-nav .active,html.native-app-mode .native-bottom-nav [aria-current="page"]{background:#eef2ff!important;color:#4146e5!important;box-shadow:none!important}

      html.native-app-mode.native-login-page body,html.native-app-mode body.native-login-page{background:radial-gradient(circle at 50% 5%,#eef2ff 0,#f7f9fc 46%,#f7f9fc 100%)!important}
      html.native-app-mode .native-login-card{border-radius:24px!important;padding:22px!important;margin:14px 16px!important;box-shadow:0 16px 42px rgba(45,55,110,.10)!important;border:1px solid rgba(99,102,241,.10)!important}
      html.native-app-mode .native-login-card button{min-height:52px!important;font-size:17px!important;font-weight:700!important;border-radius:16px!important;box-shadow:0 10px 22px rgba(79,70,229,.18)!important}
      html.native-app-mode .native-login-card input{min-height:52px!important;background:#f8faff!important}

      @media(max-width:430px){
        html.native-app-mode .adaptive-grid{grid-template-columns:minmax(0,1fr)!important}
        html.native-app-mode .native-stat-card,html.native-app-mode .stat-card>div{min-height:92px!important;padding:12px 14px!important}
        html.native-app-mode .native-content-card{padding:16px!important;margin-left:12px!important;margin-right:12px!important}
      }
    `;
    document.head.appendChild(s);
  }

  function enhance(){
    try{
      addStyle();
      replaceBrand();
      hideInstall();
      markBottomNav();
      markHeader();
      markStatCards();
      markContentCards();
      markLogin();
      document.documentElement.classList.add('native-app-mode');
      document.body&&document.body.classList.add('native-app-mode');
    }catch(e){console.warn('native enhance',e);}
  }

  let timer;
  const obs=new MutationObserver(()=>{clearTimeout(timer);timer=setTimeout(enhance,80)});
  if(document.documentElement) obs.observe(document.documentElement,{subtree:true,childList:true,characterData:true});
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',enhance,{once:true}); else enhance();
  setTimeout(enhance,400); setTimeout(enhance,1200);
})();
