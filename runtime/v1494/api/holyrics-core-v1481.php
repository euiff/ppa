<?php
declare(strict_types=1);
// Escala de Propósito — Holyrics Connect v1.4.81.
// Este arquivo só contém funções; a conexão e autenticação são dos endpoints.
function edp_hly_table(): void {
    db()->exec("CREATE TABLE IF NOT EXISTS holyrics_integracoes (
        igreja_id VARCHAR(36) NOT NULL PRIMARY KEY,
        token_hash CHAR(64) NOT NULL,
        ativo TINYINT(1) NOT NULL DEFAULT 1,
        atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_holyrics_hash (token_hash)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci");
}
function edp_hly_allowed_church(string $role, string $own, string $target): bool {
    return $target!=='' && ($role==='master' || (in_array($role,['admin','pastor'],true) && $own!=='' && hash_equals($own,$target)));
}
function edp_hly_church_by_token(string $token): ?string {
    if(strlen($token)<48 || strlen($token)>256 || !preg_match('/^[a-f0-9]+$/D',$token))return null;
    $q=db()->prepare('SELECT igreja_id FROM holyrics_integracoes WHERE token_hash=? AND ativo=1 LIMIT 1');
    $q->execute([hash('sha256',$token)]);
    $id=$q->fetchColumn();return $id?((string)$id):null;
}
function edp_hly_services(string $igreja): array {
    $q=db()->prepare("SELECT e.id,e.data,e.culto_id,c.nome culto_nome,c.horario,i.nome igreja_nome
         FROM escalas e
         LEFT JOIN cultos c ON BINARY c.id=BINARY e.culto_id
         JOIN igrejas i ON BINARY i.id=BINARY e.igreja_id
         WHERE BINARY e.igreja_id=BINARY ? AND e.status='publicado'
           AND e.data BETWEEN DATE_SUB(CURDATE(),INTERVAL 7 DAY) AND DATE_ADD(CURDATE(),INTERVAL 90 DAY)
         ORDER BY e.data ASC, COALESCE(c.horario,'23:59') ASC, COALESCE(c.nome,'') ASC, e.id ASC");
    $q->execute([$igreja]);$out=[];$seen=[];
    foreach($q->fetchAll(PDO::FETCH_ASSOC)?:[] as $r){
        $group=$r['culto_id']??null;
        $key=(string)$r['data'].'|'.($group===null?'__null__':(string)$group);
        if(isset($seen[$key]))continue;
        $seen[$key]=true;
        $out[]=[
            'id'=>(string)$r['id'],
            'data'=>(string)$r['data'],
            'culto'=>(string)($r['culto_nome']??'Culto'),
            'horario'=>substr((string)($r['horario']??''),0,5),
            'igreja'=>(string)($r['igreja_nome']??''),
        ];
        if(count($out)>=100)break;
    }
    return $out;
}
function edp_hly_songs(string $igreja,string $escalaId): array {
    $q=db()->prepare("SELECT id,data,culto_id FROM escalas WHERE BINARY id=BINARY ? AND BINARY igreja_id=BINARY ? AND status='publicado' LIMIT 1");
    $q->execute([$escalaId,$igreja]);$service=$q->fetch(PDO::FETCH_ASSOC);
    if(!$service)return ['error'=>'Culto não encontrado ou escala ainda não publicada.'];
    $params=[$igreja,$service['data']];
    $sameCulto=" AND (e.culto_id IS NULL OR e.culto_id='')";
    if(!empty($service['culto_id'])){$sameCulto=' AND BINARY e.culto_id=BINARY ?';$params[]=$service['culto_id'];}
    $sql="SELECT s.id setlist_id,d.nome departamento_nome,COUNT(si.id) qtd
          FROM escalas e
          JOIN setlists s ON BINARY s.escala_id=BINARY e.id
          LEFT JOIN departamentos d ON BINARY d.id=BINARY e.departamento_id
          LEFT JOIN setlist_itens si ON BINARY si.setlist_id=BINARY s.id
          WHERE BINARY e.igreja_id=BINARY ? AND e.data=? AND e.status='publicado' $sameCulto
          GROUP BY s.id,d.nome HAVING qtd>0";
    $q=db()->prepare($sql);$q->execute($params);$candidates=$q->fetchAll(PDO::FETCH_ASSOC)?:[];
    // Repertório canônico: prioriza departamento de Louvor/Música, depois a lista mais completa.
    usort($candidates,static function(array $a,array $b):int{
        $score=static function(array $r):int {
            $name=(string)($r['departamento_nome']??'');
            if(function_exists('iconv')){$norm=@iconv('UTF-8','ASCII//TRANSLIT//IGNORE',$name);if($norm!==false)$name=$norm;}
            return preg_match('/(louvor|musica)/i',$name)?0:1;
        };
        $p=$score($a)<=>$score($b);if($p!==0)return $p;
        $p=(int)$b['qtd']<=>(int)$a['qtd'];if($p!==0)return $p;
        return strcmp((string)$a['setlist_id'],(string)$b['setlist_id']);
    });
    if(!$candidates)return ['songs'=>[],'total'=>0];
    $id=(string)$candidates[0]['setlist_id'];
    // Permite o cadastro assistido no Holyrics quando a própria igreja já
    // registrou a letra na base. Nenhuma letra é buscada na internet.
    $letraColumn=null;
    try{
        $colRows=db()->query('SHOW COLUMNS FROM musicas')->fetchAll(PDO::FETCH_ASSOC)?:[];
        foreach(['letra','letras','lyrics','letra_musica'] as $candidate){
            foreach($colRows as $column){
                if(strcasecmp((string)($column['Field']??''),$candidate)===0){
                    $letraColumn=(string)$column['Field'];break 2;
                }
            }
        }
    }catch(Throwable $ignored){$letraColumn=null;}
    // Apenas identificadores de coluna reconhecidos de uma lista fechada.
    $letraExpr=$letraColumn===null?"''":"COALESCE(CAST(m.`".$letraColumn."` AS CHAR),'')";
    $q=db()->prepare("SELECT si.ordem,m.titulo,m.artista,m.tom, $letraExpr AS letra
       FROM setlist_itens si JOIN musicas m ON BINARY m.id=BINARY si.musica_id
       WHERE BINARY si.setlist_id=BINARY ? ORDER BY si.ordem ASC,m.titulo ASC");
    $q->execute([$id]);$songs=[];
    foreach($q->fetchAll(PDO::FETCH_ASSOC)?:[] as $r){
        $title=trim((string)($r['titulo']??''));if($title==='')continue;
        $songs[]=['titulo'=>$title,'artista'=>(string)($r['artista']??''),'tom'=>(string)($r['tom']??''),'letra'=>(string)($r['letra']??''),'ordem'=>count($songs)+1];
        if(count($songs)>=100)break;
    }
    return ['songs'=>$songs,'total'=>count($songs)];
}
