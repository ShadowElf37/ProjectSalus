function lex(string) {
	var split = string.split("\"");
	for(var i=0; i<split.length; i+=2)
		split[i] = split[i].replace(/\s+/g, "\0");
	split[split.length - 1] = split[split.length - 1].replace(/\s+/g, "\0");
	return split.join("").split("\0");
}

function Searcher(input, root, query, subqueries, def="_root", distype="initial") {
	var self = this;
	input.addEventListener("change", function(ev) {
		self.update();
	});
	
	this.input = input;
	this.root = root;
	this.query = query;
	this.def = def;
	if(!subqueries) subqueries = {};
	this.subs = subqueries;
	this.distype = distype;
	this.data = null;
	
	this.count = document.createElement("span");
	this.count.className = "searcher-count";
	this.root.appendChild(this.count);
	this.update();
}

Searcher.prototype.initialize = function() {
	var entries = this.root.querySelectorAll(this.query);
	this.data = [];
	for(var i=0; i<entries.length; i++) {
		var result = {_root: entries[i].innerText.toLowerCase(), _elem: entries[i]};
		for(let key in this.subs) {
			result[key] = entries[i].querySelector(this.subs[key]).innerText.toLowerCase();
		}
		this.data.push(result);
	}
};

Searcher.prototype.update = function() {
	if(!this.data) return;
	var tokens = lex(this.input.value);
	var entries = this.data;
	
	for(var i=0; i<entries.length; i++) {
		entries[i]._elem.style.display = "none";
	}
	this.count.innerText = "Loading...";
	
		console.log(entries);
	for(var i=0; i<tokens.length; i++) {
		var token = tokens[i].toLowerCase(), subsel = this.def;
		for(let key in this.subs) {
			if(token.startsWith(key + ":")) {
				subsel = key;
				token = token.substring(key.length + 1);
				break;
			}
		}
		entries = entries.filter(function(elem) {
			return elem[subsel].includes(token);
		});
		console.log(entries);
	}
	for(var i=0; i<entries.length; i++) {
		entries[i]._elem.style.display = this.distype;
	}
	this.count.innerText = "Found " + entries.length + " results.";
};
