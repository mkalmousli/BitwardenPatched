import {dl, day, mb, cnt} from "./common.js";
function versionTable(list,label){
  return list.map((v,i)=>`<details ${i?"":"open"}><summary>${label} ${v.tag.replace(/^browser-|^desktop-|-bwpm$/g,"")}<small>&nbsp;&middot; ${day(v.built)}</small>${i?"":'<span class="tag">latest</span>'}</summary><p style="margin:0 0 6px"><small><a href="${v.release}">Release notes and checksums</a></small></p><table>`+
    v.assets.filter(a=>a.name!=="SHA256SUMS").map(a=>`<tr><td><a href="${dl(a)}">${a.name.replace(/^bitwarden-patched-/,"")}</a><br><small>${cnt(a).replace(/^ &middot; /,"")}</small></td><td>${mb(a.size)}</td></tr>`).join("")+"</table></details>").join("");
}

export {versionTable};
