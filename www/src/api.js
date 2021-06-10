class APIError extends Error {
	constructor (obj) {
		super(obj.hasOwnProperty("error") ? obj.error : "request to API failed");
		this.name = "APIError";
		this.code = obj.hasOwnProperty("status") ? obj.status : 1;
	};
};

function extract (obj) {
	if (!obj.status) {
		let result = obj.result ? obj.result : {};
		result.ok = true;
		return result;
	} else {
		throw new APIError(obj);
	};
};

function castRequester(path, method = "GET") {
	function requester(params, json=true) {
		let options = {
			method: method,
			body: json ? JSON.stringify(params) : params
		}
		let token = localStorage.getItem("token");
		if (token) {
			options.headers = { 'Authorization': `Bearer ${token}` }
		}
		let promise = fetch(path, options)
			.then(response => response.json())
			.then(
				extract,
				console.error
			);
		return promise;
	};
	requester.toString = () => path;
	return requester;
};

var api = {
	messages: {
		overview: castRequester("/api/messages/overview", "POST"),
		get: castRequester("/api/messages/get", "POST"),
		send: castRequester("/api/messages/send", "POST"),
	},
	users: {
		search: castRequester("/api/users/search", "POST"),
		by_id: castRequester("/api/users/by_id", "POST"),
	},
	auth: {
		login: castRequester("/api/auth/login", "POST"),
		register: castRequester("/api/auth/register", "POST"),
	},
	media: {
		load: castRequester("/api/auth/load")
	}
};

export {api, APIError};

function lazygetterProxy(proxy, caster=(name)=>name) {
	return new Proxy({}, {
		get (target, name) {
			let value = target[name];
			if (!value)
				value = proxy(caster(name));
			return value;
		}
	})
}
const _api = {
	chats: lazygetterProxy(chatProxy, (name)=>{
		let [id, type, ..._] = name.split('_');
		return {id: id, type: type};
	}),

}
function chatProxy({id, type}) {
	if (id=='slice') {
		return function (start=undefined, end=undefined, ...others) {
			if (!end) {
				end = start;
				start = 0;
			}
			return {
				get: async () => {
					const url = new URL('/api/test/chats/slice', location);
					url.searchParams.set('start', start);
					url.searchParams.set('end', end);
					const response = await fetch(url, {
						headers: {'Authorization': `Bearer ${token}`}
					});
					return await response.json();
				},/*
				delete: () => {
					const url = new URL('/api/test/chats/slice', location);
					others.push(start);
					others.push(end);
					url.searchParams.set('start',  start);
					url.searchParams.set('end', end);
					const response = await fetch(url, {
						method: 'DELETE',
						headers: {'Authorization': `Bearer ${token}`,
					}});
					return await response.json();
				}*/
			}
		};
	}
	return {
		messages: lazygetterProxy(chatMessageProxy, (name)=>{
			return {
				message: name,
				chat: {id:id, type:type}
			}
		}),
		users: lazygetterProxy(chatUserProxy, (name)=>{
			return {
				user: name,
				chat: {id:id, type:type}
			}
		})
	}
}
function chatMessageProxy({chat, message}) {
	return {
		get: async (start=undefined, end=undefined) => {
			const url = new URL(`/api/test/chats/${chat}/messages/${message}`, location);
			for (let [name, value] of Object.entries({start: start, end: end})) {
				if (value) {
					url.searchParams.set(name, value);
				};
			};
			const response = await fetch(url, {
				headers: {
					'Authorization': `Bearer ${token}`
				}
			});
			return await response.json();
		},
		//post: () => {console.log('post', message, chat)},
		patch: () => {console.log('patch', message, chat)},
		delete: () => {console.log('delete', message, chat)},
	}
}
function chatUserProxy({chat, user}) {
	return {
		get: () => {console.log('get', user, chat)},
		//post: () => {console.log('post', user, chat)},
		patch: () => {console.log('patch', user, chat)},
		delete: () => {console.log('delete', user, chat)},
	}
}

//_api.chats["123_456"].messages[1].get()
_api.chats.slice(0, 100).get().then(console.log)
//_api.chats["123_456"].messages[2].post()
//_api.chats["123_456"].messages[3].patch()
//_api.chats["123_456"].messages[4].delete()


/*const modelName = 'Cristy23';
const modelsSelector = '#mls_models > div.mls_models.__ths_medium.__percent_width_grid.__filled_row > div.ls_thumb.js-ls_thumb.__s_medium';
const viewersSelector = 'div.lst_info > div.lsti_box.lst_viewers.js-lst_clink';

let int = setInterval(()=>{
    let previews = document.querySelectorAll(modelsSelector);
    let rating = undefined;
    let viewers = undefined;
    for (let el of previews) {
      if (el.firstChild.getAttribute('data-chathost')==modelName) {
        let viewersContainer = el.querySelector(viewersSelector);
        rating = el.getAttribute('data-so');
        viewers = viewersContainer.innerHTML;
      };
    };
    if (rating) {
      console.log(`${new Date()}\nМесто в топе: ${rating}\nЗрителей: ${viewers}`);
    } else {
      console.log(`${new Date()}\nНе нашёл модель на странице. Всего ${previews.length} моделей на странице`);
    }
  }, 35000
)*/
