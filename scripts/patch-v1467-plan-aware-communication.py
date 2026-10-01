from pathlib import Path

root=Path('pkg')

js=r'''(()=>{
'use strict';
const KEY='escala-facil.auth-token';
let features=null,observer=null;

const token=()=>{try{return localStorage.getItem(KEY)||''}catch{return''}};

function replaceTextNode(node){
  if(!node||node.nodeType!==3)return;
  let t=node.nodeValue||'',n=t;
  const reps=[
    [/Notificar\s+via\s+WhatsApp/gi,'Notificar pelo app'],
    [/Notificar\s+pelo\s+WhatsApp/gi,'Notificar pelo app'],
    [/Notificar\s+no\s+WhatsApp/gi,'Notificar pelo app'],
    [/Lembrete\s+WhatsApp/gi,'Lembrete pelo app'],
    [/Lembrete\s+via\s+WhatsApp/gi,'Lembrete pelo app'],
    [/Reenviar\s+via\s+WhatsApp/gi,'Reenviar notificação'],
    [/Reenviar\s+WhatsApp/gi,'Reenviar notificação'],
    [/Enviar\s+via\s+WhatsApp/gi,'Enviar notificação pelo app'],
    [/Enviar\s+WhatsApp/gi,'Enviar notificação pelo app'],
    [/Notificação\s+via\s+WhatsApp/gi,'Notificação pelo app'],
    [/Notificações\s+via\s+WhatsApp/gi,'Notificações pelo app'],
    [/Confirmação\s+via\s+WhatsApp/gi,'Confirmação pelo app'],
    [/Confirmações\s+via\s+WhatsApp/gi,'Confirmações pelo app']
  ];
  for(const [re,to] of reps)n=n.replace(re,to);
  if(n!==t)node.nodeValue=n;
}

function walkText(root){
  if(!root)return;
  try{
    const w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
    const nodes=[];while(w.nextNode())nodes.push(w.currentNode);
    nodes.forEach(replaceTextNode);
  }catch(e){}
}

function whatsappSpecific(el){
  if(!el||el.nodeType!==1)return false;
  const href=(el.getAttribute?.('href')||'').toLowerCase();
  const id=(el.id||'').toLowerCase();
  const cls=typeof el.className==='string'?el.className.toLowerCase():'';
  const txt=(el.textContent||'').trim().toLowerCase();
  if(/whatsapp|evolution/.test(href)||/whatsapp|evolution/.test(id)||/whatsapp|evolution/.test(cls)){
    if(/notificar|reenviar|lembrete|confirma/.test(txt))return false;
    return true;
  }
  return false;
}

function hideWhatsappSettings(root=document){
  try{
    root.querySelectorAll('a,button,[role="button"]').forEach(el=>{
      const txt=(el.textContent||'').trim();
      const href=(el.getAttribute('href')||'');
      if(/configura(r|ção|coes|ções)|conectar|qr|evolution|testar|instância|instancia/i.test(txt) &&
         (/whats\s*app/i.test(txt)||/whatsapp|evolution/i.test(href))){
        el.style.display='none';el.setAttribute('aria-hidden','true');
      }
    });
    root.querySelectorAll('[href*="whatsapp" i],[href*="evolution" i]').forEach(el=>{
      if(!/notificar|reenviar|lembrete|confirma/i.test((el.textContent||''))){
        el.style.display='none';el.setAttribute('aria-hidden','true');
      }
    });
  }catch(e){}
}

function normalizeNotifyControls(root=document){
  try{
    root.querySelectorAll('label').forEach(label=>{
      const txt=(label.textContent||'').trim();
      if(/notificar.*whats\s*app|whats\s*app.*notificar/i.test(txt)){
        walkText(label);
        const input=label.querySelector('input[type="checkbox"]');
        if(input){
          input.checked=true;
          input.disabled=true;
          input.setAttribute('data-app-notification','1');
          input.title='Neste plano, a notificação é feita automaticamente pelo aplicativo.';
        }
        label.title='Neste plano, os voluntários são notificados pelo aplicativo Escala de Propósito.';
      }
    });
    root.querySelectorAll('button,[role="button"]').forEach(btn=>{
      const txt=(btn.textContent||'').trim();
      if(/notificar.*whats\s*app|reenviar.*whats\s*app/i.test(txt)){
        walkText(btn);
        btn.setAttribute('data-app-notify-control','1');
        btn.title='Neste plano, a comunicação é feita pelo aplicativo.';
      }
    });
  }catch(e){}
}

function addPlanInfo(){
  if(document.getElementById('app-plan-communication-info'))return;
  const hasScaleWords=[...document.querySelectorAll('body *')].some(el=>/escala|confirmação|notificar/i.test((el.textContent||'').slice(0,120)));
  if(!hasScaleWords)return;
  const box=document.createElement('div');
  box.id='app-plan-communication-info';
  box.style.cssText='position:fixed;right:16px;bottom:16px;z-index:99990;max-width:360px;padding:10px 14px;border-radius:12px;background:#eef2ff;color:#312e81;border:1px solid #c7d2fe;font:600 13px/1.35 system-ui,-apple-system,Segoe UI,sans-serif;box-shadow:0 8px 24px rgba(15,23,42,.12)';
  box.innerHTML='<b>Comunicação pelo aplicativo</b><br><span style="font-weight:400">Este plano não utiliza WhatsApp. As confirmações e avisos são feitos pelo app Escala de Propósito.</span>';
  document.body.appendChild(box);
  setTimeout(()=>{try{box.remove()}catch(e){}},9000);
}

function applyNoWhatsapp(root=document){
  document.documentElement.dataset.whatsappEnabled='0';
  walkText(root===document?document.body:root);
  hideWhatsappSettings(root===document?document:root);
  normalizeNotifyControls(root===document?document:root);
  addPlanInfo();
}

function observe(){
  if(observer)return;
  observer=new MutationObserver(list=>{
    if(!features||features.whatsapp!==false)return;
    for(const m of list){
      if(m.type==='characterData')replaceTextNode(m.target);
      for(const n of m.addedNodes||[]){
        if(n.nodeType===3)replaceTextNode(n);
        else if(n.nodeType===1)applyNoWhatsapp(n);
      }
    }
  });
  observer.observe(document.body,{subtree:true,childList:true,characterData:true});
}

async function loadFeatures(){
  const t=token();if(!t)return;
  try{
    const r=await fetch('/api/plan-features.php',{headers:{Authorization:'Bearer '+t},cache:'no-store'});
    const j=await r.json();
    features=j?.data?.features||{};
    window.EscalaPlanFeatures=features;
    if(features.whatsapp===false){
      applyNoWhatsapp(document);
      observe();
    }else{
      document.documentElement.dataset.whatsappEnabled='1';
    }
  }catch(e){}
}

document.addEventListener('DOMContentLoaded',loadFeatures);
window.addEventListener('popstate',()=>setTimeout(()=>features?.whatsapp===false&&applyNoWhatsapp(document),100));
window.addEventListener('hashchange',()=>setTimeout(()=>features?.whatsapp===false&&applyNoWhatsapp(document),100));
})();'''

