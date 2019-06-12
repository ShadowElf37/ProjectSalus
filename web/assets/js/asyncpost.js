// USAGE:
// <button onclick="sendControlKey('shutdown');"></button>
var sendControlKey = (function() {
    var xhr = new XMLHttpRequest();
    return function(cmd) {
        xhr.open('POST', '/ctrl-words');
        xhr.send("cmd=" + cmd);
        xhr.timeout = 100;
        xhr.ontimeout = function(){};
        console.log('Command sent.');
    };
})();
