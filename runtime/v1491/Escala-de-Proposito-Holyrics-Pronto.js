/*
 * ESCALA DE PROPÓSITO — HOLYRICS
 * Script exclusivo gerado pela igreja. Contém credencial privada.
 * Não envie este código em grupos, redes sociais ou repositórios públicos.
 *
 * INSTALAÇÃO: No Holyrics, abra um item do tipo Script, APAGUE todo o código
 * anterior do quadro esquerdo, COLE este código e clique em SALVAR.
 * Para importar, execute o item em Scripts/Favoritos.
 * Não utilize a janela de teste "Ação (Receptor)".
 */
function foo() {
    var api = 'https://escaladeproposito.com.br/api/holyrics-repertoire-v1481.php';
    var chaveDaIgreja = 'ESCALA_TOKEN_SUBSTITUIR_NO_SERVIDOR';

    function requisitar(action, serviceId) {
        var url = api + '?action=' + encodeURIComponent(action);
        if (serviceId) url += '&service_id=' + encodeURIComponent(serviceId);
        var resposta = h.apiRequest(url, {
            type: 'GET',
            headers: {
                'Authorization': 'Bearer ' + chaveDaIgreja,
                'X-Holyrics-Key': chaveDaIgreja,
                'Accept': 'application/json'
            },
            timeout: 20000,
            response_data_type: 'string;utf-8'
        });
        // Em alguns provedores o PHP nao recebe os cabecalhos de autorizacao.
        // O fallback envia a credencial apenas no corpo de um POST HTTPS.
        if (resposta == null) {
            resposta = h.apiRequest(api, {
                type: 'POST',
                headers: {'Content-Type':'application/json','Accept':'application/json'},
                data: JSON.stringify({
                    action: action,
                    service_id: serviceId || '',
                    access_key: chaveDaIgreja
                }),
                timeout: 20000,
                response_data_type: 'string;utf-8'
            });
        }
        if (resposta == null) {
            throw new Error('A API nao respondeu ao acesso autenticado. Verifique a versao do Holyrics e a lista de requisicoes HTTPS permitidas.');
        }
        var body;
        try {
            if (resposta && typeof resposta === 'object' && resposta.data !== undefined) {
                body = resposta;
            } else {
                body = JSON.parse(String(resposta));
            }
        } catch (e) {
            throw new Error('A API nao retornou um JSON valido.');
        }
        if (!body || body.error) {
            throw new Error((body && body.error && body.error.message) || 'A consulta ao repertorio falhou.');
        }
        return body.data || {};
    }

    try {
        var dados = requisitar('services', null);
        var cultos = dados.services || [];
        if (!cultos.length) {
            h.ok('Nenhuma escala publicada encontrada para esta igreja.');
            return;
        }
        var opcoes = [];
        for (var i = 0; i < cultos.length; i++) {
            var culto = cultos[i];
            opcoes.push({
                id: culto.id,
                label: culto.data + ' - ' + culto.culto + (culto.horario ? ' - ' + culto.horario : '')
            });
        }
        var escolhido = h.itemChooser('Escala de Proposito - selecione o culto', opcoes);
        if (!escolhido || escolhido.id == null) return;
        var resultado = requisitar('songs', escolhido.id);
        var musicas = resultado.songs || [];
        if (!musicas.length) {
            h.ok('O culto escolhido nao possui repertorio publicado.');
            return;
        }
        if (!h.confirm('Adicionar ' + musicas.length + ' musica(s) a playlist atual do Holyrics?')) return;

        var adicionadas = 0;
        var ausentes = [];
        var canceladas = [];
        for (var j = 0; j < musicas.length; j++) {
            var musica = musicas[j];
            var encontrados = h.hly('SearchSong', {text: musica.titulo});
            var lista = encontrados && encontrados.data ? encontrados.data : [];
            if (!lista.length) {
                ausentes.push(musica.titulo);
                continue;
            }
            var item = null;
            if (lista.length === 1) {
                item = lista[0];
            } else {
                var alternativas = [];
                for (var k = 0; k < lista.length; k++) {
                    var encontrado = lista[k];
                    alternativas.push({
                        id: encontrado.id,
                        label: encontrado.title + (encontrado.artist ? ' - ' + encontrado.artist : '')
                    });
                }
                item = h.itemChooser('Selecione a versao de: ' + musica.titulo, alternativas);
            }
            if (item && item.id != null) {
                var adicao = h.hly('AddLyricsToPlaylist', {id:item.id});
                if (adicao && adicao.error) ausentes.push(musica.titulo);
                else adicionadas++;
            } else {
                canceladas.push(musica.titulo);
            }
        }
        var mensagem = 'Repertorio importado: ' + adicionadas + ' de ' + musicas.length + ' musica(s).';
        if (ausentes.length) mensagem += '\nNao encontradas: ' + ausentes.join(', ');
        if (canceladas.length) mensagem += '\nSelecao cancelada: ' + canceladas.join(', ');
        h.ok(mensagem);
    } catch (erro) {
        // Nunca incluir a chave privada em mensagens.
        var aviso = String(erro.message || erro);
        aviso = aviso.split(chaveDaIgreja).join('[chave oculta]');
        h.error('Escala de Proposito: ' + aviso);
    }
}
