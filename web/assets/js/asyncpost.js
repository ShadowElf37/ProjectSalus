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
	return function(formElem) {
        xhr.open('POST', '/submit-poll');
        var fd = new FormData(formElem);
        var data = [];
        for (let item of fd) { data.push(item.join('=')) };
        xhr.send(data.join('&'));
        xhr.timeout = 1000;
    };
})();

class Notifier{
	constructor(oncomplete=function(){}, awaiting=1){
		this.oncomplete = oncomplete;
		this.value = 0;
		this.awaiting = awaiting;
	}
	complete() {
		this.value++;
		if (this.value == this.awaiting){
			return this.oncomplete();
		};
	}
}

var requestData = (function(name, dowith, notifier=new Notifier()) {
    var xhr = new XMLHttpRequest();
    xhr.responseType = 'json';
    xhr.onreadystatechange = function() {
	    if (this.readyState == 4 && this.status == 200) {
	    	dowith(this.response);
	    	notifier.complete();
	    };
	};
    xhr.open('GET', '/data?name='+name);
    xhr.send();
});
