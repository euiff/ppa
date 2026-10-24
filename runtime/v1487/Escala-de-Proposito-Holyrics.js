/* ESCALA DE PROPÓSITO CONNECT — V1.0.6 (para Holyrics)
 *
 * SUBSTITUA TODO o conteúdo do campo ESQUERDO do editor JavaScript:
 * 1. Clique no campo esquerdo.
 * 2. Pressione Ctrl+A e Delete.
 * 3. Cole TODO este arquivo e clique em Testar → Salvar.
 *
 * NÃO cole abaixo do código de exemplo: isso gera erro "Expected an operand but found else".
 * O quadro da DIREITA (Funções adicionais) não precisa receber este script.
 * Compatível com testes do tipo Script e do tipo Ação (Receptor).
 */

/*
 * Escala de Propósito Connect — Holyrics (v1.0.6)
 * Requer Holyrics 2.23.0+ (JSLib apiRequest URL externa) e liberação do host.
 * Menu Ferramentas > Diversos > Script: crie item "Escala de Propósito".
 * Na primeira execução, informe a chave gerada em Configurações do Escala de Propósito.
 * Esse script NÃO adiciona letras novas nem limpa a lista atual.
 */
function foo() {
    var base = 'https://escaladeproposito.com.br/api/holyrics-repertoire-v1481.php';
    var storageKey = 'escala-de-proposito-holyrics-token-v1';
    // v1.0.6 — ler diretamente a chave copiada no portal, sem digitar 64 caracteres.
    function normalizeKey(v) {
        if (v == null) return '';
        if (typeof v === 'object') {
            if (v.access_key != null) v = v.access_key;
            else if (v.key != null) v = v.key;
            else if (v.value != null) v = v.value;
            else return '';
        }
        return String(v).replace(/[\\s\\u200B-\\u200D\\uFEFF]/g, '').toLowerCase();
    }
    function keyIsValid(v) {
        return /^[a-f0-9]{64}$/.test(String(v));
    }
    function clipboardKey() {
        try {
            var value = normalizeKey(h.getClipboard());
            return keyIsValid(value) ? value : '';
        } catch (e) {
            return '';
        }
    }
    function promptKey() {
        var received = h.input('Cole a chave de integração do Escala de Propósito (64 caracteres)');
        if (received == null) return null; // usuário cancelou
        var parsed = normalizeKey(received);
        if (!parsed) return null;
        if (!keyIsValid(parsed)) {
            throw new Error('A chave informada não possui 64 caracteres hexadecimais. Use COPIAR CHAVE no portal e execute o script novamente. Foram recebidos ' + parsed.length + ' caracteres (a chave não será exibida).');
        }
        return parsed;
    }
    function getNewKey(allowClipboard) {
        if (allowClipboard) {
            var copied = clipboardKey();
            if (copied && h.confirm('Encontrei uma chave de integração copiada no computador. Usar essa chave para conectar o Escala de Propósito?')) {
                return copied;
            }
        }
        return promptKey();
    }
    var token = normalizeKey(h.restore(storageKey));
    if (!keyIsValid(token)) {
        token = getNewKey(true);
        if (token == null) return;
        h.store(storageKey, token);
    }

    // Holyrics permite requisições HTTPS diretamente a partir da versão 2.23.
    // Algumas hospedagens PHP removem Authorization; X-Holyrics-Key é aceito
    // pela nossa API, sem colocar a chave na URL ou nos logs de navegação.
    function rawGet(url, headers, ms) {
        return h.apiRequest(url, {
            type: 'GET',
            headers: headers,
            timeout: ms || 15000,
            response_data_type: 'string;utf-8'
        });
    }
    function lastErrorSafe() {
        var message = '';
        try { message = String(h.getApiRequestLastError() || ''); } catch (e) {}
        // Nunca mostra uma chave no diagnóstico.
        if (token) message = message.split(token).join('[chave oculta]');
        return message.substring(0, 220);
    }
    function checkHost() {
        var reply = rawGet(base + '?action=health', {'Accept':'application/json'}, 8000);
        if (reply == null) {
            var reason = lastErrorSafe();
            throw new Error('O Holyrics não conseguiu abrir o endereço HTTPS. Em Arquivo > Configurações > Avançado > JavaScript > Configurações > Requisições permitidas, autorize escaladeproposito.com.br (sem www). Confira também versão 2.23 ou superior. ' + (reason ? 'Detalhe: ' + reason : ''));
        }
        var obj;
        try { obj = typeof reply === 'string' ? JSON.parse(reply) : reply; }
        catch (e) { throw new Error('O servidor respondeu, mas não retornou JSON válido no teste de conexão.'); }
        if (!obj || !obj.data || obj.data.health !== 'ok') {
            throw new Error('O servidor respondeu, mas a API de diagnóstico não está atualizada para a versão 1.4.84.');
        }
        return true;
    }
    function rawPost(action, serviceId) {
        // A chave segue no corpo HTTPS, NUNCA na URL.
        // Contorna provedores que descartam Authorization e cabeçalhos customizados.
        return h.apiRequest(base, {
            type: 'POST',
            headers: {'Content-Type':'application/json', 'Accept':'application/json'},
            data: JSON.stringify({action:action,service_id:serviceId || '',access_key:token}),
            timeout: 20000,
            response_data_type: 'string;utf-8'
        });
    }
    function authorizedRequest(action, serviceId) {
        var url = base + '?action=' + encodeURIComponent(action);
        if (serviceId) url += '&service_id=' + encodeURIComponent(serviceId);
        var raw = rawGet(url, {
            'X-Holyrics-Key': token,
            'Authorization': 'Bearer ' + token,
            'Accept': 'application/json'
        }, 20000);
        // Um servidor pode responder 401 ao GET por não receber cabeçalhos.
        if (raw == null) raw = rawPost(action, serviceId);
        return raw;
    }
    function request(action, serviceId) {
        var raw = authorizedRequest(action, serviceId);
        if (raw == null) {
            var reason = lastErrorSafe();
            checkHost();
            // A instância Holyrics pode ter guardado uma chave antiga depois
            // que o MASTER clicou em Gerar/renovar chave no portal.
            var fresh = clipboardKey();
            if (!fresh || fresh === token) {
                fresh = promptKey();
            } else if (!h.confirm('A consulta falhou usando a chave salva. Encontrei uma chave diferente copiada do portal. Substituir pela chave copiada?')) {
                fresh = promptKey();
            }
            if (fresh == null) {
                // Não pede nem exibe a chave quando o operador cancela.
                throw new Error('A consulta protegida não foi autorizada. Copie a chave ativa da igreja no portal e execute o script novamente. ' + (reason ? 'Detalhe: ' + reason : ''));
            }
            token = fresh;
            raw = authorizedRequest(action, serviceId);
            if (raw == null) {
                h.store(storageKey, '');
                throw new Error('A nova chave também não foi aceita. Confira Validação da chave no portal; se ela estiver válida, há um bloqueio ou erro no endpoint protegido. ' + (lastErrorSafe() || ''));
            }
            h.store(storageKey, token);
        }
        var payload;
        try { payload = typeof raw === 'string' ? JSON.parse(raw) : raw; }
        catch (err) { throw new Error('A API respondeu com um formato inesperado. Verifique o endpoint e as configurações de segurança da hospedagem.'); }
        if (payload.error) {
            var message = payload.error.message || 'Acesso negado.';
            if (/chave/i.test(message)) {
                h.store(storageKey, '');
                message += ' Execute novamente para informar uma nova chave.';
            }
            throw new Error(message);
        }
        return payload.data || {};
    }

    try {
        var data = request('services', null);
        var services = data.services || [];
        if (!services.length) {
            h.ok('Nenhuma escala publicada encontrada para os próximos 90 dias nesta igreja.');
            return;
        }
        var options = [];
        for (var i = 0; i < services.length; i++) {
            var s = services[i];
            options.push({id: s.id, label: s.data + ' — ' + s.culto + (s.horario ? ' — ' + s.horario : '')});
        }
        var chosen = h.itemChooser('Escala de Propósito — selecione o culto', options);
        if (!chosen) return;
        var rep = request('songs', chosen.id);
        var songs = rep.songs || [];
        if (!songs.length) {h.ok('Este culto não possui músicas no repertório publicado.');return;}
        if (!h.confirm('Importar ' + songs.length + ' música(s) de ' + chosen.label + ' para a lista atual?')) return;

        var added = 0, missing = [], cancelled = [];
        for (var j = 0; j < songs.length; j++) {
            var song = songs[j];
            var matches = h.hly('SearchSong', {text: song.titulo});
            var list = matches && matches.data ? matches.data : [];
            if (!list.length) {missing.push(song.titulo);continue;}
            var result = null;
            if (list.length === 1) result = list[0];
            else {
                // Não escolhe automaticamente uma versão incorreta quando há múltiplos resultados.
                var choices = [];
                for (var k = 0; k < list.length; k++) {
                    var m = list[k];
                    choices.push({id:m.id, label:m.title + (m.artist ? ' — ' + m.artist : '')});
                }
                result = h.itemChooser('Selecione a versão de: ' + song.titulo, choices);
            }
            if (result && result.id != null) {
                var response = h.hly('AddLyricsToPlaylist', {id: result.id});
                if (response && response.error) missing.push(song.titulo);
                else added++;
            } else cancelled.push(song.titulo);
        }
        var message = 'Importação concluída: ' + added + ' de ' + songs.length + ' música(s) adicionada(s) à lista.';
        if (missing.length) message += '\n\nNão encontradas na biblioteca: ' + missing.join(', ');
        if (cancelled.length) message += '\n\nSeleção cancelada: ' + cancelled.join(', ');
        h.ok(message);
    } catch (e) {
        var safeError = String(e.message || e);
        if (token) safeError = safeError.split(String(token)).join('[chave oculta]');
        h.error('Escala de Propósito: ' + safeError);
    }
}

/* Ação (Receptor): o editor de testes do Holyrics invoca scriptAction.
 * A execução comum do Script pode continuar usando foo().
 */
function scriptAction(obj) {
    return foo();
}
