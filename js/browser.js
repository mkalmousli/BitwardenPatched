import {$, ic, dl, rel, cnt, copied} from "./common.js";
const me=navigator.brave?"brave":/Firefox\//.test(navigator.userAgent)?"firefox":/Edg\//.test(navigator.userAgent)?"edge":"chrome";
const BROWSERS={firefox:{name:"Firefox",ext:"about:debugging#/runtime/this-firefox"},chrome:{name:"Chrome",ext:"chrome://extensions"},brave:{name:"Brave",ext:"brave://extensions"},edge:{name:"Edge",ext:"edge://extensions"}};
function showBrowser(k){
  document.querySelectorAll("#tabs button").forEach(b=>{b.classList.toggle("on",b.dataset.k===k);b.setAttribute("aria-selected",b.dataset.k===k)});
  const v=rel.browser;$("bro").classList.remove("skeleton");
  if(!v){$("bro").textContent="No browser release yet.";return}
  const a=v.assets,zip=a.find(x=>/chrome\.zip$/.test(x.name)),ffzip=a.find(x=>/firefox\.zip$/.test(x.name)),
    xpi=a.find(x=>x.name.endsWith(".xpi")),crx=a.find(x=>x.name.endsWith(".crx")),ver=v.tag.replace("browser-v","");
  if(k==="firefox"){
    $("bro").innerHTML=xpi?`<a class="btn full" href="${dl(xpi)}">${ic("dl")}<span>Add to Firefox<small>One click, then confirm. Updates itself. v${ver}</small></span></a>`
      :`<p>The signed Firefox add-on is not available for this version yet.</p>`+(ffzip?`<a class="btn" href="${ffzip.release_url}">${ic("dl")}Firefox zip</a><p class="muted"><small>Temporary install: open <code>about:debugging#/runtime/this-firefox</code>, choose Load Temporary Add-on, pick the zip.</small></p>`:"");
  }else{
    const b=BROWSERS[k];
    $("bro").innerHTML=`<p style="margin-top:0">${b.name} installs outside-store extensions in developer mode. About a minute. v${ver}</p>
    <ol><li><a class="btn" href="${zip?zip.release_url:"#"}">${ic("dl")}Extension zip</a> then unzip it.</li>
    <li>Open <code>${b.ext}</code> <button class="btn alt" id="ce" type="button" style="min-height:36px;padding:0 12px">${ic("copy")}Copy</button><br><small>Browsers block links to this page, so copy and paste it.</small></li>
    <li>Switch on <b>Developer mode</b>.</li><li>Click <b>Load unpacked</b> and pick the unzipped folder.</li></ol>
    ${crx?`<details><summary>Self-updating CRX (Linux, or by policy)</summary><p><a class="btn alt" href="${dl(crx)}">${ic("dl")}.crx</a></p><p class="muted"><small>Drag it onto the extensions page. Chrome on Windows and macOS only accepts it through an extension policy.</small></p></details>`:""}`;
    $("ce").onclick=()=>navigator.clipboard.writeText(b.ext).then(()=>copied($("ce"),ic("copy")+"Copy"));
  }
}

export {BROWSERS, me, showBrowser};
