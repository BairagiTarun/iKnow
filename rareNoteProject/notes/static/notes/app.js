document.getElementById('send-button').addEventListener('click', function() {
    const inputField = document.getElementById('chat-input');
    const message = inputField.value.trim();
    
    if (message) {
        displayMessage(message, 'user-message');
        inputField.value = '';  // Clear the input field
        sendMessageToBackend(message);
    }
});

function displayMessage(message, className) {
    const chatBox = document.getElementById('chat-box');
    const messageDiv = document.createElement('div');
    messageDiv.className = className;
    messageDiv.textContent = message;
    chatBox.appendChild(messageDiv);
}

function sendMessageToBackend(message) {
    fetch('/chat/', {  // Ensure your URL pattern matches this path
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message }),
    })
    .then(response => response.json())
    .then(data => {
        displayMessage(data.response, 'bot-message');
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