(root/'plan-feature-guard-v1467.js').write_text(js,encoding='utf-8')

p=root/'sistema.html'
s=p.read_text(encoding='utf-8')
s=s.replace('<script src="/plan-feature-guard-v1465.js?v=1.4.65" defer></script>','<script src="/plan-feature-guard-v1467.js?v=1.4.67" defer></script>')
if 'plan-feature-guard-v1467.js' not in s:
    raise SystemExit('new plan guard not loaded')
p.write_text(s,encoding='utf-8')

(root/'VERSION').write_text('1.4.67\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.67.md').write_text('''# Escala de Propósito v1.4.67 — Comunicação conforme o plano

- Igrejas com WhatsApp continuam vendo e usando os recursos de WhatsApp normalmente.
- Igrejas sem WhatsApp deixam de receber textos enganosos de comunicação por WhatsApp nas telas do sistema.
- Para plano sem WhatsApp:
  - "Notificar via WhatsApp" passa a aparecer como "Notificar pelo app".
  - "Lembrete WhatsApp" passa a aparecer como "Lembrete pelo app".
  - "Reenviar WhatsApp" passa a aparecer como "Reenviar notificação".
  - confirmações e avisos passam a ser apresentados como comunicação pelo aplicativo.
- Controles de configuração, conexão, QR Code, teste e Evolution/WhatsApp ficam ocultos para igrejas cujo plano não possui WhatsApp.
- O controle de notificação da escala fica identificado como notificação automática pelo app no plano sem WhatsApp.
- Um aviso curto informa ao pastor que o plano usa o aplicativo como canal de comunicação.
- O bloqueio de WhatsApp no backend da v1.4.65 continua ativo, portanto a mudança não é apenas visual.
''',encoding='utf-8')
