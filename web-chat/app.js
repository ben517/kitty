class ChatApp {
    constructor() {
        this.sessionId = null;
        this.isLoading = false;
        this.isSettingsOpen = false;

        this.elements = {
            messages: document.getElementById('chat-messages'),
            input: document.getElementById('message-input'),
            sendBtn: document.getElementById('send-btn'),
            typingIndicator: document.getElementById('typing-indicator'),
            apiBase: document.getElementById('api-base'),
            deviceId: document.getElementById('device-id'),
            deviceType: document.getElementById('device-type'),
            settingsPanel: document.getElementById('settings-panel'),
            settingsToggle: document.getElementById('settings-toggle'),
            clearHistoryBtn: document.getElementById('clear-history')
        };

        this.init();
    }

    init() {
        // Event listeners
        this.elements.sendBtn.addEventListener('click', () => this.sendMessage());
        this.elements.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Settings panel toggle
        this.elements.settingsToggle.addEventListener('click', () => this.toggleSettings());
        
        // Clear history button
        this.elements.clearHistoryBtn.addEventListener('click', () => this.clearHistory());

        // Auto-resize textarea
        this.elements.input.addEventListener('input', () => {
            this.elements.input.style.height = 'auto';
            this.elements.input.style.height = Math.min(this.elements.input.scrollHeight, 120) + 'px';
        });

        // Load saved data
        this.loadFromStorage();

        // Save settings on change
        this.elements.apiBase.addEventListener('change', () => this.saveToStorage());
        this.elements.deviceId.addEventListener('change', () => this.saveToStorage());
        this.elements.deviceType.addEventListener('change', () => this.saveToStorage());

        // Close settings when clicking outside
        document.addEventListener('click', (e) => {
            if (this.isSettingsOpen && 
                !this.elements.settingsPanel.contains(e.target) && 
                !this.elements.settingsToggle.contains(e.target)) {
                this.toggleSettings(false);
            }
        });
    }

    toggleSettings(forceState = null) {
        this.isSettingsOpen = forceState !== null ? forceState : !this.isSettingsOpen;
        this.elements.settingsPanel.style.display = this.isSettingsOpen ? 'block' : 'none';
        this.elements.settingsToggle.classList.toggle('active', this.isSettingsOpen);
    }

    loadFromStorage() {
        const saved = {
            apiBase: localStorage.getItem('apiBase'),
            deviceId: localStorage.getItem('deviceId'),
            deviceType: localStorage.getItem('deviceType'),
            sessionId: localStorage.getItem('sessionId'),
            messages: localStorage.getItem('chatMessages')
        };

        if (saved.apiBase) this.elements.apiBase.value = saved.apiBase;
        if (saved.deviceId) this.elements.deviceId.value = saved.deviceId;
        if (saved.deviceType) this.elements.deviceType.value = saved.deviceType;
        if (saved.sessionId) this.sessionId = saved.sessionId;

        // Load chat history
        if (saved.messages) {
            try {
                const messages = JSON.parse(saved.messages);
                messages.forEach(msg => {
                    this.addMessage(msg.content, msg.type, msg.sources, false);
                });
            } catch (e) {
                console.warn('Failed to load chat history:', e);
            }
        }
    }

    saveToStorage() {
        localStorage.setItem('apiBase', this.elements.apiBase.value);
        localStorage.setItem('deviceId', this.elements.deviceId.value);
        localStorage.setItem('deviceType', this.elements.deviceType.value);
        localStorage.setItem('sessionId', this.sessionId);

        // Save chat history (last 20 messages)
        const messageElements = Array.from(this.elements.messages.children);
        const messages = messageElements.slice(-20).map(el => {
            const content = el.querySelector('.message-content').textContent;
            const type = el.classList.contains('user-message') ? 'user' :
                        el.classList.contains('assistant-message') ? 'assistant' : 'system';
            const sourcesEl = el.querySelector('.message-sources');
            const sources = sourcesEl ? Array.from(sourcesEl.querySelectorAll('li')).map(li => li.textContent) : [];
            return { content, type, sources };
        });
        localStorage.setItem('chatMessages', JSON.stringify(messages));
    }

    clearHistory() {
        if (confirm('确定要清空聊天历史吗？')) {
            this.elements.messages.innerHTML = `
                <div class="message system-message">
                    <div class="message-content">
                        你好！我是智能家居助手，可以帮你查询设备状态、技术参数、操作指南或故障代码。
                    </div>
                </div>
            `;
            this.sessionId = null;
            localStorage.removeItem('chatMessages');
            localStorage.removeItem('sessionId');
        }
    }

    async sendMessage() {
        const message = this.elements.input.value.trim();
        if (!message || this.isLoading) return;

        // Add user message
        this.addMessage(message, 'user');

        // Clear input
        this.elements.input.value = '';
        this.elements.input.style.height = 'auto';

        // Show typing indicator
        this.setLoading(true);

        try {
            const response = await this.callApi(message);
            this.addMessage(response.answer, 'assistant', response.sources);

            // Save session ID for continuity
            if (response.session_id) {
                this.sessionId = response.session_id;
            }
        } catch (error) {
            this.addMessage(`请求失败: ${error.message}`, 'error');
        } finally {
            this.setLoading(false);
        }
    }

    async callApi(query) {
        // Auto-detect API base URL: use current origin if on HTTPS, otherwise use input value or default
        const currentOrigin = window.location.origin;
        const isHttps = currentOrigin.startsWith('https://');
        const inputApiBase = this.elements.apiBase.value.trim();
        const apiBase = isHttps ? currentOrigin : (inputApiBase || 'http://localhost:8000');
        const deviceId = this.elements.deviceId.value.trim() || null;
        const deviceType = this.elements.deviceType.value.trim() || null;

        const payload = {
            query: query,
            session_id: this.sessionId,
            ...(deviceId && { device_id: deviceId }),
            ...(deviceType && { device_type: deviceType })
        };

        const response = await fetch(`${apiBase}/chat/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        return await response.json();
    }

    addMessage(content, type, sources = [], save = true) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        // Format content with line breaks
        contentDiv.innerHTML = this.formatContent(content);

        messageDiv.appendChild(contentDiv);

        // Add sources if available
        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'message-sources';
            sourcesDiv.innerHTML = `
                <strong>参考来源:</strong>
                <ul>${sources.map(s => `<li>${this.escapeHtml(s)}</li>`).join('')}</ul>
            `;
            contentDiv.appendChild(sourcesDiv);
        }

        this.elements.messages.appendChild(messageDiv);
        this.scrollToBottom();
        
        if (save) {
            this.saveToStorage();
        }
    }

    formatContent(content) {
        // Escape HTML
        let formatted = this.escapeHtml(content);

        // Convert line breaks to <br>
        formatted = formatted.replace(/\n/g, '<br>');

        // Convert code blocks
        formatted = formatted.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');

        // Convert inline code
        formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');

        return formatted;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    setLoading(loading) {
        this.isLoading = loading;
        this.elements.sendBtn.disabled = loading;
        this.elements.typingIndicator.style.display = loading ? 'flex' : 'none';
        this.scrollToBottom();
    }

    scrollToBottom() {
        this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});
