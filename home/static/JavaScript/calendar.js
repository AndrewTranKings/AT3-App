var date = new Date();
var currentMonth = date.getMonth();
var currentDay = date.getDay();
var currentDate = date.getDate();
var currentYear = date.getFullYear();
var selectedHabitId = null; //Stores the ID of the selected habit
var selectedCategoryId = null; //Stores the category of the selected habit


var months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
];

document.getElementById("title").innerHTML = months[currentMonth];

//GLOW EFFECT FOR COIN INCREASE
function updateCoinCount(newCoinValue) {
    const coinCounter = document.querySelector('.coin_counter');
    const coinSpan = document.getElementById('coin_count');

    if (!coinSpan) return;

    // Get old coin value for comparison
    const oldValue = parseInt(coinSpan.innerText);

    // Update the coin count text
    coinSpan.textContent = newCoinValue;

    // Only animate if coins increased
    if (newCoinValue > oldValue) {
        // Add glow effect class
        if (coinCounter) {
            coinCounter.classList.add('glow');

            // Remove glow class after animation duration (matches CSS duration 1.2s)
            setTimeout(() => {
                coinCounter.classList.remove('glow');
            }, 1200);
        }
    }
}

//DYNAMICALLY UPDATE COIN COUNT ON NAV BAR
function updateCoinDisplay() {
    fetch('/get_user_coins')
        .then(response => response.json())
        .then(data => {
            updateCoinCount(data.coins);
        })
        .catch(err => {
            console.error("Failed to update coin display:", err);
        });
}

var habitTitle = document.getElementById("habitTitle");
habitTitle.onclick = function () {
    let habits = prompt("What's your habit", habitTitle.innerHTML);
    if (habits.length == 0) {
        habitTitle.innerHTML = "Click to set your habit";
    } else {
        habitTitle.innerHTML = habits;
    }
};

function getDaysInMonth(month, year) {
    return new Date(year, month + 1, 0).getDate();

}
var daysInThisMonth = getDaysInMonth(currentMonth, currentYear);
document.getElementById("daysInMonth").textContent = daysInThisMonth;
var daysCompleted = 0;
var totalDays = document.getElementById("totalDays");

/*SETUP CALENDAR DAYS*/
var dayCount = 0;
var rowCount = 0;
var days = document.getElementsByClassName("days");

for (var i = 0; i < days.length; i++) {
    var day = days[rowCount].getElementsByClassName("day");
    for (var j = 0; j < day.length; j++) {
        if (dayCount == currentDate - 1) {
            day[j].setAttribute("style", "color:CornflowerBlue;");
            day[j].setAttribute("style", "border:2px solid black");
        }

        if (dayCount < daysInThisMonth) {
            day[j].innerHTML = dayCount + 1;
            day[j].setAttribute("id", "day" + (dayCount + 1));
            dayCount++;
        } else {
            day[j].innerHTML = "";
            day[j].setAttribute("style", "background-color:white");
        }
    }
    rowCount++;
}

/*UPDATE CALENDAR DEPENDING ON SELECTED HABIT*/
function updateCalendarForSelectedHabit() { //Helper function
    daysInThisMonth = getDaysInMonth(currentMonth, currentYear);
    daysCompleted = 0;

    if (!selectedHabitId) {
        totalDays.innerHTML = `0/${daysInThisMonth}`; //Calculate correct days in the month
        return;
    }
    
    fetch(`/get_habit_logs?habit_id=${selectedHabitId}&month=${currentMonth + 1}&year=${currentYear}`) // ✅ NEW
        .then(response => response.json())
        .then(logs => {
            for (let i = 0; i < currentDate; i++) {
                let dayNum = i + 1;
                let dateKey = `${currentMonth + 1}-${dayNum}-${currentYear}`;
                let dayBox = document.getElementById("day" + dayNum);
                if (!dayBox) continue;

                if (logs.includes(dateKey)) {
                    dayBox.style.backgroundColor = "CornflowerBlue";
                    daysCompleted++;
                } else {
                    dayBox.style.backgroundColor = "white";
                }
            }
            totalDays.innerHTML = `${daysCompleted}/${daysInThisMonth}`;
        })
        .catch(err => {
            console.error("Failed to load habit logs:", err);
        });
}

/*UPDATE XP BAR TO REFLECT USER'S CURRENT XP PROGRESS*/
function updateXPBar(categoryData) {
    document.getElementById("category-name").textContent = categoryData.category_name || "Category";
    document.getElementById("current-level").textContent = categoryData.level;

    //Use total XP directly from backend
    var currentXP = categoryData.current_xp;             // e.g. 130 XP total
    var xpToNextLevel = categoryData.xp_to_next_level;   // e.g. 215 for level 2 → 3

    //PERCENT = totalXP / nextThreshold
    var percent = (currentXP / xpToNextLevel) * 100;
    
    //Update text and bar using total XP value
    document.getElementById("current-xp").textContent = currentXP;
    document.getElementById("xp-to-next-level").textContent = xpToNextLevel;
    document.getElementById("xp-bar-fill").style.width = percent + "%";
}

