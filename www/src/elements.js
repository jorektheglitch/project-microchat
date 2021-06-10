import { api } from './api.js';
import { createElement } from './dom.js';

function getLocationHashParams(hash) {
	let pureHash;
	if (hash) {
		pureHash = hash;
	} else {
		pureHash = location.hash.slice(1);
	}
	let hashParams = new URLSearchParams(pureHash);
	return hashParams;
}

function setLocationHashParam(name, value) {
	let hashParams = getLocationHashParams();
	if (value)
		hashParams.set(name, value);
	else
		hashParams.delete(name);
	location.hash = hashParams;
}

function lJust(number, lenght=2) {
	return number.toLocaleString('en-US', {
		minimumIntegerDigits: lenght,
		useGrouping: false
	  })	
}

function enableMessagesForm() {
	for (let child of document.getElementById('messageform').childNodes) {
		child.disabled = false
	}
}

const entryBox = {
	root: entries,
	chatsInfo: [],
	chatsPreviews: Object.create(null),
	nowSelected: null,
	newMessage: async function (interlocutor, author, text, time_sent, chat_type) {
		let nowPreview = this.chatsPreviews[interlocutor];
		let ilocName = await new Chat(interlocutor, chat_type).uname;
		let newPreview = this.renderMessage(interlocutor, ilocName, author, text, time_sent);
		if (nowPreview) {
			this.root.prepend(nowPreview);
			newPreview.style.background = nowPreview.style.background;
			nowPreview.replaceWith(newPreview);
			if (nowPreview == this.nowSelected) {
				this.nowSelected = newPreview;
			}
		} else {
			this.root.prepend(newPreview);
		}
	},
	renderMessage: function (uid, uname, last_uid, message, time_sent, chat_type) {
		let current_uid = localStorage.getItem("current_uid");
		let row = createElement('div', { classList: ['entry', 'border-bottom-gray'] });
		let avatar = createElement('div', { class: 'avatar_mini' });
		let name = createElement('h4', { class: 'entry-chatname' });
		let time = createElement('h5', { class: 'entry-time' })
		let messagebox = createElement('div', { class: 'entry-messagebox' });
		let msg_sender = createElement('h5', {
			style: {
				margin: '0px 5px 0 0',
				float: 'left',
			},
		});
		let msg_text = createElement('h5', { style: {margin: '0'} });
		let sender_name = (last_uid==current_uid) ? localStorage.getItem("current_uname") : uname;
		let short_uname = uname.slice(0, 1).toUpperCase();
		let acronym = createElement('span');
		sender_name = `${sender_name}: `;
		row.onclick = (event) => {
			if (entryBox.nowSelected)
				entryBox.nowSelected.style.background = '#A0A0A0';
			row.style.background = '#F0F0F0';
			entryBox.nowSelected = row;
			setLocationHashParam('c', uid);
		};
		const datetime = new Date(time_sent*1000);
		let fulldate = `${lJust(datetime.getDate())}.${lJust(datetime.getMonth()+1)}`;
		let fulltime = `${lJust(datetime.getHours())}:${lJust(datetime.getMinutes())}`;
		time.append(document.createTextNode(`${fulldate} ${fulltime}`));
		msg_sender.append(document.createTextNode(sender_name));
		acronym.append(document.createTextNode(short_uname));
		avatar.append(acronym);
		msg_text.append(document.createTextNode(message));
		name.append(document.createTextNode(uname));
		messagebox.append(msg_sender, msg_text);
		row.append(avatar, name, time, messagebox); // добавить счётчик непрочитанных
		this.updatePreview(uid, row);
		return row;
	},
	render_messages: function (messages) {
		let container = document.createElement('div');
		if (messages==undefined) {
			for (let interlocutor of this.chatsInfo) {
				let preview = this.chatsPreviews[interlocutor];
				container.append(preview);
			}
		} else {
			for (let msg of messages) {
				const {
					chat: {
						id: uid,
						username: uname,
						chat_type
					},
					message: {
						sender: last_uid,
						text: message,
						sent: time_sent
					}
				} = msg;
				let row = entryBox.renderMessage(uid, uname, last_uid, message, time_sent, chat_type);
				entryBox.chatsPreviews[uid] = row;
				container.append(row);
			};
		};
		container.style.height = '100%';
		container.style.width = '100%';
		entryBox.root.replaceWith(container);
		entryBox.root = container;
	},
	render_query_results: (results) => {
		let container = document.createElement('div');
		for (let [uid, username] of Object.entries(results)) {
			if (uid=='ok') continue;
			let entry = createElement('div', { classList: ['search-message-container', 'border-bottom-gray'] });
			let avatar = createElement('div', { classList: ['avatar_mini', 'search-message-avatar'] });
			let uname = createElement('h4', { class: 'search-message-sender' });
			uname.append(document.createTextNode(username));
			entry.onclick = (event) => {
				setLocationHashParam('c', uid);
			};
			entry.append(avatar, uname);
			container.append(entry);
		};
		entryBox.root.replaceWith(container);
		entryBox.root = container;
	},
	updatePreview: (interlocutor, newPreview) => {
		let idx = entryBox.chatsInfo.indexOf(interlocutor);
		if (~idx)
			entryBox.chatsInfo.splice(idx, 1);
		entryBox.chatsInfo.unshift(interlocutor);
		entryBox.chatsPreviews[interlocutor] = newPreview;
	}
};

