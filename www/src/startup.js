let options = {}
let token = localStorage.getItem("token");
if (token) {
	options.headers = { 'Authorization': `Bearer ${token}` }
}

fetch("/api/users/self", options)
.then(response => {
	switch (response.status) {
		case 200:
			return response.json();
		case 400:
			location.replace('/explain'); break
		case 403:
			return {result:0};
		default:
			location.replace(`/problems?from=index`); break
	};
})
.then(({result: self_info}) => {
	if (!self_info) {
		document.getElementById("login-popup").hidden = false;
	} else {
		onLogin(self_info);
	}
});

function onLogin({id, name, token}) {
	let change_uname = (uname) => {
		unameContainer = document.getElementById('username');
		unameContainer.innerHTML = '';
		unameContainer.append(document.createTextNode(uname));
	};
	switch (document.readyState) {
		case "loading":
			document.addEventListener(
				"DOMContentLoaded",
				() => change_uname(name)
			);
			break;
		default:
			change_uname(name);
			break;
	};
	localStorage.setItem("current_uid", id);
	localStorage.setItem("current_uname", name);
	if (token)
		localStorage.setItem("token", token);
	addEventListener("storage", event => {
		if (event.key=="current_uname") {
			change_uname(event.newValue);
		};
	});
	document.getElementById("login-popup").hidden = true;
	document.getElementById("register").hidden = true;
}

function login(form) {
	let {
		username: { value: username },
		password: { value: password }
	} = form;
	let digest = sha256(password);
	fetch("/api/auth/login", {
		method: "POST",
		body: JSON.stringify({
			username: username,
			digest: digest
		})
	})
	.then(async (response) => {
		let json = await response.json();
		if (json.status) {
			console.error(`code: ${json.status}\nreason: ${json.error}`);
			return;
		} else {
			onLogin(json.result);
			location.reload();
		}
	})
	return false;
}

function register(form) {
	let {
		username: { value: username },
		password: { value: password },
	} = form;
	fetch("/api/auth/register", {
		method: "POST",
		body: JSON.stringify({
			username: username,
			password: password
		})
	})
	.then(async (response) => {
		let json = await response.json();
		if (json.status) {
			console.error(`code: ${json.status}\nreason: ${json.error}`);
			return;
		} else {
			onLogin(json.result);
			location.reload();
		}
	})
	return false;
}

function switchToRegister() {
	let loginBlock = document.getElementById("login");
	let registerBlock = document.getElementById("register");
	loginBlock.hidden = true;
	registerBlock.hidden = false;
	return false;
}
