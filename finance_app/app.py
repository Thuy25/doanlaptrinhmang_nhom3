from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO
import requests
from ssi_fc_data import fc_md_client, model
import config as api_config
import json
import threading
import time
from ssi_fc_data.fc_md_stream import MarketDataStream  # Giả định import

app = Flask(__name__)
app.config.from_object(api_config)
socketio = SocketIO(app)

# Khởi tạo client SSI API
ssi_client = fc_md_client.MarketDataClient(api_config)

# Biến toàn cục để lưu stream data
stream_data = {}
stream_lock = threading.Lock()

# Route chính
@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', user=session.get('username'), active_tab='dashboard')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # Xác thực đơn giản
        if username == 'admin' and password == 'password':
            session['username'] = username
            return redirect(url_for('home'))
        return render_template('login.html', error='Tên đăng nhập hoặc mật khẩu không đúng')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        email = request.form.get('email', '').strip()
        
        # Xác thực đơn giản - trong thực tế nên lưu vào database
        if username and password and email:
            if username == 'admin':  # Giả định username không trùng
                return render_template('register.html', error='Tên đăng nhập đã tồn tại')
            session['username'] = username
            return redirect(url_for('home'))
        return render_template('register.html', error='Vui lòng điền đầy đủ thông tin')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Các route cho các tab (giữ nguyên từ trước)
@app.route('/place_order')
def place_order():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('place_order.html', user=session.get('username'), active_tab='place_order')

@app.route('/place_order_normal')
def place_order_normal():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('place_order.html', user=session.get('username'), active_tab='place_order')

@app.route('/place_order_agreement')
def place_order_agreement():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('place_order.html', user=session.get('username'), active_tab='place_order')

@app.route('/trade_money')
def trade_money():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('trade_money.html', user=session.get('username'), active_tab='trade_money')

@app.route('/analysis')
def analysis():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('analysis.html', user=session.get('username'), active_tab='analysis')

@app.route('/assets')
def assets():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('assets.html', user=session.get('username'), active_tab='assets')

@app.route('/utilities')
def utilities():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('utilities.html', user=session.get('username'), active_tab='utilities')

# API endpoints (giữ nguyên từ trước)
@app.route('/api/stocks')
def get_stocks():
    try:
        req = model.securities('', 1, 100)
        response = ssi_client.securities(api_config, req)
        if response:
            return jsonify(response)
        return jsonify({'error': 'No data available'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock/<symbol>')
def get_stock_data(symbol):
    try:
        details_req = model.securities_details('', symbol, 1, 1)
        details = ssi_client.securities_details(api_config, details_req)
        
        price_req = model.daily_stock_price(symbol, '', '', 1, 30, '')
        prices = ssi_client.daily_stock_price(api_config, price_req)
        
        if details and prices:
            return jsonify({
                'details': details,
                'prices': prices
            })
        return jsonify({'error': 'No data available'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ohlc/<symbol>')
def get_ohlc_data(symbol):
    try:
        req = model.daily_ohlc(symbol, '', '', 1, 30, True)
        response = ssi_client.daily_ohlc(api_config, req)
        if response:
            return jsonify(response)
        return jsonify({'error': 'No data available'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# WebSocket handlers (giữ nguyên từ trước)
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('subscribe')
def handle_subscribe(data):
    symbol = data.get('symbol')
    if symbol and isinstance(symbol, str) and symbol.strip():
        with stream_lock:
            if not hasattr(app, 'stream_thread') or not app.stream_thread.is_alive():
                start_stream_thread()
            
            stream_data[symbol] = {'last_price': 0, 'change': 0}
            print(f'Subscribed to {symbol}')

def start_stream_thread():
    def stream_worker():
        try:
            stream = MarketDataStream(api_config, ssi_client)
            
            def on_message(message):
                try:
                    data = json.loads(message)
                    content = json.loads(data.get('content', '{}'))
                    
                    symbol = content.get('Symbol')
                    if symbol and symbol in stream_data:
                        last_price = float(content.get('LastPrice', 0))
                        change = float(content.get('Change', 0))
                        
                        with stream_lock:
                            stream_data[symbol] = {
                                'last_price': last_price,
                                'change': change,
                                'data': content
                            }
                        
                        socketio.emit('price_update', {
                            'symbol': symbol,
                            'price': last_price,
                            'change': change
                        })
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    print(f'Error processing stream message: {e}')
            
            def on_error(error):
                print(f'Stream error: {error}')
            
            stream.start(on_message, on_error, 'X-QUOTE:ALL')
            
            while True:
                time.sleep(1)
        except Exception as e:
            print(f'Stream thread error: {e}')
    
    app.stream_thread = threading.Thread(target=stream_worker, daemon=True)
    app.stream_thread.start()

if __name__ == '__main__':
    socketio.run(app, debug=True)