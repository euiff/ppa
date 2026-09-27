from pathlib import Path

root=Path('pkg')
p=root/'api'/'volunteer_menu_v1435.php'
s=p.read_text(encoding='utf-8')

def rep(old,new,label):
    global s
    c=s.count(old)
    if c!=1:
        raise SystemExit(f'{label}: anchor count={c}')
    s=s.replace(old,new,1)

old='''        if($yt!=='')$m.="\n▶️ YouTube: {$yt}";
        if($cifra!=='')$m.="\n🎸 Cifra: {$cifra}";
        if($yt===''&&$cifra==='')$m.="\n🔗 Links de estudo: _não cadastrados_";'''
new='''        if($yt!=='')$m.="\n▶️ YouTube: *Clique aqui no botão abaixo*";
        if($cifra!=='')$m.="\n🎸 Cifra: *Clique aqui no botão abaixo*";
        if($yt===''&&$cifra==='')$m.="\n🔗 Links de estudo: _não cadastrados_";'''
rep(old,new,'clean repertoire links')

anchor='function v1435_show_pdf_choices(string $sender,array $profiles,?array $session=null): bool {'
helpers=r'''function v1462_valid_url(string $url): bool {
    return $url!=='' && filter_var($url,FILTER_VALIDATE_URL)!==false && preg_match('~^https?://~i',$url);
}
function v1462_send_song_links(string $sender,string $igrejaId,array $song,int $pos): bool {
    $yt=trim((string)($song['link_youtube']??''));
    $cifra=trim((string)($song['link_cifra']??''));
    $buttons=[];
    if(v1462_valid_url($yt))$buttons[]=['type'=>'url','displayText'=>'▶️ YouTube — Clique aqui','url'=>$yt];
    if(v1462_valid_url($cifra))$buttons[]=['type'=>'url','displayText'=>'🎸 Cifra — Clique aqui','url'=>$cifra];
    if(!$buttons)return true;
    $title=trim((string)($song['titulo']??''))?:('Música '.$pos);
    $tom=trim((string)($song['tom']??''));
    try{
        if(!function_exists('v1424_cfg')||!function_exists('v1424_http_json')||!function_exists('v1424_phone'))throw new RuntimeException('Transporte Evolution indisponível');
        $base=rtrim(v1424_cfg('evolution_url',$igrejaId),'/');
        $key=v1424_cfg('evolution_api_key',$igrejaId);
        $instance=v1424_cfg('evolution_instance',$igrejaId);
        $number=v1424_phone($sender);
        if($base===''||$key===''||$instance===''||strlen($number)<10)throw new RuntimeException('Evolution API não configurada');
        $endpoint=$base.'/message/sendButtons/'.rawurlencode($instance);
        $payload=[
            'number'=>$number,
            'title'=>"🎵 {$pos}. {$title}".($tom!==''?"\n🎼 Tom: {$tom}":''),
            'description'=>'Escolha o link de estudo:',
            'footer'=>'Escala de Propósito',
            'buttons'=>$buttons
        ];
        $res=v1424_http_json($endpoint,$payload,['Content-Type: application/json','apikey: '.$key]);
        try{if(function_exists('log_whatsapp'))log_whatsapp('whatsapp_repertoire_links',$number,$title,$res,$igrejaId,['song_position'=>$pos,'button_count'=>count($buttons),'transport'=>'sendButtons']);}catch(Throwable $ignored){}
        if(!empty($res['ok']))return true;
    }catch(Throwable $e){}
    $fallback="🔗 *Links de estudo — {$title}*";
    if(v1462_valid_url($yt))$fallback.="\n▶️ YouTube: {$yt}";
    if(v1462_valid_url($cifra))$fallback.="\n🎸 Cifra: {$cifra}";
    return function_exists('v1311p_send')?v1311p_send($sender,$igrejaId,$fallback,'volunteer_music_link_fallback',['song_position'=>$pos]):false;
}
function v1462_send_repertoire(string $sender,array $r): bool {
    $igrejaId=(string)($r['igreja_id']??'');
    $ok=function_exists('v1311p_send')?v1311p_send($sender,$igrejaId,v1436_repertoire_text($r),'volunteer_music_repertoire',['escala_id'=>$r['escala_id']??null,'escala_item_id'=>$r['item_id']??null]):false;
    $songs=[];try{$songs=function_exists('v1421_same_day_repertoire')?v1421_same_day_repertoire($r):[];}catch(Throwable $e){}
    $pos=0;
    foreach($songs as $song){
        $title=trim((string)($song['titulo']??''));if($title==='')continue;$pos++;
        $yt=trim((string)($song['link_youtube']??''));$cifra=trim((string)($song['link_cifra']??''));
        if(v1462_valid_url($yt)||v1462_valid_url($cifra))v1462_send_song_links($sender,$igrejaId,$song,$pos);
    }
    return $ok;
}
'''
rep(anchor,helpers+anchor,'button helpers')

old="return v1311p_send($sender,(string)($r['igreja_id']??''),v1436_repertoire_text($r),'volunteer_music_repertoire',['escala_id'=>$r['escala_id'], 'escala_item_id'=>$r['item_id']]);"
new="return v1462_send_repertoire($sender,$r);"
rep(old,new,'repertoire sender')

p.write_text(s,encoding='utf-8')

(root/'VERSION').write_text('1.4.62\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.62.md').write_text('''# Escala de Propósito v1.4.62 — Links de estudo por botão no WhatsApp

- Na opção **5 — Repertório**, o endereço completo deixa de aparecer na mensagem principal.
- Quando houver link de YouTube, o sistema tenta enviar um botão **▶️ YouTube — Clique aqui**.
- Quando houver link de cifra, o sistema tenta enviar um botão **🎸 Cifra — Clique aqui**.
- Os botões usam a rota sendButtons da Evolution API com botão do tipo URL.
- A mensagem principal continua mostrando música, artista e **Tom para tocar**.
- O Spotify continua fora do repertório enviado.
- Se a instalação/Evolution não aceitar o botão URL, o sistema usa **fallback automático** e envia o endereço normal, garantindo que o músico não perca o link.
- Não altera confirmações, recusas, pendências, PDFs ou escalas.
''',encoding='utf-8')
