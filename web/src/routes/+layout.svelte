<script lang="ts">
  import '../app.css';
  import { onMount } from 'svelte';
  let logged = false;
  let loginErr = '';
  let password = '';
  let dlg: HTMLDialogElement | null = null;
  let theme: 'modern' | 'skeleton' = 'modern';

  onMount(async () => {
    dlg = document.getElementById('login-modal') as HTMLDialogElement | null;
    await checkAuth();
    // Theme from localStorage
    const t = localStorage.getItem('theme');
    if (t === 'modern' || t === 'skeleton') theme = t;
    applyTheme();
  });

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
      const r = await fetch('/api/login', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ password })
      });
      if (!r.ok) throw new Error(String(r.status));
      logged = true;
      password = '';
      dlg?.close();
    } catch (e) {
      loginErr = 'Invalid password';
    }
  }
  async function logout() {
    await fetch('/api/logout', { method: 'POST' });
    logged = false;
  }

  function applyTheme() {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('theme', theme);
  }
</script>

<header class="sticky top-0 z-20 backdrop-blur supports-[backdrop-filter]:bg-white/70 dark:supports-[backdrop-filter]:bg-neutral-900/70 border-b border-neutral-200 dark:border-neutral-800">
  <div class="mx-auto max-w-7xl px-4 py-3 flex items-center justify-between">
    <nav class="flex items-center gap-6 text-sm">
      <a href="/" class="font-semibold tracking-tight">Skylapse</a>
      <a href="/focus" class="text-neutral-600 hover:text-neutral-900 dark:text-neutral-300 dark:hover:text-white">Focus</a>
    </nav>
    <div class="flex items-center gap-2">
      {#if logged}
        <span class="inline-flex items-center gap-1 rounded-full border border-emerald-600/40 bg-emerald-600/10 px-3 py-1 text-xs text-emerald-700 dark:text-emerald-300">Logged in</span>
        <button class="rounded-md bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900 px-3 py-1.5 text-sm hover:opacity-90" on:click={logout}>Logout</button>
      {:else}
        <span class="inline-flex items-center gap-1 rounded-full border border-rose-700/40 bg-rose-700/10 px-3 py-1 text-xs text-rose-700 dark:text-rose-300">Logged out</span>
        <button class="rounded-md bg-brand-600 text-white px-3 py-1.5 text-sm hover:bg-brand-700" on:click={() => dlg?.showModal()}>Login</button>
      {/if}
    </div>
  </div>
  </header>

<main class="mx-auto max-w-7xl px-4 py-6">
  <slot />
</main>

<dialog id="login-modal" class="rounded-lg border border-neutral-200 dark:border-neutral-800 p-0">
  <form method="dialog" class="bg-white dark:bg-neutral-900 text-neutral-900 dark:text-neutral-100 p-5 min-w-80">
    <h3 class="text-lg font-semibold">Login</h3>
    <label for="password" class="block text-xs text-neutral-500 mt-3">Password</label>
    <input id="password" type="password" bind:value={password} placeholder="Enter password" class="mt-1 w-full rounded-md border border-neutral-300 dark:border-neutral-700 bg-transparent px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand-500" />
    {#if loginErr}
      <div class="text-rose-600 text-xs mt-2">{loginErr}</div>
    {/if}
    <div class="flex gap-2 justify-end mt-4">
      <button value="cancel" class="rounded-md border border-neutral-300 dark:border-neutral-700 px-3 py-1.5 text-sm">Cancel</button>
      <button type="button" class="rounded-md bg-brand-600 text-white px-3 py-1.5 text-sm hover:bg-brand-700" on:click={login}>Login</button>
    </div>
  </form>
</dialog>
