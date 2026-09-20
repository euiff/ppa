from pathlib import Path

root=Path('pkg')
asset=next((root/'assets').glob('index-*.js'))
s=asset.read_text(encoding='utf-8')

def rep(old,new,label):
    global s
    c=s.count(old)
    if c!=1:
        raise SystemExit(f'{label}: anchor count={c}')
    s=s.replace(old,new,1)

old='href:`/escala/${encodeURIComponent((Ne[0]&&Ne[0].id)||"")}`,className:"inline-flex items-center justify-center rounded-xl bg-primary text-primary-foreground px-3 py-2 text-xs font-bold hover:opacity-90",onClick:ce=>ce.stopPropagation(),children:"Escala completa"'
new='href:`/culto?data=${encodeURIComponent(ve.data||"")}&culto_id=${encodeURIComponent((ve.culto&&ve.culto.id)||"")}`,className:"inline-flex items-center justify-center rounded-xl bg-primary text-primary-foreground px-3 py-2 text-xs font-bold hover:opacity-90",onClick:ce=>ce.stopPropagation(),children:"Página do culto"'
rep(old,new,'restore service page button')
asset.write_text(s,encoding='utf-8')

p=root/'gestao-ministerial.html'
h=p.read_text(encoding='utf-8')
old='>Imprimir / PDF — modelo clássico</button>'
new='>Imprimir / PDF — mesmo modelo da Escala Completa</button>'
if h.count(old)!=1:
    raise SystemExit(f'top print label count={h.count(old)}')
h=h.replace(old,new,1)

old='>Abrir Escala Completa — impressão/PDF</button>'
new='>Gerar pelo modelo da Escala Completa</button>'
if h.count(old)!=1:
    raise SystemExit(f'print tab label count={h.count(old)}')
h=h.replace(old,new,1)
p.write_text(h,encoding='utf-8')

(root/'VERSION').write_text('1.4.51\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.51.md').write_text('''# Escala de Propósito v1.4.51

- Na página **Escalas**, volta o botão **Página do culto**.
- A Página do Culto continua reunindo visão geral, escala, repertório, confirmações, trocas, impressão e histórico.
- O botão **Imprimir / PDF** da Página do Culto usa o **mesmo gerador clássico da Escala Completa**.
- O PDF continua com o mesmo desenho: **A4**, tabela **Departamento | Função | Voluntário | Situação**, com a ordenação alfabética/numérica já existente.
- Não cria um segundo modelo de PDF.
- Mantém as correções da v1.4.50: voluntário sem **Planos & Pagamentos**, ID correto da escala, impressão sem bloqueio de pop-up e download de PDF corrigido.
''',encoding='utf-8')
