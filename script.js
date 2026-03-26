const sessionId = crypto.randomUUID();
let ws = null;
let currentFile = null;

function connect() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${location.host}/ws/${sessionId}`);
    
    ws.onopen = () => {
        console.log('Connected');
        document.getElementById('sendBtn').disabled = false;
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        addMessage('assistant', data.response);
        document.getElementById('sendBtn').disabled = false;
    };
    
    ws.onclose = () => {
        console.log('Disconnected, reconnecting...');
        setTimeout(connect, 3000);
    };
}

function addMessage(role, content) {
    const messagesDiv = document.getElementById('messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    let formatted = content.replace(/\n/g, '<br>');
    formatted = formatted.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
    
    messageDiv.innerHTML = `<div class="message-content">${formatted}</div>`;
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', sessionId);
    
    const response = await fetch('/upload', { method: 'POST', body: formData });
    const result = await response.json();
    
    if (result.success) {
        addMessage('assistant', `📁 Uploaded: ${result.filename} (${Math.round(result.size / 1024)} KB)`);
        return result.path;
    }
    return null;
}

function showFilePreview(file) {
    const previewDiv = document.getElementById('filePreview');
    const previewItem = document.createElement('div');
    previewItem.className = 'preview-item';
    previewItem.innerHTML = `
        📄 ${file.name} (${Math.round(file.size / 1024)} KB)
        <span class="remove" onclick="this.parentElement.remove(); currentFile = null;">✕</span>
    `;
    previewDiv.innerHTML = '';
    previewDiv.appendChild(previewItem);
}

document.getElementById('sendBtn').onclick = async () => {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    const fileInput = document.getElementById('fileInput');
    
    if (!message && !currentFile) return;
    
    document.getElementById('sendBtn').disabled = true;
    
    if (currentFile) {
        addMessage('user', `📎 ${currentFile.name}`);
        const filePath = await uploadFile(currentFile);
        
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ 
                message: message || `Analyze this file: ${currentFile.name}`,
                file_path: filePath
            }));
        }
        
        currentFile = null;
        document.getElementById('filePreview').innerHTML = '';
    } else if (message) {
        addMessage('user', message);
        
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ message: message, file_path: null }));
        }
    }
    
    input.value = '';
    input.style.height = 'auto';
};

document.getElementById('attachBtn').onclick = () => {
    document.getElementById('fileInput').click();
};

document.getElementById('fileInput').onchange = (e) => {
    const file = e.target.files[0];
    if (file) {
        currentFile = file;
        showFilePreview(file);
    }
    e.target.value = '';
};

document.getElementById('messageInput').onkeydown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        document.getElementById('sendBtn').click();
    }
};

document.getElementById('messageInput').oninput = function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 150) + 'px';
};

connect();
