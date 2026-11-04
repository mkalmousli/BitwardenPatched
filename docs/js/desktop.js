import {$, dl, rel, cnt, mb} from "./common.js";
const OSN={windows:"Windows",linux:"Linux",macos:"macOS"},myos=/Win/.test(navigator.platform)?"windows":/Mac/.test(navigator.platform)?"macos":"linux";
const osOf=a=>(a.name.match(/-(windows|linux|macos)-(x64|arm64)-/)||[]).slice(1);
const kindOf=n=>/Setup/.test(n)?"Installer":/Portable/.test(n)?"Portable exe":/AppImage$/.test(n)?"AppImage":/\.deb$/.test(n)?"deb package":/\.rpm$/.test(n)?"RPM package":/\.dmg$/.test(n)?"dmg disk image":/\.zip$/.test(n)?"zip":/tar\.gz$/.test(n)?"tar.gz":n;
async function myArch(){try{const h=await navigator.userAgentData.getHighEntropyValues(["architecture"]);return h.architecture==="arm"?"arm64":"x64"}catch(e){return /Mac/.test(navigator.platform)?"arm64":"x64"}}
async function showDesktop(k){
  document.querySelectorAll("#ostabs button").forEach(b=>{b.classList.toggle("on",b.dataset.k===k);b.setAttribute("aria-selected",b.dataset.k===k)});
  const v=rel.desktop;$("dsk").classList.remove("skeleton");
  if(!v){$("dsk").textContent="No desktop release yet.";return}
  const mine=await myArch(),rows=v.assets.filter(a=>osOf(a)[0]===k&&!/source/.test(a.name)).sort((a,b)=>(osOf(b)[1]===mine)-(osOf(a)[1]===mine));
  $("dsk").innerHTML=rows.length?"<table>"+rows.map(a=>`<tr><td><a href="${dl(a)}">${kindOf(a.name)} &middot; ${osOf(a)[1]}</a>${osOf(a)[1]===mine?'<span class="tag">your device</span>':""}<br><small>v${v.tag.replace("desktop-v","")}${cnt(a)}</small></td><td>${mb(a.size)}</td></tr>`).join("")+"</table>":"Not built for "+OSN[k]+" yet.";
}

export {OSN, myos, showDesktop};
