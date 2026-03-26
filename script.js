const sessionId = crypto.randomUUID();
let ws = null;
let queue = [];

function connect() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${location.host}/ws/${sessionId}`);
    
    ws.onopen = () => {
        document.getElementById('statusText').textContent = 'Connected';
        document.querySelector('.status-dot').style.background = '#10b981';
        while (queue.length) ws.send(queue.shift());
    };
    
    ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        addMessage('assistant', data.response || 'Done');
        if (data.file_url) addMessage('system', `📎 <a href="${data.file_url}" download style="color:#a855f7;">Download File</a>`);
        if (data.tool_results) data.tool_results.forEach(r => {
            if (r.stdout) addMessage('system', `📟 ${r.stdout.slice(0, 500)}`);
        });
    };
    
    ws.onclose = () => {
        document.getElementById('statusText').textContent = 'Reconnecting...';
        document.querySelector('.status-dot').style.background = '#ef4444';
        setTimeout(connect, 3000);
    };
}

function addMessage(role, content) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = `<div class="content">${content.replace(/\n/g, '<br>').replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')}</div>`;
    document.getElementById('messages').appendChild(div);
    div.scrollIntoView({ behavior: 'smooth' });
}

document.getElementById('sendBtn').onclick = () => {
    const input = document.getElementById('messageInput');
    const msg = input.value.trim();
    if (!msg) return;
    addMessage('user', msg);
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ message: msg }));
    else queue.push(JSON.stringify({ message: msg }));
    input.value = '';
};

document.getElementById('messageInput').onkeydown = (e) => {
    if (e.ctrlKey && e.key === 'Enter') document.getElementById('sendBtn').click();
};

document.getElementById('uploadBtn').onclick = () => document.getElementById('fileInput').click();

document.getElementById('fileInput').onchange = async (e) => {
    for (const file of e.target.files) {
        const fd = new FormData();
        fd.append('file', file);
        fd.append('session_id', sessionId);
        const res = await fetch('/upload', { method: 'POST', body: fd });
        const data = await res.json();
        if (data.success) addMessage('system', `📁 Uploaded: ${data.filename}`);
        loadFiles();
    }
};

async function loadFiles() {
    const res = await fetch(`/files/${sessionId}`);
    const data = await res.json();
    const container = document.getElementById('fileList');
    container.innerHTML = '';
    if (data.files) {
        data.files.forEach(f => {
            const div = document.createElement('div');
            div.className = 'file-item';
            div.innerHTML = `<a href="${f.download_url}" download>📄 ${f.name}</a> <span style="color:#666;">${Math.round(f.size/1024)}KB</span>`;
            container.appendChild(div);
        });
    }
}

connect();
loadFiles();
setInterval(loadFiles, 5000);
