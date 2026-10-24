/* Escala de Propósito Connect v1.4.85 — instalação corrigida no Holyrics */
(function () {
  'use strict';
  var scriptUrl = '/Escala-de-Proposito-Holyrics.js?v=1.4.84';

  function insertInstaller() {
    if (document.getElementById('holyrics-copy-script-v1485')) return;
    var download = document.querySelector('a[href^="/Escala-de-Proposito-Holyrics.js"]');
    if (!download) return;
    download.href = scriptUrl;
    download.setAttribute('download', 'Escala-de-Proposito-Holyrics.js');

    var block = document.createElement('div');
    block.id = 'holyrics-copy-script-v1485';
    block.style.cssText = 'margin-top:15px;padding:15px;background:#edf5ff;border:1px solid #b9d6fa;border-radius:12px;line-height:1.6;';
    block.innerHTML =
      '<strong>Integração Holyrics — conexão e chave</strong>' +
      '<p style="margin:7px 0 12px">No editor JavaScript do Holyrics, clique <b>dentro do painel esquerdo</b>, pressione <b>Ctrl+A</b> e depois <b>Delete</b>. Só então cole o código completo. Substitua todo o código antigo. Esta versão verifica se o Holyrics consegue acessar a API e informa o motivo mais provável da falha.</p>' +
      '<button type="button" id="holyrics-copy-v1485" class="secondary">📋 Copiar código completo e corrigido</button>' +
      '<div id="holyrics-copy-result-v1485" style="margin-top:9px;font-size:12px" role="status" aria-live="polite"></div>' +
      '<textarea id="holyrics-copy-fallback-v1485" style="display:none;width:100%;min-height:140px;margin-top:8px" readonly aria-label="Código para copiar manualmente"></textarea>';
    download.insertAdjacentElement('afterend', block);
    var check = document.createElement('div');
    check.style.cssText = 'margin-top:12px;font-size:13px;';
    check.innerHTML = '<button class="secondary" type="button" id="holyrics-health-v1485">🔍 Testar API neste navegador</button>' +
      '<div id="holyrics-health-status-v1485" role="status" style="margin-top:7px;line-height:1.45"></div>';
    block.appendChild(check);
    document.getElementById('holyrics-health-v1485').addEventListener('click', async function() {
      var status = document.getElementById('holyrics-health-status-v1485');
      status.style.color='#244f8f';
      status.textContent='Verificando a resposta HTTPS do servidor...';
      try {
        var resp = await fetch('/api/holyrics-repertoire-v1481.php?action=health', {cache:'no-store'});
        var json = await resp.json();
        if (!resp.ok || !json.data || json.data.health !== 'ok') throw new Error('API não retornou status válido (HTTP '+resp.status+').');
        status.style.color='#166534';
        status.textContent='✓ API do site respondendo. Se o Holyrics continuar sem conectar, libere escaladeproposito.com.br em Arquivo > Configurações > Avançado > JavaScript > Configurações > Requisições permitidas. Verifique sua versão do Holyrics.';
      } catch(e) {
        status.style.color='#b91c1c';
        status.textContent='Falha no próprio servidor ou atualização ainda não instalada: '+(e.message||e);
      }
    });

    // Chave testada somente por HTTPS no mesmo domínio. Não é gravada nem enviada por URL.
    var verifyBox = document.createElement('div');
    verifyBox.style.cssText = 'margin-top:15px;border-top:1px solid #bad1e9;padding-top:14px;';
    verifyBox.innerHTML =
      '<label for="holyrics-key-v1485" style="font-weight:700;display:block;margin-bottom:7px">Validar chave da igreja</label>' +
      '<input id="holyrics-key-v1485" type="password" autocomplete="off" placeholder="Cole sua chave atual de 64 caracteres" style="max-width:100%;width:420px;padding:10px;border:1px solid #9baec9;border-radius:9px" /> ' +
      '<button type="button" class="secondary" id="holyrics-verify-v1485" style="margin-top:8px">🔑 Validar chave</button>' +
      '<div id="holyrics-verify-result-v1485" role="status" style="margin-top:8px;font-size:13px"></div>' +
      '<p style="font-size:12px;color:#5d6979">O Holyrics guarda a chave anterior no computador. Se ela foi renovada, o script corrigido permitirá informar a chave atual novamente. Não compartilhe a chave em capturas de tela.</p>';
    block.appendChild(verifyBox);
    document.getElementById('holyrics-verify-v1485').addEventListener('click', async function() {
      var input = document.getElementById('holyrics-key-v1485');
      var field = String(input.value || '').trim();
      var result = document.getElementById('holyrics-verify-result-v1485');
      if (!field) {
        var secret = document.getElementById('secret');
        var keybox = document.getElementById('keybox');
        if(secret && keybox && !keybox.hidden) field = String(secret.textContent || '').trim();
      }
      var igreja = document.getElementById('church');
      if(!igreja || !igreja.value) { result.textContent='Escolha a igreja primeiro.';return; }
      if(!/^[a-f0-9]{64}$/i.test(field)) {
        result.style.color='#b91c1c';
        result.textContent='A chave deve conter 64 caracteres. Cole a chave atual, não o endereço do grupo WhatsApp.';
        return;
      }
      this.disabled=true;
      result.style.color='#244f8f'; result.textContent='Validando chave para esta igreja...';
      try {
        var auth = localStorage.getItem('escala-facil.auth-token') || '';
        var response = await fetch('/api/holyrics-connect-v1481.php',{
          method:'POST',
          credentials:'include',
          headers:{'Content-Type':'application/json','Authorization':'Bearer '+auth,'Accept':'application/json'},
          body:JSON.stringify({action:'verify',igreja_id:igreja.value,holyrics_token:field}),
          cache:'no-store'
        });
        var body = await response.json();
        if(!response.ok || body.error)throw new Error(body.error&&body.error.message || ('HTTP '+response.status));
        var valid = body.data && body.data.valid === true;
        result.style.color=valid?'#166534':'#b91c1c';
        result.textContent=valid?'✓ Chave ativa e correta para esta igreja.':'✗ A chave não corresponde à chave ativa desta igreja. Utilize a última chave gerada.';
      }catch(error){
        result.style.color='#b91c1c';
        result.textContent='Falha ao verificar chave: '+(error.message||error);
      }finally{
        input.value='';
        this.disabled=false;
      }
    });

    document.getElementById('holyrics-copy-v1485').addEventListener('click', async function () {
      var btn = this, status = document.getElementById('holyrics-copy-result-v1485');
      btn.disabled = true;
      btn.textContent = 'Carregando código corrigido...';
      try {
        var response = await fetch(scriptUrl, {cache:'no-store'});
        if (!response.ok) throw new Error('HTTP ' + response.status);
        var code = await response.text();
        if (!code.includes('function foo()') || !code.includes('AddLyricsToPlaylist')) {
          throw new Error('Código incompleto');
        }
        try {
          await navigator.clipboard.writeText(code);
          status.textContent = 'Código copiado! No painel ESQUERDO do Holyrics, pressione Ctrl+A e Ctrl+V, depois Testar e Salvar.';
          status.style.color = '#17643a';
          document.getElementById('holyrics-copy-fallback-v1485').style.display = 'none';
        } catch (err) {
          var area = document.getElementById('holyrics-copy-fallback-v1485');
          area.style.display = 'block';
          area.value = code;
          area.focus(); area.select();
          status.textContent = 'Selecione e copie o código no campo abaixo (Ctrl+C); depois substitua tudo no painel esquerdo do Holyrics.';
          status.style.color = '#814a00';
        }
      } catch (err) {
        status.textContent = 'Falha ao obter o código do servidor: ' + (err.message || err);
        status.style.color = '#a21b2e';
      } finally {
        btn.textContent = '📋 Copiar código completo e corrigido';
        btn.disabled = false;
      }
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', insertInstaller);
  else insertInstaller();
})();