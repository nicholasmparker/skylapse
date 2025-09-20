

export const index = 2;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/_page.svelte.js')).default;
export const imports = ["_app/immutable/nodes/2.wyufGdDW.js","_app/immutable/chunks/scheduler.B7VdhWLQ.js","_app/immutable/chunks/index.BdQBDl6v.js"];
export const stylesheets = ["_app/immutable/assets/2.D-9mQtpo.css"];
export const fonts = [];
