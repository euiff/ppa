from pathlib import Path
import re

root=Path('pkg')
helper=root/'api'/'scale_response_notify_v1417.php'
s=helper.read_text(encoding='utf-8')

# Precisamos saber se a escala realmente possui departamento vinculado.
s=s.replace(
    "e.data,e.igreja_id,e.created_by,c.horario,c.nome culto_nome,d.nome departamento_nome,d.lider_id departamento_lider_id,",
    "e.data,e.igreja_id,e.created_by,e.departamento_id,c.horario,c.nome culto_nome,d.nome departamento_nome,d.lider_id departamento_lider_id,",
    1
)

pat=re.compile(r"function v1417_recipient\(array \$item\):\?array\{.*?\n\}",re.S)
rep=r'''function v1417_recipient(array $item):?array{
    $vol=(string)($item['voluntario_id']??'');
    $deptId=(string)($item['departamento_id']??'');
    $leaderId=(string)($item['departamento_lider_id']??'');

    /*
     * Regra v1.4.40:
     * - Havendo departamento na escala, a confirmação/recusa vai SOMENTE para o líder desse departamento.
     * - O criador da escala deixa de ter prioridade e não recebe por ser o criador.
     * - O pastor/admin só recebe quando a escala não está vinculada a nenhum departamento.
     */
    if($deptId!==''){
        if($leaderId===''||$leaderId===$vol){
            v1417_trace('department_without_valid_leader',['item'=>$item['item_id']??null,'departamento_id'=>$deptId]);
            return null;
        }
        $leader=v1417_profile($leaderId);
        if($leader&&v1417_valid_phone((string)($leader['whatsapp']??'')))return $leader;
        v1417_trace('department_leader_without_whatsapp',['item'=>$item['item_id']??null,'departamento_id'=>$deptId,'leader_id'=>$leaderId]);
        return null;
    }

    $pastorId=v1417_admin_id((string)($item['igreja_id']??''));
    if($pastorId!==''&&$pastorId!==$vol){
        $pastor=v1417_profile($pastorId);
        if($pastor&&v1417_valid_phone((string)($pastor['whatsapp']??'')))return $pastor;
    }
    return null;
}'''
s2,n=pat.subn(rep,s,count=1)
if n!=1:
    raise SystemExit('função v1417_recipient não encontrada')
helper.write_text(s2,encoding='utf-8')

(root/'VERSION').write_text('1.4.40\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.40.md').write_text('''# Escala de Propósito v1.4.40\n\n- Altera o destino das respostas de escala no WhatsApp.\n- Quando a escala possui departamento, a confirmação ou recusa do voluntário é enviada ao líder daquele departamento.\n- O pastor/admin deixa de receber respostas de escalas que possuem departamento vinculado.\n- O pastor/admin só é usado como destino quando a escala não possui departamento.\n- O criador da escala deixa de ser usado como destinatário automático.\n- A mesma regra vale para confirmação, recusa e mensagem com o motivo da indisponibilidade.\n- Não altera o recebimento 1/2 do voluntário, quiz, repertório ou transporte da Evolution.\n''',encoding='utf-8')
