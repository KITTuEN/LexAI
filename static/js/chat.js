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
        analyzeBtn.innerText = 'Analyzing...';

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
                showAnalysis(analysis);
            }
        } catch (error) {
            console.error('Error:', error);
            alert("An error occurred while analyzing your case. Please check your connection and try again.");
        } finally {
            analyzeBtn.disabled = false;
            analyzeBtn.innerText = 'Analyze My Case';
        }
    });

    const showAnalysis = (data) => {
        const modal = document.getElementById('analysisModal');
        const container = document.getElementById('analysisResult');

        container.innerHTML = `
            <h1 class="gold-text">Legal Analysis Result</h1>
            <div class="analysis-section">
                <h3>Case Summary</h3>
                <p>${data.case_summary}</p>
            </div>
            
            <div class="analysis-section next-steps-box">
                <h3 class="step-title"><i class="fas fa-list-ol"></i> Recommended Next Steps</h3>
                <div class="steps-list">
                    ${data.immediate_steps.map((step, index) => `
                        <div class="step-card">
                            <span class="step-num">${index + 1}</span>
                            <p>${step}</p>
                        </div>
                    `).join('')}
                </div>
            </div>

            <div class="analysis-grid">
                <div class="card">
                    <h4><i class="fas fa-gavel"></i> Applicable Sections</h4>
                    ${data.applicable_sections.map(s => `
                        <div class="section-item">
                            <h5>${s.section}: ${s.title}</h5>
                            <p>${s.description}</p>
                            <div class="details-row">
                                <span class="badge ${s.bailable ? 'green' : 'red'}">${s.bailable ? 'Bailable' : 'Non-Bailable'}</span>
                                <span class="badge blue">${s.punishment}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
                <div class="card">
                    <h4><i class="fas fa-shield-alt"></i> Defense Strategies</h4>
                    ${data.defense_strategies.map(s => `
                        <div class="strategy-item">
                            <strong>${s.strategy} (${s.strength})</strong>
                            <p>${s.details}</p>
                        </div>
                    `).join('')}
                </div>
            </div>

            <div class="analysis-section evidence-box">
                <h3><i class="fas fa-folder-open"></i> Evidence to Gather</h3>
                <ul class="evidence-list">
                    ${data.evidence_to_gather.map(item => `<li>${item}</li>`).join('')}
                </ul>
            </div>
        `;
        modal.style.display = 'block';
    };

    document.querySelector('.close-modal').onclick = () => {
        document.getElementById('analysisModal').style.display = 'none';
    };

    scrollToBottom();
    userInput.focus();
});
