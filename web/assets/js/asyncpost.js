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
    var xhr = new XMLHttpRequest;
	return function(formElem, dest) {
        xhr.open('POST', dest);
        console.log(formElem);
        var fd = new FormData(formElem);
        var data = [];
        for (item of fd){
            data.push(item.join('='));
        };
        xhr.timeout = 20000;
        xhr.send(data.join('&'));
    };
})();

function Notifier(cb, target) {
	this.callback = cb;
	this.count = 0;
    this.target = target;
}
Notifier.prototype.complete = function() {
    if (++this.count >= this.target) {
        this.count = 0;
        return this.callback();
    }
    return null;
};

function requestData(name, dowith, notifier=null) {
    var xhr = new XMLHttpRequest();
    xhr.responseType = 'json';
    xhr.onreadystatechange = function() {
	    if (this.readyState == 4 && this.status == 200) {
	    	dowith(this.response);
            if (notifier !== null)
                notifier.complete();
	    };
	};
    xhr.open('GET', '/data?name='+name);
    xhr.send();
}
