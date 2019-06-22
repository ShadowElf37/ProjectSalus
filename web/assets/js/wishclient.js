function Fetcher() {
	var self = this;
	this.xhr = new XMLHttpRequest();
	this.xhr.onreadystatechange = function() {
		self.resolve();
	};
	this.queue = [];
	this.cb = null;
}
Fetcher.prototype.fetch = function(method, url, data, cb) {
	this.queue.push([method, url, data, cb]);
	this.next();
};
Fetcher.prototype.next = function() {
	if(!this.queue.length) return;
	var next = this.queue[0];
	this.queue = this.queue.slice(1);
	this.xhr.open(next[0], next[1]);
	this.cb = next[3];
	this.xhr.send(next[2]);
};
Fetcher.prototype.resolve = function() {
	if(this.xhr.readyState === 4) {
		this.cb(xhr.responseText);
		this.next();
	}
};

function WishParser() {
	this.handlers = {};
};
WishParser.prototype.len = 3;
WishParser.prototype.parse = function(block) {
	var lines = block.split('\n');
	for(var i=0; i<lines.length; i++) {
		var chunk, line = lines[i];
		if(!line) continue;
		chunk = line.substring(0, this.len);
		line = line.substring(this.len).trim();
		var handler = this.handlers[chunk];
		if(handler) {
			handler(line);
		}
		else {
			throw new Error("Unknown chunk " + chunk + " at l:" + i + ", tell your sysadmin he's an idiot");
		}
	}
};
WishParser.prototype.register = function(name, handler) {
	this.handlers[name] = handler;
};

function WishUI(i, o) {
	this.in = i;
	this.out = o;
	this.out.style.whiteSpace = "pre-wrap";
	this.parser = new WishParser();
	this.parser.register("INP", this.hdl_inp);
	this.parser.register("OUT", this.hdl_out);
	this.fetcher = new Fetcher();
	this.out.addEventListener('keypress', function(ev) {
		if(ev.which === 13 || event.keyCode === 13) {
			this.onsubmit();
		}
	});
}
WishUI.prototype.onsubmit = function() {
	this.in.disabled = true;
	this.fetcher.fetch("POST", "/wish", this.in.value, function(line) {
		this.parser.parse(line);
	});
};
WishUI.prototype.hdl_inp = function(line) {
	this.in.value = line;
	this.in.disabled = false;
};
WishUI.prototype.hdl_out = function(line) {
	this.out.insertBefore(document.createTextNode(line), this.out.firstChild);
};
