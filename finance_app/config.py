import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # SSI FastConnect API Configuration
    AUTH_TYPE = 'Bearer'
    CONSUMER_ID = 'your-consumer-id'  # Lấy từ iBoard SSI
    CONSUMER_SECRET = 'your-consumer-secret'  # Lấy từ iBoard SSI
    API_BASE_URL = 'https://fc-data.ssi.com.vn/'
    STREAM_URL = 'https://fc-datahub.ssi.com.vn/'
    
    # Cấu hình WebSocket
    WS_RECONNECT_INTERVAL = 5  # seconds