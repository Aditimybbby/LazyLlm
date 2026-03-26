const sessionId = localStorage.getItem('sessionId') || crypto.randomUUID();
localStorage.setItem('sessionId', sessionId);

let ws = null;
let messageQueue = [];

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId}`;
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        document.getElementById('statusIndicator').style.background = '#10b981';
        document.getElementById('statusText').textContent = 'Connected';
        
        while (messageQueue.length) {
            ws.send(messageQueue.shift());
        }
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        addMessage('assistant', data);
        
        if (data.files_generated && data.files_generated.length) {
            data.files_generated.forEach(file => {
                addDownloadLink(file);
            });
        }
        
        if (data.file_url) {
            addMessage('system', `📎 File generated: <a href="${data.file_url}" download class="download-btn">Download ${data.file_url.split('/').pop()}</a>`);
        }
        
        if (data.execution_output) {
            addMessage('system', `📟 Execution Output:\n\`\`\`\n${data.execution_output}\n\`\`\``);
        }
        
        if (data.thinking) {
            const thinkingDiv = document.createElement('div');
            thinkingDiv.className = 'thinking';
            thinkingDiv.innerHTML = `🧠 Thinking: ${data.thinking}`;
            document.getElementById('messages').appendChild(thinkingDiv);
        }
    };
    
    ws.onclose = () => {
        document.getElementById('statusIndicator').style.background = '#ef4444';
        document.getElementById('statusText').textContent = 'Reconnecting...';
        setTimeout(connectWebSocket, 3000);
    };
}

function addMessage(role, content) {
    const messagesDiv = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    let contentHtml = '';
    if (typeof content === 'string') {
        contentHtml = content.replace(/\n/g, '<br>');
    } else {
        contentHtml = content.response || JSON.stringify(content, null, 2);
        if (content.files_generated) {
            contentHtml += '<br><br>📁 Files generated:<br>';
            content.files_generated.forEach(f => {
                contentHtml += `- ${f.name}<br>`;
            });
        }
    }
    
    contentHtml = contentHtml.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
        return `<pre><code class="language-${lang}">${escapeHtml(code)}</code></pre>`;
    });
    
    messageDiv.innerHTML = `<div class="message-content">${contentHtml}</div>`;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function addDownloadLink(file) {
    const messagesDiv = document.getElementById('messages');
    const linkDiv = document.createElement('div');
    linkDiv.className = 'message system';
    linkDiv.innerHTML = `<div class="message-content">📄 <strong>${file.name}</strong><br><a href="/download/${sessionId}/${file.name}" download class="download-btn">Download File</a></div>`;
    messagesDiv.appendChild(linkDiv);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

document.getElementById('sendButton').addEventListener('click', () => {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    if (!message) return;
    
    addMessage('user', message);
    
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ message: message }));
    } else {
        messageQueue.push(JSON.stringify({ message: message }));
        connectWebSocket();
    }
    
    input.value = '';
});

document.getElementById('messageInput').addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
        document.getElementById('sendButton').click();
    }
});

document.getElementById('uploadButton').addEventListener('click', () => {
    document.getElementById('fileInput').click();
});

document.getElementById('fileInput').addEventListener('change', async (e) => {
    const files = e.target.files;
    for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('session_id', sessionId);
        
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        if (result.success) {
            addMessage('system', `📁 Uploaded: ${result.filename}`);
            loadFiles();
        }
    }
});

async function loadFiles() {
    const response = await fetch(`/files/${sessionId}`);
    const data = await response.json();
    const fileList = document.getElementById('fileList');
    fileList.innerHTML = '';
    
    if (data.files) {
        data.files.forEach(file => {
            const div = document.createElement('div');
            div.className = 'file-item';
            div.innerHTML = `<a href="${file.download_url}" download>📄 ${file.name}</a> <span style="font-size:0.7rem; color:#666;">${Math.round(file.size/1024)}KB</span>`;
            fileList.appendChild(div);
        });
    }
}

connectWebSocket();
loadFiles();
setInterval(loadFiles, 5000);
