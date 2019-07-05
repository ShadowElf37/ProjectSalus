let currentDayElem = document.getElementById('sdatemarker');
let currentDayNumElem = document.getElementById('sdaymarker');
let arrowBack = document.getElementById('slast');
let arrowNext = document.getElementById('snext');
let periodsDiv = document.getElementById('periods');
let scheduleDiv = document.getElementById('schedule-container');
let menuDiv = document.getElementById('sagemenu');
let menuItemsDiv = document.getElementById('menuitems');
let allergenDiv = document.getElementById('allergens');
let allergenElems = Array.prototype.slice.call(allergenDiv.getElementsByTagName('p'));
let maamadDiv = document.getElementById('maamad-info');
let classInfoDiv = document.getElementById('class-info');

let classInfoName = document.getElementById('classname');
let classInfoTime = document.getElementById('start-end');
let classInfoTeacher = document.getElementById('teacher');
let classInfoEmail = document.getElementById('teacher-email');
let nextClassDefault = [classInfoName.innerHTML, classInfoTime.innerHTML, classInfoTeacher.innerHTML, classInfoEmail.innerHTML];

let allergensDefault = allergenElems.map(function(p){return p.innerHTML});

let pollTitleElem = document.getElementById("snack-poll-title");
let pollOptionsElem = document.getElementById("poll-options");
let pollNextButton = document.getElementById("poll-next-button");
let pollSubmitButton = document.getElementById("poll-submit-button");
let pollBackButton = document.getElementById("poll-back-button");
let pollQuestionElem = document.getElementById("question-container");

function nextClassDefaultClick(){
    classInfoName.innerHTML = nextClassDefault[0];
    classInfoTime.innerHTML = nextClassDefault[1];
    classInfoTeacher.innerHTML = nextClassDefault[2];
    classInfoEmail.innerHTML = nextClassDefault[3];
    revertStyle(greened);
};

function allergensDefaultHover(){
    allergenElems.forEach(function(p, i, arr){p.innerHTML = allergensDefault[i]}); //"<p>Food will contain {0}.</p><p>Food may also contain {1}.</p><p>{2}</p>"
}



function putting(name) {
	return function(data){
		window[name] = data;
	};
}

var firstDay, lastDay, schedule, menu, allergenInfo, timespan, grades;

dataLoaded = new Notifier(function(){
	firstDay = timespan[0];
	lastDay = timespan[1];
    console.log('Loaded!')
	newScheduleDay("05/21/2019"); //{{getDate()}}
}, 5);

requestData('schedule', putting('schedule'), dataLoaded);
requestData('menu', putting('menu'), dataLoaded);
requestData('allergens', putting('allergenInfo'), dataLoaded);
requestData('timespan', putting('timespan'), dataLoaded);
requestData('grades', putting('grades'), dataLoaded);

pollLoaded = new Notifier(function(){
	pollTitle = poll[0];
	pollId = poll[1];
	pollQuestions = poll[2];
	currentPollIndex = 0;

	var pollTitleValue = document.createElement('input');
	pollTitleValue.type = "hidden";
	pollTitleValue.name = "_id";
	pollTitleValue.value = pollId;
	document.getElementById("snack-poll-form").appendChild(pollTitleValue);

	updatePoll(pollTitle, pollId, pollQuestions);
})
requestData('poll', putting('poll'), pollLoaded);


document.getElementById('poll-submit-button').addEventListener('click', function(e) {
    e.preventDefault();
    let form = document.getElementById('snack-poll-form');

    for (let input of document.getElementById('poll-options').getElementsByTagName('input')) {
    	input.type = "radio";
    };

    sendForm(form, '/submit-poll');

    clear(form);
    thanksMessage = document.createElement('p');
    thanksMessage.innerText = "Thanks for submitting the form!";
    thanksMessage.style.fontSize = "20px";
    form.appendChild(thanksMessage);
    return false;
});