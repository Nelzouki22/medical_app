// Dashboard functionality
document.addEventListener('DOMContentLoaded', function() {
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    const chatMessages = document.getElementById('chatMessages');
    const quickButtons = document.querySelectorAll('.quick-btn');
    
    // Auto-focus on input
    if (userInput) {
        userInput.focus();
    }
    
    // Add message to chat
    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.innerHTML = message;
        
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Send message function
    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;
        
        // Add user message
        addMessage(message, true);
        userInput.value = '';
        
        // Show loading indicator
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message bot-message';
        loadingDiv.innerHTML = `
            <div class="message-content">
                <i class="fas fa-spinner fa-spin"></i> Analyzing symptoms...
            </div>
        `;
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    message: message,
                    language: 'en'
                })
            });
            
            // Remove loading indicator
            loadingDiv.remove();
            
            const data = await response.json();
            addMessage(data.response);
            
        } catch (error) {
            // Remove loading indicator
            loadingDiv.remove();
            
            addMessage(`
                <div class="error-message">
                    <strong>Error:</strong> Sorry, there was an error processing your request. 
                    Please try again.
                </div>
            `);
            console.error('Error:', error);
        }
    }
    
    // Event listeners
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }
    
    if (userInput) {
        userInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
    
    // Quick symptoms buttons
    quickButtons.forEach(button => {
        button.addEventListener('click', function() {
            const symptom = this.getAttribute('data-symptom');
            userInput.value = `I have ${symptom}`;
            sendMessage();
        });
    });
    
    // Appointment form handling
    const appointmentForm = document.querySelector('.appointment-form');
    if (appointmentForm) {
        appointmentForm.addEventListener('submit', function(e) {
            const appointmentDate = this.querySelector('input[type="datetime-local"]');
            const now = new Date();
            const selectedDate = new Date(appointmentDate.value);
            
            if (selectedDate <= now) {
                e.preventDefault();
                alert('Please select a future date and time for your appointment.');
                appointmentDate.focus();
            }
        });
    }
    
    // History item click handler
    const historyItems = document.querySelectorAll('.history-item');
    historyItems.forEach(item => {
        item.addEventListener('click', function() {
            const question = this.querySelector('.history-question').textContent;
            userInput.value = question;
            sendMessage();
        });
    });
    
    // Auto-adjust textarea height
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    });
    
    // Real-time date validation for appointments
    const dateInputs = document.querySelectorAll('input[type="datetime-local"]');
    dateInputs.forEach(input => {
        // Set min date to current datetime
        const now = new Date();
        const localDateTime = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
            .toISOString()
            .slice(0, 16);
        input.min = localDateTime;
        
        input.addEventListener('change', function() {
            const selectedDate = new Date(this.value);
            if (selectedDate <= now) {
                this.setCustomValidity('Please select a future date and time.');
            } else {
                this.setCustomValidity('');
            }
        });
    });
});

// Additional dashboard utilities
const DashboardUtils = {
    // Format appointment date
    formatAppointmentDate: (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            weekday: 'short',
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },
    
    // Update appointment status
    updateAppointmentStatus: (appointmentId, status) => {
        // This would typically make an API call to update the status
        console.log(`Updating appointment ${appointmentId} to ${status}`);
        MedicalApp.showNotification(`Appointment status updated to ${status}`, 'success');
    },
    
    // Export chat history
    exportChatHistory: () => {
        const chatMessages = document.querySelectorAll('.message-content');
        let exportText = 'AI Medical Assistant - Chat History\n\n';
        
        chatMessages.forEach((message, index) => {
            const isUser = message.closest('.user-message');
            const prefix = isUser ? 'You: ' : 'AI: ';
            exportText += `${prefix}${message.textContent}\n\n`;
        });
        
        const blob = new Blob([exportText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `medical-chat-${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        MedicalApp.showNotification('Chat history exported successfully!', 'success');
    }
};