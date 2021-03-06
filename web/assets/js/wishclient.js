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
	this.xhr.responseType = "text";
	this.cb = next[3];
	this.xhr.send(next[2]);
};
Fetcher.prototype.resolve = function() {
	if(this.xhr.readyState === 4) {
		this.cb(this.xhr.responseText);
		this.next();
	}
};

function WishParser() {
	this.handlers = {};
};
WishParser.prototype.len = 3;
WishParser.prototype.parse = function(block) {
	var lines = block.split('\n');
	console.log(lines);
	for(var i=0; i<lines.length; i++) {
		var chunk, line = lines[i];
		if(!line) continue;
		chunk = line.substring(0, this.len);
		line = atob(line.substring(this.len));
		var handler = this.handlers[chunk];
		if(handler) {
			handler(line);
		}
		else {
			throw new Error("Unknown chunk " + chunk + " at l:" + i + ", tell your sysadmin he's an idiot"); // hey thats me
		}
	}
};
WishParser.prototype.register = function(name, handler) {
	this.handlers[name] = handler;
};

function WishUI(i, o) {
	var self = this;
	this.in = i;
	this.out = o;
	this.output = new Output(o);
	this.cycle = false;
	this.parser = new WishParser();
	this.parser.register("INP", function(data) { self.hdl_inp(data); });
	this.parser.register("OUT", function(data) { self.hdl_out(data); });
	this.fetcher = new Fetcher();
	this.in.addEventListener('keydown', function(ev) {
		if(ev.code === "Enter" || ev.which === 13 || event.keyCode === 13) {
			self.onsubmit();
		}
	});
}
WishUI.prototype.onsubmit = function() {
	var self = this;
	this.in.disabled = true;
	this.hdl_out("$> " + this.in.value, true);
	this.fetcher.fetch("POST", "/wish", "command=" + escape(this.in.value), function(line) {
		self.parser.parse(line);
	});
};
WishUI.prototype.hdl_inp = function(line) {
	this.in.value = line.trim() ? line + ' ' : '';
	this.in.disabled = false;
	this.cycle = true;
	var quote = this.out.lastChild;
	// quote.innerText = "\"" + quote.innerText.trim() + "\"\n\n";
};
WishUI.prototype.hdl_out = function(line) {
	this.output.println(line);
};
