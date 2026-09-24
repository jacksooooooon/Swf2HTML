#!/usr/bin/env python3
"""Turn a .swf file into one self-contained HTML file that plays it full-window, offline.

Usage:
  python3 make_game.py game.swf                 -> game.html (next to the .swf)
  python3 make_game.py a.swf b.swf              -> a.html, b.html
  python3 make_game.py game.swf -o out.html --title "My Game" --open

The first run downloads the Ruffle Flash emulator from npm (about 20 MB) and
caches it; after that no internet is needed. The generated HTML never needs it.
"""
import argparse, base64, binascii, hashlib, io, os, re, subprocess, sys, tarfile, urllib.request, zlib

RUFFLE_VERSION = "0.6.0"
RUFFLE_URL = "https://registry.npmjs.org/@ruffle-rs/ruffle/-/ruffle-0.6.0.tgz"
RUFFLE_SHA512 = "P2X1zDENBoiLt2ZjPcsUzaDxoR7fVF2e1U/bi7hbIAQEjkykxljSoG8AgbywHvlVVzL9Y5tIZMRqDwIm31jgPA=="
MAGIC = (b"FWS", b"CWS", b"ZWS")

PAGE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>@@TITLE@@</title>
<style>
html,body{height:100%;margin:0;overflow:hidden;background:#000;overscroll-behavior:none;-webkit-user-select:none;user-select:none}
#stage,.swf{position:fixed;top:0;left:0;width:100%;height:100%;display:block}
#msg{position:fixed;top:0;left:0;right:0;bottom:0;display:none;align-items:center;justify-content:center;padding:24px;text-align:center;color:#ddd;font:16px/1.4 system-ui,sans-serif}
#msg.on{display:flex}
</style>
</head>
<body>
<div id="stage"></div>
<div id="msg" class="on">Loading…</div>
<script type="application/octet-stream" id="swf-data">@@SWF@@</script>
@@ENGINE@@
<script type="text/plain" id="licenses">Ruffle (https://ruffle.rs) is embedded in this file under the MIT or Apache-2.0 license, at your option. MIT license text:

@@LIC@@</script>

<script>
/* 1. Engine setup: config, decompression, and a fetch shim that serves the embedded WebAssembly. */
window.RufflePlayer={config:{polyfills:false,publicPath:"",autoplay:"on",unmuteOverlay:"hidden",letterbox:"on",splashScreen:false,warnOnUnsupportedContent:false,logLevel:"error",contextMenu:"on"}};
var SWFP=(function(){
var LB=[3,4,5,6,7,8,9,10,11,13,15,17,19,23,27,31,35,43,51,59,67,83,99,115,131,163,195,227,258],
LE=[0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4,5,5,5,5,0],
DB=[1,2,3,4,5,7,9,13,17,25,33,49,65,97,129,193,257,385,513,769,1025,1537,2049,3073,4097,6145,8193,12289,16385,24577],
DE=[0,0,0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,12,12,13,13],
CO=[16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15];
function huff(l,off,n){var c=new Uint16Array(16),s=new Uint16Array(n),f=new Uint16Array(16),i;for(i=0;i<n;i++)c[l[off+i]]++;for(i=1;i<15;i++)f[i+1]=f[i]+c[i];for(i=0;i<n;i++)if(l[off+i])s[f[l[off+i]]++]=i;return{c:c,s:s}}
function sync(z,n){
  var o=new Uint8Array(n),op=0,ip=0,bb=0,bc=0,i;
  function bits(k){var v=bb;while(bc<k){v|=z[ip++]<<bc;bc+=8}bb=v>>>k;bc-=k;return v&((1<<k)-1)}
  function dec(h){var code=0,first=0,idx=0,len,cnt;for(len=1;len<16;len++){code|=bits(1);cnt=h.c[len];if(code-cnt<first)return h.s[idx+code-first];idx+=cnt;first=(first+cnt)<<1;code<<=1}throw new Error("bad data")}
  var last,t,lc,dc;
  do{
    last=bits(1);t=bits(2);
    if(t===0){bb=0;bc=0;var L=z[ip]|(z[ip+1]<<8);ip+=4;while(L--)o[op++]=z[ip++]}
    else if(t===3){throw new Error("bad data")}
    else{
      if(t===1){var fl=new Uint8Array(288),fd=new Uint8Array(30);for(i=0;i<288;i++)fl[i]=i<144?8:i<256?9:i<280?7:8;for(i=0;i<30;i++)fd[i]=5;lc=huff(fl,0,288);dc=huff(fd,0,30)}
      else{
        var nl=bits(5)+257,nd=bits(5)+1,nc=bits(4)+4,tl=new Uint8Array(19);
        for(i=0;i<nc;i++)tl[CO[i]]=bits(3);
        var cc=huff(tl,0,19),ln=new Uint8Array(nl+nd),sy,rep,val;
        i=0;
        while(i<nl+nd){sy=dec(cc);if(sy<16){ln[i++]=sy}else{val=0;if(sy===16){val=ln[i-1];rep=3+bits(2)}else if(sy===17){rep=3+bits(3)}else{rep=11+bits(7)}while(rep--)ln[i++]=val}}
        lc=huff(ln,0,nl);dc=huff(ln,nl,nd);
      }
      for(;;){
        var s=dec(lc);
        if(s<256){o[op++]=s}else if(s===256){break}
        else{s-=257;var m=LB[s]+bits(LE[s]),q=dec(dc),d=DB[q]+bits(DE[q]);while(m--){o[op]=o[op-d];op++}}
      }
    }
  }while(!last);
  return o;
}
var api={say:function(){}},cache={};
function b64(s){var r=atob(s),n=r.length,u=new Uint8Array(n);for(var i=0;i<n;i++)u[i]=r.charCodeAt(i);return u}
function inflate(z,n){
  try{
    if(window.DecompressionStream&&window.Response&&window.Blob&&Blob.prototype.stream){
      var ds=new DecompressionStream("deflate-raw");
      return new Response(new Blob([z]).stream().pipeThrough(ds)).arrayBuffer().then(function(a){return new Uint8Array(a)},function(){return sync(z,n)});
    }
  }catch(e){}
  return new Promise(function(r){setTimeout(r,40)}).then(function(){return sync(z,n)});
}
function wasm(h){
  if(!cache[h]){
    var el=document.querySelector('script[data-h="'+h+'"]');
    if(!el)return Promise.reject(new Error("Missing engine data"));
    api.say("Unpacking the Flash engine (first run only)\u2026");
    cache[h]=new Promise(function(r){setTimeout(r,30)}).then(function(){return inflate(b64(el.textContent),+el.getAttribute("data-n"))});
  }
  return cache[h];
}
var realFetch=window.fetch;
window.fetch=function(u){
  var s=typeof u==="string"?u:(u&&(u.href||u.url))||"";
  if(s.indexOf("ruffle-wasm:")===0){
    return wasm(s.slice(12)).then(function(b){return new Response(b,{status:200,headers:{"Content-Type":"application/wasm"}})});
  }
  return realFetch.apply(this,arguments);
};
return api;
})();
</script>
@@CHUNKS@@
<script>@@RUFFLE@@</script>
<script>
(function(){
var stage=document.getElementById("stage"),msg=document.getElementById("msg");
function fail(t){msg.textContent=t;msg.className="on"}
var emb=document.getElementById("swf-data"),txt=emb?emb.textContent.replace(/\s+/g,""):"";
if(!window.WebAssembly||!window.Promise||!window.RufflePlayer||!window.RufflePlayer.newest){fail("This browser can't run the Flash engine. Try a current Chrome, Firefox, Safari or Edge.");return}
if(!txt){fail("No game is embedded in this file. Build one from a .swf with make_game.py.");return}
var u;
try{var s=atob(txt),n=s.length;u=new Uint8Array(n);for(var i=0;i<n;i++)u[i]=s.charCodeAt(i)}
catch(e){fail("The embedded game data is damaged.");return}
try{
  var p=window.RufflePlayer.newest().createPlayer();
  p.className="swf";
  stage.appendChild(p);
  Promise.resolve(p.load({data:u})).then(function(){msg.className=""},function(e){fail("Could not play this game. "+(e&&e.message?e.message:""))});
}catch(e){fail("Could not start the player. "+(e&&e.message?e.message:""))}
})();
</script>
</body>
</html>
'''


def die(msg):
    sys.exit("error: " + msg)


def esc_script(js):
    js = re.sub(r"//# sourceMappingURL=.*", "", js)
    return js.replace("</script", "<\\/script").replace("<!--", "<\\!--")


def fetch_ruffle(local):
    if local:
        data = open(local, "rb").read()
    else:
        print("Downloading Ruffle %s (first run only)..." % RUFFLE_VERSION, file=sys.stderr)
        try:
            data = urllib.request.urlopen(RUFFLE_URL, timeout=120).read()
        except Exception as e:
            die("could not download Ruffle (%s). Connect to the internet, or download %s "
                "yourself and pass it with --ruffle FILE.tgz" % (e, RUFFLE_URL))
    if base64.b64encode(hashlib.sha512(data).digest()).decode() != RUFFLE_SHA512:
        die("the Ruffle package does not match the expected checksum; refusing to use it.")
    return data


def build_player(local):
    """Return the player HTML (engine embedded, game slot empty)."""
    tar = tarfile.open(fileobj=io.BytesIO(fetch_ruffle(local)), mode="r:gz")
    files = {m.name[len("package/"):]: tar.extractfile(m).read()
             for m in tar.getmembers() if m.isfile() and m.name.startswith("package/")}
    wasm = sorted(n for n in files if n.endswith(".wasm"))
    chunks = sorted(n for n in files if re.match(r"core\.ruffle\..*\.js$", n))
    if not wasm or not chunks or "ruffle.js" not in files:
        die("unexpected Ruffle package layout.")
    ruffle = files["ruffle.js"].decode("utf-8")
    ruffle, n = re.subn(r'e\.exports=a\.p\+"([0-9a-f]+)\.wasm"', r'e.exports="ruffle-wasm:\1"', ruffle)
    if n != len(wasm):
        die("unexpected Ruffle package layout (wasm loader not found).")
    engine = ""
    for i, name in enumerate(wasm):
        raw = files[name]
        c = zlib.compressobj(9, zlib.DEFLATED, -15)
        z = c.compress(raw) + c.flush()
        engine += '<script type="application/octet-stream" id="w%d" data-h="%s" data-n="%d">%s</script>\n' % (
            i, name[:-5], len(raw), base64.b64encode(z).decode())
    page = PAGE
    for key, val in (("@@ENGINE@@", engine), ("@@CHUNKS@@", "".join("<script>%s</script>\n" % esc_script(files[c].decode("utf-8")) for c in chunks)),
                     ("@@LIC@@", files.get("LICENSE_MIT", b"").decode("utf-8")), ("@@RUFFLE@@", esc_script(ruffle))):
        page = page.replace(key, val, 1)
    return page


def get_player(local):
    cache = os.path.join(os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"), "swf2html")
    key = hashlib.sha256((PAGE + RUFFLE_SHA512).encode()).hexdigest()[:12]
    path = os.path.join(cache, "player-%s.html" % key)
    try:
        return open(path, encoding="utf-8").read()
    except OSError:
        pass
    page = build_player(local)
    try:
        os.makedirs(cache, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(page)
    except OSError:
        pass
    return page


def load_swf(path):
    try:
        data = open(path, "rb").read()
    except OSError as e:
        die(e)
    if data[:3] in MAGIC:
        return data
    text = re.sub(r"^\s*data:[^,]*,", "", data.decode("utf-8", "replace"))
    b64 = re.sub(r"\s+", "", text).replace("-", "+").replace("_", "/")
    b64 += "=" * (-len(b64) % 4)
    try:
        data = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError):
        die("%s is not a .swf file (and not base64 of one)." % path)
    if data[:3] not in MAGIC:
        die("%s does not contain a .swf (expected FWS, CWS or ZWS header)." % path)
    return data


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("swf", nargs="+", help=".swf file(s), or a text file with base64 of one")
    ap.add_argument("-o", "--out", help="output file (only with a single input)")
    ap.add_argument("-t", "--title", help="page title (default: the file name)")
    ap.add_argument("--ruffle", metavar="FILE.tgz", help="use a local copy of the Ruffle npm package instead of downloading")
    ap.add_argument("--open", action="store_true", help="open the result in your default browser")
    a = ap.parse_args()
    if a.out and len(a.swf) > 1:
        die("-o only works with a single input file.")
    swfs = [(p, load_swf(p)) for p in a.swf]
    player = get_player(a.ruffle)
    for path, swf in swfs:
        stem = os.path.splitext(os.path.basename(path))[0]
        out = a.out or os.path.join(os.path.dirname(os.path.abspath(path)), stem + ".html")
        if os.path.abspath(out) == os.path.abspath(path):
            die("refusing to overwrite " + out)
        title = (a.title or stem).replace("&", "&amp;").replace("<", "&lt;")
        html = player.replace("@@TITLE@@", title, 1).replace("@@SWF@@", base64.b64encode(swf).decode(), 1)
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
        print("wrote %s (%.1f MB, game %.1f KB)" % (out, len(html) / 1e6, len(swf) / 1024))
        if a.open:
            subprocess.Popen(["xdg-open", out], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
