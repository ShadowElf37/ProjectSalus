// USAGE:
// <button onclick="sendControlKey('shutdown');"></button>
var sendControlKey = (function() {
    var xhr = new XMLHttpRequest();
    return function(cmd) {
        xhr.open('POST', '/ctrl-words');
        xhr.timeout = 0.1; // this should cut the connection when the server doesn't respond - otherwise it retries and the request duplicates and it's just a mess
        body = 'cmd=' + cmd;
        xhr.send(body);
    };
})();