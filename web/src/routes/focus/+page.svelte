<script lang="ts">
  import { onMount } from 'svelte';
  type Sample = { ts: number; score: number };
  let logged = false;
  let auto = false;
  let tmr: any = null;
  let score = 0;
  let band = 'INIT';
  let bandColor = '#6b7280';
  let trend = '—';
  let delta = '—';
  let imgUrl = '';
  let imgTs: string | null = null;
  let lockAe = false;
  let lockAwb = false;
  let err = '';
  const hist: Sample[] = [];

  function colorFor(s:number){ if (s>300) return '#2b8a3e'; if (s>=100) return '#ca8a04'; return '#d33'; }
  function bandFor(s:number){ if (s>300) return 'GOOD'; if (s>=100) return 'FAIR'; return 'POOR'; }

  async function checkAuth(){ try{ const r=await fetch('/api/admin/health'); logged=r.ok; }catch{ logged=false; } }

  function ema(values:number[], k=5){ const a=2/(k+1); let e: number | null=null; const out:number[]=[]; for(const v of values){ e = e==null? v : a*v+(1-a)*e; out.push(e); } return out; }
  function pushSample(s: number){ const ts = Math.floor(Date.now()/1000); hist.push({ ts, score: s }); if (hist.length>30) hist.shift(); const scores = hist.map(h=>h.score); if (scores.length>=5){ const e = ema(scores.slice(-5)); const slope = e[e.length-1] - e[0]; const rel = slope / (Math.abs(e[0]) + 1e-6); trend = slope>0? 'Better (keep turning)' : (slope<0? 'Worse (reverse slightly)': 'Stable'); delta = `${(rel*100).toFixed(1)}%`; } }

  async function captureAndScore(){ err=''; if(!logged){ err='Please login'; return; }
    try {
      const r = await fetch('/api/admin/capture_and_score', { method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify({ lock_ae: lockAe, lock_awb: lockAwb })});
      if(!r.ok){ const t=await r.text(); throw new Error(`${r.status} ${t}`); }
      const d = await r.json();
      score = Number(d.score||0);
      band = bandFor(score); bandColor = colorFor(score);
      pushSample(score);
      if (d.url){ imgUrl = d.url + `?t=${Date.now()}`; }
      imgTs = d.ts ? new Date(d.ts*1000).toISOString() : null;
    } catch(e:any){ err = 'Capture failed: ' + String(e?.message||e); }
  }

  async function recompute(){ err=''; if(!logged){ err='Please login'; return; }
    try{ const r=await fetch('/api/admin/focus_score'); if(!r.ok) throw new Error(''+r.status); const d=await r.json(); score=Number(d.score||0); band=bandFor(score); bandColor=colorFor(score); pushSample(score);}catch(e:any){ err='Recompute failed: '+String(e?.message||e); }
  }

  function startAuto(){ if (!logged){ err='Please login'; return; } if (auto) return; auto=true; tmr=setInterval(captureAndScore, 500); }
  function stopAuto(){ auto=false; if (tmr) clearInterval(tmr); }

  function drawSpark(){ const c = document.getElementById('spark') as HTMLCanvasElement; if(!c) return; const ctx = c.getContext('2d'); if(!ctx) return; ctx.clearRect(0,0,c.width,c.height); if(hist.length<2) return; const scores = hist.map(h=>h.score); const min=Math.min(...scores), max=Math.max(...scores); const norm = scores.map(s=> (s-min)/(max-min+1e-6)); ctx.strokeStyle='#888'; ctx.beginPath(); norm.forEach((v,i)=>{ const x=i/(norm.length-1)*c.width; const y=(1-v)*c.height; i?ctx.lineTo(x,y):ctx.moveTo(x,y); }); ctx.stroke(); const em = ema(scores); const emn = em.map(s=> (s-min)/(max-min+1e-6)); ctx.strokeStyle='#2563eb'; ctx.beginPath(); emn.forEach((v,i)=>{ const x=i/(emn.length-1)*c.width; const y=(1-v)*c.height; i?ctx.lineTo(x,y):ctx.moveTo(x,y); }); ctx.stroke(); }

  function refresh(){ drawSpark(); }

  onMount(async()=>{ await checkAuth(); const r=await fetch('/api/latest'); if(r.ok){ const d=await r.json(); if(d && d.image_url){ imgUrl=d.image_url; imgTs=d.captured_at; } } const iv = setInterval(refresh, 250); return ()=> clearInterval(iv); });
</script>

<style>
  main { display:grid; grid-template-columns: 1fr 380px; gap:16px; padding:16px; }
  .panel { border:1px solid rgba(0,0,0,.15); border-radius:8px; padding:12px; background: Canvas; color: CanvasText; }
  img { max-width:100%; border-radius:8px; border:1px solid #ddd; }
  .row { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
  button { padding:8px 10px; border-radius:6px; cursor:pointer; border:1px solid #4b5563; background:#111827; color:#fff; }
  @media (prefers-color-scheme: light) { button { background:#2563eb; border-color:#1d4ed8; } }
  .badge { display:inline-block; padding:2px 6px; border-radius:6px; font-size:12px; color:#fff; margin-left:6px; }
</style>

<main>
  <section class="panel">
    <img alt="Latest" src={imgUrl} />
    <div style="font-size:12px; color:#666; margin-top:6px">{imgTs}</div>
  </section>
  <aside class="panel">
    <div style="font-size:40px; font-weight:800">{score.toFixed(1)} <span class="badge" style={`background:${bandColor}`}>{band}</span></div>
    <div style="margin-top:4px">Turn direction: <strong>{trend}</strong> • Delta: <strong>{delta}</strong></div>
    <div style="margin-top:8px">
      <canvas id="spark" width="340" height="72"></canvas>
    </div>
    <div class="row" style="margin-top:8px">
      <button on:click={startAuto}>Start Auto (S)</button>
      <button on:click={stopAuto}>Stop Auto</button>
      <button on:click={captureAndScore}>Capture + Compute (C)</button>
      <button on:click={recompute}>Recompute (R)</button>
    </div>
    <div class="row" style="margin-top:8px">
      <label class="row" style="gap:6px; align-items:center"><input type="checkbox" bind:checked={lockAe}/> Lock AE</label>
      <label class="row" style="gap:6px; align-items:center"><input type="checkbox" bind:checked={lockAwb}/> Lock AWB</label>
    </div>
    {#if err}<div style="color:#b00; font-size:12px; margin-top:8px">{err}</div>{/if}
  </aside>
</main>

<svelte:window on:keydown={(e)=>{ if(e.key==='s'||e.key==='S') startAuto(); if(e.key==='c'||e.key==='C') captureAndScore(); if(e.key==='r'||e.key==='R') recompute(); }} />
