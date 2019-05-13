// USAGE:
// <button onclick="sendControlKey('shutdown');"></button>
var sendControlKey = (function() {
    var xhr = new XMLHttpRequest();
    return function(cmd) {
        xhr.open('POST', '/ctrl-words');
        xhr.timeout = 0.1; // there will
        body = 'cmd=' + cmd;
        xhr.send(body);
    };
})();