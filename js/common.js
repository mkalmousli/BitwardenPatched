const R="mkalmousli/BitwardenPatched",FP="B1D78FEC2A8513EFD0EF78AE2C73887DFDC84F4CE6C786C61D524E1D4B43821B";
const $=id=>document.getElementById(id),mb=n=>(n/1048576).toFixed(0)+" MB",fmt=n=>n.toLocaleString(),day=d=>new Date(d).toLocaleDateString(undefined,{year:"numeric",month:"short",day:"numeric"});
const ic=n=>`<svg class="i"><use href="#${["dl", "qr"].includes(n) ? "icon-" + n : n}"/></svg>`;
const base=location.origin+location.pathname.replace(/[^/]*$/,"");
const repoUrl=base+"repo?fingerprint="+FP;
$("fd").href=repoUrl.replace(/^https?:\/\//,"fdroidrepos://");
const copied=(b,html)=>{b.innerHTML=ic("check")+"Copied";setTimeout(()=>b.innerHTML=html,1500)};
$("cp").onclick=()=>navigator.clipboard.writeText(repoUrl).then(()=>copied($("cp"),ic("copy")+"Copy"));

const ABI={"arm64-v8a":"Most phones since 2017","armeabi-v7a":"Older 32-bit phones","x86_64":"Emulators, Chromebooks","x86":"Old emulators","universal":"Any device (larger)"};
async function guessAbi(){
  try{const h=await navigator.userAgentData.getHighEntropyValues(["architecture","bitness"]);
    if(h.architecture==="arm")return h.bitness==="32"?"armeabi-v7a":"arm64-v8a";
    if(h.architecture==="x86")return h.bitness==="32"?"x86":"x86_64";}catch(e){}
  return /armv7|armeabi/i.test(navigator.userAgent)?"armeabi-v7a":"arm64-v8a";
}
const abiOf=a=>(a.name.match(/-(arm64-v8a|armeabi-v7a|x86[_-]64|x86|universal)\.apk$/)||[])[1]?.replace("x86-64","x86_64");
const rel={},counts={};
const dl=a=>a.release_url,cnt=a=>counts[a.name]!=null?` &middot; ${fmt(counts[a.name])} downloads`:"";

export {R, $, ic, base, ABI, abiOf, guessAbi, dl, mb, day, cnt, copied, rel, counts};