class Chat {
	static root = view;
	static messagesbox = messages;
	static instances = new Map();
	static nowShow = undefined;
	static prevShow = undefined;
	constructor (uid, type=1) {
		uid = Number.parseInt(uid);
		if (Chat.instances.has(type)) {
			const chats = Chat.instances.get(type);
			if (chats.has(uid))
			    return chats.get(uid);
		} else {
			Chat.instances.set(type, new Map());
		}
		Chat.instances.get(type).set(uid, this);
		this.uid = uid;
		this.type = type;
		this.uname = new Promise((resolve, reject)=>{
			api.users.by_id({
				'uid': uid
			}).then(result=>{
				resolve(result.name);
			}, reject);
		});
		this.messages = new Promise((resolve, reject)=>{
			api.messages.get({
				'user_id': uid
			}).then(messages=>{
				resolve(messages.sort((a, b)=>a.id-b.id));
			}, reject);
		});
	};
	async newMessage(message) {
		let messages = await this.messages;
		messages.push(message);
		if (Chat.nowShow===this) {
			this.showMessage(message);
		}
	};
	async oldMessage(message) {
		let messages = await this.messages;
		messages.unshift(message);
		if (Chat.nowShow===this)
			this.showMessage(message, prepend=true);
	}
	async showMessage(packedMessage, container, prepend=false) {
		if (!container) {
			container = Chat.messagesbox.childNodes[0];
		}
		/*{
            "attachment": {
                "id": msg.File.id,
                "name": msg.File.name,
                "size": msg.File.size
            }
        }*/
		const {
			id: mid,
			sender: sender_uid,
			text: message,
			sent: time_sent,
			edit: time_edit,
			chat_type,
			attachments
		} = packedMessage;
		const uname = await this.uname;
		const current_uid = localStorage.getItem("current_uid");
		const current_uname = localStorage.getItem("current_uname");
		const message_container = createElement('div', {class: 'view-message-container'} );
		const message_tail = createElement('div', {class: 'view-message-tail'} );
		const message_content = createElement('div', {class: 'view-message-content'});
		const avatar = createElement('div', {classList: ['view-message-avatar', 'avatar_mini']} );
		const sender = createElement('h5', {class: 'view-message-sender'} );
		const text = createElement('div', {class: 'view-message-text'} );
		//const additional = createElement('div', {class: 'view-message-additional'} );
		const time = createElement('time', {class: 'view-message-time'} );
		const datetime = new Date(time_sent*1000);
		let fulldate = `${lJust(datetime.getDate())}.${lJust(datetime.getMonth()+1)}`;
		let fulltime = `${lJust(datetime.getHours())}:${lJust(datetime.getMinutes())}`;
		time.innerText = `${fulldate} ${fulltime}`;
		const actions = createElement('div', {class: 'view-message-actions'} );
		let reply = createElement('a');
		reply.innerText = 'reply';
		let edit = createElement('a');
		edit.innerText = 'edit';
		let del = createElement('a');
		del.innerText = 'delete';
		let sender_name = (sender_uid==current_uid) ? current_uname : uname;
		if (sender_uid==current_uid) {
			actions.append(edit, del);
			message_container.style.flexDirection = 'row-reverse';
			sender.hidden = true;
			sender.hidden = true;
			message_container.classList.add('view-selfMessage');
			//additional.style.height = '0.5rem';
		} else {
			message_container.classList.add('view-otherMessage');
		}
		if (this.type == 1)
			avatar.hidden = true;
			sender.hidden = true;
		sender.append(document.createTextNode(sender_name));
		text.append(document.createTextNode(message));
		actions.prepend(reply);
		//additional.append(time, actions);
		message_tail.append(createElement('div'), createElement('div'));
		message_content.append(sender, actions, text, time);
		message_container.append(avatar, message_tail, message_content);
		if (attachments.length) {
			const attachments_container = createElement('div', {class: 'view-message-attachments'} );
			for (let {id, name, size} of attachments) {
				const attach = createElement('h5');
				const link = createElement('a');
				link.innerText = 'download';
				const url = new URL('/api/media/load', location.origin);
				url.searchParams.set('message', mid);
				url.searchParams.set('id', id);
				link.download = name;
				link.href = url;
				attach.append(document.createTextNode(name), link);
				attachments_container.append(attach);
			}
			message_content.append(attachments_container);
		}
		if (prepend)
			container.prepend(message_container);
		else
			container.append(message_container);
	};
	async render () {
		if (Chat.nowShow==this)
			return;
		Chat.prevShow = Chat.nowShow;
		Chat.nowShow = this;
		let container = createElement('div', {style: {margin: '0 0 0 0.75em;'}});
		/*container.addEventListener('scroll', e => {
			let windowRelativeBottom = document.documentElement.getBoundingClientRect().top;
			if (windowRelativeBottom > document.documentElement.clientHeight + 100)
				return;
			console.log('onscroll!');
		})//*/
		document.getElementById('messageform').to.value = this.uid;
		let messages = await this.messages;
		let uname = await this.uname;
		let chat_header = chat_info.previousElementSibling;
		chat_header.innerHTML = '';
		chat_header.append(document.createTextNode(uname));
		messages.map(msg=>this.showMessage(msg, container));
		Chat.messagesbox.innerHTML = '';
		Chat.messagesbox.append(container);
		Chat.root.style.display = 'flex';
	};
	static wipe () {
		Chat.prevShow = Chat.nowShow;
		Chat.nowShow = undefined;
		Chat.root.style.display = 'none';
	}
};


