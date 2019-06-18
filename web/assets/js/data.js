var requestData = (function(name, into) {
    var xhr = new XMLHttpRequest();
    xhr.responseType = 'json';
    xhr.onreadystatechange = function() {
	    if (this.readyState == 4 && this.status == 200) {
	       // Typical action to be performed when the document is ready:
	       window[into] = this.response;
	    }
	};
    xhr.open('GET', '/data?name='+name);
    xhr.send();
    // return test;
});

requestData('WEEKSCHEDULE', 'schedule');
requestData('WEEKMENU', 'menu');