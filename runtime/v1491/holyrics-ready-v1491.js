/* Escala de Propósito Holyrics v1.4.91 — script completo por igreja */
(function () {
  'use strict';

  var ENDPOINT='/api/holyrics-connect-v1481.php';
  var AUTH_KEY='escala-facil.auth-token';
  var codeInMemory='';
  var generatedChurch='';
  var generatedChurchName='';

  function byId(id){return document.getElementById(id);}
  function secretToken(){try{return localStorage.getItem(AUTH_KEY)||'';}catch(err){return '';}}
  function showMessage(text,isError){
    var status=byId('holyrics-ready-message-v1491');
    if(!status)return;
    status.style.color=isError?'#a21b2e':'#166534';
    status.textContent=text;
  }
  function setNewCode(value,church,name){
    codeInMemory=value;
    generatedChurch=church;
    generatedChurchName=name;
    var tools=byId('holyrics-ready-tools-v1491');
    if(tools)tools.hidden=!value;
    var fallback=byId('holyrics-ready-fallback-v1491');
    if(fallback){fallback.value='';fallback.hidden=true;}
  }
  function validCode(value){
    if(typeof value!=='string')return false;
    return value.indexOf("function foo()")>=0 &&
      value.indexOf('AddLyricsToPlaylist')>=0 &&
      value.indexOf('ESCALA_TOKEN_SUBSTITUIR_NO_SERVIDOR')===-1 &&
      /var chaveDaIgreja = '[a-f0-9]{64}';/.test(value) &&
      value.indexOf('function scriptAction')===-1;
  }

  function mount(){
    var select=byId('church');
    var existing=byId('generate');
    if(!select||!existing||byId('holyrics-ready-v1491'))return;
    var wrapper=document.createElement('section');
    wrapper.id='holyrics-ready-v1491';
    wrapper.style.cssText='margin:16px 0 12px;padding:18px;border:1px solid #b6c5ff;border-radius:14px;background:#edf3ff;';
    wrapper.innerHTML=
      '<div style="font-size:17px;font-weight:800;margin-bottom:6px">Código Holyrics completo, por igreja</div>'+
      '<p style="font-size:13px;line-height:1.55;margin:6px 0 12px">Escolha a igreja e clique uma vez. O sistema já coloca a chave dentro do script. Você não precisará digitar chave longa nem código de conexão no Holyrics.</p>'+
      '<button type="button" id="holyrics-ready-generate-v1491" style="font-weight:800">Gerar e copiar código completo</button>'+
      '<div id="holyrics-ready-message-v1491" role="status" aria-live="polite" style="margin-top:10px;font-size:13px"></div>'+
      '<div id="holyrics-ready-tools-v1491" hidden style="display:flex;gap:9px;flex-wrap:wrap;margin-top:9px">'+
      '<button type="button" class="secondary" id="holyrics-ready-copy-v1491">Copiar script completo</button>'+
      '<button type="button" class="secondary" id="holyrics-ready-download-v1491">Baixar script .js</button>'+
      '</div>'+
      '<textarea id="holyrics-ready-fallback-v1491" hidden readonly aria-label="Script completo, selecionar tudo e copiar" style="width:100%;height:140px;margin-top:12px;padding:10px;border:1px solid #96a8cf;border-radius:9px;font:12px monospace"></textarea>'+
      '<p style="margin:12px 0 0;font-size:12px;color:#596579;line-height:1.5"><b>Atenção:</b> gerar um código completo novo substitui a chave anterior dessa igreja. Se houver Holyrics em outro computador, será necessário instalar o novo código nele também. O código contém uma credencial privada: não compartilhe em grupos nem tire print.</p>'+
      '<p style="margin:8px 0 0;font-size:12px;color:#596579">No computador: abra um item em <b>Ferramentas → Diversos → Script</b>, substitua TODO o código do quadro esquerdo e clique em <b>Salvar</b>. Não use a janela Testar — Ação (Receptor).</p>';
    existing.parentElement.insertAdjacentElement('beforebegin',wrapper);
    // Respect the hidden state even though this div uses display:flex.
    var controls=byId('holyrics-ready-tools-v1491');
    controls.style.display='none';
    function toggleControls(on){controls.style.display=on?'flex':'none';}
    setNewCode('','','');
    toggleControls(false);
    select.addEventListener('change',function(){
      setNewCode('','','');toggleControls(false);
      showMessage('',false);
    });

    async function copyScript(){
      if(!codeInMemory)throw new Error('Gere primeiro o código da igreja.');
      try{
        await navigator.clipboard.writeText(codeInMemory);
        byId('holyrics-ready-fallback-v1491').hidden=true;
        return true;
      }catch(err){
        var area=byId('holyrics-ready-fallback-v1491');
        area.hidden=false;
        area.value=codeInMemory;
        area.focus();area.select();
        return false;
      }
    }

    byId('holyrics-ready-generate-v1491').addEventListener('click',async function(){
      var church=select.value;
      if(!church){showMessage('Selecione uma igreja primeiro.',true);return;}
      var name=select.options[select.selectedIndex].text;
      if(!window.confirm('Gerar um script novo para '+name+'? Isso revoga a chave anterior e exige substituir o script nos computadores já conectados.'))return;
      var btn=this;
      btn.disabled=true;
      btn.textContent='Gerando código seguro...';
      setNewCode('','','');toggleControls(false);
      showMessage('Gerando script exclusivo desta igreja...',false);
      try{
        var resp=await fetch(ENDPOINT,{
          method:'POST',credentials:'include',cache:'no-store',
          headers:{
            'Authorization':'Bearer '+secretToken(),
            'Accept':'application/json',
            'Content-Type':'application/json'
          },
          body:JSON.stringify({action:'ready_script',igreja_id:church})
        });
        var json;
        try{json=await resp.json();}catch(err){throw new Error('O servidor não retornou JSON válido (HTTP '+resp.status+').');}
        if(!resp.ok||json.error)throw new Error((json.error&&json.error.message)||'HTTP '+resp.status);
        var script=json.data&&json.data.script;
        if(!validCode(script))throw new Error('O script recebido está incompleto ou não foi personalizado.');
        setNewCode(script,church,name);
        toggleControls(true);
        var copied=await copyScript();
        showMessage(copied
          ? 'Código completo gerado e copiado! Agora cole no quadro esquerdo do Holyrics e clique Salvar.'
          : 'Código gerado! O navegador não permitiu copiar automaticamente. Copie pelo campo selecionado abaixo ou use o botão de download.',!copied);
      }catch(e){
        showMessage('Falha ao gerar código completo: '+(e.message||String(e)),true);
      }finally{
        btn.disabled=false;
        btn.textContent='Gerar e copiar código completo';
      }
    });

    byId('holyrics-ready-copy-v1491').addEventListener('click',async function(){
      try{
        var copied=await copyScript();
        showMessage(copied?'Código completo copiado! Cole no editor Script do Holyrics e salve.':'Selecione o texto no campo exibido para copiar (Ctrl+C).',!copied);
      }catch(e){showMessage(e.message,true);}
    });
    byId('holyrics-ready-download-v1491').addEventListener('click',function(){
      if(!codeInMemory)return;
      var blob=new Blob([codeInMemory],{type:'application/javascript;charset=utf-8'});
      var link=document.createElement('a');
      var url=URL.createObjectURL(blob);
      link.href=url;
      link.download='Escala-de-Proposito-Holyrics-'+generatedChurchName.replace(/[^a-z0-9]+/gi,'-').slice(0,50)+'.js';
      document.body.appendChild(link);link.click();link.remove();
      setTimeout(function(){URL.revokeObjectURL(url);},1000);
      showMessage('Arquivo gerado. Ele contém uma credencial privada: guarde-o em local seguro.',false);
    });
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount);
  else mount();
})();
