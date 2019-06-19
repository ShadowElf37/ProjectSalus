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

var requestData = (function(name, dowith) {
    var xhr = new XMLHttpRequest();
    xhr.responseType = 'json';
    xhr.onreadystatechange = function() {
	    if (this.readyState == 4 && this.status == 200) {
	       return dowith(this.response);
	    };
	};
    xhr.open('GET', '/data?name='+name);
    xhr.send();
});
