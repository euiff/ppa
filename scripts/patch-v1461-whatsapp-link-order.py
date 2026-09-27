from pathlib import Path

root=Path('pkg')
menu=root/'api'/'volunteer_menu_v1435.php'
s=menu.read_text(encoding='utf-8')

def rep(old,new,label):
    global s
    c=s.count(old)
    if c!=1:
        raise SystemExit(f'{label}: anchor count={c}')
    s=s.replace(old,new,1)

rep("$spotify=trim((string)($song['link_spotify']??''));\n","",'remove spotify var')

old="""        if($cifra!=='')$m.="\n🎸 Cifra: {$cifra}";
        if($yt!=='')$m.="\n▶️ YouTube: {$yt}";
        if($spotify!=='')$m.="\n🟢 Spotify: {$spotify}";
        if($cifra===''&&$yt===''&&$spotify==='')$m.="\n🔗 Links de estudo: _não cadastrados_";"""
new="""        if($yt!=='')$m.="\n▶️ YouTube: {$yt}";
        if($cifra!=='')$m.="\n🎸 Cifra: {$cifra}";
        if($yt===''&&$cifra==='')$m.="\n🔗 Links de estudo: _não cadastrados_";"""
rep(old,new,'link order')

menu.write_text(s,encoding='utf-8')

(root/'VERSION').write_text('1.4.61\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.61.md').write_text('''# Escala de Propósito v1.4.61 — Ordem dos links no repertório do WhatsApp

- Ajusta a opção **5 — Repertório** do WhatsApp.
- O **Spotify deixa de ser enviado** na mensagem de repertório.
- Para cada música, os links aparecem nesta ordem:
  1. **YouTube**
  2. **Cifra**
- Mantém nome da música, artista e **Tom para tocar** em destaque.
- Quando não houver YouTube nem cifra cadastrados, continua mostrando **Links de estudo: não cadastrados**.
- Não altera confirmação 1/2, recusas, pendências, PDFs, escalas ou demais funções do WhatsApp.
''',encoding='utf-8')
