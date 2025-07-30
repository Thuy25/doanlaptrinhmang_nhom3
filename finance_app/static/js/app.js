document.addEventListener('DOMContentLoaded', async () => {
    // Load danh sách cổ phiếu
    await loadStocks();
    
    // Xử lý tìm kiếm
    document.getElementById('stockSearch').addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        filterStocks(searchTerm);
    });
    
    // Xử lý đặt lệnh
    document.getElementById('orderForm').addEventListener('submit', (e) => {
        e.preventDefault();
        placeOrder();
    });
});

async function loadStocks() {
    const stocks = await api.getStocks();
    const stockList = document.getElementById('stockList');
    
    stockList.innerHTML = '';
    
    if (stocks.data && stocks.data.length > 0) {
        stocks.data.forEach(stock => {
            const stockElement = document.createElement('div');
            stockElement.className = 'list-group-item stock-item';
            stockElement.dataset.symbol = stock.Symbol;
            stockElement.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${stock.Symbol}</strong>
                        <div class="small text-muted">${stock.StockName}</div>
                    </div>
                    <div class="text-end">
                        <div class="stock-price">-</div>
                        <span class="stock-change badge bg-secondary">-</span>
                    </div>
                </div>
            `;
            
            stockElement.addEventListener('click', () => {
                selectStock(stock);
            });
            
            stockList.appendChild(stockElement);
            
            // Thêm vào dropdown đặt lệnh
            const option = document.createElement('option');
            option.value = stock.Symbol;
            option.textContent = `${stock.Symbol} - ${stock.StockName}`;
            document.getElementById('orderSymbol').appendChild(option);
        });
    }
}

function filterStocks(searchTerm) {
    const stockItems = document.querySelectorAll('.stock-item');
    
    stockItems.forEach(item => {
        const symbol = item.dataset.symbol.toLowerCase();
        const name = item.textContent.toLowerCase();
        
        if (symbol.includes(searchTerm) || name.includes(searchTerm)) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

async function selectStock(stock) {
    api.currentStock = stock;
    document.getElementById('chartTitle').textContent = `${stock.Symbol} - ${stock.StockName}`;
    
    // Cập nhật dropdown đặt lệnh
    document.getElementById('orderSymbol').value = stock.Symbol;
    
    // Load dữ liệu cổ phiếu
    const stockData = await api.getStockData(stock.Symbol);
    if (stockData) {
        updateStockDetails(stockData);
    }
    
    // Load dữ liệu biểu đồ
    const ohlcData = await api.getOHLCData(stock.Symbol);
    if (ohlcData) {
        updateChart(ohlcData);
    }
    
    // Đăng ký nhận dữ liệu realtime
    api.subscribeToStock(stock.Symbol);
}

function updateStockDetails(stockData) {
    const details = stockData.details?.dataList?.[0]?.repeatedinfoList?.[0];
    const prices = stockData.prices?.dataList?.[0];
    
    if (prices) {
        document.getElementById('currentPrice').textContent = prices.closeprice.toLocaleString();
        
        const change = parseFloat(prices.pricechange);
        const changeElement = document.getElementById('priceChange');
        changeElement.textContent = `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
        changeElement.className = `badge ${change >= 0 ? 'bg-success' : 'bg-danger'}`;
        
        document.getElementById('priceChangeDetails').innerHTML = `
            <div>Giá tham chiếu: ${prices.refprice.toLocaleString()}</div>
            <div>Giá mở cửa: ${prices.openprice.toLocaleString()}</div>
            <div>Giá cao nhất: ${prices.highestprice.toLocaleString()}</div>
            <div>Giá thấp nhất: ${prices.lowestprice.toLocaleString()}</div>
        `;
        
        document.getElementById('tradeInfo').innerHTML = `
            <div>KL khớp: ${prices.totalmatchvol.toLocaleString()}</div>
            <div>GT khớp: ${prices.totalmatchval.toLocaleString()}</div>
        `;
        
        document.getElementById('priceRange').innerHTML = `
            <div>Trần: ${prices.ceilingprice.toLocaleString()}</div>
            <div>Sàn: ${prices.floorprice.toLocaleString()}</div>
        `;
    }
}

function updateChart(ohlcData) {
    const ctx = document.getElementById('priceChart').getContext('2d');
    
    if (api.priceChart) {
        api.priceChart.destroy();
    }
    
    const labels = ohlcData.dataList.map(item => item.tradingdate);
    const data = ohlcData.dataList.map(item => item.close);
    
    api.priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Giá đóng cửa',
                data: data,
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Giá: ${context.parsed.y.toLocaleString()}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

function placeOrder() {
    const symbol = document.getElementById('orderSymbol').value;
    const type = document.getElementById('orderType').value;
    const quantity = document.getElementById('orderQuantity').value;
    const price = document.getElementById('orderPrice').value;
    
    if (!symbol || !quantity || !price) {
        addAlert('Vui lòng điền đầy đủ thông tin đặt lệnh', 'danger');
        return;
    }
    
    // Gọi API đặt lệnh
    addAlert(`Đã đặt lệnh ${type === 'buy' ? 'MUA' : 'BÁN'} ${quantity} ${symbol} @ ${price}`, 'success');
    
    // Reset form
    document.getElementById('orderForm').reset();
}

function addAlert(message, type = 'info') {
    const alertsDiv = document.getElementById('alerts');
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertsDiv.prepend(alert);
    
    if (alertsDiv.children.length > 5) {
        alertsDiv.removeChild(alertsDiv.lastChild);
    }
}