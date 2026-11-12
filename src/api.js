export async function api(path,body){
 const r=await fetch('/api'+path,body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 const data=await r.json(); if(!r.ok)throw new Error(typeof data.detail==='string'?data.detail:'Check the required fields and try again.'); return data;
}
export function download(name,content,type='text/plain'){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([content],{type}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}
export const number=(x,n=3)=>x==null?'—':Number(x).toLocaleString('en-US',{maximumFractionDigits:n,minimumFractionDigits:n});
export const date=x=>new Date(x).toLocaleString(undefined,{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'});
export const csv=rows=>rows.map(r=>r.map(v=>'"'+String(v??'').replaceAll('"','""')+'"').join(',')).join('\n');
export function go(path){location.hash='/'+path;}
