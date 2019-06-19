var overrideClasses = false;

var nextScheduleDay = function(){
	let currentDay = currentDayElem.innerHTML;
	let newIndex = timespan.indexOf(currentDay) + 1;
	arrowBack.disabled = false;
	if (newIndex==timespan.length-1){
		arrowNext.disabled = true;
	} else{ arrowNext.disabled = false; };
	newScheduleDay(timespan[newIndex]);
}

var lastScheduleDay = function(){
	let currentDay = currentDayElem.innerHTML;
	let newIndex = timespan.indexOf(currentDay) - 1;
	arrowNext.disabled = false;
	if (newIndex==0){
		arrowBack.disabled = true;
	} else{ arrowBack.disabled = false; };
	newScheduleDay(timespan[newIndex]);
}

var newScheduleDay = function(dayStr) {
	overrideClasses = false;
	backToNormalBorder(scheduleDiv, menuDiv, maamadDiv, classInfoDiv);
	
	let newDay = dayStr;
	let newSchedule = schedule[newDay] || {};
	let newScheduleKeys = Object.keys(newSchedule);

	currentDayElem.innerText = newDay;
	currentDayNumElem.innerText = "";

	newPeriods = [];

	while(periodsDiv.firstChild){
	    periodsDiv.removeChild(periodsDiv.firstChild);
	};

	// No classes for day
	if (newScheduleKeys.length === 0) {
		currentDayNumElem.innerText = "Day of No Class";
		
		noPeriods = document.createElement('span');
		noPeriods.style = "font-size: 24px;";
		noPeriods.innerText = "No Classes Today";
		periodsDiv.appendChild(noPeriods);

		noClassesRedBorder(scheduleDiv, menuDiv, maamadDiv, classInfoDiv);
		return;
	}

	newScheduleKeys.forEach(function(period, i, arr){
		data = newSchedule[period];
		if (period == 'DAY'){
			if (currentDayNumElem.innerText=="") {currentDayNumElem.innerText = "Day " + data;};
		}
		else if (period == 'SPECIAL'){
			if (data.length > 0) {
				special = data.join('/').toLowerCase();
				// Something is happening on this day that causes no classes
				if (special.includes('cancel') || special.includes('close') || special.includes('field day')){
					currentDayNumElem.innerText = "Day of No Class";
					console.log(currentDayNumElem.innerText)

					noPeriods = document.createElement('span');
					noPeriods.style = "font-size: 24px";
					noPeriods.innerHTML = unique(newSchedule['SPECIALFMT']).join('<br>');
					periodsDiv.appendChild(noPeriods);

					noClassesRedBorder(scheduleDiv, menuDiv, maamadDiv, classInfoDiv);
					overrideClasses = true;
				};
			};
		} else if (period == 'SPECIALFMT') {} else if (period == 'ORD') {} // dumb shut up
		else if (!overrideClasses){
			if (data['real']) {
				var newPeriodDiv = document.createElement('div');
				newPeriodDiv.className = "class-tab";

				var newPeriodSpan = document.createElement('span');
				newPeriodSpan.className = "period";
				newPeriodSpan.innerText = period;

				var newClassnameSpan = document.createElement('span');
				newClassnameSpan.className = "classname";
				newClassnameSpan.innerText = data['title'];
				
				newPeriodDiv.appendChild(newPeriodSpan);
				newPeriodDiv.appendChild(newClassnameSpan);
				periodsDiv.appendChild(newPeriodDiv);
			}
			else {
				var newPeriodDiv = document.createElement('div');
				newPeriodDiv.className = "null-class";
				newPeriodDiv.innerText = period;

				periodsDiv.appendChild(newPeriodDiv);
			};
		};
	});
};


var styleCache = {};
var noClassesRedBorder = function(...elems) {
	elems.forEach(function(elem, i, arr){
		if ( !Object.keys(styleCache).includes(elem) ) {
			styleCache[elem] = elem.style;
		};
		elem.style = elem.style + "; border: 1px solid #f00; box-shadow: 0 0 20px #400;";
	});
};
var backToNormalBorder = function(...elems) {
	elems.forEach(function(elem, i, arr){
		elem.style = styleCache[elem];
	});
};