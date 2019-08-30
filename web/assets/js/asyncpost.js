// USAGE:
// <button onclick="sendControlKey('shutdown');"></button>
var sendControlKey = (function() {
    var xhr = new XMLHttpRequest();
    return function(cmd) {
        xhr.open('POST', '/ctrl-words');
        xhr.send("cmd=" + cmd);
        xhr.timeout = 1000;
        xhr.ontimeout = function(){};
        console.log('Command sent.');
    };
})();

var sendForm = (function() {
    console.log('Sending custom form.')
    var xhr = new XMLHttpRequest;
	return function(formElem, dest) {
        xhr.open('POST', dest);
        console.log(formElem);
        var fd = new FormData(formElem);
        var data = [];
        for (item of fd){
            console.log(item);
            if (item[1] instanceof File) {
                item[1] = item[1].name;
            };
            console.log(encodeURI(item.join('=')));
            data.push(encodeURI(item.join('=')).replace(/;/g, '%3B').replace(/&/g, '%26'));
        };
        xhr.timeout = 20000;
        xhr.send(data.join('&'));
    };
})();

function Notifier(cb, target=1) {
	this.callback = cb;
	this.count = 0;
    this.target = target;
    this.result = null;
}
Notifier.prototype.complete = function() {
    if (++this.count >= this.target) {
        this.count = 0;
        this.result = this.callback();
        return this.result;
    }
    return null;
};

function putting(name) {
    return function(data){
        window[name] = data;
        return data;
    };
};

function requestData(name, dowith, notifier=null) {
    var xhr = new XMLHttpRequest();
    xhr.responseType = 'json';
    xhr.onreadystatechange = function() {
	    if (this.readyState == 4 && this.status == 200) {
	    	dowith(this.response);
            notifier.result = this.response;
            if (notifier !== null)
                notifier.complete();
	    };
	};
    xhr.open('GET', '/data?name='+name);
    xhr.send();
}
