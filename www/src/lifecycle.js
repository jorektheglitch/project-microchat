import { api } from './api.js';
import { entryBox, Chat, setLocationHashParam, router } from './elements.js';
import { createElement } from './dom.js';


function search_user(submit_event) {
	submit_event.preventDefault();
	setLocationHashParam('s', submit_event.target.username.value);
	return false;
}

const searchHeader = document.querySelector('#sidebar-menu > .search-h');
const createHeader = document.querySelector('#sidebar-menu > .create-h');
const actionForms = document.querySelector('#actionforms-container');
const searchForm = document.querySelector('#searchform');
const createForm = document.querySelector('#createform');

for (let searchEl of [searchHeader, searchForm]) {
	searchEl.onmouseover = function (event) {
		for (let el of [searchHeader, createHeader])
			if (el.timer){
				clearTimeout(el.timer);
				el.timer = undefined;
			};
		actionForms.viewed = this;
		createform.style.display = 'none';
		searchform.style.display = 'flex';
		createHeader.style.background = 'transparent';
		searchHeader.style.background = 'rgb(216, 216, 216)';
	};
	searchEl.onmouseout = function (event) {
		searchHeader.timer = setTimeout(()=>{
			searchform.style.display = 'none';
			searchHeader.style.background = 'transparent';
		}, 500);
	};
};
for (let createEl of [createHeader, createForm]) {
	createEl.onmouseover = function (event) {
		for (let el of [searchHeader, createHeader])
			if (el.timer){
				clearTimeout(el.timer);
				el.timer = undefined;
			};
		actionForms.viewed = this;
		searchform.style.display = 'none';
		createform.style.display = 'grid';
		searchHeader.style.background = 'transparent';
		createHeader.style.background = 'rgb(216, 216, 216)';
	};
	createEl.onmouseout = function (event) {
		createHeader.timer = setTimeout(()=>{
			createform.style.display = 'none';
			createHeader.style.background = 'transparent';
		}, 500);
	};
};
createHeader.onmouseover = function (event) {
	for (let el of [searchHeader, createHeader])
		if (el.timer){
			clearTimeout(el.timer);
			el.timer = undefined;
		};
	searchform.style.display = 'none';
	createform.style.display = 'grid';
}
createHeader.onmouseout = function (event) {
	this.timer = setTimeout(()=>{
		createform.style.display = 'none';
	}, 500)
}

async function mainloop() {
	api.messages.overview().then(entryBox.render_messages);
	const url = new URL('/api/events/', location.origin);
	const token = localStorage.getItem('token');
	const current_uid = localStorage.getItem("current_uid");
	if (token)
		url.searchParams.set("access_token", token)
	let eventSource = new EventSource(url);
	eventSource.addEventListener('MessageReceive', e => {
		let data = JSON.parse(e.data);
		//let event = new CustomEvent('MessageReceive', {detail: data});
		const {chat_type, sender, receiver, text, time_sent, time_edit} = data;
		if (!data.sent)
			data.sent = time_sent;
		if (!data.edit)
			data.edit = time_edit;
		if (sender==current_uid) {
			entryBox.newMessage(receiver, sender, text, time_sent, chat_type);
			new Chat(receiver, chat_type).newMessage(data);
		} else {
			entryBox.newMessage(sender, sender, text, time_sent, chat_type);
			new Chat(sender, chat_type).newMessage(data);
		}
		console.log(e);
	})
};

searchForm.addEventListener('submit', search_user);
createForm.addEventListener('submit', function (event) {
	event.preventDefault();
	let {username, type} = event.target;
	console.log(username.value, type.value);
	api.messages.create_conversation({
		username: username.value,
		type: type.value,
		users: []
	}).then(info => {
		new Chat(info.conference, type);
		entryBox.newMessage(info.conference, localStorage.getItem("current_uid"), 'conversation created', new Date(), type);
	})
	return false;
})

document.getElementById('search-input').addEventListener('search', e => {
	let target = e.target;
	setLocationHashParam('s', target.value);
	if (!target.value) {
		entryBox.render_messages();
	}
});

document.querySelector('#chat_info-container .arrow-back').onclick = (e) => {
	setLocationHashParam('c', undefined);
};

function send_message(formElement) {
	let form = new FormData(formElement);
	for (let child of formElement) {
		child.disabled = true;
	}
	api.messages.send(form, false).then((response) => {
		for (let child of formElement) {
			child.disabled = false;
		};
		if (response.ok) {
			for (let el of [formElement.text, formElement.attachments, messagearea, messagearea.parentNode.dataset]) {
				el.value = '';
			}
			let attachments = document.getElementById("view-attachments");
			attachments.innerHTML = '';
			attachments.hidden = true;
		};
		document.getElementById('messagearea').focus();
	},
	()=>{
		for (let child of formElement) {
			child.disabled = false;
		}
		let stdBorder = messagebox.style.border;
		messagebox.style.border = '2px solid #F00';
		setTimeout(()=>{
			messagebox.style.border = stdBorder;
		}, 2000);
		document.getElementById('messagearea').focus();
	});
	return false;
}

document.getElementById('messageform').addEventListener('submit', (submit_event) => {
	submit_event.preventDefault();
	const formElement = submit_event.target;
	return send_message(formElement);
});

