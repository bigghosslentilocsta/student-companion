document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const chatWindow = document.getElementById('chat-window');

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault(); // Prevent the default form submission

        const userMessage = messageInput.value.trim();
        if (userMessage === '') return;

        // Display the user's message
        appendMessage(userMessage, 'user-message');
        messageInput.value = '';

        // Show a thinking indicator
        const thinkingIndicator = appendMessage('...', 'ai-message thinking');
        
        try {
            // Send the message to the Flask backend
            const response = await fetch('/ask_ai', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: userMessage }),
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            // Replace the thinking indicator with the actual AI response
            thinkingIndicator.innerHTML = `<p>${data.response}</p>`;
            thinkingIndicator.classList.remove('thinking');
            
        } catch (error) {
            console.error('Error:', error);
            thinkingIndicator.innerHTML = `<p>Sorry, an error occurred. Please try again.</p>`;
            thinkingIndicator.classList.remove('thinking');
        }
    });

    function appendMessage(message, className) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${className}`;
        
        const p = document.createElement('p');
        p.innerHTML = message; // Using innerHTML to render line breaks if any
        messageDiv.appendChild(p);

        chatWindow.appendChild(messageDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight; // Auto-scroll to the bottom
        return messageDiv; // Return the element to be modified later
    }
});