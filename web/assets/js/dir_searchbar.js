window.addEventListener('load', function(e){
	var pc = document.getElementById("page-container");
	var width = document.documentElement.clientWidth
	var students = document.getElementById("students");
	var teachers = document.getElementById("teachers");
	if (width > 1800) {
		pc.style.width = "80%";
		students.style.marginLeft = "5%";
		teachers.style.marginRight = "5%";
	} else if (width > 1500) {
		pc.style.width = "80%";
	};

	var studentInput = document.getElementById('student-search');
	var teacherInput = document.getElementById('teacher-search');

	new Searcher(studentInput, students, '.card', {
		'grade': '.grade',
		'address': '.address'
	}, 'block');

	new Searcher(teacherInput, teachers, '.card', {
		'dept': '.dept'
	}, 'block');
});

/*window.onload = function () {
	var pc = document.getElementById("page-container");
	var width = document.documentElement.clientWidth
	var students = document.getElementById("students");
	var teachers = document.getElementById("teachers");
	if (width > 1800) {
		pc.style.width = "80%";
		students.style.marginLeft = "5%";
		teachers.style.marginRight = "5%";
	} else if (width > 1500) {
		pc.style.width = "80%";
	};

	var allStudentCards = students.getElementsByClassName('card');
	var allTeacherCards = teachers.getElementsByClassName('card');

	// Optimization technique; much simpler than searching the element itself for data
	var studentsNameMap = [];
	var studentsGradeMap = {};
	var studentsAddrMap = {};
	for (card of allStudentCards) {
		studentsNameMap.push([card.id, card.getElementsByClassName('name')[0].innerText.toLowerCase()]);
		studentsGradeMap[card.id] = card.getElementsByClassName('grade')[0].innerText.toLowerCase();
		studentsAddrMap[card.id] = card.getElementsByClassName('address')[0].innerText.toLowerCase();
	};

	var teachersNameMap = [];
	var teachersDeptMap = {};
	for (card of allTeacherCards) {
		teachersNameMap.push([card.id, card.getElementsByClassName('name')[0].innerText.toLowerCase()]);
		teachersDeptMap[card.id] = card.getElementsByClassName('dept')[0].innerText.toLowerCase();
	};

	// Search bar elems
	var studentSearch = document.getElementById('student-search');
	var teacherSearch = document.getElementById('teacher-search');

	// When input is received, search the cards
	studentSearch.oninput = function(){
		var input = studentSearch.value.toLowerCase().trim();
		let gradeIndex = input.indexOf('grade:')
		let addrIndex = input.indexOf('address:')
		if (gradeIndex===addrIndex) {
			var grade = null;
			var addr = null;
		} else if (addrIndex===-1) {
			var grade = input.slice(gradeIndex+6).trim()
			var addr = null;
			input = input.slice(0, gradeIndex).trim();
		} else if (gradeIndex===-1) {
			var addr = input.slice(addrIndex+8).trim()
			var grade = null;
			input = input.slice(0, addrIndex).trim();
		} else if (gradeIndex > addrIndex) {
			var grade = input.slice(gradeIndex+6).trim()
			var addr = (addrIndex != -1) ? input.slice(addrIndex+8, gradeIndex).trim() : null;
			input = input.slice(0, addrIndex).trim();
		} else if (gradeIndex < addrIndex) {
			var addr = input.slice(addrIndex+8).trim()
			var grade = (gradeIndex != -1) ? input.slice(gradeIndex+6, addrIndex).trim() : null;
			input = input.slice(0, gradeIndex).trim();
		};

		if (!input && grade===null && addr===null) {
			for (card of allStudentCards) {
				card.style.display = "block";
			};
			return;
		};
		for (cardIdName of studentsNameMap) {
			let id = cardIdName[0];
			let name = cardIdName[1];
			let card = document.getElementById(id);
			if (name.includes(input) && ((grade===null) || studentsGradeMap[id].includes(grade)) && ((addr===null) || studentsAddrMap[id].includes(addr))) {
				card.style.display = "block";
			} else {
				card.style.display = "none";
			};
		};
	};
	teacherSearch.oninput = function(){
		var input = teacherSearch.value.toLowerCase().trim();
		let deptIndex = input.indexOf('dept:')
		var dept = (deptIndex != -1) ? input.slice(deptIndex+5).trim() : null;
		if (dept !== null) {input = input.slice(0, deptIndex)};

		if (!input && dept===null) {
			for (card of allTeacherCards) {
				card.style.display = "block";
			};
			return;
		};
		for (cardIdName of teachersNameMap) {
			let id = cardIdName[0];
			let name = cardIdName[1];
			let card = document.getElementById(id);
			if (name.includes(input) && (dept===null || teachersDeptMap[id].includes(dept))) {
				card.style.display = "block";
			} else {
				card.style.display = "none";
			};
		};
	};
};*/