Chat.messagesbox.addEventListener('scroll', e => {
	let mbox = Chat.messagesbox;
	let shiftTop = mbox.scrollHeight - mbox.clientHeight + mbox.scrollTop;
	if (shiftTop > 100)
		return;
	console.log('onscroll!');
})


const router = (event) => {
	let oldHash = (event.oldURL) ? event.oldURL.split("#").slice(1).join('#') : "";
	let oldHashParams = oldHash ? getLocationHashParams(oldHash) : new URLSearchParams();
	let newHashParams = getLocationHashParams();
	let oldSearch = oldHashParams.get('s');
	let newSearch = newHashParams.get('s');
	let search = (oldSearch==newSearch) ? undefined : newSearch;
	let oldChatId = oldHashParams.get('c');
	let newChatId = newHashParams.get('c');
	let chatId = (oldChatId==newChatId) ? undefined : newChatId;
	console.log(search, chatId);
	if (search) {
		searchform.username.value = search;
		let form = new FormData();
		form.set('username', search);
		api.users.search(form, false)
		.then(entryBox.render_query_results);
	}
	if (chatId) {
		let chat = new Chat(chatId);
		chat.render().then( ()=>{
			if (entryBox.nowSelected)
				entryBox.nowSelected.style.background = '#A0A0A0';
			let chatRow = entryBox.chatsPreviews[chatId];
			if (chatRow)
				chatRow.style.background = '#F0F0F0';
			entryBox.nowSelected = chatRow;
		});
	}
	if (oldChatId && !newChatId) {
		Chat.wipe();
		if (entryBox.nowSelected)
			entryBox.nowSelected.style.background = '#A0A0A0';
		entryBox.nowSelected = undefined;
	}
}


function populate() {
	while (true) {
		let windowRelativeBottom = document.documentElement.getBoundingClientRect().bottom;
		if (windowRelativeBottom > document.documentElement.clientHeight + 100)
			break;
		document.body.insertAdjacentHTML("beforeend", `<p>Date: ${new Date()}</p>`);
	}
}

//window.addEventListener('scroll', populate);

//populate(); // инициализация документа

export { entryBox, Chat, setLocationHashParam, router };
