(() => {
  "use strict";
  const itemSelector = "a.shortcut,a.deskicon,a.app";
  const style = document.createElement("style");
  style.textContent = `
    .oct-windowbar{height:36px;display:flex;align-items:center;gap:7px;padding:5px 10px;background:#071b2de8;border-bottom:1px solid #ffffff24;cursor:move;user-select:none}
    .oct-windowbar strong{font:600 12px system-ui;margin-right:auto}
    .oct-windowbar button{width:25px;height:25px;border:1px solid #ffffff35;border-radius:50%;background:#ffffff18;color:inherit;cursor:pointer;line-height:1}
    .oct-windowbar button:hover{filter:brightness(1.3);transform:translateY(-1px)}
    .oct-managed-window{min-width:240px;min-height:170px;max-width:calc(100vw - 16px);max-height:calc(100vh - 54px);overflow:auto;resize:both;scrollbar-gutter:stable;overscroll-behavior:contain}
    .oct-managed-window.oct-maximized{position:fixed!important;inset:42px 12px 84px 12px!important;width:auto!important;height:auto!important;max-width:none!important;max-height:none!important;transform:none!important;resize:none!important;z-index:9500!important}
    .oct-managed-window.oct-minimized{display:none!important}
    .oct-restore-tray{position:fixed;z-index:9998;left:12px;bottom:14px;display:flex;gap:6px;max-width:calc(100vw - 24px);overflow:auto}
    .oct-restore-tray button{border:1px solid #a6eaff55;border-radius:10px;padding:8px 12px;background:#071b2df2;color:#f3fbff;cursor:pointer}
    .oct-window-arrange{outline:2px solid #8deeff;outline-offset:-2px}
    .oct-windowbar button:focus-visible,.oct-restore-tray button:focus-visible{outline:2px solid #8deeff;outline-offset:2px}
    .window,.widget,.optional-apps-window{overflow:auto;scrollbar-gutter:stable;overscroll-behavior:contain}
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
      if(same && delta>700 && (e.target.closest("span,small,b,strong")||e.target===item)){select(item);rename(item);}
      else select(item);
      lastClickItem=item;lastClickAt=now;
    });
    item.addEventListener("dblclick",e=>{e.preventDefault();closeContext();clearTimeout(pendingOpen);pendingOpen=setTimeout(()=>{if(lastTripleItem!==item){playUiSound("open");openItem(item);}},260);});
    item.addEventListener("contextmenu",e=>{e.preventDefault();showContext(item,e.clientX,e.clientY);});
    item.setAttribute("aria-keyshortcuts","Enter F2 Shift+F10");
  });
  document.addEventListener("pointerdown",e=>{if(context&&!context.contains(e.target))closeContext();if(activeMenu&&!activeMenu.popup.contains(e.target)&&!activeMenu.button.contains(e.target))closeMenu();});
  document.addEventListener("keydown",e=>{
    const editing=e.target.matches("input,textarea,select,[contenteditable=true]");
    const primary=e.ctrlKey||e.metaKey;
    if(!editing&&primary&&e.key.toLowerCase()==="c"&&selected){
      e.preventDefault();
      const href=selected.getAttribute("href")||"";
      navigator.clipboard?.writeText(new URL(href,location.href).href).then(()=>toast("Link copied")).catch(()=>toast("Clipboard unavailable"));
      return;
    }
    if(!editing&&primary&&["x","v"].includes(e.key.toLowerCase())){
      e.preventDefault();toast("Cut/Paste is disabled in this preview; no filesystem changes were made.");return;
    }
    if(e.altKey&&e.key==="F4"){
      closeContext();closeMenu();document.getElementById("octDesktopProperties")?.close();document.getElementById("octDesktopInfo")?.close();
      toast("Close the desktop window using your operating system.");return;
    }
    if(e.key==="Delete"&&selected&&!editing){e.preventDefault();toast("Delete is disabled in this preview; no files were changed.");return;}
    if(e.key==="Escape"){closeContext();closeMenu();document.getElementById("octDesktopProperties")?.close();document.getElementById("octDesktopInfo")?.close();return;}
    if(e.key==="F2"&&selected){e.preventDefault();rename(selected);return;}
    if(e.key==="Enter"&&selected&&!e.target.matches("input,textarea,button,select")){e.preventDefault();openItem(selected);return;}
    if((e.shiftKey&&e.key==="F10")&&selected){e.preventDefault();const r=selected.getBoundingClientRect();showContext(selected,r.left,r.bottom);return;}
    if(e.metaKey&&e.code==="Space"){const start=document.getElementById("startmenu");if(start){e.preventDefault();start.classList.toggle("open");document.getElementById("start")?.setAttribute("aria-expanded",String(start.classList.contains("open")));}}
    if(e.metaKey&&e.key.toLowerCase()==="e"){const files=[...document.querySelectorAll(itemSelector)].find(a=>/files|explorer/i.test(a.textContent));if(files){e.preventDefault();openItem(files);}}
    if(e.ctrlKey&&e.altKey&&e.key.toLowerCase()==="t"){const terminal=[...document.querySelectorAll(itemSelector)].find(a=>/terminal/i.test(a.textContent));if(terminal){e.preventDefault();openItem(terminal);}}
  });
  document.addEventListener("click",e=>{if(e.target.matches("[data-rename-label]")){const item=e.target.closest(itemSelector);if(item)rename(item);}});
  document.addEventListener("contextmenu",e=>{if(!e.target.closest(itemSelector)){closeContext();}});

  let activeMenu = null;
  const menuDefinitions = {
    File: [["Open Files / Explorer","files"],["Open Terminal","terminal"],["Properties","properties"]],
    Edit: [["Rename Selected","rename"],["Copy Selected Link","copy"]],
    View: [["Backgrounds","backgrounds"],["Refresh Desktop","refresh"]],
    Window: [["Tile Windows","tile"],["Cascade Windows","cascade"],["Minimize Active Window","minimize"],["Maximize / Restore Active Window","maximize"],["Show Start / Applications","start"],["Show Desktop","showdesktop"]],
    Help: [["Keyboard Shortcuts","shortcuts"],["About OctavianOS","about"]]
  };
  const closeMenu = () => {
    if(activeMenu){activeMenu.button?.setAttribute("aria-expanded","false");activeMenu.popup.remove();activeMenu=null;}
  };
  const infoDialog = (heading,body) => {
    let dialog=document.getElementById("octDesktopInfo");
    if(!dialog){
      dialog=document.createElement("dialog");dialog.id="octDesktopInfo";dialog.className="oct-desktop-dialog";
      dialog.innerHTML='<header><strong data-title></strong><button type="button" data-close>Close</button></header><main><p data-body></p></main><footer><button type="button" data-done>Done</button></footer>';
      document.body.append(dialog);
      dialog.querySelectorAll("[data-close],[data-done]").forEach(b=>b.addEventListener("click",()=>dialog.close()));
    }
    dialog.querySelector("[data-title]").textContent=heading;
    dialog.querySelector("[data-body]").textContent=body;
    if(!dialog.open)dialog.showModal();
  };
  const openNamedItem = pattern => {
    const item=[...document.querySelectorAll(itemSelector)].find(a=>pattern.test(labelNode(a).textContent));
    if(item)openItem(item);else toast("No matching desktop shortcut is available.");
  };
  const runMenuAction = action => {
    if(action==="files")return openNamedItem(/files|explorer/i);
    if(action==="terminal")return openNamedItem(/terminal/i);
    if(action==="properties")return selected?showProperties(selected):toast("Select a shortcut first.");
    if(action==="rename")return selected?rename(selected):toast("Select a shortcut first.");
    if(action==="copy"){
      if(!selected)return toast("Select a shortcut first.");
      const href=selected.getAttribute("href")||"";
      navigator.clipboard?.writeText(new URL(href,location.href).href).then(()=>toast("Link copied")).catch(()=>toast("Clipboard unavailable"));
      return;
    }
    if(action==="backgrounds"){document.getElementById("wallpaperButton")?.click();return;}
    if(action==="refresh"){location.reload();return;}
    if(action==="start"){
      const start=document.getElementById("start");
      if(start){start.click();return;}
      const apps=[...document.querySelectorAll("button")].find(b=>/applications/i.test(b.textContent));
      if(apps){apps.click();return;}
      toast("No application launcher is available in this preview.");return;
    }
    if(action==="showdesktop"){
      closeContext();closeMenu();document.getElementById("octDesktopProperties")?.close();document.getElementById("octDesktopInfo")?.close();
      document.querySelectorAll(".oct-desktop-selected").forEach(n=>n.classList.remove("oct-desktop-selected"));
      selected=null;return;
    }
    if(action==="shortcuts"){
      infoDialog("Desktop keyboard shortcuts","F2: rename selected shortcut\nEnter: open selected shortcut\nShift+F10: context menu\nCtrl/Cmd+C: copy selected link\nCtrl/Cmd+X or V: blocked in preview\nMeta+E: Files / Explorer\nMeta+Space: Start menu (Marine)\nCtrl+Alt+T: Terminal\nAlt+F4: dismiss dialogs\nDelete: blocked in preview\nEscape: close popup");
      return;
    }
    if(["tile","cascade","minimize","maximize"].includes(action)){windowAction(action);return;}
    if(action==="about"){
      infoDialog("About OctavianOS","Aurora and Marine desktop interaction preview. Native compositor, host filesystem operations and app installation are separate runtime capabilities.");
    }
  };
  const showMenu = button => {
    closeMenu();closeContext();
    const name=button.dataset.desktopMenu;
    const actions=menuDefinitions[name]||[];
    const popup=document.createElement("div");popup.className="oct-desktop-context oct-desktop-menupopup";popup.setAttribute("role","menu");
    for(const [label,action] of actions){
      const item=document.createElement("button");item.type="button";item.textContent=label;item.setAttribute("role","menuitem");
      item.addEventListener("click",()=>{closeMenu();runMenuAction(action);});
      popup.append(item);
    }
    document.body.append(popup);
    const r=button.getBoundingClientRect(), p=popup.getBoundingClientRect();
    popup.style.left=Math.max(8,Math.min(r.left,innerWidth-p.width-8))+"px";
    popup.style.top=Math.max(8,Math.min(r.bottom+5,innerHeight-p.height-8))+"px";
    button.setAttribute("aria-expanded","true");activeMenu={button,popup};popup.querySelector("button")?.focus();
  };
  document.querySelectorAll("[data-desktop-menu]").forEach(button=>{
    button.addEventListener("click",()=>showMenu(button));
    button.setAttribute("aria-haspopup","menu");button.setAttribute("aria-expanded","false");
  });


  // Browser-preview window manager: controls act on visible preview panels only.
  const managedWindows = [...document.querySelectorAll(".window,.widget,[data-managed-window]")];
  const restoreTray=document.createElement("nav");restoreTray.className="oct-restore-tray";restoreTray.setAttribute("aria-label","Minimized preview windows");document.body.append(restoreTray);
  let activeWindow=managedWindows[0]||null;
  const soundEnabledKey="octavian.desktop.sounds.v1";
  let soundsEnabled=localStorage.getItem(soundEnabledKey)!=="off";
  const playUiSound=(kind="click")=>{
    if(!soundsEnabled)return;
    try{
      const Audio=window.AudioContext||window.webkitAudioContext;if(!Audio)return;
      const ctx=playUiSound.ctx||(playUiSound.ctx=new Audio());
      if(ctx.state==="suspended")ctx.resume();
      const osc=ctx.createOscillator(),gain=ctx.createGain();
      const tones={click:[620,.035],open:[760,.075],close:[340,.09],minimize:[430,.07],maximize:[690,.07],error:[180,.12]};
      const [hz,duration]=tones[kind]||tones.click;
      osc.type="sine";osc.frequency.setValueAtTime(hz,ctx.currentTime);
      gain.gain.setValueAtTime(.0001,ctx.currentTime);gain.gain.exponentialRampToValueAtTime(.035,ctx.currentTime+.008);
      gain.gain.exponentialRampToValueAtTime(.0001,ctx.currentTime+duration);
      osc.connect(gain);gain.connect(ctx.destination);osc.start();osc.stop(ctx.currentTime+duration+.01);
    }catch{}
  };
  const updateRestoreTray=()=>{
    restoreTray.replaceChildren();
    managedWindows.filter(w=>w.classList.contains("oct-minimized")).forEach((w,i)=>{
      const b=document.createElement("button");b.type="button";b.textContent="Restore "+(w.dataset.windowTitle||("Window "+(i+1)));
      b.addEventListener("click",()=>{w.classList.remove("oct-minimized");w.hidden=false;activeWindow=w;playUiSound("open");});
      restoreTray.append(b);
    });
  };
  const windowTitle=w=>w.dataset.windowTitle||w.querySelector(".windowtitle,h1,h2")?.textContent?.trim()||"Workspace";
  const focusWindow=w=>{activeWindow=w;w.style.zIndex=String(9600+managedWindows.indexOf(w));};
  const addWindowControls=w=>{
    w.classList.add("oct-managed-window");w.dataset.windowTitle=windowTitle(w);
    let bar=w.querySelector(".titlebar");
    if(!bar){bar=document.createElement("div");bar.className="oct-windowbar";bar.innerHTML="<strong></strong>";w.prepend(bar);}
    bar.classList.add("oct-windowbar");
    if(!bar.querySelector("strong")){const title=document.createElement("strong");title.textContent=w.dataset.windowTitle;bar.prepend(title);}
    if(bar.dataset.controlsReady)return;bar.dataset.controlsReady="true";
    const controls=[["−","Minimize","minimize"],["□","Maximize or restore","maximize"],["×","Close panel","close"]];
    for(const [glyph,label,action] of controls){
      const b=document.createElement("button");b.type="button";b.textContent=glyph;b.title=label;b.setAttribute("aria-label",label);
      b.addEventListener("click",e=>{e.stopPropagation();focusWindow(w);if(action==="minimize"){w.classList.add("oct-minimized");playUiSound("minimize");updateRestoreTray();}
        if(action==="maximize"){w.classList.toggle("oct-maximized");playUiSound("maximize");}
        if(action==="close"){w.classList.add("oct-minimized");playUiSound("close");updateRestoreTray();}});
      bar.append(b);
    }
    w.addEventListener("pointerdown",()=>focusWindow(w));
    bar.addEventListener("dblclick",e=>{if(e.target.closest("button"))return;w.classList.toggle("oct-maximized");playUiSound("maximize");});
  };
  managedWindows.forEach(addWindowControls);
  const arrangeWindows=mode=>{
    const visible=managedWindows.filter(w=>!w.classList.contains("oct-minimized"));
    if(!visible.length){toast("There are no open preview windows.");return;}
    visible.forEach((w,i)=>{
      w.classList.remove("oct-maximized");w.classList.add("oct-window-arrange");
      w.style.position="fixed";w.style.transform="none";w.style.margin="0";
      if(mode==="tile"){
        const cols=Math.ceil(Math.sqrt(visible.length)),rows=Math.ceil(visible.length/cols);
        const col=i%cols,row=Math.floor(i/cols),gap=12,top=48,bottom=88;
        w.style.left=(12+col*(innerWidth-24)/cols)+"px";w.style.top=(top+row*(innerHeight-top-bottom)/rows)+"px";
        w.style.width=((innerWidth-24)/cols-gap)+"px";w.style.height=((innerHeight-top-bottom)/rows-gap)+"px";
      }else{
        const offset=i*28;w.style.left=(24+offset)+"px";w.style.top=(52+offset)+"px";
        w.style.width="min(720px, calc(100vw - 48px))";w.style.height="min(520px, calc(100vh - 150px))";
      }
      w.style.zIndex=String(9600+i);
    });
    toast(mode==="tile"?"Preview windows tiled.":"Preview windows cascaded.");
  };
  const windowAction=action=>{
    if(action==="tile"||action==="cascade"){arrangeWindows(action);return;}
    if(!activeWindow){toast("No active preview window.");return;}
    if(action==="minimize"){activeWindow.classList.add("oct-minimized");updateRestoreTray();playUiSound("minimize");}
    if(action==="maximize"){activeWindow.classList.toggle("oct-maximized");playUiSound("maximize");}
  };
  document.addEventListener("click",e=>{
    if(e.target.closest("button,a"))playUiSound("click");
  },true);
  // A third click on a desktop item opens Properties; double-click remains Open.
  let pendingOpen=null,lastClickCount=0,lastTripleItem=null;
  document.querySelectorAll(itemSelector).forEach(item=>{
    item.addEventListener("click",e=>{if(e.detail===3){clearTimeout(pendingOpen);lastTripleItem=item;}},true);
    item.addEventListener("click",e=>{
      if(e.detail===3){e.preventDefault();clearTimeout(pendingOpen);lastTripleItem=item;select(item);showProperties(item);playUiSound("open");}
      else if(e.detail===1){lastTripleItem=null;}
    },true);
  });
  toast("Desktop interactions ready · right-click for Properties");
})();