import { c as create_ssr_component, f as each, b as add_attribute, e as escape } from "../../chunks/ssr.js";
const css = {
  code: "main.svelte-8joy3y{display:grid;grid-template-columns:1fr 360px;gap:16px;padding:16px}.panel.svelte-8joy3y{border:1px solid rgba(0,0,0,.15);border-radius:8px;padding:12px;background:Canvas;color:CanvasText}img.svelte-8joy3y{max-width:100%;border-radius:8px;border:1px solid #ddd}button.svelte-8joy3y{padding:8px 10px;border-radius:6px;cursor:pointer;border:1px solid #4b5563;background:#111827;color:#fff}@media(prefers-color-scheme: light){button.svelte-8joy3y{background:#2563eb;border-color:#1d4ed8}}",
  map: `{"version":3,"file":"+page.svelte","sources":["+page.svelte"],"sourcesContent":["<script lang=\\"ts\\">var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {\\n    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }\\n    return new (P || (P = Promise))(function (resolve, reject) {\\n        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }\\n        function rejected(value) { try { step(generator[\\"throw\\"](value)); } catch (e) { reject(e); } }\\n        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }\\n        step((generator = generator.apply(thisArg, _arguments || [])).next());\\n    });\\n};\\nimport { onMount } from 'svelte';\\nlet latest = { image_url: null, captured_at: null };\\nlet items = [];\\nlet err = '';\\nfunction loadLatest() {\\n    return __awaiter(this, void 0, void 0, function* () {\\n        try {\\n            const r = yield fetch('/api/latest');\\n            if (!r.ok)\\n                throw new Error('' + r.status);\\n            latest = yield r.json();\\n        }\\n        catch (e) {\\n            err = 'Failed to load latest';\\n        }\\n    });\\n}\\nfunction loadRecent() {\\n    return __awaiter(this, void 0, void 0, function* () {\\n        try {\\n            const r = yield fetch('/api/images?page=1&page_size=10');\\n            if (!r.ok)\\n                throw new Error('' + r.status);\\n            const data = yield r.json();\\n            items = (data.items || []);\\n        }\\n        catch (e) {\\n            err = 'Failed to load recent';\\n        }\\n    });\\n}\\nfunction refresh() { loadLatest(); loadRecent(); }\\nonMount(refresh);\\n<\/script>\\n\\n<style>\\n  main { display: grid; grid-template-columns: 1fr 360px; gap: 16px; padding: 16px; }\\n  .panel { border: 1px solid rgba(0,0,0,.15); border-radius: 8px; padding: 12px; background: Canvas; color: CanvasText; }\\n  img { max-width: 100%; border-radius: 8px; border: 1px solid #ddd; }\\n  button { padding: 8px 10px; border-radius: 6px; cursor: pointer; border: 1px solid #4b5563; background: #111827; color: #fff; }\\n  @media (prefers-color-scheme: light) { button { background: #2563eb; border-color: #1d4ed8; } }\\n</style>\\n\\n<main>\\n  <section class=\\"panel\\">\\n    <h2>Latest</h2>\\n    {#if latest.image_url}\\n      <div style=\\"font-size:12px; color:#666\\">Captured: {latest.captured_at ?? ''}</div>\\n      <img src={latest.image_url} alt=\\"Latest\\" />\\n    {:else}\\n      <div>No image available</div>\\n    {/if}\\n  </section>\\n  <aside class=\\"panel\\">\\n    <h3>Recent</h3>\\n    {#if err}<div style=\\"color:#b00; font-size:12px\\">{err}</div>{/if}\\n    <ul style=\\"list-style:none; padding:0; margin:0\\">\\n      {#each items as it}\\n        <li style=\\"padding:6px 0; border-bottom:1px solid #eee\\">\\n          <a href={it.url} target=\\"_blank\\">{it.url}</a><br/>\\n          <small>{new Date(it.captured_at*1000).toISOString()}</small>\\n        </li>\\n      {/each}\\n    </ul>\\n    <div style=\\"margin-top:8px\\"><button on:click={refresh}>Refresh</button></div>\\n  </aside>\\n</main>\\n"],"names":[],"mappings":"AA6CE,kBAAK,CAAE,OAAO,CAAE,IAAI,CAAE,qBAAqB,CAAE,GAAG,CAAC,KAAK,CAAE,GAAG,CAAE,IAAI,CAAE,OAAO,CAAE,IAAM,CAClF,oBAAO,CAAE,MAAM,CAAE,GAAG,CAAC,KAAK,CAAC,KAAK,CAAC,CAAC,CAAC,CAAC,CAAC,CAAC,GAAG,CAAC,CAAE,aAAa,CAAE,GAAG,CAAE,OAAO,CAAE,IAAI,CAAE,UAAU,CAAE,MAAM,CAAE,KAAK,CAAE,UAAY,CACtH,iBAAI,CAAE,SAAS,CAAE,IAAI,CAAE,aAAa,CAAE,GAAG,CAAE,MAAM,CAAE,GAAG,CAAC,KAAK,CAAC,IAAM,CACnE,oBAAO,CAAE,OAAO,CAAE,GAAG,CAAC,IAAI,CAAE,aAAa,CAAE,GAAG,CAAE,MAAM,CAAE,OAAO,CAAE,MAAM,CAAE,GAAG,CAAC,KAAK,CAAC,OAAO,CAAE,UAAU,CAAE,OAAO,CAAE,KAAK,CAAE,IAAM,CAC9H,MAAO,uBAAuB,KAAK,CAAE,CAAE,oBAAO,CAAE,UAAU,CAAE,OAAO,CAAE,YAAY,CAAE,OAAS,CAAE"}`
};
const Page = create_ssr_component(($$result, $$props, $$bindings, slots) => {
  (function(thisArg, _arguments, P, generator) {
    function adopt(value) {
      return value instanceof P ? value : new P(function(resolve) {
        resolve(value);
      });
    }
    return new (P || (P = Promise))(function(resolve, reject) {
      function fulfilled(value) {
        try {
          step(generator.next(value));
        } catch (e) {
          reject(e);
        }
      }
      function rejected(value) {
        try {
          step(generator["throw"](value));
        } catch (e) {
          reject(e);
        }
      }
      function step(result) {
        result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected);
      }
      step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
  });
  let items = [];
  $$result.css.add(css);
  return `<main class="svelte-8joy3y"><section class="panel svelte-8joy3y"><h2 data-svelte-h="svelte-1w99m3x">Latest</h2> ${`<div data-svelte-h="svelte-1wg8do7">No image available</div>`}</section> <aside class="panel svelte-8joy3y"><h3 data-svelte-h="svelte-1215uob">Recent</h3> ${``} <ul style="list-style:none; padding:0; margin:0">${each(items, (it) => {
    return `<li style="padding:6px 0; border-bottom:1px solid #eee"><a${add_attribute("href", it.url, 0)} target="_blank">${escape(it.url)}</a><br> <small>${escape(new Date(it.captured_at * 1e3).toISOString())}</small> </li>`;
  })}</ul> <div style="margin-top:8px"><button class="svelte-8joy3y" data-svelte-h="svelte-1e4tnv4">Refresh</button></div></aside></main>`;
});
export {
  Page as default
};
