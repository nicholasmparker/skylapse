export const manifest = (() => {
function __memo(fn) {
	let value;
	return () => value ??= (value = fn());
}

return {
	appDir: "_app",
	appPath: "_app",
	assets: new Set([]),
	mimeTypes: {},
	_: {
		client: {"start":"_app/immutable/entry/start.DNTycs6P.js","app":"_app/immutable/entry/app.oiakjalr.js","imports":["_app/immutable/entry/start.DNTycs6P.js","_app/immutable/chunks/entry.BUef4XgJ.js","_app/immutable/chunks/scheduler.B7VdhWLQ.js","_app/immutable/entry/app.oiakjalr.js","_app/immutable/chunks/scheduler.B7VdhWLQ.js","_app/immutable/chunks/index.BdQBDl6v.js"],"stylesheets":[],"fonts":[],"uses_env_dynamic_public":false},
		nodes: [
			__memo(() => import('./nodes/0.js')),
			__memo(() => import('./nodes/1.js')),
			__memo(() => import('./nodes/2.js')),
			__memo(() => import('./nodes/3.js'))
		],
		routes: [
			{
				id: "/",
				pattern: /^\/$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 2 },
				endpoint: null
			},
			{
				id: "/focus",
				pattern: /^\/focus\/?$/,
				params: [],
				page: { layouts: [0,], errors: [1,], leaf: 3 },
				endpoint: null
			}
		],
		matchers: async () => {
			
			return {  };
		},
		server_assets: {}
	}
}
})();
