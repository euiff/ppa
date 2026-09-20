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

old='},ke=ce=>ce==="confirmado"?"Confirmado":ce==="recusado"?"Recusado":ce==="faltou"?"Faltou":ce==="tarde"?"Tarde":"Pendente",Fe='
new='},restoreRefused=async ce=>{var me;if(!window.confirm(`Voltar ${((me=ce.profiles)==null?void 0:me.nome)||"este voluntário"} para esta escala em ${ce.funcao}?\\n\\nEle voltará como Pendente para confirmar novamente.`))return;const{data:$,error:ue}=await I.rpc("adjust_escala_item_status",{p_item_id:ce.id,p_new_status:"pendente",p_justificativa:"Voluntário retornou à escala após cancelamento da indisponibilidade/substituição."}),Me=$;if(ue||!(Me!=null&&Me.ok)){V.error((Me==null?void 0:Me.error)||(ue==null?void 0:ue.message)||"Não foi possível voltar o voluntário para a escala");return}await I.from("escala_itens").update({justificativa_recusa:null}).eq("id",ce.id);await I.from("trocas").update({status:"recusado"}).eq("escala_item_id",ce.id).eq("status","pendente");await I.from("indisponibilidades").delete().eq("voluntario_id",ce.voluntario_id).eq("data",e.data);V.success("Voluntário voltou para a escala como Pendente."),Le();if(e.status==="publicado")try{const He=await Ye({escala_id:e.id,escala_item_id:ce.id,force_resend:!0});((He==null?void 0:He.queued)||0)>0?V.success("Nova confirmação agendada no WhatsApp."):((He==null?void 0:He.sent)||0)>0?V.success("Nova confirmação enviada no WhatsApp."):V.warning("Voluntário restaurado, mas o WhatsApp não foi enviado agora.")}catch{V.warning("Voluntário restaurado. A notificação pode ser reenviada manualmente.")}},ke=ce=>ce==="confirmado"?"Confirmado":ce==="recusado"?"Recusado":ce==="faltou"?"Faltou":ce==="tarde"?"Tarde":"Pendente",Fe='
rep(old,new,'restore handler')

old='ce.status_confirmacao==="recusado"&&s&&r.jsxs(ie,{size:"sm",variant:"outline",className:"h-6 text-[10px] px-2",onClick:()=>Yt(ce),children:[r.jsx(jo,{className:"w-3 h-3 mr-1"})," Substituir"]})'
new='ce.status_confirmacao==="recusado"&&s&&r.jsxs(ie,{size:"sm",variant:"outline",className:"h-6 text-[10px] px-2 border-status-confirmed/40 text-status-confirmed hover:bg-status-confirmed/10",title:"Cancelar a recusa e devolver este voluntário para a mesma função",onClick:()=>restoreRefused(ce),children:[r.jsx(ic,{className:"w-3 h-3 mr-1"})," Voltar para escala"]}),ce.status_confirmacao==="recusado"&&s&&r.jsxs(ie,{size:"sm",variant:"outline",className:"h-6 text-[10px] px-2",onClick:()=>Yt(ce),children:[r.jsx(jo,{className:"w-3 h-3 mr-1"})," Substituir"]})'
rep(old,new,'restore button')

asset.write_text(s,encoding='utf-8')
(root/'VERSION').write_text('1.4.54\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.54.md').write_text('''# Escala de Propósito v1.4.54 — Voltar para escala

- Em voluntários com status **Recusado**, Pastor/Admin/Líder passa a ver o botão **Voltar para escala**.
- O botão mantém a pessoa na **mesma escala e mesma função**, sem precisar remover e adicionar novamente.
- O status volta de **Recusado** para **Pendente**, para o voluntário confirmar novamente.
- O motivo antigo da recusa é limpo da ficha atual.
- Eventual **solicitação de troca ainda pendente** desse mesmo item é encerrada para não continuar aparecendo como pendência.
- Eventual **indisponibilidade daquele dia** é removida, pois o voluntário foi recolocado na escala.
- Se a escala já estiver publicada, o sistema tenta reenviar automaticamente a notificação/WhatsApp de confirmação.
- A mudança de status passa pelo mesmo RPC de ajuste já usado pelo sistema, preservando o **histórico/auditoria**.
- O botão **Substituir** continua disponível caso realmente seja necessário trocar a pessoa.
- Não altera PDF, Página do Culto, geração de escalas ou demais recursos.
''',encoding='utf-8')