/*HANDLE CLICK ON CALENDAR DAYS*/
var dayDivs = document.querySelectorAll(".day");
for (let i = 0; i < currentDate; i++) {
    dayDivs[i].onclick = function (e) {
        if (!selectedHabitId) {
            alert("Please select a habit first.");
            return;
        }

        let num = parseInt(e.target.innerText);
        if (isNaN(num)) return;

        let dateKey = `${currentMonth + 1}-${num}-${currentYear}`;
        let selectedDate = document.getElementById("day" + num);
        
        //Find days that are already logged by exact matching cornflowerblue colour
        let currentBgColor = window.getComputedStyle(selectedDate).backgroundColor;
        let wasAlreadyLogged = (currentBgColor === "rgb(100, 149, 237)");
        let markAsCompleted = !wasAlreadyLogged;

        //Immediately update UI to blue or white depending on if already logged or no
        selectedDate.style.backgroundColor = markAsCompleted ? "CornflowerBlue" : "white";
        daysCompleted += markAsCompleted ? 1 : -1;
        totalDays.innerHTML = `${daysCompleted}/${daysInThisMonth}`;

        //Contact with server route of same name
        fetch('/log_habit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                habit_id: selectedHabitId,
                date: dateKey,
                completed: markAsCompleted
            })
        })
        .then(response => response.json())
        .then(data => {
            console.log("Server response:", data);
            if (selectedCategoryId) {
                fetch(`/get_category_progress/${selectedCategoryId}`)
                    .then(res => res.json())
                    .then(updateXPBar)
                    .catch(err => console.error("XP fetch failed after log:", err));
            }
            updateCoinDisplay();
        })
        .catch(err => {
            console.error("Failed to log habit:", err);
            alert("Could not save log to server.");
        });
    };
}

/*RESET BUTTON FUNCTIONALITY*/
var resetButton = document.getElementById("resetButton");
resetButton.onclick = function () {
    if (!selectedHabitId) {
        alert("Select a habit to reset its logs.");
        return;
    }

    //Confirmation before user deletes progress
    if (!confirm("Are you sure you want to reset all logs for this habit this month?")) return;

    fetch('/reset_habit_logs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            habit_id: selectedHabitId,
            month: currentMonth + 1,
            year: currentYear
        })
    })
    .then(res => res.json())
    .then(data => {
        for (var i = 0; i < currentDate; i++) {
            let curDay = document.getElementById("day" + (i + 1));
            if (curDay) curDay.style.backgroundColor = "white";
        }
        daysCompleted = 0;
        totalDays.innerHTML = `${daysCompleted}/${daysInThisMonth}`;
        console.log("Logs reset for habit:", selectedHabitId);
        
        // Refresh XP bar
        if (selectedCategoryId) {
            fetch(`/get_category_progress/${selectedCategoryId}`)
                .then(res => res.json())
                .then(updateXPBar);
        }
    })
    .catch(err => {
        console.error("Failed to reset logs:", err);
        alert("Could not reset logs on the server.");
    });
};

/*HABIT BUTTONS*/
const habitButtons = document.querySelectorAll('.habit_btn');
habitButtons.forEach(button => {
    button.addEventListener('click', () => {
        selectedHabitId = button.getAttribute('data-habit-id');
        selectedCategoryId = button.getAttribute('data-category-id');
        console.log("Selected Habit ID:", selectedHabitId);
        console.log("Selected Category ID:", selectedCategoryId);
        updateCalendarForSelectedHabit();

        //GET XP BAR FOR THAT HABIT'S CATEGORY
        if (selectedCategoryId) {
            fetch(`/get_category_progress/${selectedCategoryId}`)
                .then(res => res.json())
                .then(updateXPBar)
                .catch(err => console.error("Failed to fetch XP progress:", err));
        }

        /*HELPS WITH CSS FOR HIGHLIGHTING SELECTED HABIT*/
        habitButtons.forEach(btn => btn.classList.remove('selected')); //Removes highlight from each button
        button.classList.add('selected'); //Only highlights the selected habit
    });
});

//ONLY ALLOW EDIT AND DELETE ONCE HABIT IS SELECTED
document.querySelectorAll('.habit_btn').forEach(button => {
    button.addEventListener('click', function () {
        selectedHabitId = this.getAttribute('data-habit-id');
        selectedCategoryId = this.getAttribute('data-category-id');

        // Enable buttons
        document.querySelector('.edit_habit_btn').disabled = false;
        document.querySelector('.delete_habit_btn').disabled = false;

        // Update form actions
        document.getElementById('editHabitForm').action = `/edit_habit/${selectedHabitId}`;
        document.getElementById('deleteHabitForm').action = `/delete_habit/${selectedHabitId}`;
    });
});
