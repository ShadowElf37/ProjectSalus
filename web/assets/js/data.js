function putting(name) {
	return function(data){
		window[name] = data;
	};
}

var firstDay, lastDay, schedule, menu, allergenInfo, timespan, grades;

dataLoaded = new Notifier(function(){
	firstDay = timespan[0];
	lastDay = timespan[1];
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

    sendForm(form);

    clear(form);
    thanksMessage = document.createElement('p');
    thanksMessage.innerText = "Thanks for submitting the form!";
    thanksMessage.style.fontSize = "20px";
    form.appendChild(thanksMessage);
    return false;
});