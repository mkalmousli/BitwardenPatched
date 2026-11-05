import {R, $, ic, ABI, abiOf, guessAbi, dl, mb, OSN, BROWSERS, me, myos, showBrowser, showDesktop, versionTable, rel, counts} from "./shared.js";
let metadata;
function renderHistory(d) {
  metadata = d;
  $("dl").innerHTML=(d.android.length?"<h3>Android</h3>"+versionTable(d.android,"Android"):"")+(d.browser.length?"<h3 style='margin-top:18px'>Browser extension</h3>"+versionTable(d.browser,"Browser"):"")+((d.desktop||[]).length?"<h3 style='margin-top:18px'>Desktop</h3>"+versionTable(d.desktop,"Desktop"):"")||"No releases yet.";
}
// Render local metadata first; download counts must never delay downloads.
fetch(new URL("data/versions.json", document.baseURI), {cache: "no-cache"})
.then(response => {
  if (!response.ok) throw new Error(`Version metadata: ${response.status}`);
  return response.json();
}).then(async d => {
  for (const target of ["android", "browser", "desktop"]) {
    d[target] = Array.isArray(d[target]) ? d[target] : [];
    rel[target] = d[target][0];
  }
  const apks=(rel.android?.assets||[]).filter(abiOf),guess=await guessAbi(),best=apks.find(a=>abiOf(a)===guess)||apks[0];
  $("apk").classList.remove("skeleton");
  if(best){
    $("apk").innerHTML=`<a class="btn full" href="${dl(best)}">${ic("dl")}<span>Download APK<small>${abiOf(best)} &middot; ${mb(best.size)} &middot; v${rel.android.tag.replace(/^v|-bwpm$/g,"")}</small></span></a><p class="muted" style="margin:8px 0 0"><small>Picked for your device. Wrong? See other CPU types.</small></p>`;
    $("heroApk").href=dl(best);$("heroApk").innerHTML=`${ic("dl")}<span>Android APK<small>${abiOf(best)} &middot; ${mb(best.size)}</small></span>`;
  }else $("apk").textContent="No Android release yet.";
  $("apks").innerHTML="<table>"+apks.map(a=>`<tr><td><a href="${dl(a)}">${abiOf(a)}</a>${abiOf(a)===guess?'<span class="tag">your device</span>':""}<br><small>${ABI[abiOf(a)]}</small></td><td>${mb(a.size)}</td></tr>`).join("")+"</table>";
  $("tabs").innerHTML=Object.entries(BROWSERS).map(([k,b])=>`<button data-k="${k}" role="tab" type="button">${b.name}</button>`).join("");
  document.querySelectorAll("#tabs button").forEach(b=>b.onclick=()=>showBrowser(b.dataset.k));
  showBrowser(me);
  $("ostabs").innerHTML=Object.entries(OSN).map(([k,n])=>`<button data-k="${k}" role="tab" type="button">${n}</button>`).join("");
  document.querySelectorAll("#ostabs button").forEach(b=>b.onclick=()=>showDesktop(b.dataset.k));
  showDesktop(myos);
  renderHistory(d);
}).catch(()=>{for(const i of["apk","bro","dsk","dl"]){$(i).classList.remove("skeleton");$(i).innerHTML=`<a class="btn" href="https://github.com/${R}/releases">Open releases on GitHub</a>`}});

// Counts are optional enrichment; tolerate unavailable or rate-limited GitHub API.
fetch(`https://api.github.com/repos/${R}/releases?per_page=30`)
  .then(r => r.ok ? r.json() : [])
  .then(rs => { if (Array.isArray(rs)) for (const r of rs)
    for (const a of r.assets || []) counts[a.name] = a.download_count;
    if (metadata) {
      renderHistory(metadata);
      showDesktop(document.querySelector("#ostabs .on")?.dataset.k || myos);
    }
  })
  .catch(() => {});
