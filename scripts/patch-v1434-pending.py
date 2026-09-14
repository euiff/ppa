from pathlib import Path
import sys
root=Path(sys.argv[1])
api=root/'api'
pending=api/'pending_router_v1311.php'
s=pending.read_text()
needle="require_once __DIR__.'/whatsapp_transport_v1424.php';"
assert needle in s
if "volunteer_menu_v1434.php" not in s:
    s=s.replace(needle, needle+" require_once __DIR__.'/volunteer_menu_v1434.php';",1)
old="if($state==='quiz')return v1311p_handle_locked_quiz($session,$profiles,$sender,$text); v1311p_delete_session($session);"
new="if($state==='quiz')return v1311p_handle_locked_quiz($session,$profiles,$sender,$text); if(function_exists('v1434_is_menu_state')&&v1434_is_menu_state($state))return v1434_handle_menu_session($session,$profiles,$sender,$text); v1311p_delete_session($session);"
assert old in s
s=s.replace(old,new,1)
old="$options=v1311p_collect_options($profiles); if(!$options)return false; if(v1311p_is_menu_word($text)||count($options)>1){"
new="$options=v1311p_collect_options($profiles); if(!$options){ if(v1311p_is_menu_word($text)){ if(!v1311p_mark_event($msg))return true; return function_exists('v1434_show_home')?v1434_show_home($sender,$profiles,null):false; } return false; } if(v1311p_is_menu_word($text)||count($options)>1){"
assert old in s
s=s.replace(old,new,1)
old='Digite *MENU* a qualquer momento para ver a lista novamente."; return $m; }'
new='Digite *MENU* a qualquer momento para ver a lista novamente.\n\n_Depois de concluir as pendências, envie MENU para consultar suas próximas escalas, repertórios e PDF._"; return $m; }'
assert old in s
s=s.replace(old,new,1)
pending.write_text(s)
(root/'VERSION').write_text('1.4.34\n')
sw=root/'sw.js'
if sw.exists(): sw.write_text(sw.read_text()+"\n/* volunteer-whatsapp-menu-v1.4.34 */\n")
print('patched pending router v1.4.34')
