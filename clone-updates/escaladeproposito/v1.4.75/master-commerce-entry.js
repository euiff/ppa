(()=>{
  const TARGET='/master-comercial.html';
  function isMasterPage(){
    const txt=(document.body?.innerText||'');
    return txt.includes('Painel Master') && txt.includes('MASTER');
  }
  function inject(){
    if(!isMasterPage()||document.getElementById('master-commerce-launcher'))return;
    const h=[...document.querySelectorAll('h1')].find(x=>x.textContent.trim()==='Painel Master');
    if(!h)return;
    let page=h.parentElement;
    while(page&&page!==document.body){
      const cls=String(page.className||'');
      if(cls.includes('space-y-6')&&cls.includes('w-full'))break;
      page=page.parentElement;
    }
    if(!page||page===document.body)page=h.parentElement?.parentElement?.parentElement;
    if(!page)return;
    const box=document.createElement('a');
    box.id='master-commerce-launcher';box.href=TARGET;
    box.innerHTML='<div class="mc-icon">💳</div><div class="mc-copy"><b>Gestão Comercial</b><span>Planos, preços, promoções, assinaturas, pagamentos, Mercado Pago e clientes</span></div><div class="mc-go">›</div>';
    box.style.cssText='display:flex;align-items:center;gap:14px;padding:16px 17px;margin:2px 0 16px;border:1px solid rgba(70,72,243,.22);border-radius:18px;background:linear-gradient(135deg,rgba(70,72,243,.10),rgba(7,152,168,.07));color:inherit;text-decoration:none;box-shadow:0 8px 24px rgba(15,23,42,.05)';
    const style=document.createElement('style');style.textContent='#master-commerce-launcher .mc-icon{width:46px;height:46px;border-radius:14px;display:flex;align-items:center;justify-content:center;background:#4648f3;color:#fff;font-size:22px;flex:0 0 auto}#master-commerce-launcher .mc-copy{display:flex;flex-direction:column;min-width:0;flex:1}#master-commerce-launcher .mc-copy b{font-size:15px}#master-commerce-launcher .mc-copy span{font-size:11px;color:#7b8495;line-height:1.35;margin-top:3px}#master-commerce-launcher .mc-go{font-size:28px;color:#7b8495}';document.head.appendChild(style);
    const header=h.parentElement?.parentElement;
    if(header&&header.parentElement===page)header.insertAdjacentElement('afterend',box);else page.insertBefore(box,page.children[1]||null);
  }
  document.addEventListener('click',e=>{const a=e.target.closest&&e.target.closest('a[href="'+TARGET+'"]');if(a){e.preventDefault();location.href=TARGET}},true);
  new MutationObserver(()=>inject()).observe(document.documentElement,{subtree:true,childList:true});
  setTimeout(inject,600);setTimeout(inject,1800);
})();
