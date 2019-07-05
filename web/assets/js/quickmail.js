#include lib.js
#include asyncpost.js
#include fileify.js
// THIS FILE INCLUDES lib.js AND asyncpost.js
// TO AVOID CONFLICTS, DO NOT REQUEST THESE FILES SEPARATELY
// DO SO AT YOUR OWN RISK

window.addEventListener('load', function(e){
	// Now we can make the sendbox
	var sendBox = document.createElement('div');
	sendBox.classList.add('--qm-send-box');
	sendBox.id = "--qm-global-send-box";
	sendBox.style.display = "none";

	// Make the form
	var form = document.createElement('form');
	form.id = "--qm-form";
	form.enctype = "multipart/form-data";

	// Form innards
	var insideForm = '\
	<input type="text" value="" name="to" id="--qm-to" autocomplete=off>\
	<input type="text" value="" name="subject" id="--qm-subject" autocomplete=off>\
	<label style="top: 17px">To: </label><label style="top: 60px">Subject: </label>\
	';

	// Unfortunately there's another <center> we need to add to the form manually
	var center = document.createElement('center');

	// And then the textarea, but textarea is gay so let's make a div
	var bodyInputDiv = document.createElement('div');
	bodyInputDiv.classList.add('--qm-send-box-body');
	bodyInputDiv.contentEditable = true;
	bodyInputDiv.id = "--qm-send-box-body";

	// Hidden input to capture that textarea
	var bodyInput = document.createElement('input');
	bodyInput.hidden = true;
	bodyInput.id = "--qm-send-box-body-input";
	bodyInput.name = "body";

	// Attachments!
	var attachmentInput = document.createElement('input');
	attachmentInput.type = "file";
	attachmentInput.classList.add('--qm-attach');
	attachmentInput.id = '--qm-attach'
	attachmentInput.name = 'attachments'
	attachmentInput.multiple = true;

	// Make the submit button with some async
	var submit = document.createElement('input');
	submit.type = "submit";
	submit.value = "Send Email";
	submit.id = "--qm-send";
	submit.addEventListener('click', function(e){
		e.preventDefault();
		// Grab body div value and stuff it in my input
		document.getElementById("--qm-send-box-body-input").value = document.getElementById("--qm-send-box-body").innerHTML;
		sendForm(form, '/mail');
		document.getElementById("--qm-global-send-box").style.display = "none";
	});

	// Submit, BodyInput, Attachments => Center, Autocomplete => Form => Box
	form.innerHTML = insideForm;
	center.appendChild(bodyInputDiv);
	center.appendChild(bodyInput);
	center.appendChild(attachmentInput);
	center.appendChild(submit);
	form.appendChild(center);
	form.appendChild(options);
	sendBox.appendChild(form);
	// Brush the box under the carpet
	document.documentElement.appendChild(sendBox);

	// Draggable window, very fancy
	makeDraggable(sendBox, 'center', 'form', 'label');
	// Fileify, very fancy
	fileify(form);

	// Give click event to all the quickable emails in document
	var quickies = document.querySelectorAll('.--qm-email');
	for (var i=0; i < quickies.length; i++) {
		if (!quickies[i].innerText.includes('@')){
			quickies[i].classList.remove('--qm-email');
			continue;
		};
		quickies[i].addEventListener('click', function(e){
			openSendBox(this);
		});
	};

	// Done!
});

// Clickaway
document.addEventListener('mousedown', function(e){
	// console.log(e.target);
	var sendBox = document.getElementById("--qm-global-send-box");
	// If we're not clicking something in the sendbox, or the sendbox, or the link to open the sendbox,
	if (!isDescendant(sendBox, e.target) && e.target != sendBox && !array(e.target.classList).includes('--qm-email')) {
		// Then hide the sendbox
		sendBox.style.display = "none";
	};
});

function openSendBox(onElem) {
	var address = onElem.innerText;
	var sendBox = document.getElementById("--qm-global-send-box");
	var parent = onElem.parentNode;
	var parentIsContainer = array(parent.classList).includes("--qm-send-box-container");

	sendBox.querySelector('#--qm-to').value = address + ", ";

	// Make a new container for nicer positioning
	var container = document.createElement('span');
	container.className = "--qm-send-box-container";

	if (parentIsContainer) { // If we've already gone through this
		parent.parentNode.insertBefore(container, parent);
	} else { // If we've never stuck the box on it before
		parent.insertBefore(container, onElem);
	};
	// Kill the original element
	parent.removeChild(onElem);

	// Go around earlier container if it exists because it's cancerous
	sendBox.parentNode.removeChild(sendBox);

	// Now dump the original element and the box in our container
	container.appendChild(onElem);
	container.appendChild(sendBox);
	
	// Kill the last container
	if (parentIsContainer) {
		parent.parentNode.removeChild(parent);
	};

	sendBox.style.display = "block";
};