window.onload = function () {
	var pc = document.getElementById("page-container");
	var students = document.getElementById("students");
	var teachers = document.getElementById("teachers");
	var width = document.documentElement.clientWidth
	if (width > 1800) {
		pc.style.width = "80%";
		students.style.marginLeft = "5%";
		teachers.style.marginRight = "5%";
	} else if (width > 1500) {
		pc.style.width = "80%";
	};
};