from pathlib import Path
import re

root = Path('pkg')
scale = root / 'api' / 'whatsapp_scale_message_v1421.php'

s = scale.read_text(encoding='utf-8')
pattern = re.compile(r"function v1421_same_day_repertoire\(array \$r\): array \{.*?\n\}\n\nfunction v1421_build_scale_message", re.S)
replacement = r'''function v1421_same_day_repertoire(array $r): array {
    try {
        $esc=(string)($r['escala_id']??'');
        $ig=(string)($r['igreja_id']??'');
        $data=(string)($r['data']??'');
        $culto=(string)($r['culto_id']??'');
        $rows=[];

        /*
         * Um mesmo culto pode ter varias escalas (uma por departamento).
         * O repertorio e do culto/dia, nao do voluntario/departamento.
         * Usa como fonte canonica o setlist mais completo daquele culto e dia,
         * para todos receberem exatamente a mesma lista e a mesma ordem.
         */
        if($ig!=='' && $data!=='' && $culto!=='') {
            $sql="SELECT s.id setlist_id,COUNT(si.musica_id) qtd,MAX(s.created_at) criado
                  FROM setlists s
                  JOIN escalas e2 ON BINARY e2.id=BINARY s.escala_id
                  LEFT JOIN setlist_itens si ON BINARY si.setlist_id=BINARY s.id
                  WHERE BINARY e2.igreja_id=BINARY ? AND e2.data=? AND BINARY e2.culto_id=BINARY ?
                  GROUP BY s.id
                  ORDER BY qtd DESC,criado DESC,s.id DESC
                  LIMIT 1";
            $q=db()->prepare($sql);$q->execute([$ig,$data,$culto]);
            $setlist=(string)($q->fetchColumn()?:'');
            if($setlist!=='') {
                $sql="SELECT si.musica_id,si.ordem,m.titulo,m.artista,m.tom,m.link_youtube
                      FROM setlist_itens si
                      JOIN musicas m ON BINARY m.id=BINARY si.musica_id
                      WHERE BINARY si.setlist_id=BINARY ?
                      ORDER BY si.ordem ASC,m.titulo ASC";
                $q=db()->prepare($sql);$q->execute([$setlist]);$rows=$q->fetchAll(PDO::FETCH_ASSOC)?:[];
            }
        }

        /* Fallback para instalacoes antigas ou escalas sem culto_id. */
        if(!$rows && $esc!=='') {
            $sql="SELECT si.musica_id,si.ordem,m.titulo,m.artista,m.tom,m.link_youtube
                  FROM setlists s
                  JOIN setlist_itens si ON BINARY si.setlist_id=BINARY s.id
                  JOIN musicas m ON BINARY m.id=BINARY si.musica_id
                  WHERE BINARY s.escala_id=BINARY ?
                  ORDER BY si.ordem ASC,m.titulo ASC";
            $q=db()->prepare($sql);$q->execute([$esc]);$rows=$q->fetchAll(PDO::FETCH_ASSOC)?:[];
        }

        $out=[];$seen=[];
        foreach($rows as $x){
            $id=(string)($x['musica_id']??'');
            $title=trim((string)($x['titulo']??''));
            $key=$id!==''?$id:(function_exists('mb_strtolower')?mb_strtolower($title,'UTF-8'):strtolower($title));
            if($key===''||isset($seen[$key]))continue;
            $seen[$key]=true;$out[]=$x;
            if(count($out)>=30)break;
        }
        return $out;
    } catch(Throwable $e) {
        return [];
    }
}

function v1421_build_scale_message'''

s2, n = pattern.subn(replacement, s, count=1)
if n != 1:
    raise SystemExit('Funcao v1421_same_day_repertoire nao encontrada')
scale.write_text(s2, encoding='utf-8')

(root / 'VERSION').write_text('1.4.37\n', encoding='utf-8')
(root / 'ATUALIZACAO-v1.4.37.md').write_text('''# Escala de Propósito v1.4.37\n\n- Corrige divergência de repertório entre voluntários da mesma igreja, mesmo dia e mesmo culto.\n- Um culto pode possuir várias escalas internas, uma por departamento; agora todos usam um único repertório canônico do culto/dia.\n- Quando existirem setlists diferentes para o mesmo culto, o sistema utiliza o repertório mais completo e preserva a ordem cadastrada.\n- A correção vale para o MENU do WhatsApp, a notificação inicial de escala e o PDF completo do dia.\n- Mantém nome, artista, tom e link do YouTube das músicas.\n- Não altera o núcleo de confirmação/recusa do WhatsApp.\n''', encoding='utf-8')