document.getElementById("messagearea").addEventListener('keydown', function(e) {
	if (e.keyCode === 13) {
		send_message(e.target.form);
	}
});

document.getElementById("fileLoadButton").onclick = (click) => {
	click.preventDefault();
	const messageForm = messageform;
	const attachments = messageForm.attachments;
	const attachmentsView = document.getElementById("view-attachments");
	const form = document.createElement('form');
	const file = document.createElement('input');
	const filename = document.createElement('input');
	const mimetype = document.createElement('input');
	file.name = "content";
	file.type = "file";
	filename.name = "filename";
	mimetype.name = "mimetype";
	form.append(filename, mimetype, file);
	file.onchange = (change) => {
		const name = filename.value = file.files[0].name;
		const data = new FormData(form);
		const xhr = new XMLHttpRequest();
		const container = createElement('div', {class: 'attachment-container'});
		const nameEl = createElement('h5', {class: 'attachment-name'} );
		const progressEl = document.createElement('progress')//, {class: 'attachment-progress'});
		document.createElement('div').style.grid
		const del = createElement('button', {class: 'attachment-delbtn'});
		const delImage = createElement('img', {style: {height: '100%'}});
		delImage.src = 'images/pictorgams/close.svg';
		del.append(delImage);
		nameEl.append(document.createTextNode(name));
		container.append(nameEl, del, progressEl);
		attachmentsView.append(container);
		attachmentsView.hidden = false;
		xhr.open("POST", "/api/media/store");
		xhr.setRequestHeader('Authorization', `Bearer ${localStorage.getItem("token")}`);
		xhr.upload.onprogress = (progress) => {
			let {loaded, total} = progress;
			progressEl.max = total;
			progressEl.value = loaded;
			//let percents = (loaded/total*100).toFixed(2);
			//console.log(`Loaded ${percents}% (${loaded}/${total})`);
		};
		xhr.onload = (event) => {
			if (xhr.status!=200) {
				console.error(`File load request failed with status ${xhr.status} (${xhr.statusText})`);
				return;
			}
			const info = JSON.parse(xhr.response);
			let ids = [];
			if (attachments.value.trim())
				ids = attachments.value.split(" ");
			ids.push(info.file.id);
			attachments.value = ids.join(" ");
			progressEl.remove();
		};
		xhr.onerror = (event) => {};
		xhr.send(data);
	};
	file.click();
}

function getEditArea(messageTextElement, message_id, interlocutor, chat_type) {
	let messageText = messageTextElement.innerText;
	let container = createElement('div', {class: 'view-message-editarea'});
	let label = createElement('label', {
		classList: ['input-sizer', 'stacked'],
		style: {
			width: '100%',
			maxHeight: '100%',
			padding: 0,
		}
	});
	let textarea = createElement('textarea');
	label.append(textarea);
	textarea.oninput = function () {
		this.parentNode.dataset.value = this.value;
	}
	label.dataset.value = textarea.value = messageText;
	let button_params = {style: {height: '100%', border: 0}};
	let ok_button = createElement('button', button_params);
	ok_button.innerText = '✔';
	let mark_error = () => {
		let stdBorder = container.style.border;
		container.style.border = '2px solid #F00';
		setTimeout(()=>{
			container.style.border = stdBorder;
		}, 2000);
		textarea.disabled = false;
		textarea.focus();
	};
	ok_button.onclick = () => {
		textarea.disabled = true;
		api.messages.edit({
			user_id: interlocutor,
			message_id: message_id,
			text: textarea.value,
			chat_type: chat_type
		}).then(
			(response)=>{
				if (response.ok) {
					messageTextElement.innerText = textarea.value
					container.replaceWith(messageTextElement);
				} else {
					mark_error();
				};
			},
			mark_error
		);
	}
	let cancel_button = createElement('button', button_params);
	cancel_button.innerText = '✘';
	cancel_button.style.borderRadius = '0 0.5rem 0.5rem 0';
	cancel_button.onclick = () => {container.replaceWith(messageTextElement)};
	container.append(label, ok_button, cancel_button);
	return container;
}

document.getElementById('messages').addEventListener('click', function (event) {
	const {chat_id, chat_type} = this;
	const target = event.target;
	const message_content = target.parentNode.parentNode;
	const message_container = message_content.parentNode;
	const message_id = message_container.message_id;
	const action = target.action;
	if (!(chat_id&&chat_type&&message_id&&action))
		return;
	switch (action) {
		case 'edit':
			let messageTextElement = message_content.querySelector('.view-message-text');
			let editArea = getEditArea(messageTextElement, message_id, chat_id, chat_type);
			messageTextElement.replaceWith(editArea);
			break;
		case 'delete':
			api.messages.delete({
				user_id: chat_id,
				message_id: message_id,
				chat_type: chat_type,
			}).then(
				(response)=>{
					if (response.ok) {
						message_container.parentNode.removeChild(message_container);
					}
				},
				console.error
			);
			break;
		case 'reply':
			break;
		default:
			break;
	}
	console.log(message_id, chat_id, chat_type, action);
});

window.addEventListener('hashchange', router);
window.addEventListener('load', router);

mainloop();

export { api };