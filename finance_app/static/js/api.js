class SSIApi {
    constructor() {
        this.baseUrl = '/api';
        this.socket = io();
        this.currentStock = null;
        this.priceChart = null;
    }

    async getStocks() {
        try {
            const response = await fetch(`${this.baseUrl}/stocks`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching stocks:', error);
            return [];
        }
    }

    async getStockData(symbol) {
        try {
            const response = await fetch(`${this.baseUrl}/stock/${symbol}`);
            return await response.json();
        } catch (error) {
            console.error(`Error fetching data for ${symbol}:`, error);
            return null;
        }
    }

    async getOHLCData(symbol) {
        try {
            const response = await fetch(`${this.baseUrl}/ohlc/${symbol}`);
            return await response.json();
        } catch (error) {
            console.error(`Error fetching OHLC data for ${symbol}:`, error);
            return null;
        }
    }

    subscribeToStock(symbol) {
        this.socket.emit('subscribe', { symbol: symbol });
    }

    setupSocketListeners() {
        this.socket.on('price_update', (data) => {
            this.updateStockPrice(data.symbol, data.price, data.change);
            
            if (this.currentStock && this.currentStock.symbol === data.symbol) {
                this.updateCurrentStock(data);
            }
        });

        this.socket.on('connect', () => {
            console.log('Connected to WebSocket server');
            if (this.currentStock) {
                this.subscribeToStock(this.currentStock.symbol);
            }
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from WebSocket server');
        });
    }

    updateStockPrice(symbol, price, change) {
        const stockElements = document.querySelectorAll(`.stock-item[data-symbol="${symbol}"]`);
        
        stockElements.forEach(element => {
            const priceElement = element.querySelector('.stock-price');
            const changeElement = element.querySelector('.stock-change');
            
            if (priceElement) priceElement.textContent = price.toLocaleString();
            if (changeElement) {
                changeElement.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
                changeElement.className = `stock-change badge ${change >= 0 ? 'bg-success' : 'bg-danger'}`;
            }
        });
    }

    updateCurrentStock(data) {
        document.getElementById('currentPrice').textContent = data.price.toLocaleString();
        
        const changeElement = document.getElementById('priceChange');
        changeElement.textContent = `${data.change >= 0 ? '+' : ''}${data.change.toFixed(2)}%`;
        changeElement.className = `badge ${data.change >= 0 ? 'bg-success' : 'bg-danger'}`;
    }
}

const api = new SSIApi();
api.setupSocketListeners();

document.addEventListener('DOMContentLoaded', () => {
    api.setupSocketListeners();
});