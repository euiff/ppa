/*
 * Escala de Proposito — MODULO para Holyrics 2.23+
 * Este codigo e privado da igreja: contem credencial confidencial.
 * No Holyrics: Ferramentas > Modulos > Adicionar novo modulo.
 * Cole o codigo como MODULO (nao como item de Script/Receptor).
 * Depois ative o modulo e use a acao "Importar repertorio".
 *
 * Nao publique ou envie este arquivo em grupos.
 */
function info() {
    return {
        id: 'escala-de-proposito-holyrics-connect',
        name: 'Escala de Proposito',
        description: 'Importe o repertorio publicado no Escala de Proposito para a playlist do Holyrics.',
        min_version: '2.23.0',
        allowed_requests: ['https://escaladeproposito.com.br/'],
        available_in_main_window: true,
        available_in_bible_window: false
    };
}

function actions(module) {
    return [{
        id: 'importar_repertorio',
        name: 'Importar repertorio da escala',
        icon: 'playlist_add',
        action: function (evt) {
            edp_importar_repertorio();
        }
    }];
}

function edp_importar_repertorio() {
    var api = 'https://escaladeproposito.com.br/api/holyrics-repertoire-v1481.php';
    var token = 'ESCALA_MODULO_TOKEN_SUBSTITUIR_NO_SERVIDOR';

    function requisitar(acao, id) {
        var url = api + '?action=' + encodeURIComponent(acao);
        if (id) url += '&service_id=' + encodeURIComponent(id);
        var result = h.apiRequest(url, {
            type: 'GET',
            headers: {
                'Authorization': 'Bearer ' + token,
                'X-Holyrics-Key': token,
                'Accept': 'application/json'
            },
            timeout: 20000,
            response_data_type: 'string;utf-8'
        });
        if (result == null) {
            result = h.apiRequest(api, {
                type: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                data: JSON.stringify({
                    action: acao,
                    service_id: id || '',
                    access_key: token
                }),
                timeout: 20000,
                response_data_type: 'string;utf-8'
            });
        }
        if (result == null) {
            throw new Error('Nao foi possivel consultar o servidor. Confira HTTPS liberado no Holyrics.');
        }
        var payload;
        try {
            if (typeof result === 'object' && result.data !== undefined) payload = result;
            else payload = JSON.parse(String(result));
        } catch (e) {
            throw new Error('O servidor nao retornou JSON valido.');
        }
        if (!payload || payload.error) {
            throw new Error(payload && payload.error ? payload.error.message : 'Erro desconhecido na API.');
        }
        return payload.data || {};
    }

    try {
        var resposta = requisitar('services', null);
        var cultos = resposta.services || [];
        if (!cultos.length) {
            h.ok('Nenhuma escala publicada encontrada para esta igreja.');
            return;
        }
        var opcoes = [];
        for (var i=0; i<cultos.length; i++) {
            var culto=cultos[i];
            opcoes.push({
                id: culto.id,
                label: culto.data + ' - ' + culto.culto + (culto.horario ? ' - ' + culto.horario : '')
            });
        }
        var selecionado=h.itemChooser('Escala de Proposito - selecione o culto', opcoes);
        if (!selecionado || selecionado.id == null) return;

        var musicas=(requisitar('songs', selecionado.id).songs || []);
        if (!musicas.length) {
            h.ok('O culto selecionado ainda nao tem musicas no repertorio.');
            return;
        }
        if (!h.confirm('Adicionar '+musicas.length+' musica(s) a playlist atual do Holyrics?')) return;

        var adicionadas=0;
        var naoEncontradas=[];
        for (var j=0; j<musicas.length; j++) {
            var musica=musicas[j];
            var encontrado=h.hly('SearchSong', {text:musica.titulo});
            var lista=encontrado && encontrado.data ? encontrado.data : [];
            if (!lista.length) {
                naoEncontradas.push(musica.titulo);
                continue;
            }
            var item;
            if (lista.length===1) item=lista[0];
            else {
                var alternativas=[];
                for (var k=0; k<lista.length; k++) {
                    alternativas.push({
                        id:lista[k].id,
                        label:lista[k].title+(lista[k].artist?' - '+lista[k].artist:'')
                    });
                }
                item=h.itemChooser('Selecione a versao: '+musica.titulo, alternativas);
            }
            if (!item || item.id==null) continue;
            var added=h.hly('AddLyricsToPlaylist', {id:item.id});
            if (added && added.error) naoEncontradas.push(musica.titulo);
            else adicionadas++;
        }
        var mensagem='Importacao concluida: '+adicionadas+' de '+musicas.length+' musica(s).';
        if (naoEncontradas.length) mensagem+='\nNao encontradas: '+naoEncontradas.join(', ');
        h.ok(mensagem);
    } catch(e) {
        var msg=String(e.message || e);
        msg=msg.split(token).join('[credencial oculta]');
        h.error('Escala de Proposito: '+msg);
    }
}
