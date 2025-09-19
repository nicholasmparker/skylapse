<script lang="ts">
  import { onMount } from 'svelte';
  let logged = false;
  let showLogin = false;
  let password = '';
  let loginErr = '';

  async function checkAuth() {
    try {
      const r = await fetch('/api/admin/health');
      logged = r.ok;
    } catch {
      logged = false;
    }
  }
  async function login() {
    loginErr = '';
    try {
      const r = await fetch('/api/login', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ password }) });
      if (!r.ok) throw new Error(String(r.status));
      logged = true; showLogin = false; password = '';
    } catch {
      loginErr = 'Invalid password';
    }
  }
  async function logout() {
    await fetch('/api/logout', { method: 'POST' });
    logged = false;
  }
  onMount(checkAuth);
</script>

<style>
  header { position: sticky; top: 0; z-index: 20; display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border-bottom: 1px solid #ddd; backdrop-filter: blur(6px); background: color-mix(in oklab, Canvas 85%, transparent); }
  nav a { margin-right: 12px; text-decoration: none; color: inherit; }
  .chip { padding: 4px 10px; border-radius: 999px; font-size: 12px; border: 1px solid #4b5563; }
  .ok { background: #065f46; color: #fff; border-color: #065f46; }
  .err { background: #7f1d1d; color: #fff; border-color: #7f1d1d; }
  dialog { border: 1px solid #4b5563; border-radius: 8px; padding: 0; }
  dialog form { padding: 16px; background: Canvas; color: CanvasText; min-width: 320px; }
  button { padding: 8px 10px; border-radius: 6px; cursor: pointer; border: 1px solid #4b5563; background: #111827; color: #fff; }
  @media (prefers-color-scheme: light) { button { background: #2563eb; border-color: #1d4ed8; } }
</style>

<header>
  <nav>
    <a href="/"><strong>Skylapse</strong></a>
    <a href="/focus">Focus</a>
  </nav>
  <div style="display:flex; gap:8px; align-items:center">
    {#if logged}
      <span class="chip ok">Logged in</span>
      <button on:click={logout}>Logout</button>
    {:else}
      <span class="chip err">Logged out</span>
      <button on:click={() => { showLogin = true; loginErr = ''; }}>Login</button>
    {/if}
  </div>
</header>

<slot />

<dialog bind:open={showLogin} on:close={() => (loginErr = '')}>
  <form method="dialog">
    <h3>Login</h3>
    <label>Password</label>
    <input type="password" bind:value={password} placeholder="Enter password" style="width:100%" />
    {#if loginErr}<div style="color:#b00; font-size:12px; margin-top:8px">{loginErr}</div>{/if}
    <div style="display:flex; gap:8px; justify-content:flex-end; margin-top:12px">
      <button value="cancel">Cancel</button>
      <button type="button" on:click={login}>Login</button>
    </div>
  </form>
</dialog>
