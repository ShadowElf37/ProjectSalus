'use strict';
function cloneTo(src, dest) {
	for(let property in src) {
		if(src.hasOwnProperty(property) && isNaN(+property)) {
			console.log(property);
			console.log(dest, src);
			dest[property] = src[property];
		}
	}
}
function Output(elem) {
	this.wrap = elem;
	this.tagnodes = {};
	cloneTo({
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
"1	fontWeight:bold\n" +
"2	fontWeight:lighter\n" +
"3	fontStyle:italic\n" +
"4	textDecoration:underline\n" +
"5	animation:0.8s ease-in-out blink alternate infinite\n" +
"6	animation:0.1s ease-in-out blink alternate infinite\n" +
"7	filter:invert(100%)\n" +
"21	fontWeight:normal\n" +
"22	@21\n" +
"23	fontStyle:normal\n" +
"24	textDecoration:none\n" +
"25	animation:none\n" +
"27	filter:none\n" +
"30	color:black\n" +
"31	color:darkred\n" +
"32	color:green\n" +
"33	color:gold\n" +
"34	color:darkblue\n" +
"35	color:darkmagenta\n" +
"36	color:darkcyan\n" +
"37	color:lightgrey\n" +
"39	color:inherit\n" +
"90	color:darkgrey\n" +
"91	color:red\n" +
"92	color:lightgreen\n" +
"93	color:yellow\n" +
"94	color:blue\n" +
"95	color:magenta\n" +
"96	color:cyan\n" +
"97	color:white\n" +
"40	backgroundColor:black\n" +
"41	backgroundColor:darkred\n" +
"42	backgroundColor:green\n" +
"43	backgroundColor:gold\n" +
"44	backgroundColor:darkblue\n" +
"45	backgroundColor:darkmagenta\n" +
"46	backgroundColor:darkcyan\n" +
"47	backgroundColor:lightgrey\n" +
"49	backgroundColor:inherit\n" +
"100	backgroundColor:darkgrey\n" +
"101	backgroundColor:red\n" +
"102	backgroundColor:lightgreen\n" +
"103	backgroundColor:yellow\n" +
"104	backgroundColor:blue\n" +
"105	backgroundColor:magenta\n" +
"106	backgroundColor:cyan\n" +
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
		cloneTo(this.onode.style, nnode.style);
	out.appendChild(nnode);
	this.onode = nnode;
};
Output.prototype.fmtupdate = function(obj) {
	cloneTo(obj, this.onode.style);
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
	var self = this;
	var fragments = str.replace(/\0/g, '').replace(/\x1b\[([0-9;]+)m/g, function(match, nums) {
		var style = {};
		var args = nums.split(';');
		for(var i=0; i<args.length; i++) {
			if(args[i] === '0') {
				console.log('lr');
				style._clear = true;
			}
			else if(self.mongols[args[i]])
				i += self.mongols[args[i]](args.splice(i + 1), function(obj) { return cloneTo(obj, style); });
			else if(self.lut[args[i]])
				cloneTo(self.lut[args[i]], style);
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
