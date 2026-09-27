from pathlib import Path
import re

root=Path('pkg')
p=root/'api'/'volunteer_menu_v1435.php'
s=p.read_text(encoding='utf-8')

def rep(old,new,label):
    global s
    c=s.count(old)
    if c!=1:
        raise SystemExit(f'{label}: anchor count={c}')
    s=s.replace(old,new,1)

pat_links=re.compile(r'''        if\(\$yt!==''\)\$m\.="\n▶️ YouTube: \*Clique aqui no botão abaixo\*";
        if\(\$cifra!==''\)\$m\.="\n🎸 Cifra: \*Clique aqui no botão abaixo\*";
        if\(\$yt===''&&\$cifra===''\)\$m\.="\n🔗 Links de estudo: _não cadastrados_";''')
new_links='''        if($yt!=='')$m.="
▶️ YouTube: {$yt}";
        if($cifra!=='')$m.="
🎸 Cifra: {$cifra}";
        if($yt===''&&$cifra==='')$m.="
🔗 Links de estudo: _não cadastrados_";'''
s,n=pat_links.subn(new_links,s,count=1)
if n!=1:
    raise SystemExit(f'restore visible urls: {n}')


pat=re.compile(r"function v1462_valid_url.*?(?=function v1435_show_pdf_choices)",re.S)
s,n=pat.subn('',s,count=1)
if n!=1:
    raise SystemExit(f'remove v1462 helpers: {n}')

rep(
"return v1462_send_repertoire($sender,$r);",
"return v1311p_send($sender,(string)($r['igreja_id']??''),v1436_repertoire_text($r),'volunteer_music_repertoire',['escala_id'=>$r['escala_id'],'escala_item_id'=>$r['item_id']]);",
'restore repertoire sender'
)

p.write_text(s,encoding='utf-8')

(root/'VERSION').write_text('1.4.63\\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.63.md').write_text('''# Escala de Propósito v1.4.63 — Links visíveis novamente no repertório

- Reverte somente a mudança de botões da v1.4.62.
- A opção **5 — Repertório** volta exatamente ao formato anterior:
  - **▶️ YouTube: https://...**
  - **🎸 Cifra: https://...**
- O **YouTube continua aparecendo primeiro** e a **Cifra depois**.
- O Spotify continua fora da mensagem.
- Mantém nome da música, artista e **Tom para tocar**.
- Remove o envio por sendButtons; o repertório volta a ser uma mensagem normal de texto, como na v1.4.61.
- Não altera confirmações, recusas, pendências, PDFs, escalas ou qualquer outra função.
''',encoding='utf-8')
