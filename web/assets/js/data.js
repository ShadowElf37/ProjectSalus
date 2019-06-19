class Notifier{
	constructor(oncomplete=function(){}){
		this.oncomplete = oncomplete;
		this.value = false;
	}
	complete() {
		this.value = true;
		return this.oncomplete();
	}
}

function putting(name, notifier=new Notifier()) {
	return function(data){
		window[name] = data;
		notifier.complete()
	};
}


scheduleLoaded = new Notifier(function(){console.log('Schedule loaded')});
menuLoaded = new Notifier();

requestData('WEEKSCHEDULE', putting('schedule', scheduleLoaded));
requestData('WEEKMENU', putting('menu', menuLoaded));
requestData('WEEK', putting('timespan'));

