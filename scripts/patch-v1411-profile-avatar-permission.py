from pathlib import Path
import re, sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'pkg')

# 1) Backend: the upload endpoint itself persists the avatar URL for the authenticated user.
# This avoids routing the avatar change through generic profile-update permissions.
upload = root / 'api/upload.php'
s = upload.read_text()
old = "if(!move_uploaded_file($f['tmp_name'],$dest))out(['data'=>null,'error'=>['message'=>'Não foi possível salvar imagem']],500);if($bucket==='profile-avatars')audit($u['id'],'profile_avatar_upload','profiles:'.$u['id'],['path'=>$safe],'info');out(['data'=>['path'=>$safe,'fullPath'=>$bucket.'/'.$safe],'error'=>null]);"
new = "if(!move_uploaded_file($f['tmp_name'],$dest))out(['data'=>null,'error'=>['message'=>'Não foi possível salvar imagem']],500);if($bucket==='profile-avatars'){updater_ensure_profile_avatar_schema();$avatarUrl='/uploads/'.$bucket.'/'.$safe.'?v='.time();$st=db()->prepare('UPDATE profiles SET avatar_url=? WHERE id=?');$st->execute([$avatarUrl,$u['id']]);audit($u['id'],'profile_avatar_upload','profiles:'.$u['id'],['path'=>$safe,'avatar_url'=>$avatarUrl],'info');out(['data'=>['path'=>$safe,'fullPath'=>$bucket.'/'.$safe,'publicUrl'=>$avatarUrl],'error'=>null]);}out(['data'=>['path'=>$safe,'fullPath'=>$bucket.'/'.$safe],'error'=>null]);"
if old not in s:
    raise SystemExit('upload.php avatar persistence anchor not found')
s = s.replace(old, new, 1)
upload.write_text(s)

# 2) Frontend: after a successful self-upload, do not issue a second generic profiles UPDATE.
# The backend has already saved avatar_url securely for the authenticated user.
js = root / 'assets/index-C6Ng0a8i.js'
t = js.read_text()
old_js = 'const{data:ke}=I.storage.from("profile-avatars").getPublicUrl(xe),Fe=`${ke.publicUrl}?v=${Date.now()}`,{error:ae}=await I.from("profiles").update({avatar_url:Fe}).eq("id",e.id);if(ae)throw new Error(ae.message);l(Fe),window.dispatchEvent(new Event("escala-profile-updated"))'
new_js = 'const{data:ke}=I.storage.from("profile-avatars").getPublicUrl(xe),Fe=`${ke.publicUrl}?v=${Date.now()}`;l(Fe),window.dispatchEvent(new Event("escala-profile-updated"))'
if old_js not in t:
    raise SystemExit('frontend avatar update anchor not found')
t = t.replace(old_js, new_js, 1)
js.write_text(t)

# 3) Cache bust so installed PWAs receive the fix immediately.
h = root / 'sistema.html'
x = h.read_text()
x = re.sub(r'/assets/index-C6Ng0a8i\.js\?v=[^\"\']+', '/assets/index-C6Ng0a8i.js?v=1.4.11', x)
h.write_text(x)

sw = root / 'sw.js'
x = sw.read_text()
x = re.sub(r'url:\"sistema\.html\",revision:\"[^\"]*\"', 'url:\"sistema.html\",revision:\"v1411-profile-avatar\"', x)
x = re.sub(r'url:\"assets/index-C6Ng0a8i\.js\",revision:(?:null|\"[^\"]*\")', 'url:\"assets/index-C6Ng0a8i.js\",revision:\"v1411-profile-avatar\"', x)
if 'profile-avatar-permission-cache-bust-v1.4.11' not in x:
    x += '\n/* profile-avatar-permission-cache-bust-v1.4.11 */\n'
sw.write_text(x)

(root / 'registerSW.js').write_text("if('serviceWorker' in navigator){window.addEventListener('load',async()=>{try{const r=await navigator.serviceWorker.register('/sw.js?v=1.4.11',{scope:'/',updateViaCache:'none'});await r.update()}catch(e){console.warn('[SW v1.4.11]',e)}})}")
