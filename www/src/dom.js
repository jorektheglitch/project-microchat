function isObject(obj) {
	return typeof obj === 'object' && obj !== null;
};

function isArray(obj) {
	return obj instanceof Array;
};

function createElement(tagName, {classList, style, ...options} = {}) {
	let el = document.createElement(tagName);
	if (isArray(classList)) {
		classList.map(className=>el.classList.add(className));
	};
	if (isObject(style)) {
		let styles = el.style;
		Object.entries(style).forEach(([name, value]) => {
			styles.setProperty(name, value);
		});
	};
	if (options.class) {
		el.classList.add(options.class);
	};
	return el;
};

export { createElement };
