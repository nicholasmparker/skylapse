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

  function colorFor(s:number){ if (s>300) return '#16a34a'; if (s>=100) return '#ca8a04'; return '#dc2626'; }
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

  function drawSpark(){ const c = document.getElementById('spark') as HTMLCanvasElement; if(!c) return; const ctx = c.getContext('2d'); if(!ctx) return; ctx.clearRect(0,0,c.width,c.height); if(hist.length<2) return; const scores = hist.map(h=>h.score); const min=Math.min(...scores), max=Math.max(...scores); const norm = scores.map(s=> (s-min)/(max-min+1e-6)); ctx.strokeStyle='#9ca3af'; ctx.beginPath(); norm.forEach((v,i)=>{ const x=i/(norm.length-1)*c.width; const y=(1-v)*c.height; i?ctx.lineTo(x,y):ctx.moveTo(x,y); }); ctx.stroke(); const em = ema(scores); const emn = em.map(s=> (s-min)/(max-min+1e-6)); ctx.strokeStyle='#6366f1'; ctx.beginPath(); emn.forEach((v,i)=>{ const x=i/(emn.length-1)*c.width; const y=(1-v)*c.height; i?ctx.lineTo(x,y):ctx.moveTo(x,y); }); ctx.stroke(); }

  onMount(async()=>{ await checkAuth(); const r=await fetch('/api/latest'); if(r.ok){ const d=await r.json(); if(d && d.image_url){ imgUrl=d.image_url; imgTs=d.captured_at; } } const iv = setInterval(()=>drawSpark(), 250); return ()=> clearInterval(iv); });
</script>

<section class="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-4">
  <div class="rounded-lg border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-3">
    <div class="aspect-[4/3] w-full overflow-hidden rounded-md border border-neutral-200 dark:border-neutral-800 bg-neutral-100 dark:bg-neutral-800">
      {#if imgUrl}
        <img alt="Latest" src={imgUrl} class="h-full w-full object-contain" />
      {:else}
        <div class="h-full w-full grid place-items-center text-neutral-400">No image yet</div>
      {/if}
    </div>
    <div class="mt-2 text-xs text-neutral-500">{imgTs}</div>
  </div>

  <aside class="rounded-lg border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-4">
    <div class="flex items-center gap-3">
      <div class="text-4xl font-extrabold tabular-nums">{score.toFixed(1)}</div>
      <span class="inline-flex items-center rounded-md px-2 py-1 text-xs font-medium text-white" style={`background:${bandColor}`}>{band}</span>
    </div>
    <div class="mt-1 text-sm text-neutral-600 dark:text-neutral-300">
      Turn direction: <strong>{trend}</strong>
      <span class="mx-1">•</span>
      Delta: <strong>{delta}</strong>
    </div>
    <div class="mt-3">
      <canvas id="spark" width="340" height="72" class="w-full h-20"></canvas>
    </div>
    <div class="mt-3 flex flex-wrap gap-2">
      <button class="rounded-md bg-brand-600 text-white px-3 py-1.5 text-sm hover:bg-brand-700" on:click={startAuto}>Start Auto (S)</button>
      <button class="rounded-md border border-neutral-300 dark:border-neutral-700 px-3 py-1.5 text-sm" on:click={stopAuto}>Stop Auto</button>
      <button class="rounded-md bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900 px-3 py-1.5 text-sm" on:click={captureAndScore}>Capture + Compute (C)</button>
      <button class="rounded-md border border-neutral-300 dark:border-neutral-700 px-3 py-1.5 text-sm" on:click={recompute}>Recompute (R)</button>
    </div>
    <div class="mt-3 flex items-center gap-4 text-sm">
      <label class="inline-flex items-center gap-2"><input class="accent-brand-600" type="checkbox" bind:checked={lockAe}/> Lock AE</label>
      <label class="inline-flex items-center gap-2"><input class="accent-brand-600" type="checkbox" bind:checked={lockAwb}/> Lock AWB</label>
    </div>
    {#if err}
      <div class="mt-3 text-xs text-rose-600">{err}</div>
    {/if}
    <div class="mt-4 text-[11px] text-neutral-500">Shortcuts: S=Start Auto, C=Capture+Compute, R=Recompute</div>
  </aside>
</section>

<svelte:window on:keydown={(e)=>{ if(e.key==='s'||e.key==='S') startAuto(); if(e.key==='c'||e.key==='C') captureAndScore(); if(e.key==='r'||e.key==='R') recompute(); }} />
