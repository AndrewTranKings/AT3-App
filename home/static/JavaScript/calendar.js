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
    let habits = prompt("You can display any text, your choice! (Max 29 characters)", habitTitle.innerHTML);
    if (!habits || habits.length === 0) {
        habitTitle.innerHTML = "Click to write text!";
    } else if (habits.length > 29) {
        alert("Text too long! Please enter 29 characters or less.");
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
function setupCalendar() {
    const tracker = document.getElementById("tracker");
    tracker.innerHTML = "";

    const dayNamesRow = document.createElement("div");
    dayNamesRow.classList.add("day-names");
    const weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    weekdays.forEach(day => {
        const dayDiv = document.createElement("div");
        dayDiv.textContent = day;
        dayNamesRow.appendChild(dayDiv);
    });
    tracker.appendChild(dayNamesRow);

    const daysInMonth = getDaysInMonth(currentMonth, currentYear);
    const firstDay = new Date(currentYear, currentMonth, 1).getDay();

    let dayNum = 1;
    while (dayNum <= daysInMonth) {
        const weekRow = document.createElement("div");
        weekRow.classList.add("days");

        for (let i = 0; i < 7; i++) {
            const cell = document.createElement("div");
            cell.classList.add("day");

            if (tracker.childElementCount === 1 && i < firstDay) {
                cell.innerHTML = "";
            } else if (dayNum <= daysInMonth) {
                cell.innerHTML = dayNum;
                cell.id = "day" + dayNum;
                //Make days keyboard navigable
                cell.setAttribute('tabindex', '0');

                if (dayNum === currentDate) {
                    //The current day is outlined in black
                    cell.style.border = "2px solid black";
                }

                cell.addEventListener("click", function () {
                    if (!selectedHabitId) {
                        alert("Please select a habit first.");
                        return;
                    }

                    let clickedDay = parseInt(this.innerText);
                    if (isNaN(clickedDay)) return; // safeguard

                    //Users can only log until the current day (no logging days that have not happened)
                    if (
                        currentYear === new Date().getFullYear() &&
                        currentMonth === new Date().getMonth() &&
                        clickedDay > currentDate
                    )return;

                    let dateKey = `${currentMonth + 1}-${clickedDay}-${currentYear}`;
                    let currentColor = window.getComputedStyle(this).backgroundColor;
                    let wasLogged = (currentColor === "rgb(100, 149, 237)");
                    let completed = !wasLogged;

                    this.style.backgroundColor = completed ? "CornflowerBlue" : "white";
                    daysCompleted += completed ? 1 : -1;
                    totalDays.textContent = `${daysCompleted}/${daysInMonth}`;

                    fetch('/log_habit', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            habit_id: selectedHabitId,
                            date: dateKey,
                            completed: completed
                        })
                    }).then(response => response.json())
                    .then(data => {
                        if (selectedCategoryId) {
                            fetch(`/get_category_progress/${selectedCategoryId}`)
                                .then(res => res.json())
                                .then(updateXPBar);
                        }
                        updateCoinDisplay();
                    });
                });

                //Can log days by pressing enter or space
                cell.addEventListener("keydown", (event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        cell.click();
                    }
                });

                dayNum++;
            } else {
                cell.innerHTML = "";
            }

            weekRow.appendChild(cell);
        }

        tracker.appendChild(weekRow);
    }
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
//ONLY ALLOW EDIT AND DELETE ONCE HABIT IS SELECTED
const habitButtonsContainer = document.querySelector('.habit_buttons');

habitButtonsContainer.addEventListener('click', (event) => {
    // Check if a .habit_btn was clicked (or inside a .habit_btn)
    const button = event.target.closest('.habit_btn');

    if (!button || !habitButtonsContainer.contains(button)) return;

    // Grab the habit and category IDs from data attributes
    selectedHabitId = button.getAttribute('data-habit-id');
    selectedCategoryId = button.getAttribute('data-category-id');

    console.log("Selected Habit ID:", selectedHabitId);
    console.log("Selected Category ID:", selectedCategoryId);

    //Update the calendar based on selected habit
    updateCalendarForSelectedHabit();

    //Fetch and update XP bar
    if (selectedCategoryId) {
        fetch(`/get_category_progress/${selectedCategoryId}`)
            .then(res => res.json())
            .then(updateXPBar)
            .catch(err => console.error("Failed to fetch XP progress:", err));
    }

    //Highlight selected habit button
    document.querySelectorAll('.habit_btn').forEach(btn => {
        btn.classList.remove('selected');
    });
    button.classList.add('selected');

    //Enable edit/delete buttons
    document.querySelector('.edit_habit_btn').disabled = false;
    document.querySelector('.delete_habit_btn').disabled = false;

    //Update the form's action URLs
    document.getElementById('editHabitForm').action = `/edit_habit/${selectedHabitId}`;
    document.getElementById('deleteHabitForm').action = `/delete_habit/${selectedHabitId}`;
});

//Fade out the flashed message after purchasing an item
document.addEventListener('DOMContentLoaded', () => {
    setupCalendar();
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(msg => {
        setTimeout(() => {
        msg.style.transition = 'opacity 1s ease-out';
        msg.style.opacity = '0';
        setTimeout(() => msg.remove(), 1000);  //Remove from after fading
        }, 3000); //Show for 3 seconds
  });
});

document.addEventListener('DOMContentLoaded', () => {
  const categoryFilter = document.getElementById('category-filter');
  const sortOrder = document.getElementById('sort-order');
  const habitButtonsContainer = document.querySelector('.habit_buttons');

  // Clone the original habit buttons once and keep in an array (master copy)
  const masterHabitButtons = Array.from(habitButtonsContainer.querySelectorAll('.habit_btn')).map(btn => btn.cloneNode(true));

  function filterAndSortHabits() {
    const selectedCategory = categoryFilter.value;
    const selectedSort = sortOrder.value;

    // Filter from the master list to avoid cumulative filtering issues
    let filteredHabits = masterHabitButtons.filter(btn => {
      return selectedCategory === 'all' || btn.dataset.categoryId === selectedCategory;
    });

    // Sort habits
    if (selectedSort === 'alpha-asc') {
      filteredHabits.sort((a, b) => a.textContent.localeCompare(b.textContent));
    } else if (selectedSort === 'alpha-desc') {
      filteredHabits.sort((a, b) => b.textContent.localeCompare(a.textContent));
    }
    // if default, keep master order (no sort)

    // Clear container and append updated buttons
    habitButtonsContainer.innerHTML = '';

    filteredHabits.forEach(btn => {
    // Highlight the correct one based on selectedHabitId
    if (btn.dataset.habitId === selectedHabitId) {
        btn.classList.add('selected');
    } else {
        btn.classList.remove('selected');
    }
    habitButtonsContainer.appendChild(btn);
    });
  }

  categoryFilter.addEventListener('change', filterAndSortHabits);
  sortOrder.addEventListener('change', filterAndSortHabits);
});