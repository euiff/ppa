from pathlib import Path

root=Path('pkg')

schema = r'''<?php
declare(strict_types=1);

function v1466_plan_feature_columns(): array {
    return [
        'whatsapp_enabled' => "TINYINT(1) NOT NULL DEFAULT 1",
        'app_notifications_enabled' => "TINYINT(1) NOT NULL DEFAULT 1",
    ];
}

function v1466_plan_feature_column_exists(string $column): bool {
    $q=db()->prepare("SELECT COUNT(*) FROM information_schema.columns
                      WHERE table_schema=DATABASE() AND table_name='saas_plans' AND column_name=?");
    $q->execute([$column]);
    return (int)$q->fetchColumn()>0;
}

function v1466_ensure_plan_feature_columns(): void {
    $pdo=db();
    foreach(v1466_plan_feature_columns() as $column=>$definition){
        if(v1466_plan_feature_column_exists($column)) continue;
        try{
            $pdo->exec("ALTER TABLE saas_plans ADD COLUMN ".$column." ".$definition);
        }catch(Throwable $e){
            if(!v1466_plan_feature_column_exists($column)){
                throw new RuntimeException(
                    "Nao foi possivel atualizar a estrutura de planos do banco (coluna ".$column."). ".
                    "Verifique se o usuario MySQL da hospedagem possui permissao ALTER TABLE. Detalhe: ".$e->getMessage()
                );
            }
        }
    }
}
'''
(root/'api'/'plan_features_schema_v1466.php').write_text(schema,encoding='utf-8')

p=root/'api'/'billing-master-v1314.php'
s=p.read_text(encoding='utf-8')
anchor="require __DIR__.'/bootstrap.php';require __DIR__.'/billing_lib_v1314.php';"
if anchor not in s:
    raise SystemExit('billing master require anchor not found')
s=s.replace(anchor,anchor+"require_once __DIR__.'/plan_features_schema_v1466.php';",1)

old="""billing_v1314_ensure_schema();try{billing_add_col('saas_plans','whatsapp_enabled',"TINYINT(1) NOT NULL DEFAULT 1");}catch(Throwable $e){}try{billing_add_col('saas_plans','app_notifications_enabled',"TINYINT(1) NOT NULL DEFAULT 1");}catch(Throwable $e){}$req=input_json();"""
new="""billing_v1314_ensure_schema();v1466_ensure_plan_feature_columns();$req=input_json();"""
if old not in s:
    raise SystemExit('v1465 swallowed schema anchor not found')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')

p=root/'api'/'plan_features_v1465.php'
s=p.read_text(encoding='utf-8')
if "plan_features_schema_v1466.php" not in s:
    s=s.replace("declare(strict_types=1);","declare(strict_types=1);\nrequire_once __DIR__.'/plan_features_schema_v1466.php';",1)
old="function v1465_plan_features(string $igrejaId): array {\n    $defaults=['whatsapp'=>true,'app_notifications'=>true];"
new="function v1465_plan_features(string $igrejaId): array {\n    $defaults=['whatsapp'=>true,'app_notifications'=>true];\n    try{v1466_ensure_plan_feature_columns();}catch(Throwable $e){return $defaults;}"
if old not in s:
    raise SystemExit('plan feature helper anchor not found')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')

p=root/'api'/'billing_lib_v1314.php'
s=p.read_text(encoding='utf-8')
if "plan_features_schema_v1466.php" not in s:
    s=s.replace("require_once __DIR__.'/billing_lib_v1313.php';","require_once __DIR__.'/billing_lib_v1313.php';\nrequire_once __DIR__.'/plan_features_schema_v1466.php';",1)
old="function billing_v1314_ensure_schema(): void {\n    billing_ensure_schema();\n    $pdo=db();"
new="function billing_v1314_ensure_schema(): void {\n    billing_ensure_schema();\n    $pdo=db();\n    v1466_ensure_plan_feature_columns();"
if old not in s:
    raise SystemExit('billing schema anchor not found')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')

mig=root/'database'/'migrations'/'20261001_1466_plan_features.sql'
mig.parent.mkdir(parents=True,exist_ok=True)
mig.write_text("""-- Escala de Proposito v1.4.66
-- A aplicacao executa esta migracao automaticamente.
ALTER TABLE saas_plans ADD COLUMN whatsapp_enabled TINYINT(1) NOT NULL DEFAULT 1;
ALTER TABLE saas_plans ADD COLUMN app_notifications_enabled TINYINT(1) NOT NULL DEFAULT 1;
""",encoding='utf-8')

(root/'VERSION').write_text('1.4.66\n',encoding='utf-8')
(root/'ATUALIZACAO-v1.4.66.md').write_text('''# Escala de Propósito v1.4.66 — Correção do banco dos planos

- Corrige o erro Unknown column whatsapp_enabled in SET ao editar/salvar um plano no Master.
- O sistema verifica automaticamente se whatsapp_enabled e app_notifications_enabled existem em saas_plans.
- Se estiverem ausentes, cria automaticamente com valor padrão 1 (ativado), preservando planos, preços, assinaturas e clientes.
- A migração roda antes da Gestão Comercial e também quando a biblioteca de cobrança inicializa.
- Remove o comportamento da v1.4.65 que ignorava silenciosamente uma falha ao criar as colunas.
- Se o usuário MySQL não tiver permissão ALTER TABLE, o Master recebe uma mensagem clara indicando a permissão necessária.
- Mantém as regras de plano com/sem WhatsApp e notificações pelo app da v1.4.65.
''',encoding='utf-8')
