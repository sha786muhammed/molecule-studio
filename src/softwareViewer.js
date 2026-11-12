// Data-driven Canvas2D fallback for environments without WebGL.
// All atoms, bonds and positions are read from the calculated MDL structure.
const COLORS={H:'#f4f4f4',C:'#62666a',N:'#365bdb',O:'#d93434',F:'#6bc859',Cl:'#43a35b',S:'#e2bd32',P:'#e39535',Br:'#a94d34',I:'#8760ad'};
export function parseMolblock(text){
 const lines=text.split('\n'),count=lines[3]||'',n=parseInt(count.slice(0,3)),nb=parseInt(count.slice(3,6));
 if(!n||!Number.isFinite(n))throw new Error('Expected a V2000 molblock.');
 const atoms=lines.slice(4,4+n).map((l,index)=>({index,x:parseFloat(l.slice(0,10)),y:parseFloat(l.slice(10,20)),z:parseFloat(l.slice(20,30)),elem:l.slice(31,34).trim(),properties:{}}));
 const bonds=lines.slice(4+n,4+n+nb).map(l=>({a:parseInt(l.slice(0,3))-1,b:parseInt(l.slice(3,6))-1,order:parseInt(l.slice(6,9))}));
 return {atoms,bonds};
}
export function createSoftwareViewer(host){
 const canvas=document.createElement('canvas');canvas.style.cssText='width:100%;height:100%;display:block;touch-action:none;cursor:grab;';canvas.setAttribute('aria-label','Interactive molecular structure. Drag to rotate; scroll to zoom.');host.append(canvas);
 const ctx=canvas.getContext('2d');let atoms=[],bonds=[],rx=-.25,ry=.35,zoom=1,width=1,height=1,spinTimer=null,chargeMode=false,drag=null;
 const render=()=>{
  const dpr=Math.min(window.devicePixelRatio||1,2);width=host.clientWidth||500;height=host.clientHeight||350;
  if(canvas.width!==width*dpr||canvas.height!==height*dpr){canvas.width=width*dpr;canvas.height=height*dpr;}
  ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,width,height);if(!atoms.length)return;
  const center=['x','y','z'].map(k=>atoms.reduce((v,a)=>v+a[k],0)/atoms.length);
  const points=atoms.map(a=>{const x=a.x-center[0],y=a.y-center[1],z=a.z-center[2],x1=x*Math.cos(ry)+z*Math.sin(ry),z1=-x*Math.sin(ry)+z*Math.cos(ry);return {...a,px:x1,py:y*Math.cos(rx)-z1*Math.sin(rx),pz:y*Math.sin(rx)+z1*Math.cos(rx)};});
  const extent=Math.max(...points.map(a=>Math.abs(a.px)),...points.map(a=>Math.abs(a.py)),1.2);const scale=Math.min(width,height)/(2*extent+2)*zoom;
  points.forEach(p=>{p.sx=width/2+p.px*scale;p.sy=height/2-p.py*scale;p.radius=(p.elem==='H'?.24:.36)*scale;p.color=chargeMode?(p.properties.charge<0?'#d35454':'#4a6ec3'):(COLORS[p.elem]||'#bd9d89');});
  const entities=[...bonds.map(b=>({bond:b,z:(points[b.a].pz+points[b.b].pz)/2})),...points.map(p=>({atom:p,z:p.pz}))].sort((a,b)=>a.z-b.z);
  for(const item of entities){
   if(item.bond){const b=item.bond,a=points[b.a],c=points[b.b],dx=c.sx-a.sx,dy=c.sy-a.sy,len=Math.hypot(dx,dy)||1,nx=-dy/len,ny=dx/len;for(let i=0;i<Math.min(b.order,3);i++){const off=(i-(Math.min(b.order,3)-1)/2)*scale*.15;const grad=ctx.createLinearGradient(a.sx,a.sy,c.sx,c.sy);grad.addColorStop(0,a.color);grad.addColorStop(.49,a.color);grad.addColorStop(.51,c.color);grad.addColorStop(1,c.color);ctx.beginPath();ctx.moveTo(a.sx+nx*off,a.sy+ny*off);ctx.lineTo(c.sx+nx*off,c.sy+ny*off);ctx.lineWidth=scale*.14;ctx.lineCap='round';ctx.strokeStyle='#555b60';ctx.stroke();ctx.lineWidth=scale*.105;ctx.strokeStyle=grad;ctx.stroke();}}
   else{const p=item.atom,r=p.radius;const g=ctx.createRadialGradient(p.sx-r*.33,p.sy-r*.36,r*.03,p.sx,p.sy,r);g.addColorStop(0,'#ffffff');g.addColorStop(.3,p.color);g.addColorStop(.78,p.color);g.addColorStop(1,p.elem==='H'?'#b6b9b8':'#2c3335');ctx.beginPath();ctx.arc(p.sx,p.sy,r,0,Math.PI*2);ctx.fillStyle=g;ctx.fill();}
  }
 };
 const down=e=>{drag=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId);canvas.style.cursor='grabbing';};
 const move=e=>{if(!drag)return;ry+=(e.clientX-drag[0])*.012;rx+=(e.clientY-drag[1])*.012;drag=[e.clientX,e.clientY];render();};
 const up=()=>{drag=null;canvas.style.cursor='grab';};const wheel=e=>{e.preventDefault();zoom=Math.max(.3,Math.min(4,zoom*Math.exp(-e.deltaY*.001)));render();};
 canvas.addEventListener('pointerdown',down);canvas.addEventListener('pointermove',move);canvas.addEventListener('pointerup',up);canvas.addEventListener('wheel',wheel,{passive:false});
 return {clear(){atoms=[];bonds=[];chargeMode=false;render();},addModel(text){({atoms,bonds}=parseMolblock(text));},setStyle(sel,style){chargeMode=Boolean(style?.sphere?.colorfunc);},getModel(){return{selectedAtoms:()=>atoms};},zoomTo(){zoom=1.3;rx=-.25;ry=.35;},zoom(f){zoom=Math.max(.3,Math.min(4,zoom*f));},render,resize:render,spin(value){clearInterval(spinTimer);if(value)spinTimer=setInterval(()=>{ry+=.012;render();},35);}};
}
