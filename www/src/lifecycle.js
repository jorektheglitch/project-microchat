import { api } from './api.js';
import { entryBox, Chat, setLocationHashParam, router } from './elements.js';
import { createElement } from './dom.js';


function search_user(submit_event) {
	submit_event.preventDefault();
	setLocationHashParam('s', submit_event.target.username.value);
	return false;
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
			entryBox.newMessage(receiver, sender, text, time_sent);
			new Chat(receiver, chat_type).newMessage(data);
		} else {
			entryBox.newMessage(sender, sender, text, time_sent);
			new Chat(sender, chat_type).newMessage(data);
		}
		console.log(e);
	})
};

searchform.addEventListener('submit', search_user);

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

window.addEventListener('hashchange', router);
window.addEventListener('load', router);

mainloop();

export { api };