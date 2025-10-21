// Chat-specific functionality
class MedicalChat {
    constructor() {
        this.isProcessing = false;
        this.conversationHistory = [];
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadConversationHistory();
    }
    
    bindEvents() {
        // Message sending
        document.getElementById('sendButton')?.addEventListener('click', () => this.sendMessage());
        document.getElementById('userInput')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Quick actions
        document.querySelectorAll('.quick-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const symptom = e.target.dataset.symptom;
                this.insertSymptom(symptom);
            });
        });
        
        // Clear chat
        document.getElementById('clearChat')?.addEventListener('click', () => this.clearChat());
        
        // Export chat
        document.getElementById('exportChat')?.addEventListener('click', () => this.exportChat());
    }
    
    async sendMessage() {
        const userInput = document.getElementById('userInput');
        const message = userInput?.value.trim();
        
        if (!message || this.isProcessing) return;
        
        this.isProcessing = true;
        this.addMessage(message, 'user');
        userInput.value = '';
        
        try {
            const response = await this.getAIResponse(message);
            this.addMessage(response, 'bot');
            this.saveToHistory(message, response);
        } catch (error) {
            this.addMessage('Sorry, I encountered an error. Please try again.', 'bot');
            console.error('Chat error:', error);
        }
        
        this.isProcessing = false;
    }
    
    async getAIResponse(message) {
        // This would typically call your backend API
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
        
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        
        const data = await response.json();
        return data.response;
    }
    
    addMessage(content, sender) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.innerHTML = content;
        
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Add to conversation history
        this.conversationHistory.push({
            sender,
            content,
            timestamp: new Date().toISOString()
        });
    }
    
    insertSymptom(symptom) {
        const userInput = document.getElementById('userInput');
        if (userInput) {
            userInput.value = `I have ${symptom}`;
            userInput.focus();
        }
    }
    
    clearChat() {
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.innerHTML = '';
            this.conversationHistory = [];
            this.addMessage('Hello! How can I help you with your symptoms today?', 'bot');
        }
    }
    
    exportChat() {
        if (this.conversationHistory.length === 0) {
            MedicalApp.showNotification('No chat history to export', 'warning');
            return;
        }
        
        let exportText = 'Medical Assistant Chat History\n\n';
        this.conversationHistory.forEach(entry => {
            const prefix = entry.sender === 'user' ? 'You: ' : 'AI: ';
            const time = new Date(entry.timestamp).toLocaleString();
            exportText += `[${time}] ${prefix}${entry.content}\n\n`;
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
        
        MedicalApp.showNotification('Chat exported successfully!', 'success');
    }
    
    saveToHistory(userMessage, botResponse) {
        // Save to localStorage for persistence
        const history = JSON.parse(localStorage.getItem('medicalChatHistory') || '[]');
        history.push({
            user: userMessage,
            bot: botResponse,
            timestamp: new Date().toISOString()
        });
        
        // Keep only last 50 conversations
        if (history.length > 50) {
            history.shift();
        }
        
        localStorage.setItem('medicalChatHistory', JSON.stringify(history));
    }
    
    loadConversationHistory() {
        const history = JSON.parse(localStorage.getItem('medicalChatHistory') || '[]');
        this.conversationHistory = history.flatMap(entry => [
            { sender: 'user', content: entry.user, timestamp: entry.timestamp },
            { sender: 'bot', content: entry.bot, timestamp: entry.timestamp }
        ]);
    }
}

// Initialize chat when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.medicalChat = new MedicalChat();
});