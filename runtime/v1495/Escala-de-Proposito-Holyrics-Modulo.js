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
        description: 'Sincronizacao automatica com cadastro assistido de letras no Holyrics gratuito.',
        min_version: '2.23.0',
        allowed_requests: ['https://escaladeproposito.com.br/'],
        available_in_main_window: true,
        available_in_bible_window: false
    };
}

function actions(module) {
    return [{
        id: 'importar_repertorio',
        name: 'Sincronizar repertorio automaticamente',
        icon: 'playlist_add',
        action: function (evt) {
            edp_importar_repertorio(module, false);
        }
    }, {
        id: 'cadastrar_pendentes',
        name: 'Cadastrar letras ausentes (assistido)',
        icon: 'edit',
        action: function (evt) {
            edp_importar_repertorio(module, true);
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

function edp_importar_repertorio(module, modoAssistido) {
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
        // As letras existentes sao adicionadas automaticamente.
        // As ausentes podem ser cadastradas pela API popupCreateSong (gratuita
        // no Holyrics 2.24+), com uma unica janela por vez e confirmacao humana.
        var todas=h.hly('GetSongs');
        var listagemDisponivel=todas && todas.data && typeof todas.data.length==='number';
        var local=listagemDisponivel?todas.data:[];
        // A acao escolhida pelo operador ja autoriza sincronizar esta lista.
        // No modo automatico nao ha confirmacoes repetidas.
        var criacaoAutomaticaDisponivel=!!(module && typeof module.hly==='function');

        var adicionadas=0;
        var cadastradas=0;
        var automaticamenteCriadas=0;
        var naoEncontradas=[];
        var canceladas=[];
        var erros=[];
        var indice=0;
        var popupAberto=false;

        function adicionarNaLista(id,titulo,novo) {
            try {
                var resultado=h.hly('AddLyricsToPlaylist',{id:String(id)});
                if(resultado && (resultado.error || resultado.status==='error')) {
                    erros.push(titulo);
                    return;
                }
                adicionadas++;
                if(novo)cadastradas++;
            } catch(e) {
                erros.push(titulo+' ('+String(e.message||e)+')');
            }
        }

        function finalizar() {
            var resumo='Repertorio recebido: '+musicas.length+' musica(s).\n'+
              'Adicionadas a playlist: '+adicionadas+'.';
            if(cadastradas)resumo+='\nCadastradas agora no Holyrics: '+cadastradas+'.';
            if(automaticamenteCriadas)resumo+='\nCriadas sem janela: '+automaticamenteCriadas+'.';
            if(naoEncontradas.length)resumo+='\nSem letra disponivel para cadastro: '+naoEncontradas.join(', ')+'.';
            if(canceladas.length)resumo+='\nCadastros/selecoes cancelados: '+canceladas.join(', ')+'.';
            if(erros.length)resumo+='\nFalhas: '+erros.join(', ')+'.';
            if(naoEncontradas.length)resumo+='\nPara as pendentes, abra "Cadastrar letras ausentes (assistido)" e informe a letra autorizada.';
            h.ok(resumo);
        }

        function proxima() {
            if(popupAberto)return; // nunca abre mais de uma janela
            if(indice>=musicas.length){finalizar();return;}
            var musica=musicas[indice++];
            var titulo=String(musica.titulo||'').trim();
            if(!titulo){proxima();return;}

            var matches=edp_procurar_musica(titulo,local);
            var escolhida=null;
            if(matches.length===1 && matches[0].score===100) {
                escolhida=matches[0].song;
            } else if(matches.length) {
                var opcoes=[];
                for(var x=0;x<matches.length;x++) {
                    var item=matches[x].song;
                    opcoes.push({id:item.id,label:item.title+(item.artist?' - '+item.artist:'')});
                }
                var escolhido=h.itemChooser('Confirme a versao para: '+titulo,opcoes);
                if(escolhido && escolhido.id!=null)escolhida=escolhido;
                else {
                    canceladas.push(titulo);
                    proxima();
                    return;
                }
            }
            if(escolhida) {
                adicionarNaLista(escolhida.id,titulo,false);
                proxima();
                return;
            }

            // Nunca recuperar automaticamente letras de paginas sem permissao.
            // A letra pode vir do cadastro licito do Escala de Proposito.

            // Criacao completamente automatica: funcionalidade oficial
            // disponivel somente com Holyrics Plan + permissao para este modulo.
            // Nunca cria musicas sem letras autorizadas.
            var letra=String(musica.letra||'').trim();
            if(letra.length>=5 && criacaoAutomaticaDisponivel) {
                try {
                    var partes=letra.replace(/\\r\\n/g,'\\n').split(/\\n\\s*\\n/);
                    var slides=[];
                    for(var n=0;n<partes.length;n++) {
                        var trecho=String(partes[n]).trim();
                        if(trecho) slides.push({text:trecho});
                    }
                    if(slides.length) {
                        var dadosNovaMusica={
                            title:titulo,
                            artist:String(musica.artista||''),
                            slides:slides
                        };
                        if(musica.tom && /^[A-G](#|b)?m?$/.test(String(musica.tom)))dadosNovaMusica.key=String(musica.tom);
                        var criada=module.hly('CreateSong',dadosNovaMusica);
                        var idCriado=criada && criada.data ? criada.data.id : null;
                        if(idCriado!=null && String(idCriado)!=='') {
                            adicionarNaLista(idCriado,titulo,true);
                            automaticamenteCriadas++;
                            local.push({id:String(idCriado),title:titulo,artist:dadosNovaMusica.artist});
                            proxima();
                            return;
                        }
                        // Resposta de bloqueio/plano: nao tenta criar outras
                        // dezenas de musicas com a permissao negada.
                        criacaoAutomaticaDisponivel=false;
                    }
                } catch (erroPlano) {
                    criacaoAutomaticaDisponivel=false;
                }
            }
            if(!letra) {
                if(!modoAssistido) {
                    naoEncontradas.push(titulo);
                    proxima();
                    return;
                }
                if(!h.confirm('Nao encontramos uma letra de "'+titulo+'". Deseja informar uma letra autorizada?')) {
                    naoEncontradas.push(titulo);proxima();return;
                }
                letra=h.inputTextArea('Cole a letra autorizada de: '+titulo);
                if(letra==null || !String(letra).trim()) {
                    naoEncontradas.push(titulo);proxima();return;
                }
                letra=String(letra).trim();
            }
            if(letra.length<5) {
                naoEncontradas.push(titulo);proxima();return;
            }
            // No Holyrics gratuito a API oficial popupCreateSong exige
            // revisao e clique em Salvar. Nao existe API publica de criacao
            // silenciosa gratuita; nunca simular sucesso antes da confirmacao.
            popupAberto=true;
            try {
                var song={
                    title:titulo,
                    artist:String(musica.artista||''),
                    lyrics:letra
                };
                if(musica.tom && /^[A-G](#|b)?m?$/.test(String(musica.tom)))song.key=String(musica.tom);
                h.popupCreateSong(song,function(savedId) {
                    popupAberto=false;
                    if(savedId!=null && String(savedId)!=='') {
                        adicionarNaLista(savedId,titulo,true);
                        // Evita duplicidade se o mesmo titulo aparecer outra vez.
                        local.push({id:String(savedId),title:titulo,artist:song.artist});
                    }else {
                        canceladas.push(titulo);
                    }
                    proxima();
                });
            } catch(e) {
                popupAberto=false;
                erros.push(titulo+' (cadastro nao disponivel: '+String(e.message||e)+')');
                proxima();
            }
        }
        proxima();
    } catch(e) {
        var msg=String(e.message || e);
        msg=msg.split(token).join('[credencial oculta]');
        h.error('Escala de Proposito: '+msg);
    }
}
