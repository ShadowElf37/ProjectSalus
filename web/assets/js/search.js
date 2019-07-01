function lex(string) {
	var split = string.split("\"");
	for(var i=0; i<split.length; i+=2)
		split[i] = split[i].replace(/\s+/g, "\0");
	split[split.length - 1] = split[split.length - 1].replace(/\s+/g, "\0");
	return split.join("").split("\0");
}

function Searcher(input, root, query, subqueries, distype="initial") {
	var self = this;
	input.addEventListener("input", function(ev) {
		self.update();
	});
	
	this.input = input;
	this.root = root;
	this.query = query;
	if(!subqueries) subqueries = {};
	this.subs = subqueries;
	this.distype = distype;
	
	this.count = document.createElement("span");
	this.count.className = "searcher-count";
	this.root.appendChild(this.count);
	this.update();
}

Searcher.prototype.update = function() {
	var tokens = lex(this.input.value);
	var entries = this.root.querySelectorAll(this.query);
	
	for(var i=0; i<entries.length; i++) {
		entries[i].style.display = "none";
	}
	this.count.innerText = "Loading...";
	
	for(var i=0; i<tokens.length; i++) {
		var token = tokens[i].toLowerCase(), subsel = null;
		for(let key in this.subs) {
			if(token.startsWith(key + ":")) {
				subsel = this.subs[key];
				break;
			}
		}
		entries = Array.prototype.slice.call(entries).filter(function(elem) {
			return (subsel ? elem.querySelector(subsel) : elem).innerText.toLowerCase().includes(token);
		});
	}
	for(var i=0; i<entries.length; i++) {
		entries[i].style.display = this.distype;
	}
	this.count.innerText = "Found " + entries.length + " results.";
};
