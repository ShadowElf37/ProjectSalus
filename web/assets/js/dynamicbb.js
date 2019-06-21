// Fix the Ma'amad schedule because it sucks ass when scaled down
window.onload = function(){
	let screenWidth = document.documentElement.clientWidth;
	if (screenWidth < 1827) {
		maamadDiv.id = "smaller-maamad-info";

		let helperCenter = document.createElement('center');
		maamadDiv.appendChild(helperCenter);

		maamadTabs = Array.prototype.slice.call(document.getElementsByClassName("maamad-tab"));
		maamadTabs.forEach(function(tab, i, arr){
			maamadDiv.removeChild(tab);
			helperCenter.appendChild(tab);
			tab.className = "smaller-maamad-tab";
		});
	}
};
// window.onresize = window.onload;

// Key bindings!
document.onkeydown = function(e) {
	if (e.key == "ArrowRight" && !arrowNext.disabled) {
		nextScheduleDay();
	} else if (e.key == "ArrowLeft" && !arrowBack.disabled) {
    	lastScheduleDay();
    }
};

// To help clear classes on days with schedule items but no school
var overrideClasses = false;

// Go forward one schedule day
var nextScheduleDay = function(){
	let currentDay = currentDayElem.innerHTML;
	let newDate = new Date(currentDay).addDays(1).dateString()
	arrowBack.disabled = false;
	arrowNext.disabled = newDate==lastDay ? true : false;
	return newScheduleDay(newDate);
}

// Go backwards one schedule day
var lastScheduleDay = function(){
	let currentDay = currentDayElem.innerHTML;
	let newDate = new Date(currentDay).addDays(-1).dateString()
	arrowNext.disabled = false;
	arrowBack.disabled = newDate==firstDay ? true : false;
	return newScheduleDay(newDate);
}

