// Send a friend request when the button is clicked
function sendFriendRequest(userId) {
    fetch(`/send_friend_request/${userId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(res => res.json())
    .then(data => {
        alert(data.status);
        // Optionally disable the button or change its label
        const button = document.getElementById(`add-friend-btn-${userId}`);
        if (button) {
            button.textContent = 'Request Sent';
            button.disabled = true;
        }
    })
    .catch(err => console.error('Error sending friend request:', err));
}
