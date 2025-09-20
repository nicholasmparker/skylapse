

export const index = 0;
let component_cache;
export const component = async () => component_cache ??= (await import('../entries/pages/_layout.svelte.js')).default;
export const imports = ["_app/immutable/nodes/0.vP4B26Qm.js","_app/immutable/chunks/scheduler.B7VdhWLQ.js","_app/immutable/chunks/index.BdQBDl6v.js"];
export const stylesheets = ["_app/immutable/assets/0.BpmiOtnh.css"];
export const fonts = [];
