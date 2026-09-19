from pathlib import Path
import shutil

root=Path('pkg')
asset=next((root/'assets').glob('index-*.js'))
js=asset.read_text(encoding='utf-8')

def rep(text,old,new,label):
    c=text.count(old)
    if c!=1: raise SystemExit(f'{label} anchor count={c}')
    return text.replace(old,new,1)

old='mLG=()=>r.jsx("iframe",{src:"/master-logs.html",title:"Logs e erros",className:"w-full h-full min-h-[calc(100dvh-80px)] border-0 bg-background"}),aQ='
new='mLG=()=>r.jsx("iframe",{src:"/master-logs.html",title:"Logs e erros",className:"w-full h-full min-h-[calc(100dvh-80px)] border-0 bg-background"}),mSE=()=>r.jsx("iframe",{src:"/master-escalas.html",title:"Excluir escalas",className:"w-full h-full min-h-[calc(100dvh-80px)] border-0 bg-background"}),aQ='
js=rep(js,old,new,'master iframe')
old='{path:"/vinculos-voluntarios",label:"Vínculos voluntários",icon:Cs},{path:"/limpeza-dados",label:"Limpeza de dados",icon:Xn}'
new='{path:"/vinculos-voluntarios",label:"Vínculos voluntários",icon:Cs},{path:"/master-escalas",label:"Excluir escalas",icon:Xs},{path:"/limpeza-dados",label:"Limpeza de dados",icon:Xn}'
js=rep(js,old,new,'master sidebar')
old='r.jsx(nn,{path:"/vinculos-voluntarios",element:r.jsx(DS,{children:r.jsx(mVL,{})})}),r.jsx(nn,{path:"/atualizacoes"'
new='r.jsx(nn,{path:"/vinculos-voluntarios",element:r.jsx(DS,{children:r.jsx(mVL,{})})}),r.jsx(nn,{path:"/master-escalas",element:r.jsx(DS,{children:r.jsx(mSE,{})})}),r.jsx(nn,{path:"/atualizacoes"'
js=rep(js,old,new,'master route')
asset.write_text(js,encoding='utf-8')

shutil.copyfile('patches/v1446/master-scales.php', root/'api'/'master-scales.php')
shutil.copyfile('patches/v1446/master-escalas.html', root/'master-escalas.html')
(root/'VERSION').write_text('1.4.46\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.46.md').write_text('''# Escala de Propósito v1.4.46

- Adiciona ao **Master** a nova opção **Excluir escalas**.
- Lista as escalas completas separadas por **igreja + data + culto**, mostrando nome do culto, horário, quantidade de departamentos e itens.
- Permite excluir somente a **escala completa selecionada**. Exemplo: se em 20/09 existirem **Culto** e **Culto da Família**, apagar **Culto** não altera **Culto da Família**.
- A exclusão remove apenas os registros vinculados à escala escolhida, incluindo itens, confirmações/contextos do WhatsApp, PDFs temporários, check-ins, trocas, SOS e repertório/setlist ligados àquela escala.
- Exige confirmação digitando **EXCLUIR** antes da operação.
- A exclusão é executada em transação e fica registrada nos logs/auditoria do sistema.
''',encoding='utf-8')
