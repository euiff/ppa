/*
 * Escala de Propósito Connect — Holyrics (v1.0)
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

    function request(action, serviceId) {
        var url = base + '?action=' + encodeURIComponent(action);
        if (serviceId) url += '&service_id=' + encodeURIComponent(serviceId);
        var raw = h.apiRequest(url, {
            type: 'GET',
            headers: {'Authorization': 'Bearer ' + token, 'Accept': 'application/json'},
            timeout: 15000,
            response_data_type: 'string;utf-8'
        });
        if (raw == null) throw new Error('Não foi possível conectar. Confira o acesso HTTPS liberado nas configurações JavaScript do Holyrics.');
        var payload;
        try { payload = typeof raw === 'string' ? JSON.parse(raw) : raw; }
        catch (err) { throw new Error('O servidor não retornou um JSON válido.'); }
        if (payload.error) {
            var message = payload.error.message || 'Acesso negado.';
            if (String(message).indexOf('Chave') >= 0 || String(message).indexOf('chave') >= 0) {
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
