// ============================================
// DOBBIE - Frontend JavaScript
// ============================================

class DobbieFrontend {
    constructor() {
        this.isListening = false;
        this.recognition = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initSpeechRecognition();
        this.greet();
    }

    setupEventListeners() {
        // Send button
        document.getElementById('send-btn').addEventListener('click', () => this.sendCommand());
        
        // Enter key in input
        document.getElementById('command-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendCommand();
        });

        // Mic button
        document.getElementById('mic-btn').addEventListener('click', () => this.toggleListening());

        // Quick buttons
        document.querySelectorAll('.quick-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const command = btn.dataset.command;
                document.getElementById('command-input').value = command;
                this.sendCommand();
            });
        });
    }

    initSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (SpeechRecognition) {
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.lang = 'en-US';

            this.recognition.onstart = () => {
                this.isListening = true;
                document.getElementById('mic-btn').classList.add('listening');
                this.setStatus('Listening...');
            };

            this.recognition.onresult = (event) => {
                const transcript = Array.from(event.results)
                    .map(result => result[0].transcript)
                    .join('')
                    .trim();

                if (transcript) {
                    document.getElementById('command-input').value = transcript;
                    this.sendCommand();
                }
            };

            this.recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                this.setStatus(`Error: ${event.error}`);
            };

            this.recognition.onend = () => {
                this.isListening = false;
                document.getElementById('mic-btn').classList.remove('listening');
                this.setStatus('Voice ready. Click Mic and speak a command.');
            };
        } else {
            document.getElementById('mic-btn').disabled = true;
            this.setStatus('Voice input not supported in this browser.');
        }
    }

    toggleListening() {
        if (!this.recognition) return;

        if (this.isListening) {
            this.recognition.stop();
        } else {
            this.recognition.start();
        }
    }

    sendCommand() {
        const input = document.getElementById('command-input');
        const command = input.value.trim();

        if (!command) return;

        // Display user message
        this.addMessage('You', command);
        input.value = '';

        // Send to backend
        this.sendToBackend(command);
    }

    async sendToBackend(command) {
        this.setStatus('Processing your command...');

        try {
            const response = await fetch('/api/command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ command: command })
            });

            const data = await response.json();

            if (data.success) {
                this.addMessage('Dobbie', data.response);
                this.setStatus(data.status || 'Ready for your next command.');

                // Handle special actions
                if (data.action) {
                    this.handleAction(data.action);
                }
            } else {
                this.addMessage('Dobbie', '⚠️ Error: ' + (data.error || 'Unknown error'));
                this.setStatus('Error occurred - check the message above.');
                console.error('Dobbie error:', data);
            }
        } catch (error) {
            console.error('Network error:', error);
            this.addMessage('Dobbie', `⚠️ Connection error: ${error.message}`);
            this.setStatus('Connection error - is the server running?');
        }
    }

    handleAction(action) {
        switch (action.type) {
            case 'open_browser':
                window.open(action.url, '_blank');
                break;
            case 'open_file':
                fetch('/api/open-file', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ path: action.path })
                });
                break;
            case 'open_app':
                fetch('/api/open-app', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ app: action.app })
                });
                break;
            case 'check_email':
                this.displayEmails(action.emails);
                break;
        }
    }

    addMessage(sender, text) {
        const log = document.getElementById('conversation-log');
        const time = new Date().toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: true 
        });

        const messageDiv = document.createElement('div');
        messageDiv.className = 'message';
        messageDiv.innerHTML = `
            <span class="message-time">[${time}]</span>
            <span class="message-sender ${sender.toLowerCase()}">${sender}:</span>
            <span class="message-text">${this.escapeHtml(text)}</span>
        `;

        log.appendChild(messageDiv);
        log.scrollTop = log.scrollHeight;
    }

    displayEmails(emails) {
        let emailText = 'Here are your emails, master:\n\n';
        emails.forEach((email, index) => {
            emailText += `${index + 1}. From: ${email.from}\n`;
            emailText += `   Subject: ${email.subject}\n`;
            emailText += `   Preview: ${email.preview}\n\n`;
        });
        this.addMessage('Dobbie', emailText);
    }

    setStatus(text) {
        document.getElementById('status-text').textContent = text;
    }

    greet() {
        const hour = new Date().getHours();
        let greeting = '';

        if (hour < 12) {
            greeting = 'Good morning, master!';
        } else if (hour < 18) {
            greeting = 'Good afternoon, master!';
        } else {
            greeting = 'Good evening, master!';
        }

        this.addMessage('Dobbie', `${greeting} Dobbie welcomes you back. How may Dobbie serve you today?`);
    }

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.dobbie = new DobbieFrontend();
});
