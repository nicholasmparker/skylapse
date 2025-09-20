<script lang="ts">
  import { onMount } from 'svelte';
  type Latest = { image_url: string | null; captured_at: string | null };
  type Item = { url: string; captured_at: number };
  let latest: Latest = { image_url: null, captured_at: null };
  let items: Item[] = [];
  let err = '';

  async function loadLatest() {
    try {
      const r = await fetch('/api/latest');
      if (!r.ok) throw new Error('' + r.status);
      latest = await r.json();
    } catch (e) {
      err = 'Failed to load latest';
    }
  }
  async function loadRecent() {
    try {
      const r = await fetch('/api/images?page=1&page_size=10');
      if (!r.ok) throw new Error('' + r.status);
      const data = await r.json();
      items = (data.items || []) as Item[];
    } catch (e) {
      err = 'Failed to load recent';
    }
  }
  function refresh() { loadLatest(); loadRecent(); }
  onMount(refresh);
</script>

<style>
  main { display: grid; grid-template-columns: 1fr 360px; gap: 16px; padding: 16px; }
  .panel { border: 1px solid rgba(0,0,0,.15); border-radius: 8px; padding: 12px; background: Canvas; color: CanvasText; }
  img { max-width: 100%; border-radius: 8px; border: 1px solid #ddd; }
  button { padding: 8px 10px; border-radius: 6px; cursor: pointer; border: 1px solid #4b5563; background: #111827; color: #fff; }
  @media (prefers-color-scheme: light) { button { background: #2563eb; border-color: #1d4ed8; } }
</style>

<main>
  <section class="panel">
    <h2>Latest</h2>
    {#if latest.image_url}
      <div style="font-size:12px; color:#666">Captured: {latest.captured_at ?? ''}</div>
      <img src={latest.image_url} alt="Latest" />
    {:else}
      <div>No image available</div>
    {/if}
  </section>
  <aside class="panel">
    <h3>Recent</h3>
    {#if err}<div style="color:#b00; font-size:12px">{err}</div>{/if}
    <ul style="list-style:none; padding:0; margin:0">
      {#each items as it}
        <li style="padding:6px 0; border-bottom:1px solid #eee">
          <a href={it.url} target="_blank">{it.url}</a><br/>
          <small>{new Date(it.captured_at*1000).toISOString()}</small>
        </li>
      {/each}
    </ul>
    <div style="margin-top:8px"><button on:click={refresh}>Refresh</button></div>
  </aside>
</main>
