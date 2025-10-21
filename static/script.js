document.addEventListener('DOMContentLoaded', function() {
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    const chatMessages = document.getElementById('chatMessages');
    const symptomCount = document.getElementById('symptomCount');
    const quickButtons = document.querySelectorAll('.quick-btn');

    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.innerHTML = message;
        
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        addMessage(message, true);
        userInput.value = '';

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();
            addMessage(data.response);
            
            // Update symptom count
            symptomCount.textContent = data.symptoms_found.length;
            
        } catch (error) {
            addMessage('Sorry, there was an error processing your request. Please try again.');
        }
    }

    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Quick symptoms buttons
    quickButtons.forEach(button => {
        button.addEventListener('click', function() {
            const symptom = this.getAttribute('data-symptom');
            userInput.value = `I have ${symptom}`;
            sendMessage();
        });
    });

    // Auto-focus on input
    userInput.focus();
});