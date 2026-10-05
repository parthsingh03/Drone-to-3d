"""Assemble the fully self-contained page.html for the DRONE->3D artifact.
Reads from assets/: three.min.js, GLTFLoader.js, OrbitControls.js,
cloud.bin.b64 (+cloud.meta.json), model.glb.b64, photo_*.b64, stats.json.
Writes page.html (everything inline, no external requests)."""
import json, os, base64

A = 'assets'
def rd(p, mode='r'):
    with open(os.path.join(A, p), mode) as f:
        return f.read()

three_js = rd('three.min.js')
gltf_js = rd('GLTFLoader.js')
orbit_js = rd('OrbitControls.js')
cloud_b64 = rd('cloud.bin.b64').strip()
cloud_meta = json.loads(rd('cloud.meta.json'))
model_b64 = rd('model.glb.b64').strip()
stats = json.loads(rd('stats.json'))
photos = []
for i in range(8):
    photos.append(rd(f'photo_{i}.b64').strip())

n_img = stats['registered_images']
n_pts = stats['cloud_points']
n_src = stats['source_images']
photo_imgs = '\n'.join(
    f'<figure class="shot"><img src="data:image/jpeg;base64,{p}" alt="drone photo {i+1}" loading="lazy">'
    f'<figcaption>#{i+1:02d}</figcaption></figure>' for i, p in enumerate(photos))

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DRONE &rarr; 3D &mdash; from drone photos to an interactive 3D model</title>
<style>
:root{
  --bg:#060d09; --panel:#0b1710; --panel2:#0e1d14;
  --green:#22c55e; --green-dim:#14532d; --saffron:#ff9933; --saffron-dim:#7c4a12;
  --ink:#e8f5ec; --muted:#9fb8a8;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  background-image:radial-gradient(1200px 500px at 50% -80px,rgba(34,197,94,.10),transparent 60%),
                   radial-gradient(900px 420px at 85% 30%,rgba(255,153,51,.05),transparent 60%);
}
.wrap{max-width:1120px;margin:0 auto;padding:0 20px}
header.hero{padding:64px 0 28px;text-align:center}
.kicker{display:inline-block;font-size:12px;letter-spacing:.35em;color:var(--saffron);
  border:1px solid var(--saffron-dim);border-radius:999px;padding:8px 18px;margin-bottom:22px;
  text-transform:uppercase;background:rgba(255,153,51,.06)}
