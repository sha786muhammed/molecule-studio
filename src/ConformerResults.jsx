import React,{useState} from 'react';
import {ArrowRight,DownloadSimple,BookOpen} from '@phosphor-icons/react';
import {number,download,csv} from './api';
import {MoleculeView} from './MoleculeView';

export function ConformerResults({job,onUseConformer}){
 const r=job.result,s=r.search;
 const [rank,setRank]=useState(1),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const selected=r.conformers.find(c=>c.rank===rank)||r.conformers[0];
 async function refine(){setBusy(true);setError('');try{await onUseConformer(selected);}catch(e){setError(e.message);}finally{setBusy(false);}}
 return <>
  <div className="ensemble-heading"><div><span className="eyebrow">CONFORMER ENSEMBLE</span><h2>{s.unique} distinct optimized {s.unique===1?'structure':'structures'}</h2><p>{s.generated} generated · {s.duplicates_removed} duplicates removed · {s.unconverged_sample_ids.length} unconverged</p></div><button className="button secondary" onClick={()=>download(job.molecule.name+'-conformers.csv',csv([['Rank','Sample','Energy_kcal_mol','Relative_energy_kcal_mol','Method'],...r.conformers.map(c=>[c.rank,c.sample_id,c.energy,c.relative_energy,r.method])]),'text/csv')}><DownloadSimple/>Export ranking</button></div>
  {error&&<div className="alert error" role="alert">{error}</div>}
  <div className="ensemble-layout"><section className="conformer-view"><div className="conformer-title"><strong>Conformer {selected.rank}</strong><span>ΔE {number(selected.relative_energy,3)} kcal/mol</span></div><MoleculeView molecule={selected} height={350}/><div className="result-actions"><a className="text-link" href={`/api/jobs/${job.id}/export/xyz?conformer=${selected.rank}`} download><DownloadSimple/>Selected XYZ</a><button className="text-link" disabled={busy} onClick={refine}>{busy?'Saving structure…':'Refine with xTB'}<ArrowRight/></button></div></section>
   <section className="conformer-ranking"><h3>Energy ranking</h3><p>Select a row to inspect its geometry.</p><div className="table-wrap ensemble-table"><table><thead><tr><th>Conformer</th><th>Energy<br/>kcal/mol</th><th>ΔE<br/>kcal/mol</th></tr></thead><tbody>{r.conformers.map(c=><tr key={c.rank} className={selected.rank===c.rank?'selected-conformer':''} onClick={()=>setRank(c.rank)}><td><button aria-label={`View conformer ${c.rank}`} aria-pressed={selected.rank===c.rank} onClick={()=>setRank(c.rank)}><span className="conformer-number">{c.rank}</span>{c.rank===1?'Lowest found':'Conformer '+c.rank}</button></td><td>{number(c.energy,4)}</td><td className="relative-energy">{number(c.relative_energy,3)}</td></tr>)}</tbody></table></div><dl className="search-details"><dt>Sampling</dt><dd>{s.generator} · seed {s.seed}</dd><dt>Optimization</dt><dd>{r.method} · gas phase</dd><dt>Duplicate threshold</dt><dd>{s.rmsd_threshold_angstrom} Å · heavy atoms</dd><dt>Runtime</dt><dd>{r.duration} s</dd></dl></section></div>
  <div className="method-notes"><h3><BookOpen/>How to interpret this ensemble</h3>{r.notes.map(n=><p key={n}>{n}</p>)}<small>{r.engine} · Energies in kcal/mol · Coordinates in Å</small></div>
 </>;
}
