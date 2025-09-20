

export const index = 3;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/focus/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/3.CFNizh12.js","_app/immutable/chunks/scheduler.B7VdhWLQ.js","_app/immutable/chunks/index.BdQBDl6v.js"];
export const stylesheets = ["_app/immutable/assets/3.ufP7hxLM.css"];
export const fonts = [];
