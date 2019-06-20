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

function putting(name, notifier=new Notifier()) {
	return function(data){
		window[name] = data;
		notifier.complete()
	};
}

var firstDay, lastDay, schedule, menu, allergenInfo, timespan, grades;

dataLoaded = new Notifier(function(){
	firstDay = timespan[0];
	lastDay = timespan[1];
	newScheduleDay("05/21/2019"); //{{getDate()}}
}, 5);

requestData('schedule', putting('schedule', dataLoaded));
requestData('menu', putting('menu', dataLoaded));
requestData('allergens', putting('allergenInfo', dataLoaded));
requestData('timespan', putting('timespan', dataLoaded));
requestData('grades', putting('grades', dataLoaded));