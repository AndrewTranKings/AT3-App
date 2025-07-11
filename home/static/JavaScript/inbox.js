function respondToRequest(requestId, action) {
    fetch(`/respond_friend_request/${requestId}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ action: action })
    }).then(res => {
        if (res.ok) {
            location.reload();
        } else {
            alert("Failed to respond to friend request.");
        }
    });
}
