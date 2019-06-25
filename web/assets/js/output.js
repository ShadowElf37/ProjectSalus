'use strict';
function copy(src, dest) {
	for(let property in src) {
		if(src.hasOwnProperty(property)) {
			dest[property] = src[property];
		}
	}
}
function Output(elem) {
	this.wrap = elem;
	this.tagnodes = {};
	copy({
		overflowY: 'auto',
		fontFamily: 'monospace',
		whiteSpace: 'pre-wrap'
	}, this.wrap.style);
	this.onode = null;
	this.flush(this.wrap);
};
Output.prototype.type = 'span';
Output.parselut = function(str) {
	var result = {};
	var lines = str.split('\n');
	for(var i=0; i<lines.length; i++) {
		if(!lines[i].length) continue;
		var kv = lines[i].split('\t');
		var k = kv[0], v = kv[1];
		var obj = {};
		if(v.startsWith('@')) {
			result[k] = result[v.substring(1)];
			continue;
		}
		var fmts = v.split(';');
		for(let j=0; j<fmts.length; j++) {
			if(!fmts[j].length) continue;
			var kv = fmts[j].split(':');
			obj[kv[0]] = kv[1];
		}
		result[k] = obj;
	}
	return result;
};
Output.prototype.lut = Output.parselut(
"1	fontWeight:bold" +
"2	fontWeight:lighter" +
"3	fontStyle:italic" +
"4	textDecoration:underline" +
"5	animation:0.8s ease-in-out blink alternate infinite" +
"6	animation:0.1s ease-in-out blink alternate infinite" +
"7	filter:invert(100%)" +
"21	fontWeight:normal" +
"22	@21" +
"23	fontStyle:normal" +
"24	textDecoration:none" +
"25	animation:none" +
"27	filter:none" +
"30	color:black" +
"31	color:darkred" +
"32	color:green" +
"33	color:gold" +
"34	color:darkblue" +
"35	color:darkmagenta" +
"36	color:darkcyan" +
"37	color:lightgrey" +
"39	color:inherit" +
"90	color:darkgrey" +
"91	color:red" +
"92	color:lightgreen" +
"93	color:yellow" +
"94	color:blue" +
"95	color:magenta" +
"96	color:cyan" +
"97	color:white" +
"40	backgroundColor:black" +
"41	backgroundColor:darkred" +
"42	backgroundColor:green" +
"43	backgroundColor:gold" +
"44	backgroundColor:darkblue" +
"45	backgroundColor:darkmagenta" +
"46	backgroundColor:darkcyan" +
"47	backgroundColor:lightgrey" +
"49	backgroundColor:inherit" +
"100	backgroundColor:darkgrey" +
"101	backgroundColor:red" +
"102	backgroundColor:lightgreen" +
"103	backgroundColor:yellow" +
"104	backgroundColor:blue" +
"105	backgroundColor:magenta" +
"106	backgroundColor:cyan" +
"107	backgroundColor:white"
);
Output.prototype.mongols = {
	'38': function(args, out) {
		switch(args[0]) {
		case '2':
			out({color: `rgb(${args.slice(1, 4).join(',')})`});
			return 4;
		default:
			return 0;
		}
	},
	'48': function(args, out) {
		switch(args[0]) {
		case '2':
			out({backgroundColor: `rgb(${args.slice(1, 4).join(',')})`});
			return 4;
		default:
			return 0;
		}
	},
};
Output.prototype.flush = function(out) {
	var nnode = document.createElement(this.type);
	if(this.onode !== null)
		copy(this.onode.style, nnode.style);
	out.appendChild(nnode);
	this.onode = nnode;
};
Output.prototype.fmtupdate = function(obj) {
	copy(obj, this.onode.style);
};
Output.prototype.fmtclear = function() {
	this.onode.style = '';
};
Output.prototype.taginit = function(tag) {
	var pnode = this.tagnodes[tag];
	if(!tag)
		pnode = this.wrap;
	else if(pnode) {
		var first = pnode.firstChild;
		while(pnode.firstChild)
			pnode.removeChild(pnode.firstChild);
		this.onode = first;
	}
	else {
		pnode = this.tagnodes[tag] = document.createElement(this.type);
		pnode.id = 'tag-' + tag;
		this.wrap.appendChild(pnode);
		
	}
	this.flush(pnode);
	this.onode = pnode.lastChild;
	return pnode;
};
Output.prototype._print = function(str) {
	this.onode.appendChild(document.createTextNode(str));
};
Output.prototype.print = function(str, tag) {
	var styles = [];
	var fragments = str.replace(/\0/g, '').replace(/\x1b\[([0-9;]+)m/g, function(match, nums) {
		var style = {};
		var args = nums.split(';');
		for(var i=0; i<args.length; i++) {
			if(args[i] === '0') {
				style._clear = true;
			}
			else if(this.mongols[args[i]])
				i += this.mongols[args[i]](args.splice(i + 1), function(obj) { return copy(obj, style); });
			else if(this.lut[args[i]])
				copy(this.lut[args[i]], style);
		}
		styles.push(style);
		return '\0';
	}).split('\0');
	var out = this.taginit(tag);
	this._print(fragments[0]);
	for(var i=0; i<styles.length; i++) {
		this.flush(out);
		if(styles[i]._clear)
			this.fmtclear();
		else
			this.fmtupdate(styles[i]);
		this._print(fragments[i + 1]);
	}
	this.wrap.scrollTop = this.wrap.scrollHeight - this.wrap.clientHeight;
};
Output.prototype.println = function(str, tag) {
	this.print(str + '\n', tag);
};
