(() => {
  "use strict";
  const itemSelector = "a.shortcut,a.deskicon,a.app";
  const style = document.createElement("style");
  style.textContent = `
    .oct-desktop-selected{outline:2px solid #8deeff!important;outline-offset:2px!important;filter:brightness(1.14)}
    .oct-desktop-context{position:fixed;z-index:10000;min-width:190px;padding:7px;border:1px solid #a8e9ff66;border-radius:14px;background:#071b2df2;color:#f3fbff;box-shadow:0 18px 48px #000b, inset 0 1px #ffffff22;backdrop-filter:blur(22px)}
    .oct-desktop-context button{display:flex;width:100%;align-items:center;gap:10px;padding:10px 12px;border:1px solid transparent;border-radius:9px;background:transparent;color:inherit;text-align:left;font:inherit;cursor:pointer}
    .oct-desktop-context button:hover,.oct-desktop-context button:focus-visible{background:#78dff32b;border-color:#9ceaff55;outline:none}
    .oct-desktop-dialog{width:min(460px,calc(100vw - 28px));padding:0;border:1px solid #a8e9ff66;border-radius:20px;background:#081c30;color:#effaff;box-shadow:0 28px 90px #000c}
    .oct-desktop-dialog::backdrop{background:#020914b8;backdrop-filter:blur(7px)}
    .oct-desktop-dialog header,.oct-desktop-dialog footer{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:16px 18px;border-bottom:1px solid #ffffff20}
    .oct-desktop-dialog footer{justify-content:flex-end;border:0;border-top:1px solid #ffffff20}
    .oct-desktop-dialog main{padding:18px;display:grid;gap:10px}
    .oct-desktop-dialog button,.oct-desktop-rename{border:1px solid #a6eaff44;border-radius:10px;background:linear-gradient(155deg,#ffffff25,#ffffff08 48%,#00000022);color:inherit;padding:9px 13px;font:inherit;box-shadow:0 4px 0 #0005,0 7px 16px #0005;cursor:pointer;transition:transform .12s ease,box-shadow .12s ease,filter .12s ease}
    .oct-desktop-dialog button:hover{transform:translateY(-2px);filter:brightness(1.18);box-shadow:0 6px 0 #0005,0 12px 22px #0006}
    .oct-desktop-dialog button:active{transform:translateY(2px);box-shadow:0 1px 0 #0005,0 3px 8px #0006}
    .oct-desktop-rename{width:min(220px,90%);padding:5px 8px}
    .oct-desktop-hint{color:#b7d2e3;font-size:12px;line-height:1.5}
    a.shortcut,a.deskicon,a.app,.start,.taskapp,.tile{box-shadow:0 7px 0 #0004,0 12px 25px #0005;transition:transform .14s ease,filter .14s ease,box-shadow .14s ease}
    button:hover,a.shortcut:hover,a.deskicon:hover,a.app:hover,.start:hover,.taskapp:hover,.tile:hover{filter:brightness(1.12);transform:translateY(-2px)}
    button:active,a.shortcut:active,a.deskicon:active,a.app:active,.start:active,.taskapp:active,.tile:active{transform:translateY(2px) scale(.985)}
    :focus-visible{outline:2px solid #8deeff!important;outline-offset:3px}
    @media(prefers-reduced-motion:reduce){*,*::before,*::after{transition:none!important}}
  `;
  document.head.append(style);

  let selected = null;
  let lastClickAt = 0;
  let lastClickItem = null;
  let context = null;
  const labelsKey = "octavian.desktop.item-labels.v1";
  const readLabels = () => { try { return JSON.parse(localStorage.getItem(labelsKey) || "{}"); } catch { return {}; } };
  const labels = readLabels();
  const itemKey = item => item.dataset.desktopId || item.getAttribute("href") || item.textContent.trim();
  const labelNode = item => item.querySelector("span:last-child,small") || item;
  const toast = message => {
    let node = document.getElementById("octDesktopNotice");
    if (!node) { node=document.createElement("div"); node.id="octDesktopNotice"; node.setAttribute("role","status"); node.style.cssText="position:fixed;z-index:10002;left:50%;bottom:84px;transform:translateX(-50%);padding:11px 16px;border:1px solid #a6eaff66;border-radius:12px;background:#071b2df2;color:#f3fbff;box-shadow:0 12px 35px #0009;font:13px system-ui"; document.body.append(node); }
    node.textContent=message; node.hidden=false; clearTimeout(toast.timer); toast.timer=setTimeout(()=>node.hidden=true,2600);
  };
  const select = item => {
    document.querySelectorAll(".oct-desktop-selected").forEach(n=>n.classList.remove("oct-desktop-selected"));
    selected=item; item?.classList.add("oct-desktop-selected");
  };
  const openItem = item => {
    if (!item) return;
    const href=item.getAttribute("href");
    if (href && href !== "#") window.location.assign(href);
    else item.click();
  };
  const rename = item => {
    if (!item) return;
    const label=labelNode(item), old=label.textContent.trim();
    if (label.querySelector("input")) return;
    const input=document.createElement("input");
    input.className="oct-desktop-rename"; input.value=old; input.setAttribute("aria-label","Rename "+old);
    label.replaceChildren(input); input.focus(); input.select();
    let saved=false;
    const finish=commit=>{
      if(saved)return; saved=true;
      const value=input.value.trim() || old;
      label.textContent=value;
      if(commit){labels[itemKey(item)]=value;try{localStorage.setItem(labelsKey,JSON.stringify(labels));}catch{} toast("Renamed to "+value);}
    };
    input.addEventListener("keydown",e=>{if(e.key==="Enter"){e.preventDefault();finish(true)}if(e.key==="Escape"){e.preventDefault();finish(false)}});
    input.addEventListener("blur",()=>finish(true),{once:true});
  };
  const closeContext = () => { context?.remove(); context=null; };
  const showProperties = item => {
    let dialog=document.getElementById("octDesktopProperties");
    if(!dialog){
      dialog=document.createElement("dialog"); dialog.id="octDesktopProperties"; dialog.className="oct-desktop-dialog";
      dialog.innerHTML='<header><strong>Item properties</strong><button type="button" data-close>Close</button></header><main><div><b data-name></b></div><div data-url></div><div data-kind></div><p class="oct-desktop-hint">This is desktop-preview metadata. It does not grant filesystem permissions or prove that a native application is installed.</p></main><footer><button type="button" data-rename>Rename</button><button type="button" data-done>Done</button></footer>';
      document.body.append(dialog);
      dialog.querySelectorAll("[data-close],[data-done]").forEach(b=>b.addEventListener("click",()=>dialog.close()));
      dialog.querySelector("[data-rename]").addEventListener("click",()=>{dialog.close();rename(selected)});
    }
    dialog.querySelector("[data-name]").textContent=labelNode(item).textContent.trim();
    dialog.querySelector("[data-url]").textContent="Location: "+(item.getAttribute("href")||"No external location");
    dialog.querySelector("[data-kind]").textContent="Element: "+item.tagName.toLowerCase()+" · "+(item.className||"desktop item");
    if(!dialog.open)dialog.showModal();
  };
  const showContext = (item,x,y) => {
    closeContext(); select(item);
    context=document.createElement("div"); context.className="oct-desktop-context"; context.setAttribute("role","menu");
    const actions=[["Open","open"],["Rename","rename"],["Properties","properties"],["Copy link","copy"]];
    for(const [title,action] of actions){
      const button=document.createElement("button"); button.type="button"; button.textContent=title; button.setAttribute("role","menuitem");
      button.addEventListener("click",()=>{
        closeContext();
        if(action==="open")openItem(item);
        if(action==="rename")rename(item);
        if(action==="properties")showProperties(item);
        if(action==="copy"){const href=item.getAttribute("href")||"";navigator.clipboard?.writeText(new URL(href,location.href).href).then(()=>toast("Link copied")).catch(()=>toast("Clipboard unavailable"));}
      });
      context.append(button);
    }
    document.body.append(context);
    const rect=context.getBoundingClientRect();
    context.style.left=Math.max(8,Math.min(x,innerWidth-rect.width-8))+"px";
    context.style.top=Math.max(8,Math.min(y,innerHeight-rect.height-8))+"px";
    context.querySelector("button")?.focus();
  };
  document.querySelectorAll(itemSelector).forEach((item,index)=>{
    item.dataset.desktopId=item.dataset.desktopId||"desktop-item-"+index;
    const saved=labels[itemKey(item)];
    if(saved){const node=labelNode(item);if(node)node.textContent=saved;}
    item.addEventListener("click",e=>{
      const now=Date.now(), same=lastClickItem===item, delta=now-lastClickAt;
      if(item.matches("a") && item.closest(".desktop,.workspace,.shortcuts,.icon-grid,.apps,.dock,.taskbar"))e.preventDefault();
      if(same && delta>360 && (e.target.closest("span,small,b,strong")||e.target===item)){select(item);rename(item);}
      else select(item);
      lastClickItem=item;lastClickAt=now;
    });
    item.addEventListener("dblclick",e=>{e.preventDefault();closeContext();openItem(item);});
    item.addEventListener("contextmenu",e=>{e.preventDefault();showContext(item,e.clientX,e.clientY);});
    item.setAttribute("aria-keyshortcuts","Enter F2 Shift+F10");
  });
  document.addEventListener("pointerdown",e=>{if(context&&!context.contains(e.target))closeContext();});
  document.addEventListener("keydown",e=>{
    if(e.key==="Escape"){closeContext();document.getElementById("octDesktopProperties")?.close();return;}
    if(e.key==="F2"&&selected){e.preventDefault();rename(selected);return;}
    if(e.key==="Enter"&&selected&&!e.target.matches("input,textarea,button,select")){e.preventDefault();openItem(selected);return;}
    if((e.shiftKey&&e.key==="F10")&&selected){e.preventDefault();const r=selected.getBoundingClientRect();showContext(selected,r.left,r.bottom);return;}
    if(e.metaKey&&e.code==="Space"){const start=document.getElementById("startmenu");if(start){e.preventDefault();start.classList.toggle("open");document.getElementById("start")?.setAttribute("aria-expanded",String(start.classList.contains("open")));}}
    if(e.metaKey&&e.key.toLowerCase()==="e"){const files=[...document.querySelectorAll(itemSelector)].find(a=>/files|explorer/i.test(a.textContent));if(files){e.preventDefault();openItem(files);}}
    if(e.ctrlKey&&e.altKey&&e.key.toLowerCase()==="t"){const terminal=[...document.querySelectorAll(itemSelector)].find(a=>/terminal/i.test(a.textContent));if(terminal){e.preventDefault();openItem(terminal);}}
  });
  document.addEventListener("click",e=>{if(e.target.matches("[data-rename-label]")){const item=e.target.closest(itemSelector);if(item)rename(item);}});
  document.addEventListener("contextmenu",e=>{if(!e.target.closest(itemSelector)){closeContext();}});
  toast("Desktop interactions ready · right-click for Properties");
})();