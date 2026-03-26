const sessionId = crypto.randomUUID();
let ws = null;
let messageQueue = [];

function connect() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${location.host}/ws/${sessionId}`);
    
    ws.onopen = () => {
        document.getElementById('statusText').textContent = 'Connected';
        document.querySelector('.status-dot').style.background = '#10a37f';
        while (messageQueue.length) {
            ws.send(messageQueue.shift());
        }
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        let content = data.response || 'Done';
        
        if (data.execution && data.execution.stdout) {
            content += '\n\n```\n' + data.execution.stdout + '\n```';
        }
        
        addMessage('assistant', content);
    };
    
    ws.onclose = () => {
        document.getElementById('statusText').textContent = 'Reconnecting...';
        document.querySelector('.status-dot').style.background = '#ef4444';
        setTimeout(connect, 3000);
    };
}

function addMessage(role, content) {
    const messagesDiv = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    let formattedContent = content.replace(/\n/g, '<br>');
    formattedContent = formattedContent.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
    
    messageDiv.innerHTML = `<div class="message-content">${formattedContent}</div>`;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

document.getElementById('sendBtn').onclick = () => {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    if (!message) return;
    
    addMessage('user', message);
    
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ message: message }));
    } else {
        messageQueue.push(JSON.stringify({ message: message }));
        connect();
    }
    
    input.value = '';
};

document.getElementById('messageInput').onkeydown = (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
        document.getElementById('sendBtn').click();
    }
};

document.getElementById('uploadBtn').onclick = () => {
    document.getElementById('fileInput').click();
};

document.getElementById('fileInput').onchange = async (e) => {
    for (const file of e.target.files) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('session_id', sessionId);
        
        const response = await fetch('/upload', { method: 'POST', body: formData });
        const result = await response.json();
        
        if (result.success) {
            addMessage('assistant', `📁 Uploaded: ${result.filename} (${Math.round(result.size / 1024)} KB)`);
            loadFiles();
        }
    }
};

async function loadFiles() {
    const response = await fetch(`/files/${sessionId}`);
    const data = await response.json();
    const container = document.getElementById('fileList');
    container.innerHTML = '';
    
    if (data.files && data.files.length) {
        data.files.forEach(file => {
            const div = document.createElement('div');
            div.className = 'file-item';
            div.innerHTML = `
                <a href="${file.download_url}" download>📄 ${file.name}</a>
                <span>${Math.round(file.size / 1024)} KB</span>
            `;
            container.appendChild(div);
        });
    } else {
        container.innerHTML = '<div style="color:#8e8ea0; font-size:0.7rem;">No files</div>';
    }
}

connect();
loadFiles();
setInterval(loadFiles, 3000);
