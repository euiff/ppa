from pathlib import Path

root=Path('pkg')
asset=next((root/'assets').glob('index-*.js'))
s=asset.read_text(encoding='utf-8')

def rep(text,old,new,label):
    c=text.count(old)
    if c!=1:
        raise SystemExit(f'{label}: anchor count={c}')
    return text.replace(old,new,1)

old='V.error((Fe==null?void 0:Fe.message)||"Não foi possível gerar o PDF")}};if(a)return'
new='V.error((Fe==null?void 0:Fe.message)||"Não foi possível gerar o PDF")}};if(!a&&l){const Fe=new URLSearchParams(window.location.search),ke=Fe.get("auto_pdf"),Ne=Fe.get("auto_print");if(ke==="1"||Ne==="1"){window.history.replaceState(null,"",window.location.pathname),window.setTimeout(()=>{ke==="1"?he():G()},180)}}if(a)return'
s=rep(s,old,new,'auto pdf/print trigger')
asset.write_text(s,encoding='utf-8')

p=root/'gestao-ministerial.html'
h=p.read_text(encoding='utf-8')

old='<button class="btn primary" onclick="top.location.href=\'/escala/\'+encodeURIComponent(b.id)">Imprimir / PDF — mesmo modelo da Escala Completa</button>'
new='<a class="btn secondary" target="_top" href="/escala/${encodeURIComponent(b.id)}?auto_print=1">Imprimir</a><a class="btn primary" target="_top" href="/escala/${encodeURIComponent(b.id)}?auto_pdf=1">Baixar PDF</a>'
h=rep(h,old,new,'top service print buttons')

old='<button class="btn primary" onclick="top.location.href=\'/escala/\'+encodeURIComponent(b.id)">Gerar pelo modelo da Escala Completa</button>'
new='<div class="actions"><a class="btn secondary" target="_top" href="/escala/${encodeURIComponent(b.id)}?auto_print=1">Imprimir no modelo da Escala Completa</a><a class="btn primary" target="_top" href="/escala/${encodeURIComponent(b.id)}?auto_pdf=1">Baixar PDF no modelo da Escala Completa</a></div>'
h=rep(h,old,new,'print tab buttons')

p.write_text(h,encoding='utf-8')

(root/'VERSION').write_text('1.4.52\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.52.md').write_text('''# Escala de Propósito v1.4.52

- Corrige os botões **Imprimir** e **Baixar PDF** dentro da **Página do Culto**.
- Os botões agora são links reais, sem depender de `onclick` dentro da página dinâmica.
- **Baixar PDF** abre a Escala Completa correta e dispara automaticamente o mesmo gerador clássico de PDF.
- **Imprimir** abre a Escala Completa correta e dispara automaticamente a mesma impressão clássica.
- Mantém exatamente o modelo já usado na Escala Completa: A4, tabela Departamento | Função | Voluntário | Situação e ordenação alfabética/numérica.
- A Página do Culto continua disponível e organizada.
- Mantém as correções de permissões e faturamento das versões anteriores.
''',encoding='utf-8')
