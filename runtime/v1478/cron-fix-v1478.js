(()=>{
'use strict';
const API='/api/cron-control-v1478.php';
const TOKEN_KEY='escala-facil.auth-token';
const originalFetch=window.fetch.bind(window);
let installedPatch=false;

function authHeaders(extra={}){
  let token='';
  try{token=localStorage.getItem(TOKEN_KEY)||''}catch(e){}
  return {...extra,...(token?{Authorization:'Bearer '+token}:{})};
}
function urlOf(input){
  try{return typeof input==='string'?input:(input&&input.url)||''}catch(e){return''}
}
function parseBody(init){
  try{
    if(!init||typeof init.body!=='string')return null;
    return JSON.parse(init.body);
  }catch(e){return null}
}

function installFetchPatch(){
  if(installedPatch)return;
  installedPatch=true;
  window.fetch=async function(input,init={}){
    const url=urlOf(input);
    const body=parseBody(init);

    if(/\/api\/functions\.php(?:\?|$)/.test(url) && body && body.name==='system-cron-config'){
      return originalFetch(API+'?action=config',{
        method:'GET',
        headers:authHeaders({Accept:'application/json'}),
        credentials:'include',
        cache:'no-store'
      });
    }

    if(/\/api\/cron-runner\.php\?key=/.test(url)){
      return originalFetch(API+'?action=test',{
        method:'POST',
        headers:authHeaders({'Content-Type':'application/json',Accept:'application/json'}),
        credentials:'include',
        cache:'no-store',
        body:'{}'
      });
    }

    return originalFetch(input,init);
  };
}

async function api(action,method='GET'){
  const r=await originalFetch(API+'?action='+encodeURIComponent(action),{
    method,
    headers:authHeaders({'Content-Type':'application/json',Accept:'application/json'}),
    credentials:'include',
    cache:'no-store',
    ...(method==='POST'?{body:'{}'}:{})
  });
  let j={};
  try{j=await r.json()}catch(e){}
  if(!r.ok||j.error)throw new Error(j?.error?.message||('HTTP '+r.status));
  return j.data||{};
}
function isConfigGlobal(){
  return location.pathname==='/configuracoes' && (document.body?.innerText||'').includes('CRON do Sistema');
}
function isMaster(){
  const t=document.body?.innerText||'';
  return t.includes('MASTER') && t.includes('Config. Global');
}
function findCronCard(){
  const title=[...document.querySelectorAll('h1,h2,h3,h4,div,p')].find(el=>(el.textContent||'').trim().includes('CRON do Sistema'));
  if(!title)return null;
  let el=title;
  for(let i=0;i<6&&el;i++,el=el.parentElement){
    const txt=(el.textContent||'');
    if(txt.includes('Testar CRON agora')&&txt.includes('Linha completa para crontab/terminal'))return el;
  }
  return title.parentElement?.parentElement?.parentElement||null;
}
function fmtSummary(s){
  if(!s||typeof s!=='object')return 'Sem resumo disponível';
  const due=Number(s.group_reminders_due||0);
  const sent=Number(s.group_reminders_sent||0);
  const failed=Number(s.group_reminders_failed||0);
  const jobs=Number(s.jobs_sent||0);
  return 'Grupo: '+due+' devido(s), '+sent+' enviado(s), '+failed+' falha(s) · WhatsApp individual: '+jobs+' enviado(s)';
}
function toast(text,ok=true){
  let n=document.getElementById('cron1478-toast');
  if(!n){
    n=document.createElement('div');n.id='cron1478-toast';
    n.style.cssText='position:fixed;right:18px;top:18px;z-index:999999;padding:12px 15px;border-radius:12px;color:white;font:700 13px system-ui;box-shadow:0 10px 35px #0003;max-width:min(420px,calc(100vw - 36px))';
    document.body.appendChild(n);
  }
  n.style.background=ok?'#166534':'#b91c1c';n.textContent=text;n.style.display='block';
  clearTimeout(n._t);n._t=setTimeout(()=>n.style.display='none',4500);
}

async function refreshPanel(){
  const box=document.getElementById('cron-health-v1478');
  if(!box)return;
  try{
    const d=await api('config');
    const ct=d.crontab||{};
    box.querySelector('[data-cron-url]').textContent=d.url||'—';
    box.querySelector('[data-cron-last]').textContent=d.last_run||'Ainda não executou';
    box.querySelector('[data-cron-summary]').textContent=fmtSummary(d.last_summary||{});
    const status=box.querySelector('[data-cron-status]');
    if(ct.installed){
      status.textContent='Ativo no servidor';
      status.style.color='#15803d';
    }else if(ct.old_domain_detected){
      status.textContent='CRON antigo detectado (domínio antigo)';
      status.style.color='#b91c1c';
    }else if(ct.supported===false){
      status.textContent='Precisa configurar pelo cPanel';
      status.style.color='#b45309';
    }else{
      status.textContent='Não encontrado no crontab';
      status.style.color='#b91c1c';
    }
    const err=box.querySelector('[data-cron-error]');
    if(d.last_error){
      err.style.display='block';err.textContent='Último erro: '+d.last_error;
    }else{
      err.style.display='none';err.textContent='';
    }
  }catch(e){
    const status=box.querySelector('[data-cron-status]');
    status.textContent='Falha ao consultar: '+e.message;status.style.color='#b91c1c';
  }
}

function mountPanel(){
  if(!isConfigGlobal()||!isMaster()||document.getElementById('cron-health-v1478'))return;
  const card=findCronCard();if(!card)return;

  const box=document.createElement('div');
  box.id='cron-health-v1478';
  box.style.cssText='margin-top:14px;border:1px solid rgba(79,70,229,.25);border-radius:18px;background:linear-gradient(135deg,rgba(79,70,229,.06),rgba(14,165,233,.04));padding:16px;';
  box.innerHTML=`
    <div style="display:flex;gap:12px;align-items:flex-start;justify-content:space-between;flex-wrap:wrap">
      <div>
        <div style="font-weight:900;font-size:14px">🛠️ Diagnóstico do CRON</div>
        <div style="font-size:11px;color:#64748b;margin-top:4px">O endereço oficial agora é <b>https://escaladeproposito.com.br</b>. O domínio antigo não deve mais ser usado.</div>
      </div>
      <b data-cron-status style="font-size:12px">Verificando...</b>
    </div>
    <div style="display:grid;grid-template-columns:1fr;gap:8px;margin-top:12px;font-size:12px">
      <div><span style="color:#64748b">URL atual:</span> <code data-cron-url style="word-break:break-all">—</code></div>
      <div><span style="color:#64748b">Última execução:</span> <b data-cron-last>—</b></div>
      <div><span style="color:#64748b">Último resumo:</span> <span data-cron-summary>—</span></div>
      <div data-cron-error style="display:none;color:#b91c1c"></div>
    </div>
    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:14px">
      <button type="button" data-cron-install style="border:0;border-radius:10px;background:#4f46e5;color:#fff;padding:10px 13px;font-weight:800;cursor:pointer">Corrigir CRON no servidor</button>
      <button type="button" data-cron-run style="border:1px solid #cbd5e1;border-radius:10px;background:#fff;color:#172033;padding:10px 13px;font-weight:800;cursor:pointer">Executar automações agora</button>
      <button type="button" data-cron-refresh style="border:1px solid #cbd5e1;border-radius:10px;background:#fff;color:#172033;padding:10px 13px;font-weight:800;cursor:pointer">Atualizar diagnóstico</button>
    </div>
    <div style="font-size:11px;color:#64748b;margin-top:9px">Ao corrigir, o sistema tenta remover a linha antiga do cron e instalar a nova execução a cada minuto. Se a hospedagem bloquear essa ação, use a linha exibida acima no cPanel.</div>
  `;
  card.insertAdjacentElement('afterend',box);

  box.querySelector('[data-cron-install]').addEventListener('click',async e=>{
    const b=e.currentTarget;b.disabled=true;b.textContent='Corrigindo...';
    try{
      const d=await api('install','POST');
      toast(d.install?.message||'CRON atualizado.');
      setTimeout(refreshPanel,500);
    }catch(err){
      toast(err.message,false);
      setTimeout(refreshPanel,500);
    }finally{b.disabled=false;b.textContent='Corrigir CRON no servidor'}
  });

  box.querySelector('[data-cron-run]').addEventListener('click',async e=>{
    const b=e.currentTarget;b.disabled=true;b.textContent='Executando...';
    try{
      const d=await api('test','POST');
      const a=d.automation||{};
      toast('CRON executado. Grupo: '+Number(a.group_reminders_sent||0)+' enviado(s), '+Number(a.group_reminders_failed||0)+' falha(s).',!!d.success);
      setTimeout(refreshPanel,500);
    }catch(err){toast(err.message,false);setTimeout(refreshPanel,500)}
    finally{b.disabled=false;b.textContent='Executar automações agora'}
  });
  box.querySelector('[data-cron-refresh]').addEventListener('click',refreshPanel);

  refreshPanel();

  setTimeout(()=>{
    const buttons=[...document.querySelectorAll('button')];
    const update=buttons.find(b=>(b.textContent||'').trim()==='Atualizar configuração');
    if(update)update.click();
  },350);
}

installFetchPatch();
const obs=new MutationObserver(()=>mountPanel());
obs.observe(document.documentElement,{childList:true,subtree:true});
document.addEventListener('DOMContentLoaded',()=>setTimeout(mountPanel,100));
setTimeout(mountPanel,500);
setInterval(mountPanel,2500);
})();