h1{font-size:clamp(44px,8vw,92px);margin:0 0 6px;font-weight:800;letter-spacing:-.02em;line-height:1}
h1 .arr{color:var(--saffron)}
h1 .d3{color:var(--green)}
.sub{color:var(--muted);font-size:clamp(15px,2.4vw,19px);max-width:720px;margin:14px auto 0;line-height:1.6}
.stats{display:flex;gap:14px;justify-content:center;flex-wrap:wrap;margin:30px 0 8px}
.stat{background:var(--panel);border:1px solid #16301f;border-radius:14px;padding:16px 26px;min-width:150px}
.stat b{display:block;font-size:30px;color:var(--green);font-variant-numeric:tabular-nums}
.stat span{font-size:12px;color:var(--muted);letter-spacing:.08em;text-transform:uppercase}
.pipe{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:34px 0}
@media(max-width:760px){.pipe{grid-template-columns:1fr}}
.step{background:linear-gradient(180deg,var(--panel2),var(--panel));border:1px solid #16301f;
  border-radius:16px;padding:22px;position:relative}
.step .n{font-size:12px;color:var(--saffron);letter-spacing:.25em;font-weight:700}
.step h3{margin:10px 0 8px;font-size:18px}
.step p{margin:0;color:var(--muted);font-size:14px;line-height:1.65}
.step .tag{display:inline-block;margin-top:12px;font-size:11px;padding:5px 12px;border-radius:999px;
  letter-spacing:.12em;text-transform:uppercase;font-weight:700}
.tag.computed{background:rgba(34,197,94,.14);color:var(--green);border:1px solid var(--green-dim)}
.tag.borrowed{background:rgba(255,153,51,.12);color:var(--saffron);border:1px solid var(--saffron-dim)}
section.block{margin:44px 0}
h2{font-size:clamp(24px,4vw,34px);margin:0 0 6px;letter-spacing:-.01em}
h2 .o{color:var(--saffron)}
.lede{color:var(--muted);font-size:15px;margin:0 0 18px;line-height:1.65;max-width:760px}
.strip{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
@media(max-width:760px){.strip{grid-template-columns:repeat(2,1fr)}}
.shot{margin:0;position:relative;border-radius:12px;overflow:hidden;border:1px solid #16301f;background:#000}
.shot img{display:block;width:100%;height:150px;object-fit:cover;filter:saturate(1.05)}
.shot figcaption{position:absolute;left:8px;bottom:6px;font-size:11px;color:#fff;
  background:rgba(0,0,0,.55);padding:2px 8px;border-radius:6px;letter-spacing:.1em}
.viewer{background:#020604;border:1px solid #16301f;border-radius:18px;overflow:hidden;position:relative}
.viewer canvas{display:block;width:100%;height:520px}
@media(max-width:760px){.viewer canvas{height:380px}}
.vlabel{position:absolute;top:14px;left:16px;z-index:2;font-size:11px;letter-spacing:.22em;
  text-transform:uppercase;color:var(--muted);background:rgba(0,0,0,.5);padding:7px 14px;border-radius:999px;
  border:1px solid #1c3826}
.vhint{position:absolute;bottom:14px;right:16px;z-index:2;font-size:11px;color:var(--muted);
  background:rgba(0,0,0,.5);padding:6px 12px;border-radius:999px;border:1px solid #1c3826}
.honest{background:rgba(255,153,51,.06);border:1px solid var(--saffron-dim);border-radius:16px;
  padding:22px 24px;margin:40px 0}
.honest h3{margin:0 0 10px;color:var(--saffron);font-size:16px;letter-spacing:.06em}
.honest p{margin:8px 0;color:var(--muted);font-size:14.5px;line-height:1.7}
.honest b{color:var(--ink)}
footer{border-top:1px solid #12271633;margin-top:56px;padding:26px 0 60px;color:var(--muted);font-size:13px;
  text-align:center;line-height:1.8}
footer a{color:var(--saffron)}
.badge{display:inline-block;margin-top:10px;font-size:11px;letter-spacing:.2em;text-transform:uppercase;
  border:1px solid #1c3826;border-radius:999px;padding:8px 16px;color:var(--green)}
#err{position:fixed;left:12px;bottom:12px;z-index:99;max-width:80vw;background:#3b0a0a;color:#ffd7d7;
  font:12px/1.5 monospace;padding:10px 14px;border-radius:10px;display:none;white-space:pre-wrap}
</style>
</head>
<body>
<div id="err"></div>
<header class="hero wrap">
  <div class="kicker">Photogrammetry &middot; live demo</div>
  <h1>DRONE <span class="arr">&rarr;</span> <span class="d3">3D</span></h1>
  <p class="sub">Sixty-one drone photos of one building went in. A real structure-from-motion
  pipeline ran &mdash; on this machine, right now &mdash; and out came camera positions
  and a 3D point cloud you can orbit below.</p>
  <div class="stats">
    <div class="stat"><b>""" + str(n_src) + """</b><span>drone photos</span></div>
    <div class="stat"><b>""" + str(n_img) + """</b><span>images registered</span></div>
    <div class="stat"><b>""" + f"{n_pts:,}" + """</b><span>3D points</span></div>
  </div>
</header>

<div class="wrap">
  <div class="pipe">
    <div class="step">
      <div class="n">STEP 01</div><h3>Drone photos</h3>
      <p>Overlapping aerial photos from a DJI drone circling a two-storey shingle-roof building.
      Heavy overlap (60&ndash;80%) is what lets the math work.</p>
      <span class="tag borrowed">source: open dataset</span>
    </div>
    <div class="step">
      <div class="n">STEP 02</div><h3>Sparse reconstruction</h3>
      <p>SIFT features matched frame-to-frame, cameras solved by incremental bundle adjustment
      (COLMAP / pycolmap). This is the actual output you can spin below.</p>
      <span class="tag computed">computed on this VM</span>
    </div>
    <div class="step">
      <div class="n">STEP 03</div><h3>Dense mesh + texture</h3>
      <p>Multi-view stereo densifies the cloud into a textured mesh &mdash; but it needs a GPU
      and hours of compute, so the textured model below is the dataset author's own reconstruction.</p>
      <span class="tag borrowed">borrowed reference</span>
    </div>
  </div>

  <section class="block">
    <h2>The raw material <span class="o">&mdash;</span> 8 of the 61 photos</h2>
    <p class="lede">Shot from a drone on an orbital flight path around the building. Each frame overlaps
    its neighbours &mdash; that's the fuel for the reconstruction.</p>
    <div class="strip">""" + photo_imgs + """</div>
  </section>

  <section class="block">
    <h2>What <span class="o">we</span> computed &mdash; the sparse point cloud</h2>
    <p class="lede">Every dot is a real 3D point triangulated from matched features across the photos.
    Drag to orbit, scroll to zoom. It ran here on 2 CPUs with no GPU.</p>
    <div class="viewer">
      <div class="vlabel">sparse cloud &middot; computed on this VM</div>
      <div class="vhint">drag &middot; scroll &middot; right-drag</div>
      <canvas id="cloud"></canvas>
    </div>
  </section>

  <section class="block">
    <h2>The finished look <span class="o">&mdash;</span> textured reference model</h2>
    <p class="lede">The dataset author's dense reconstruction of the same building &mdash; textured mesh
    from multi-view stereo. Ours stopped at the sparse stage: dense MVS needs a beefy GPU machine.</p>
    <div class="viewer">
      <div class="vlabel">dense textured mesh &middot; dataset author's</div>
      <div class="vhint">drag &middot; scroll &middot; right-drag</div>
      <canvas id="model"></canvas>
    </div>
  </section>

  <div class="honest">
    <h3>HONEST LABELS &mdash; WHAT RAN WHERE</h3>
    <p><b>On this VM (just now):</b> SIFT feature extraction, sequential matching and incremental
    bundle adjustment over """ + str(n_src) + """ downsampled photos &rarr; <b>""" + str(n_img) + """ registered</b>,
    <b>""" + f"{n_pts:,}" + """ 3D points</b>. No GPU. That point cloud above is 100% ours.</p>
    <p><b>Borrowed from the dataset:</b> the original 61 full-resolution photos and the textured
    .glb mesh (the author's own dense multi-view-stereo reconstruction). Our VM can't run dense MVS.</p>
  </div>
</div>

<footer>
  <div class="wrap">
    Drone imagery by <b>Matt1up</b> &middot; licensed <b>CC BY 4.0</b><br>
    Dataset: <a href="https://huggingface.co/datasets/Matt1up/drone-building-scans" target="_blank" rel="noopener">Matt1up/drone-building-scans</a>
    &mdash; two-storey shingle-roof building<br>
    <span class="badge">built with pycolmap &middot; three.js</span>
  </div>
</footer>

<script>""" + three_js + """</script>
<script>""" + orbit_js + """</script>
<script>""" + gltf_js + """</script>
<script id="cloudata" type="text/plain">""" + cloud_b64 + """</script>
<script id="glbdata" type="text/plain">""" + model_b64 + """</script>
<script>
(function(){
"use strict";
var errBox=document.getElementById('err');
function fail(m){errBox.style.display='block';errBox.textContent+='ERR: '+m+'\\n';}
window.addEventListener('error',function(e){fail((e.message||'script error')+' @'+(e.filename||'')+':'+(e.lineno||''));});

function b64ToBytes(b64){
  var bin=atob(b64),n=bin.length,out=new Uint8Array(n);
  for(var i=0;i<n;i++)out[i]=bin.charCodeAt(i);
  return out;
}
function makeRenderer(canvas){
  var r=new THREE.WebGLRenderer({canvas:canvas,antialias:true});
  r.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
  function fit(){var w=canvas.clientWidth,h=canvas.clientHeight;
    if(canvas.width!==w*r.getPixelRatio()||canvas.height!==h*r.getPixelRatio()){
      r.setSize(w,h,false);}}
  return {renderer:r,fit:fit};
}
function addControls(camera,dom){
  var c=new THREE.OrbitControls(camera,dom);
  c.enableDamping=true;c.dampingFactor=0.08;c.autoRotate=true;c.autoRotateSpeed=0.9;
  dom.addEventListener('pointerdown',function(){c.autoRotate=false;},{once:true});
  return c;
}

/* ---------- point cloud viewer ---------- */
try{
  var META=""" + json.dumps(cloud_meta) + """;
  var raw=b64ToBytes(document.getElementById('cloudata').textContent.replace(/\\s+/g,''));
  var N=META.n, STRIDE=15;
  if(raw.length<N*STRIDE) fail('cloud buffer short: '+raw.length);
  var pos=new Float32Array(N*3), col=new Float32Array(N*3);
  var dv=new DataView(raw.buffer);
  var minx=1e9,miny=1e9,minz=1e9,maxx=-1e9,maxy=-1e9,maxz=-1e9;
  for(var i=0;i<N;i++){
    var x=dv.getFloat32(i*STRIDE,true),y=dv.getFloat32(i*STRIDE+4,true),z=dv.getFloat32(i*STRIDE+8,true);
    pos[i*3]=x;pos[i*3+1]=y;pos[i*3+2]=z;
    col[i*3]=raw[i*STRIDE+12]/255;col[i*3+1]=raw[i*STRIDE+13]/255;col[i*3+2]=raw[i*STRIDE+14]/255;
    if(x<minx)minx=x;if(y<miny)miny=y;if(z<minz)minz=z;
    if(x>maxx)maxx=x;if(y>maxy)maxy=y;if(z>maxz)maxz=z;
  }
  var cx=(minx+maxx)/2,cy=(miny+maxy)/2,cz=(minz+maxz)/2;
  var span=Math.max(maxx-minx,maxy-miny,maxz-minz)||1;
  var canvas=document.getElementById('cloud');
  var R=makeRenderer(canvas);
  var scene=new THREE.Scene();scene.background=new THREE.Color(0x020604);
  var geo=new THREE.BufferGeometry();
  geo.setAttribute('position',new THREE.BufferAttribute(pos,3));
  geo.setAttribute('color',new THREE.BufferAttribute(col,3));
  var pts=new THREE.Points(geo,new THREE.PointsMaterial({size:0.012*span,vertexColors:true,sizeAttenuation:true}));
  pts.position.set(-cx,-cy,-cz);
  scene.add(pts);
  var camera=new THREE.PerspectiveCamera(55,canvas.clientWidth/Math.max(1,canvas.clientHeight),0.01,100*span);
  camera.position.set(span*0.9,span*0.55,span*0.9);
  var ctl=addControls(camera,canvas);ctl.target.set(0,0,0);
  // ground grid for depth cue
  var grid=new THREE.GridHelper(span*1.6,16,0x14532d,0x0e2417);
  grid.position.y=minz-cz-span*0.02;scene.add(grid);
  (function loop(){requestAnimationFrame(loop);
    if(!window.__freeze){R.fit();ctl.update();R.renderer.render(scene,camera);}})();
  window.__snap=function(){
    var out={};
    R.fit();R.renderer.render(scene,camera);
    var c=R.renderer.domElement,gl=R.renderer.getContext();
    var px=new Uint8Array(64*64*4);
    gl.readPixels(c.width/2-32|0,c.height/2-32|0,64,64,gl.RGBA,gl.UNSIGNED_BYTE,px);
    var s=0;for(var i=0;i<px.length;i+=4)s+=px[i]+px[i+1]+px[i+2];out.cloud=s;
    out.cloudCalls=R.renderer.info.render.calls;out.cloudPts=R.renderer.info.render.points;
    R2.fit();R2.renderer.render(scene2,camera2);
    var c2=R2.renderer.domElement,gl2=R2.renderer.getContext();
    var px2=new Uint8Array(64*64*4);
    gl2.readPixels(c2.width/2-32|0,c2.height/2-32|0,64,64,gl2.RGBA,gl2.UNSIGNED_BYTE,px2);
    var s2=0;for(var i=0;i<px2.length;i+=4)s2+=px2[i]+px2[i+1]+px2[i+2];out.model=s2;
    out.modelCalls=R2.renderer.info.render.calls;out.modelTris=R2.renderer.info.render.triangles;
    return out;};
  window.__unfreeze=function(){window.__freeze=false;};
  window.__cloudOK=N;
}catch(e){fail('cloud viewer: '+(e&&e.stack||e));}

/* ---------- textured glb viewer ---------- */
try{
  var gbytes=b64ToBytes(document.getElementById('glbdata').textContent.replace(/\\s+/g,''));
  var canvas2=document.getElementById('model');
  var R2=makeRenderer(canvas2);
  var scene2=new THREE.Scene();scene2.background=new THREE.Color(0x020604);
  scene2.add(new THREE.HemisphereLight(0xd8ffe2,0x0a140d,0.95));
  var d1=new THREE.DirectionalLight(0xffffff,0.85);d1.position.set(4,6,3);scene2.add(d1);
  var d2=new THREE.DirectionalLight(0xff9933,0.25);d2.position.set(-5,2,-4);scene2.add(d2);
  var camera2=new THREE.PerspectiveCamera(50,1,0.01,1000);
  var ctl2=addControls(camera2,canvas2);
  new THREE.GLTFLoader().parse(gbytes.buffer,'',function(gltf){
    var obj=gltf.scene;
    var box=new THREE.Box3().setFromObject(obj);
    var size=box.getSize(new THREE.Vector3()),ctr=box.getCenter(new THREE.Vector3());
    var s=6/Math.max(size.x,size.y,size.z);
    obj.scale.setScalar(s);
    obj.position.set(-ctr.x*s,-ctr.y*s,-ctr.z*s);
    scene2.add(obj);
    camera2.position.set(4.6,3.2,4.6);
    ctl2.target.set(0,0,0);
    window.__modelOK=true;
    (function loop2(){requestAnimationFrame(loop2);
    if(!window.__freeze){R2.fit();ctl2.update();R2.renderer.render(scene2,camera2);}})();
  },function(e){fail('glb parse: '+e);});
}catch(e){fail('model viewer: '+(e&&e.stack||e));}
})();
</script>
</body>
</html>
"""

with open('page.html', 'w') as f:
    f.write(html)
print('page.html written:', len(html)/1e6, 'MB')
