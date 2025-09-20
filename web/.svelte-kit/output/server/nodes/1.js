

export const index = 1;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/fallbacks/error.svelte.js')).default;
export const imports = ["_app/immutable/nodes/1.Qnz8Y2_W.js","_app/immutable/chunks/scheduler.B7VdhWLQ.js","_app/immutable/chunks/index.BdQBDl6v.js","_app/immutable/chunks/entry.eTFZcxOZ.js"];
export const stylesheets = [];
export const fonts = [];
