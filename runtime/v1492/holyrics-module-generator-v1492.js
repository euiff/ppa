/* Escala de Proposito Holyrics — gerador de modulo por igreja v1.4.92 */
(function () {
  'use strict';
  var memoryCode = '';
  var memoryChurch = '';

  function el(id) { return document.getElementById(id); }
  function status(message, isError) {
    var out = el('edp-hly-module-status-v1492');
    if (!out) return;
    out.style.color = isError ? '#b91c1c' : '#17643a';
    out.textContent = message;
  }
  function verifyModule(code) {
    return typeof code === 'string' &&
      code.indexOf('function info()') >= 0 &&
      code.indexOf('function actions(module)') >= 0 &&
      code.indexOf('AddLyricsToPlaylist') >= 0 &&
      code.indexOf('ESCALA_MODULO_TOKEN_SUBSTITUIR_NO_SERVIDOR') < 0 &&
      /var token = '[a-f0-9]{64}';/.test(code);
  }
  function mount() {
    var select = el('church');
    var generate = el('generate');
    if (!select || !generate || el('edp-hly-module-v1492')) return;

    var panel = document.createElement('section');
    panel.id = 'edp-hly-module-v1492';
    panel.style.cssText = 'padding:18px;margin:15px 0;border:2px solid #b3c7fb;border-radius:16px;background:#eef4ff;line-height:1.6';
    panel.innerHTML =
      '<h3 style="margin:0 0 8px">Integração Holyrics — Módulo recomendado</h3>' +
      '<p style="margin:0 0 12px;font-size:14px">Escolha a igreja acima. O sistema gera o módulo COMPLETO com a conexão pronta. Não precisa editar o código, digitar chave ou usar o editor antigo de Script.</p>' +
      '<button type="button" id="edp-hly-module-generate-v1492" style="font-weight:800">Gerar e copiar módulo Holyrics</button>' +
      '<div id="edp-hly-module-status-v1492" aria-live="polite" role="status" style="margin-top:10px;font-size:13px"></div>' +
      '<div id="edp-hly-module-actions-v1492" style="display:none;margin-top:12px;gap:9px;flex-wrap:wrap">' +
        '<button type="button" class="secondary" id="edp-hly-module-copy-v1492">Copiar novamente</button>' +
        '<button type="button" class="secondary" id="edp-hly-module-download-v1492">Baixar arquivo .js</button>' +
      '</div>' +
      '<textarea id="edp-hly-module-fallback-v1492" aria-label="Módulo gerado para cópia manual" readonly hidden style="margin-top:12px;width:100%;height:140px;font:12px monospace;border:1px solid #bac6d6;border-radius:10px;padding:10px"></textarea>' +
      '<p style="font-size:13px;margin:12px 0 0"><b>Instalação única no Holyrics:</b> Ferramentas → Módulos → adicionar módulo → colar o código gerado → salvar e ativar. Depois use a ação <b>Importar repertório da escala</b>.</p>' +
      '<p style="font-size:12px;color:#5b6780;margin:8px 0 0">Segurança: este código é particular da igreja. Gerar outro código revoga a chave anterior dessa igreja; atualize outros computadores caso existam. Não compartilhe o módulo com outras igrejas.</p>';

    var old = el('holyrics-ready-v1491');
    if (old) old.insertAdjacentElement('beforebegin', panel);
    else generate.parentElement.insertAdjacentElement('beforebegin', panel);
    var actionRow = el('edp-hly-module-actions-v1492');
    var fallback = el('edp-hly-module-fallback-v1492');

    // Hide legacy generator behind an expandable option instead of removing it.
    if (old && !el('edp-hly-legacy-v1492')) {
      var legacy = document.createElement('details');
      legacy.id = 'edp-hly-legacy-v1492';
      legacy.style.cssText = 'margin:12px 0;border:1px solid #d4d9e8;border-radius:10px;padding:10px;';
      var summary = document.createElement('summary');
      summary.textContent = 'Opções antigas — Script e código de conexão (avançado)';
      summary.style.cursor = 'pointer';
      old.parentNode.insertBefore(legacy, old);
      legacy.appendChild(summary);
      legacy.appendChild(old);
    }

    select.addEventListener('change', function () {
      memoryCode = '';
      memoryChurch = '';
      actionRow.style.display = 'none';
      fallback.hidden = true;
      fallback.value = '';
      status('', false);
    });

    async function copyNow() {
      try {
        await navigator.clipboard.writeText(memoryCode);
        fallback.hidden = true;
        fallback.value = '';
        return true;
      } catch(e) {
        fallback.hidden = false;
        fallback.value = memoryCode;
        fallback.focus();
        fallback.select();
        return false;
      }
    }

    el('edp-hly-module-generate-v1492').addEventListener('click', async function () {
      if (!select.value) { status('Escolha a igreja primeiro.', true); return; }
      var churchId = select.value;
      var churchName = select.options[select.selectedIndex].text;
      if (!window.confirm('Gerar um módulo para ' + churchName + '? Isso substitui a chave anterior dessa igreja. Se outros computadores já estiverem conectados, precisarão receber o módulo novo.')) return;
      var btn = this;
      btn.disabled = true;
      btn.textContent = 'Gerando módulo...';
      memoryCode = '';
      actionRow.style.display = 'none';
      fallback.hidden = true;
      status('Criando um módulo seguro para esta igreja...', false);
      try {
        var jwt = localStorage.getItem('escala-facil.auth-token') || '';
        var response = await fetch('/api/holyrics-connect-v1481.php', {
          method: 'POST',
          credentials: 'same-origin',
          cache: 'no-store',
          headers: { 'Content-Type':'application/json', 'Accept':'application/json', 'Authorization': 'Bearer ' + jwt },
          body: JSON.stringify({action:'ready_module', igreja_id:churchId})
        });
        var answer = await response.json();
        if (!response.ok || answer.error) throw new Error(answer.error && answer.error.message || 'Falha HTTP '+response.status);
        var code = answer.data && answer.data.module;
        if (!verifyModule(code)) throw new Error('O servidor retornou um módulo incompleto. A credencial não foi exibida.');
        memoryCode = code;
        memoryChurch = churchName;
        actionRow.style.display = 'flex';
        var copied = await copyNow();
        status(copied ? 'Módulo gerado e copiado! Cole em Ferramentas → Módulos no Holyrics e ative.' :
          'Módulo gerado! Copie o texto selecionado abaixo ou baixe o arquivo .js.', false);
      } catch(e) {
        status('Não foi possível gerar o módulo: ' + (e.message || e), true);
      } finally {
        btn.disabled = false;
        btn.textContent = 'Gerar e copiar módulo Holyrics';
      }
    });

    el('edp-hly-module-copy-v1492').addEventListener('click', async function () {
      if (!memoryCode) return;
      var copied = await copyNow();
      status(copied ? 'Módulo copiado novamente. Pronto para instalar no Holyrics.' :
        'Selecione o texto exibido e copie manualmente.', false);
    });

    el('edp-hly-module-download-v1492').addEventListener('click', function () {
      if (!memoryCode) return;
      var url = URL.createObjectURL(new Blob([memoryCode], {type:'application/javascript;charset=utf-8'}));
      var a = document.createElement('a');
      a.href = url;
      a.download = 'Escala-de-Proposito-Holyrics-'+memoryChurch.replace(/[^a-z0-9]+/gi,'-').slice(0,45)+'.js';
      document.body.appendChild(a);a.click();a.remove();
      setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
      status('Arquivo gerado. Guarde-o com segurança: contém acesso privado desta igreja.', false);
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
  else mount();
})();
