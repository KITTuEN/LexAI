document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chatMessages');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const typingIndicator = document.getElementById('typingIndicator');
    const analyzeBtn = document.getElementById('analyzeBtn');

    const scrollToBottom = () => {
        setTimeout(() => {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 100);
    };

    const addMessage = (content, role) => {
        const div = document.createElement('div');
        div.className = `message ${role}`;
        div.innerHTML = `
            <div class="bubble">
                ${content}
                <span class="timestamp">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
            </div>
        `;
        chatMessages.appendChild(div);
        scrollToBottom();
    };

    const sendMessage = async () => {
        const message = userInput.value.trim();
        if (!message) return;

        addMessage(message, 'user');
        userInput.value = '';
        typingIndicator.style.display = 'block';

        try {
            const response = await fetch(window.location.pathname.replace('chat', 'message'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
                },
                body: JSON.stringify({ message })
            });
            const data = await response.json();
            typingIndicator.style.display = 'none';
            addMessage(data.response, 'ai');
        } catch (error) {
            console.error('Error:', error);
            typingIndicator.style.display = 'none';
        }
    };

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    analyzeBtn.addEventListener('click', async () => {
        analyzeBtn.disabled = true;
        const originalText = analyzeBtn.innerText;
        analyzeBtn.innerText = '...';

        try {
            const response = await fetch(window.location.pathname.replace('chat', 'analyze'), {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
                }
            });
            const analysis = await response.json();
            if (analysis.error) {
                alert("Analysis failed: " + analysis.error);
            } else {
                if (typeof window.showAnalysis === 'function') {
                    window.showAnalysis(analysis);
                }
            }
        } catch (error) {
            console.error('Error:', error);
            alert("An error occurred. Please try again.");
        } finally {
            analyzeBtn.disabled = false;
            analyzeBtn.innerText = originalText;
        }
    });

    const showAnalysis = (data) => {
        // Obsolete: now handled in template
    };

    document.querySelector('.close-modal').onclick = () => {
        document.getElementById('analysisModal').style.display = 'none';
    };

    scrollToBottom();
    userInput.focus();
});
