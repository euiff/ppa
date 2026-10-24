/* Escala de Propósito Connect v1.4.83 — instalação corrigida no Holyrics */
(function () {
  'use strict';
  var scriptUrl = '/Escala-de-Proposito-Holyrics.js?v=1.4.82';

  function insertInstaller() {
    if (document.getElementById('holyrics-copy-script-v1483')) return;
    var download = document.querySelector('a[href^="/Escala-de-Proposito-Holyrics.js"]');
    if (!download) return;
    download.href = scriptUrl;
    download.setAttribute('download', 'Escala-de-Proposito-Holyrics.js');

    var block = document.createElement('div');
    block.id = 'holyrics-copy-script-v1483';
    block.style.cssText = 'margin-top:15px;padding:15px;background:#edf5ff;border:1px solid #b9d6fa;border-radius:12px;line-height:1.6;';
    block.innerHTML =
      '<strong>Correção do erro “Expected an operand but found else”</strong>' +
      '<p style="margin:7px 0 12px">No editor JavaScript do Holyrics, clique <b>dentro do painel esquerdo</b>, pressione <b>Ctrl+A</b> e depois <b>Delete</b>. Só então cole o código completo. Substitua todo o código antigo; a versão nova inclui as funções foo e scriptAction.</p>' +
      '<button type="button" id="holyrics-copy-v1483" class="secondary">📋 Copiar código completo e corrigido</button>' +
      '<div id="holyrics-copy-result-v1483" style="margin-top:9px;font-size:12px" role="status" aria-live="polite"></div>' +
      '<textarea id="holyrics-copy-fallback-v1483" style="display:none;width:100%;min-height:140px;margin-top:8px" readonly aria-label="Código para copiar manualmente"></textarea>';
    download.insertAdjacentElement('afterend', block);

    document.getElementById('holyrics-copy-v1483').addEventListener('click', async function () {
      var btn = this, status = document.getElementById('holyrics-copy-result-v1483');
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
          document.getElementById('holyrics-copy-fallback-v1483').style.display = 'none';
        } catch (err) {
          var area = document.getElementById('holyrics-copy-fallback-v1483');
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