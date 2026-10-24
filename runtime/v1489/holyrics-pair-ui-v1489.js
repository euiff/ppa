(()=>{
'use strict';
const API='/api/holyrics-connect-v1481.php';
function attach() {
  if(document.getElementById('holyrics-pair-v1489'))return;
  const generate=document.getElementById('generate');
  const church=document.getElementById('church');
  if(!generate||!church)return;
  const panel=document.createElement('section');
  panel.id='holyrics-pair-v1489';
  panel.style.cssText='padding:16px;margin:14px 0;border:1px solid #bad7fd;background:#eef6ff;border-radius:14px;';
  panel.innerHTML='<div style="font-size:17px;font-weight:800;margin-bottom:6px">Conectar Holyrics por código</div>'+
    '<p style="margin:6px 0 12px;line-height:1.55">Agora é simples: gere um código curto, digite no Holyrics e pronto. Não precisa digitar nem copiar a chave longa de 64 caracteres.</p>'+
    '<button type="button" id="holyrics-pair-generate-v1489">Gerar código de conexão</button>'+
    '<div id="holyrics-pair-result-v1489" role="status" aria-live="polite" style="display:none;margin-top:14px"></div>'+
    '<p style="margin:12px 0 0;color:#596578;font-size:12px">O código vale 10 minutos, funciona uma vez e, quando utilizado, substitui a chave antiga desta igreja. Outros computadores já conectados precisarão se reconectar.</p>';
  generate.parentNode.insertAdjacentElement('afterend',panel);
  const oldLabel=generate.textContent;
  generate.textContent='Gerar / renovar chave longa (avançado)';
  generate.classList.add('secondary');
  generate.title='Opção antiga: a forma recomendada é Gerar código de conexão.';
  const btn=document.getElementById('holyrics-pair-generate-v1489');
  const result=document.getElementById('holyrics-pair-result-v1489');
  btn.addEventListener('click',async()=>{
    if(!church.value){
      result.style.display='block';
      result.textContent='Escolha a igreja antes de gerar o código.';
      return;
    }
    btn.disabled=true;
    btn.textContent='Gerando...';
    try{
      const token=localStorage.getItem('escala-facil.auth-token')||'';
      const response=await fetch(API,{
        method:'POST',credentials:'include',cache:'no-store',
        headers:{'Authorization':'Bearer '+token,'Content-Type':'application/json','Accept':'application/json'},
        body:JSON.stringify({action:'pair_start',igreja_id:church.value})
      });
      let payload={};
      try{payload=await response.json()}catch(e){}
      if(!response.ok||payload.error)throw new Error(payload?.error?.message||'HTTP '+response.status);
      const data=payload.data||{};
      if(!/^[A-HJ-NP-Z2-9]{4}-[A-HJ-NP-Z2-9]{4}-[A-HJ-NP-Z2-9]{4}$/.test(data.code||'')){
        throw new Error('O servidor não devolveu um código válido.');
      }
      result.style.display='block';
      result.innerHTML='';
      const code=document.createElement('div');
      code.style.cssText='font-family:ui-monospace,monospace;font-size:clamp(18px,5vw,27px);font-weight:900;letter-spacing:1px;padding:12px;background:#fff;border:1px dashed #7189bd;border-radius:10px;overflow-wrap:anywhere;';
      code.textContent=data.code;
      result.appendChild(code);
      const copy=document.createElement('button');
      copy.textContent='Copiar código curto';
      copy.className='secondary';
      copy.style.marginTop='10px';
      copy.addEventListener('click',async()=>{try{await navigator.clipboard.writeText(data.code);copy.textContent='Código copiado!'}catch(e){copy.textContent='Copie o código acima manualmente.'}});
      result.appendChild(copy);
      const instruction=document.createElement('p');
      instruction.style.cssText='font-size:13px;margin:9px 0;color:#215281;';
      instruction.textContent='No Holyrics, abra o script Escala de Propósito e digite somente este código quando solicitado. Válido por 10 minutos, uma única vez.';
      result.appendChild(instruction);
    }catch(e){
      result.style.display='block';result.style.color='#a21b2e';result.textContent='Não foi possível gerar código: '+(e.message||e);
    }finally{
      btn.disabled=false;btn.textContent='Gerar código de conexão';
    }
  });
  church.addEventListener('change',()=>{result.textContent='';result.style.display='none';});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',attach);
else attach();
})();