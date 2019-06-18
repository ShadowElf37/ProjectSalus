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

var requestData = (function() {
    var xhr = new XMLHttpRequest();
    return function(varname) {
        xhr.open('GET', '/data?name='+varname);
        xhr.send();
        return xhr.response;
    }()});
