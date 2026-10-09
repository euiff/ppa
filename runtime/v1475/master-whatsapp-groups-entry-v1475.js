(()=>{
  const TARGET='/master-grupos-whatsapp.html';
  const ID='master-whatsapp-groups-nav-v1475';

  function isMaster(){
    const t=(document.body?.innerText||'');
    return t.includes('MASTER') && (t.includes('Painel Master') || t.includes('Config. Global') || t.includes('Atualizações'));
  }

  function addSidebar(){
    if(!isMaster() || document.getElementById(ID)) return;
    const links=[...document.querySelectorAll('a')];
    const base=links.find(a=>(a.textContent||'').trim().includes('Config. Global'))
      || links.find(a=>(a.textContent||'').trim().includes('Atualizações'));
    if(!base)return;
    const link=base.cloneNode(true);
    link.id=ID;
    link.setAttribute('href',TARGET);
    link.removeAttribute('aria-current');
    const spans=link.querySelectorAll('span');
    if(spans.length){
      spans[spans.length-1].textContent='Grupos WhatsApp';
    }else{
      link.textContent='💬 Grupos WhatsApp';
    }
    const svg=link.querySelector('svg');
    if(svg)svg.outerHTML='<span aria-hidden="true" style="width:20px;display:inline-flex;align-items:center;justify-content:center;font-size:16px">💬</span>';
    base.insertAdjacentElement('afterend',link);
  }

  function addDashboardCard(){
    if(!isMaster() || document.getElementById('master-whatsapp-groups-card-v1475'))return;
    const h=[...document.querySelectorAll('h1')].find(x=>(x.textContent||'').trim()==='Painel Master');
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
    box.id='master-whatsapp-groups-card-v1475';
    box.href=TARGET;
    box.innerHTML='<div class="mwg-icon">💬</div><div class="mwg-copy"><b>Grupos do WhatsApp oficial</b><span>Atualizar grupos na API, localizar o endereço @g.us e copiar para enviar à igreja</span></div><div class="mwg-go">›</div>';
    box.style.cssText='display:flex;align-items:center;gap:14px;padding:16px 17px;margin:2px 0 16px;border:1px solid rgba(22,163,74,.25);border-radius:18px;background:linear-gradient(135deg,rgba(22,163,74,.10),rgba(16,185,129,.05));color:inherit;text-decoration:none;box-shadow:0 8px 24px rgba(15,23,42,.05)';
    const st=document.createElement('style');
    st.textContent='#master-whatsapp-groups-card-v1475 .mwg-icon{width:46px;height:46px;border-radius:14px;display:flex;align-items:center;justify-content:center;background:#16a34a;color:#fff;font-size:22px;flex:0 0 auto}#master-whatsapp-groups-card-v1475 .mwg-copy{display:flex;flex-direction:column;min-width:0;flex:1}#master-whatsapp-groups-card-v1475 .mwg-copy b{font-size:15px}#master-whatsapp-groups-card-v1475 .mwg-copy span{font-size:11px;color:#7b8495;line-height:1.35;margin-top:3px}#master-whatsapp-groups-card-v1475 .mwg-go{font-size:28px;color:#7b8495}';
    document.head.appendChild(st);

    const commerce=document.getElementById('master-commerce-launcher');
    if(commerce&&commerce.parentElement===page)commerce.insertAdjacentElement('afterend',box);
    else{
      const header=h.parentElement?.parentElement;
      if(header&&header.parentElement===page)header.insertAdjacentElement('afterend',box);
      else page.insertBefore(box,page.children[1]||null);
    }
  }

  function inject(){addSidebar();addDashboardCard();}
  document.addEventListener('click',e=>{
    const a=e.target.closest&&e.target.closest('a[href="'+TARGET+'"]');
    if(a){e.preventDefault();location.href=TARGET;}
  },true);
  new MutationObserver(inject).observe(document.documentElement,{subtree:true,childList:true});
  setTimeout(inject,350);
  setTimeout(inject,1000);
  setInterval(inject,2200);
})();
