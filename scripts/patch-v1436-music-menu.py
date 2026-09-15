from pathlib import Path

root = Path('pkg')
menu = root / 'api' / 'volunteer_menu_v1435.php'
scale = root / 'api' / 'whatsapp_scale_message_v1421.php'

s = scale.read_text(encoding='utf-8')
s = s.replace('SELECT si.musica_id,si.ordem,m.titulo,m.artista,m.tom',
              'SELECT si.musica_id,si.ordem,m.titulo,m.artista,m.tom,m.link_youtube')
scale.write_text(s, encoding='utf-8')

s = menu.read_text(encoding='utf-8')
s = s.replace("return in_array($state,['vmenu_home','vmenu_scales','vmenu_pdf','vmenu_unavailability'],true);",
              "return in_array($state,['vmenu_home','vmenu_scales','vmenu_pdf','vmenu_unavailability','vmenu_music'],true);")
s = s.replace("*4* - 🚫 Adicionar dias em que estou indisponível\\n\\n_Responda somente com 1, 2, 3 ou 4._",
              "*4* - 🚫 Adicionar dias em que estou indisponível\\n*5* - 🎵 Repertório de músicas\\n\\n_Responda somente com 1, 2, 3, 4 ou 5._")

needle = "function v1435_show_pdf_choices(string $sender,array $profiles,?array $session=null): bool {\n"
if needle not in s:
    raise SystemExit('Ponto de inserção do repertório não encontrado')
insert = r'''function v1436_show_music_choices(string $sender,array $profiles,?array $session=null): bool {
    $days=v1435_confirmed_days($profiles);$ig=v1435_igreja_id($profiles);
    if(!$days){if(function_exists('v1311p_save_session'))v1311p_save_session($sender,$profiles,'vmenu_home',[],null,null,$session);return v1311p_send($sender,$ig,"🎵 Não encontrei escala confirmada sua nos próximos 30 dias para consultar repertório.\n\n".v1435_home_text($profiles),'volunteer_no_music_scale');}
    if(function_exists('v1311p_save_session'))v1311p_save_session($sender,$profiles,'vmenu_music',array_slice($days,0,20),null,null,$session);
    $msg=v1435_days_text($days,'🎵 *Escolha a escala para ver o repertório de músicas:*')."\n➡️ Responda com o *número da escala*.\nDigite *MENU* para voltar.";
    return v1311p_send($sender,$ig,$msg,'volunteer_music_choices',['count'=>count($days)]);
}
function v1436_repertoire_text(array $r): string {
    $date=!empty($r['data'])?date('d/m/Y',strtotime((string)$r['data'])):'—';$time=trim((string)($r['horario']??''));$time=$time!==''?substr($time,0,5):'—';$culto=trim((string)($r['culto_nome']??''))?:'Culto';
    $songs=[];try{$songs=function_exists('v1421_same_day_repertoire')?v1421_same_day_repertoire($r):[];}catch(Throwable$e){}
    $m="🎵 *REPERTÓRIO DE MÚSICAS*\n\n📋 *{$culto}*\n📅 {$date}\n🕒 {$time}";
    if(!$songs)return $m."\n\n_Ainda não há músicas cadastradas no repertório desse culto._\n\nDigite *MENU* para voltar ao menu principal.";
    $n=0;foreach($songs as $song){$title=trim((string)($song['titulo']??''));if($title==='')continue;$n++;$artist=trim((string)($song['artista']??''));$tom=trim((string)($song['tom']??''));$yt=trim((string)($song['link_youtube']??''));$m.="\n\n*{$n}. {$title}*";if($artist!=='')$m.="\n👤 {$artist}";if($tom!=='')$m.="\n🎼 Tom: {$tom}";if($yt!=='')$m.="\n▶️ YouTube: {$yt}";else$m.="\n▶️ YouTube: _link não cadastrado_";}
    $m.="\n\n_As músicas aparecem na mesma ordem definida no repertório da escala._\n\n➡️ Digite outro número da lista para consultar outra escala ou *MENU* para voltar.";
    return $m;
}
'''
s = s.replace(needle, insert + needle, 1)

old = "if($t==='4')return v1435_show_unavailability_prompt($sender,$profiles,$session);\n        return v1311p_send($sender,v1435_igreja_id($profiles),\"🤔 Escolha *1, 2, 3 ou 4*.\\n\\n\".v1435_home_text($profiles),'volunteer_home_invalid');"
new = "if($t==='4')return v1435_show_unavailability_prompt($sender,$profiles,$session);\n        if($t==='5')return v1436_show_music_choices($sender,$profiles,$session);\n        return v1311p_send($sender,v1435_igreja_id($profiles),\"🤔 Escolha *1, 2, 3, 4 ou 5*.\\n\\n\".v1435_home_text($profiles),'volunteer_home_invalid');"
if old not in s:
    raise SystemExit('Bloco do menu principal não encontrado')
s = s.replace(old, new, 1)

needle = "    if($state==='vmenu_pdf'){\n"
if needle not in s:
    raise SystemExit('Estado PDF não encontrado')
insert = r'''    if($state==='vmenu_music'){
        $opts=json_decode((string)($session['options_json']??''),true);if(!is_array($opts))$opts=[];
        if(!preg_match('/^\d{1,2}$/',$t))return v1311p_send($sender,v1435_igreja_id($profiles),"🤔 Responda somente com o *número da escala* ou digite MENU.",'volunteer_music_select_invalid');
        $idx=(int)$t-1;if($idx<0||$idx>=count($opts))return v1311p_send($sender,v1435_igreja_id($profiles),"⚠️ Essa opção não existe. Escolha um número entre *1 e ".count($opts)."*.",'volunteer_music_select_range');
        $r=v1435_scale_row((string)$opts[$idx]['item_id']);if(!$r||($r['status_confirmacao']??'')!=='confirmado')return v1436_show_music_choices($sender,$profiles,$session);
        return v1311p_send($sender,(string)($r['igreja_id']??''),v1436_repertoire_text($r),'volunteer_music_repertoire',['escala_id'=>$r['escala_id'],'escala_item_id'=>$r['item_id']]);
    }
'''
s = s.replace(needle, insert + needle, 1)
menu.write_text(s, encoding='utf-8')

(root / 'VERSION').write_text('1.4.36\n', encoding='utf-8')
(root / 'ATUALIZACAO-v1.4.36.md').write_text('''# Escala de Propósito v1.4.36\n\n- Adiciona a opção 5 — Repertório de músicas ao MENU do voluntário no WhatsApp.\n- O voluntário escolhe uma de suas escalas confirmadas dos próximos 30 dias e recebe o repertório daquele culto.\n- As músicas são exibidas na mesma ordem definida no repertório da escala.\n- Cada item mostra nome da música, artista, tom e o link do YouTube cadastrado no painel.\n- Quando a música ainda não possui link do YouTube, a mensagem informa que o link não está cadastrado.\n- Mantém as opções 1 Pendências, 2 Dias escalados, 3 PDF completo e 4 Indisponibilidade.\n- Mantém intacto o núcleo de confirmação/recusa e a resiliência da Evolution.\n''', encoding='utf-8')
