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

// Busca em letras JA CADASTRADAS no Holyrics. Nao copia letras externas.
function edp_normalizar_nome(texto) {
    return String(texto || '').toLowerCase()
        .replace(/[áàâãä]/g,'a').replace(/[éèêë]/g,'e')
        .replace(/[íìîï]/g,'i').replace(/[óòôõö]/g,'o')
        .replace(/[úùûü]/g,'u').replace(/ç/g,'c')
        .replace(/[^a-z0-9]+/g,' ').replace(/^\s+|\s+$/g,'')
        .replace(/\s+/g,' ');
}
function edp_variacoes_nome(texto) {
    var full=String(texto || '');
    var pieces=[full];
    var parentheses=full.match(/^(.*?)\s*\(([^)]+)\)/);
    if(parentheses){
        pieces.push(parentheses[1]);
        pieces.push(parentheses[2]);
    }
    if(full.indexOf(' - ')>=0)pieces.push(full.split(' - ')[0]);
    var unique={};var out=[];
    for(var i=0;i<pieces.length;i++){
        var name=edp_normalizar_nome(pieces[i]);
        if(name.length>=5 && !unique[name]){unique[name]=true;out.push(name);}
    }
    return out;
}
function edp_pontuar_nome(candidato,variacoes) {
    var got=edp_normalizar_nome(candidato);
    if(!got)return 0;
    for(var i=0;i<variacoes.length;i++)if(got===variacoes[i])return 100;
    // Sugere aproximacoes, mas nao escolhe automaticamente um titulo impreciso.
    for(var j=0;j<variacoes.length;j++){
        var expected=variacoes[j];
        var short=got.length<expected.length?got:expected;
        var long=got.length>=expected.length?got:expected;
        if(short.length>=8 && long.indexOf(short)===0 && short.length/long.length>=0.60)return 70;
    }
    return 0;
}
function edp_procurar_musica(titulo,biblioteca) {
    var variations=edp_variacoes_nome(titulo);
    var found=[];var seen={};
    function incluir(item) {
        if(!item || item.id==null || !item.title)return;
        var score=edp_pontuar_nome(item.title,variations);
        if(!score)return;
        var id=String(item.id);
        if(!seen[id]){seen[id]=true;found.push({song:item,score:score});}
        else for(var j=0;j<found.length;j++)if(String(found[j].song.id)===id && score>found[j].score)found[j].score=score;
    }
    for(var i=0;i<biblioteca.length;i++)incluir(biblioteca[i]);
    // Busca alternativa pelo nome se a lista local nao estiver acessivel.
    if(!biblioteca.length){
        for(var k=0;k<variations.length;k++){
            var resp=h.hly('SearchLyrics',{
                text: variations[k],title:true,artist:false,note:false,lyrics:false
            });
            var items=resp && resp.data && resp.data.length ? resp.data : [];
            for(var z=0;z<items.length;z++)incluir(items[z]);
        }
    }
    found.sort(function(a,b){return b.score-a.score;});
    return found;
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
        // GetSongs acessa a biblioteca de letras salva no computador Holyrics.
        var todas=h.hly('GetSongs');
        var local=todas && todas.data && todas.data.length ? todas.data : [];
        if(!local.length){
            // Alguns perfis nao disponibilizam GetSongs; tente busca por titulo.
            var primeira=edp_procurar_musica(musicas[0].titulo,[]);
            if(!primeira.length){
                h.ok('O Escala de Proposito recebeu '+musicas.length+' musica(s) do culto, mas nao encontrou letras cadastradas nesta biblioteca do Holyrics.\n\nAbra a aba Letras do Holyrics e cadastre/importe as letras antes de tentar adicionar a playlist. Nenhuma musica foi criada automaticamente.');
                return;
            }
        }
        if (!h.confirm('Repertorio recebido: '+musicas.length+' musica(s).\nProcurar na biblioteca do Holyrics e adicionar a lista atual?'))return;

        var adicionadas=0;
        var naoEncontradas=[];
        var cancelar=[];
        var erros=[];
        for(var j=0;j<musicas.length;j++){
            var musica=musicas[j];
            var matches=edp_procurar_musica(musica.titulo,local);
            if(!matches.length){
                naoEncontradas.push(musica.titulo);
                continue;
            }
            var selecionada=null;
            if(matches.length===1 && matches[0].score===100){
                selecionada=matches[0].song;
            }else{
                // Mais de uma versao ou aproximacao: usuario escolhe.
                var opcoes=[];
                for(var k=0;k<matches.length;k++){
                    var x=matches[k].song;
                    opcoes.push({id:x.id,label:x.title+(x.artist?' - '+x.artist:'')});
                }
                var chosen=h.itemChooser('Confirme a versao para: '+musica.titulo,opcoes);
                if(chosen && chosen.id!=null)selecionada=chosen;
            }
            if(!selecionada){
                cancelar.push(musica.titulo);
                continue;
            }
            var adicionou=h.hly('AddLyricsToPlaylist',{id:String(selecionada.id)});
            if(adicionou && (adicionou.error || adicionou.status==='error'))erros.push(musica.titulo);
            else adicionadas++;
        }
        var resumo='Repertorio consultado: '+musicas.length+' musica(s).\nAdicionadas ao Holyrics: '+adicionadas+'.';
        if(naoEncontradas.length)resumo+='\nLetras ainda nao encontradas: '+naoEncontradas.join(', ')+'.';
        if(cancelar.length)resumo+='\nSelecao nao concluida: '+cancelar.join(', ')+'.';
        if(erros.length)resumo+='\nFalha ao adicionar: '+erros.join(', ')+'.';
        if(naoEncontradas.length)resumo+='\nCadastre/importe as letras ausentes na aba Letras do Holyrics para adicionar posteriormente.';
        h.ok(resumo);
    } catch(e) {
        var msg=String(e.message || e);
        msg=msg.split(token).join('[credencial oculta]');
        h.error('Escala de Proposito: '+msg);
    }
}
