from pathlib import Path
import re

root=Path('pkg')
scale=root/'api'/'whatsapp_scale_message_v1421.php'
menu=root/'api'/'volunteer_menu_v1435.php'

# Garante que o repertório do WhatsApp receba também links de cifra e Spotify.
s=scale.read_text(encoding='utf-8')
if 'm.link_spotify' not in s or 'm.link_cifra' not in s:
    n=s.count('m.tom,m.link_youtube')
    if n < 1:
        raise SystemExit('anchor dos campos de música não encontrado')
    s=s.replace('m.tom,m.link_youtube','m.tom,m.link_youtube,m.link_spotify,m.link_cifra')
scale.write_text(s,encoding='utf-8')

# Deixa a opção 5 explícita no menu.
m=menu.read_text(encoding='utf-8')
m=m.replace('*5* - 🎵 Repertório de músicas','*5* - 🎵 Repertório de músicas + tons')
m=m.replace('*5* - 🎵 Repertório das escalas','*5* - 🎵 Repertório + tons das escalas')

# Substitui a apresentação do repertório por uma ficha de treino mais completa.
pat=re.compile(r"function v1436_repertoire_text\(array \$r\): string \{.*?\n\}\nfunction v1435_show_pdf_choices",re.S)
new=r'''function v1436_repertoire_text(array $r): string {
    $date=!empty($r['data'])?date('d/m/Y',strtotime((string)$r['data'])):'—';
    $time=trim((string)($r['horario']??''));$time=$time!==''?substr($time,0,5):'—';
    $culto=trim((string)($r['culto_nome']??''))?:'Culto';
    $songs=[];try{$songs=function_exists('v1421_same_day_repertoire')?v1421_same_day_repertoire($r):[];}catch(Throwable$e){}
    $m="🎵 *REPERTÓRIO PARA TREINO*\n\n📋 *{$culto}*\n📅 {$date}\n🕒 {$time}";
    if(!$songs)return $m."\n\n_Ainda não há músicas cadastradas no repertório desse culto._\n\nDigite *MENU* para voltar ao menu principal.";
    $m.="\n🎶 ".count($songs)." música".(count($songs)===1?'':'s')." no repertório";
    $n=0;
    foreach($songs as $song){
        $title=trim((string)($song['titulo']??''));if($title==='')continue;$n++;
        $artist=trim((string)($song['artista']??''));
        $tom=trim((string)($song['tom']??''));
        $yt=trim((string)($song['link_youtube']??''));
        $cifra=trim((string)($song['link_cifra']??''));
        $spotify=trim((string)($song['link_spotify']??''));
        $m.="\n\n*{$n}. {$title}*";
        $m.="\n🎤 Artista: ".($artist!==''?$artist:'_não informado_');
        $m.="\n🎼 *Tom para tocar: ".($tom!==''?$tom:'não informado')."*";
        if($cifra!=='')$m.="\n🎸 Cifra: {$cifra}";
        if($yt!=='')$m.="\n▶️ YouTube: {$yt}";
        if($spotify!=='')$m.="\n🟢 Spotify: {$spotify}";
        if($cifra===''&&$yt===''&&$spotify==='')$m.="\n🔗 Links de estudo: _não cadastrados_";
    }
    $m.="\n\n🎯 _Use o tom informado acima para ensaiar na tonalidade definida para o culto._";
    $m.="\n_As músicas permanecem na mesma ordem definida no repertório da escala._";
    $m.="\n\n➡️ Digite outro número da lista para consultar outra escala ou *MENU* para voltar.";
    return $m;
}
function v1435_show_pdf_choices'''
m2,n=pat.subn(new,m,count=1)
if n!=1:
    raise SystemExit(f'função v1436_repertoire_text não encontrada: {n}')
menu.write_text(m2,encoding='utf-8')

(root/'VERSION').write_text('1.4.60\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.60.md').write_text('''# Escala de Propósito v1.4.60 — Repertório de treino no WhatsApp

- Melhora a opção **5 — Repertório** do MENU do WhatsApp.
- Cada música passa a mostrar de forma destacada o **Tom para tocar**, para os músicos treinarem na tonalidade correta definida para o culto.
- A mensagem também mostra **artista** e, quando estiverem cadastrados, **Cifra, YouTube e Spotify**.
- Quando o tom não estiver cadastrado, o WhatsApp mostra **Tom para tocar: não informado** em vez de simplesmente esconder a informação.
- Quando não houver links de estudo, a mensagem informa **Links de estudo: não cadastrados**.
- O cabeçalho mostra culto, data, horário e quantidade de músicas.
- Mantém a ordem manual do repertório definida no sistema.
- A mesma melhoria vale para voluntários e para o cargo Secretária ao consultar repertórios pelo WhatsApp.
- Não altera confirmações 1/2, recusas, pendências, geração de PDF, escalas ou transporte da Evolution API.
''',encoding='utf-8')