// Set the schedule day, and update the menu and schedule accordingly
var newScheduleDay = function(newDay) {
	overrideClasses = false;
	revertStyle(scheduleDiv, menuDiv, maamadDiv, classInfoDiv);
	
	let newSchedule = schedule[newDay] || {};
	let newScheduleKeys = Object.keys(newSchedule); // Sort by newSchedule['ord'] if necessary
	let newMenu = menu[newDay] || {};

	currentDayElem.innerText = newDay;
	currentDayNumElem.innerText = "";

	var newPeriods = [];

	clear(periodsDiv);
	clear(menuItemsDiv);

	let defaultAllergenStr = ['nothing', 'nothing', ''];

	// No classes for day
	if (newScheduleKeys.length === 0) {
		currentDayNumElem.innerText = "Day of No Class";
		
		let noPeriods = document.createElement('span');
		noPeriods.style = "font-size: 24px;";
		noPeriods.innerText = "No Classes Today";
		periodsDiv.appendChild(noPeriods);

		let noFood = document.createElement('span');
		noFood.style = "font-size: 24px; text-align: left";
		noFood.innerText = "There is no food.";
		menuItemsDiv.appendChild(noFood);

		allergenElems[0].innerText = 'Food will contain ' + defaultAllergenStr[0] + '.';
		allergenElems[1].innerText = 'Food may also contain ' + defaultAllergenStr[1] + '.';
		allergenElems[2].innerText = defaultAllergenStr[2];
		allergenElems[3].innerText = '';

		noClassesRedBorder(scheduleDiv, menuDiv, maamadDiv, classInfoDiv);
		return;
	}

	// Update general allergens
	allergensDefault = allergenElems.map(p => p.innerHTML);
	allergenElems[0].innerText = 'Food will contain ' + (allergenInfo[newDay] || defaultAllergenStr)[0] + '.';
	allergenElems[1].innerText = 'Food may also contain ' + (allergenInfo[newDay] || defaultAllergenStr)[1] + '.';
	allergenElems[2].innerText = (allergenInfo[newDay] || defaultAllergenStr)[2];

	// Update whole menu
	newMenu.forEach(function(foodstuff, i, arr){
		// <span class="{veg}menuitem">{name}</span>
		let menuItem = document.createElement('span')
		menuItem.className = "vegitem menuitem";
		menuItem.innerHTML = foodstuff;

		let allergens = allergenInfo[foodstuff];
		if (allergens.some(function(al){return al[1] == "Vegetarian"})){
			menuItem.className = "menuitem";
		};

		//<p>Food will contain {0}.</p><p>Food may also contain {1}.</p><p>{2}</p><p></p>
		menuItem.onmouseleave = allergensDefaultHover;
		menuItem.onmouseover = function(){
			let allergens = allergenInfo[foodstuff];
			let foodContains = [];
			let foodMayContain = [];
			let xContamWarning = "";
			let veg = "Vegan";

			allergens.forEach(function(al, i, arr){
				switch (al[0]){
					case 0:
						foodContains.push(al[1]);
						break;
					case 1:
						foodMayContain.push(al[1]);
						break;
					case 2:
						xContamWarning = "This item is subject to cross-contamination in oil."
						break;
					case 3:
						if (al[1] == veg == "Vegan") {veg = "Vegetarian"};
						if (al[1] == "Vegetarian") {veg = "Contains meat"};
						break;
				};
			});

			if (foodContains.length > 2) {
				allergenElems[0].innerText = "Item contains " + foodContains.slice(0, -1).join(', ') + ', and ' + foodContains.slice(-1) + "."
			} else if (foodContains.length == 2) {
				allergenElems[1].innerText = "Item contains " + foodMayContain.join(' and ') + '.'
			} else if (foodContains.length == 1) {
				allergenElems[0].innerText = "Item contains " + foodContains[0] + '.'
			} else { allergenElems[0].innerText = "" }

			if (foodMayContain.length > 2) {
				allergenElems[1].innerText = "Item may also contain " + foodMayContain.slice(0, -1).join(', ') + ', and ' + foodMayContain.slice(-1) + "."
			} else if (foodContains.length == 2) {
				allergenElems[1].innerText = "Item may also contain " + foodMayContain.join(' and ') + '.'
			} else if (foodContains.length == 1) {
				allergenElems[1].innerText = "Item may also contain " + foodMayContain[0] + '.'
			} else { allergenElems[1].innerText = "" }

			allergenElems[2].innerText = xContamWarning;
			allergenElems[3].innerText = veg+'.';
		}

		menuItemsDiv.appendChild(menuItem);
	});

	// Update classes
	newScheduleKeys.forEach(function(period, i, arr){
		let data = newSchedule[period];
		let gradeInfo = data ? grades[data['id']] : null;
		if (period == 'DAY'){
			if (currentDayNumElem.innerText=="") {currentDayNumElem.innerText = "Day " + data;};
		}
		else if (period == 'SPECIAL'){
			if (data.length > 0) {
				special = data.join('/').toLowerCase();
				// Something is happening on this day that causes no classes
				if (special.includes('cancel') || special.includes('close') || special.includes('field day')){
					currentDayNumElem.innerText = "Day of No Class";

					let noPeriods = document.createElement('span');
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
				let newPeriodDiv = document.createElement('div');
				newPeriodDiv.className = "class-tab";
				newPeriodDiv.onclick = function(){
					revertStyle
					clickedGreenBorder(newPeriodDiv);
					classInfoName.innerText = data['title'];
					classInfoTime.innerHTML = stripAmPm(stripTimeZeroes(data['start'])) + ' - ' + stripAmPm(stripTimeZeroes(data['end']));
					classInfoTeacher.innerText = gradeInfo['teacher'];
					classInfoEmail.innerText = gradeInfo['teacher-email'] ? gradeInfo['teacher-email'] : 'No email on record.';
				};

				let newPeriodSpan = document.createElement('span');
				newPeriodSpan.className = "period";
				newPeriodSpan.innerText = period;

				let newClassnameSpan = document.createElement('span');
				newClassnameSpan.className = "classname";
				newClassnameSpan.innerText = data['title'];
				
				newPeriodDiv.appendChild(newPeriodSpan);
				newPeriodDiv.appendChild(newClassnameSpan);
				periodsDiv.appendChild(newPeriodDiv);
			}
			else {
				let newPeriodDiv = document.createElement('div');
				newPeriodDiv.className = "null-class";
				newPeriodDiv.innerText = period;

				periodsDiv.appendChild(newPeriodDiv);
			};
		};
	});
};


var styleCache = {};
var greened = null;
var noClassesRedBorder = function(...elems) {
	elems.forEach(function(elem, i, arr){
		if ( !Object.keys(styleCache).includes(elem) ) {
			styleCache[elem] = elem.style;
		};
		elem.style += "; border: 1px solid #f00; box-shadow: 0 0 20px #400;";
	});
};
var clickedGreenBorder = function(elem) {
	if (greened !== null) { revertStyle(greened) };
	if ( !Object.keys(styleCache).includes(elem) ) {
			styleCache[elem] = elem.style;
		};
		elem.style += "; border: 1px solid #0f0; box-shadow: 0 0 20px #030;";
		greened = elem;
}

var revertStyle = function(...elems) {
    elems.forEach(function(elem, i, arr){
        elem.style = styleCache[elem];
    });
};


var updatePoll = function(title, id, questions) {
	let i = currentPollIndex;
	pollTitleElem.innerText = title;
	let q = questions[i];
	pollQuestionElem.innerText = q[0];
	let pollTitleValue = document.createElement('input');
	pollTitleValue.type = "hidden";
	pollTitleValue.name = "_id";
	pollTitleValue.value = id;
	pollOptionsElem.appendChild(pollTitleValue);

	hideInputs(pollOptionsElem);
	array(pollOptionsElem.getElementsByTagName('label')).forEach(function(label, i, arr){
		label.style.display = "none";
	});
	array(pollOptionsElem.getElementsByTagName('br')).forEach(function(br, i, arr){
		br.style.display = "none";
	});

	newQuestionInputs = array(pollOptionsElem.querySelectorAll('input[name="'+q[0]+'"]'));
	if (newQuestionInputs.length != 0){
		newQuestionInputs.forEach(function(input, i, arr){
			input.type = "radio";
			pollOptionsElem.querySelector('label[for="'+input.id+'"]').style.display = "inline-block";
			array(pollOptionsElem.getElementsByClassName('br-'+input.id))[0].style.display = "initial";
		});
	} else {
		q[1].forEach(function(answer, j, arr){
			let newInput = document.createElement('input');
			newInput.type = "radio";
			newInput.name = q[0];
			newInput.value = answer;
			newInput.id = q[0]+'-'+answer.split(' ').join('-');

			let newLabel = document.createElement('label');
			newLabel.htmlFor = q[0]+'-'+answer.split(' ').join('-');
			newLabel.innerText = answer;

			let br = document.createElement('br');
			br.className = 'br-'+q[0]+'-'+answer.split(' ').join('-');

			pollOptionsElem.appendChild(newInput);
			pollOptionsElem.appendChild(newLabel);
			pollOptionsElem.appendChild(br);
		});
	};

	if (i == questions.length-1){
		pollNextButton.disabled = true;
		pollSubmitButton.disabled = false;
		pollBackButton.disabled = false;
	} else if (i == 0) {
		pollBackButton.disabled = true;
		pollSubmitButton.disabled = true;
		pollNextButton.disabled = false;
	} else {
		pollNextButton.disabled = false;
		pollBackButton.disabled = false;
		pollSubmitButton.disabled = true;
	};
}

var pollNextQuestion = function(){
	currentPollIndex++;
	updatePoll(pollTitle, pollDesc, pollQuestions);
}
var pollLastQuestion = function(){
	currentPollIndex--;
	updatePoll(pollTitle, pollDesc, pollQuestions);
}
