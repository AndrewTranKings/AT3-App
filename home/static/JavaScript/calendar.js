var date = new Date();
console.log(date);

var currentMonth = date.getMonth();
var currentDay = date.getDay();
var currentDate = date.getDate();
var currentYear = date.getFullYear();

var months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
];

var title = document.getElementById("title");
title.innerHTML = months[currentMonth];

var habitTitle = document.getElementById("habitTitle");
habitTitle.onclick = function () {
    let habits = prompt("What's your habit", habitTitle.innerHTML)
    if(habits.length == 0){
        habitTitle.innerHTML = "Click to set your habit";
    } else{
        habitTitle.innerHTML = habits;
    }
}

var daysInTheMonthList = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
var daysInThisMonth = daysInTheMonthList[currentMonth];

var daysCompleted = 0; /*Change this value back to zero once days completed total fraction problem is solved*/
var totalDays = document.getElementById("totalDays");

/* SETUP CALENDAR DAYS */
var dayCount = 0;
var rowCount = 0;
var days = document.getElementsByClassName("days");

for(var i=0; i < days.length; i++ ){
    var day = days[rowCount].getElementsByClassName("day");
    for (var j=0; j < day.length; j++){
        if (dayCount == currentDate - 1){
            day[j].setAttribute("style", "color:CornflowerBlue;");
            day[j].setAttribute("style", "border:2px solid black");
        }

        if (dayCount < daysInThisMonth){
            day[j].innerHTML = dayCount + 1;
            day[j].setAttribute("id", "day" + (dayCount +1));
            dayCount++;
        } else{
            day[j].innerHTML = "";
            day[j].setAttribute("style", "background-color:white");
        }
    }
    rowCount++;
}

/*INITIALISE COMPLETED ARRAY*/
var completed = new Array(31);
for(var i = 0; i < dayCount; i++){
    var tempString =
        "" + (currentMonth + 1) + "-" + (i + 1) + "-" + currentYear; /*initalise a key with the date*/
        console.log("storing date: " + tempString);
        var tempDay = localStorage.getItem(tempString);
        console.log(tempDay);
        if(tempDay == null || tempDay == "false"){
            localStorage.setItem(tempString, "false");
        } else if(tempDay == "true"){
            daysCompleted++; /*Update 'total days completed' fraction*/
        }
        totalDays.innerHTML = daysCompleted + "/" + daysInThisMonth;
}

console.log("completed array: " + completed);
console.log("total days completed: " + daysCompleted);

/*CHECK LOCAL STORAGE AND UPDATE ARRAY*/
for (var i = 0; i < currentDate; i++){
    var tempString = 
    "" + (currentMonth + 1) + "-" + (i+1) + "-" + currentYear;
    console.log(tempString);

    var chosenDay = localStorage.getItem(tempString);
    console.log(i + 1 + ": " + chosenDay);
    var chosenDayDiv = document.getElementById("day" + (i+1));
    if (chosenDay === "true"){
        chosenDayDiv.style.backgroundColor = "CornflowerBlue"; /*Become blue if habit is completed*/
    } else if (chosenDay === "false"){
        chosenDayDiv.style.backgroundColor = "white"; /*Become white if not completed*/
    }
}

/*UPDATE COMPLETED ON CALENDAR*/
var dayDivs = document.querySelectorAll(".day");
for (var i=0; i<currentDate; i++){ /*Only allows to click up to the current date*/
    dayDivs[i].onclick = function (e) {
        var num = parseInt(e.target.innerText); // Use the text content directly to detect when a day is clicked
        if (isNaN(num)) return; // Prevent clicking on empty cells

        var storageString = (currentMonth + 1) + "-" + num + "-" + currentYear;
        var selectedDate = document.getElementById("day" + num);

        if(localStorage.getItem(storageString) === "false"){
            selectedDate.style.backgroundColor = "CornflowerBlue"; /*Set colour to blue if clicked*/
            localStorage.setItem(storageString, true);
            daysCompleted++;
        } else if(localStorage.getItem(storageString) === "true"){
            selectedDate.style.backgroundColor = "white"; /*Set colour to white if unclickable day is clicked*/
            localStorage.setItem(storageString, false);
            daysCompleted--;
        }

        totalDays.innerHTML = daysCompleted + "/" + dayCount;
    }
}

/*REST BUTTON FUNCTIONALITY */
var resetButton = document.getElementById("resetButton");
resetButton.onclick = function(){
    for (var i = 0; i < dayCount; i++) {
        var tempStrings =
        "" + (currentMonth + 1) + "-" + (i + 1) + "-" + currentYear;
        console.log(tempStrings);
        localStorage.setItem(tempStrings, "false");
        var curDay = document.getElementById("day" + (i +1));
        curDay.style.backgroundColor = "white";
    }
    daysCompleted = 0;
    totalDays.innerHTML = daysCompleted + "/" + daysInThisMonth;
};

