// Entrada discreta no painel existente. A autorização real é sempre verificada no backend.
(function(){
  var target='/holyrics-connect.html',id='edp-holyrics-link-v1481';
  function mount(){
    if(document.getElementById(id))return;
    var links=[].slice.call(document.querySelectorAll('a'));
    var anchor=links.find(function(a){return /configurações|configurações da igreja|config\. global/i.test((a.textContent||'').trim())});
    if(!anchor)return;
    var a=document.createElement('a');a.id=id;a.href=target;a.textContent='🎵 Integração Holyrics';
    a.style.cssText='display:flex;align-items:center;padding:11px 15px;text-decoration:none;color:inherit;font-weight:600;font-size:13px;border-radius:11px;';
    anchor.insertAdjacentElement('afterend',a);
  }
  new MutationObserver(mount).observe(document.documentElement,{childList:true,subtree:true});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount);
  else mount();
})();
