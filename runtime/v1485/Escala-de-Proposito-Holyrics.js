/* ESCALA DE PROPÓSITO CONNECT — V1.0.4 (para Holyrics)
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
 * Escala de Propósito Connect — Holyrics (v1.0.4)
 * Requer Holyrics 2.23.0+ (JSLib apiRequest URL externa) e liberação do host.
 * Menu Ferramentas > Diversos > Script: crie item "Escala de Propósito".
 * Na primeira execução, informe a chave gerada em Configurações do Escala de Propósito.
 * Esse script NÃO adiciona letras novas nem limpa a lista atual.
 */
function foo() {
    var base = 'https://escaladeproposito.com.br/api/holyrics-repertoire-v1481.php';
    var storageKey = 'escala-de-proposito-holyrics-token-v1';
    var token = h.restore(storageKey);
    if (token == null || String(token).trim() === '') {
        token = h.input('Cole a chave Holyrics gerada no Escala de Propósito');
        if (token == null || String(token).trim() === '') return;
        token = String(token).trim();
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
            var fresh = h.input('Não consegui autenticar esta igreja. Cole a chave atual da integração Holyrics (se ela foi renovada, use a NOVA chave). Deixe vazio para cancelar.');
            if (fresh == null || String(fresh).trim() === '') {
                throw new Error('A API respondeu, mas a consulta protegida falhou. Verifique a chave no portal, use Validar chave e reabra o script. ' + (reason ? 'Detalhe: ' + reason : ''));
            }
            fresh = String(fresh).trim().toLowerCase();
            if (!/^[a-f0-9]{64}$/.test(fresh)) {
                throw new Error('Formato de chave inválido: use a chave de 64 caracteres criada no portal.');
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
        h.error('Escala de Propósito: ' + (e.message || e));
    }
}

/* Ação (Receptor): o editor de testes do Holyrics invoca scriptAction.
 * A execução comum do Script pode continuar usando foo().
 */
function scriptAction(obj) {
    return foo();
}
