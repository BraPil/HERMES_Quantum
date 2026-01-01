#!/usr/bin/env python3
"""
HERMES Quantum Trading Dashboard
==================================
Web-based dashboard for monitoring and controlling the trading system.

Features:
- Real-time signal display
- Position and P&L tracking
- Breaking news alerts with popup
- Manual trade execution buttons
- Market regime indicator

Run with: python scripts/dashboard.py
Open: http://localhost:5000

Author: HERMES Development Team
Version: 0.1.0
"""

import asyncio
import json
import logging
import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Python 3.14+ compatibility
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# FLASK APP
# =============================================================================

app = Flask(__name__)
CORS(app)

# Global state (would be replaced with proper state management)
dashboard_state = {
    "connected": False,
    "mode": "simulated",
    "market_open": False,
    "last_update": None,
    "signals": [],
    "positions": [],
    "open_orders": [],
    "account": {
        "net_liquidation": 0,
        "cash": 0,
        "available_funds": 0,
        "daily_pnl": 0,
        "daily_pnl_pct": 0
    },
    "market_regime": "sideways",
    "watchlist_quotes": {},
    "breaking_alerts": []
}

# Trading orchestrator (initialized lazily)
orchestrator = None


# =============================================================================
# HTML TEMPLATE
# =============================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HERMES Quantum - Trading Dashboard</title>
    <style>
        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-card: #1a1a24;
            --text-primary: #e0e0e0;
            --text-secondary: #888;
            --accent-green: #00ff88;
            --accent-red: #ff4444;
            --accent-blue: #4488ff;
            --accent-yellow: #ffcc00;
            --accent-purple: #aa44ff;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
        }
        
        .header {
            background: linear-gradient(135deg, var(--bg-secondary), var(--bg-card));
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #333;
        }
        
        .logo {
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--accent-purple);
        }
        
        .logo span {
            color: var(--accent-blue);
        }
        
        .status-bar {
            display: flex;
            gap: 1rem;
            align-items: center;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            background: var(--bg-card);
            border-radius: 20px;
            font-size: 0.9rem;
        }
        
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        
        .status-dot.connected { background: var(--accent-green); }
        .status-dot.disconnected { background: var(--accent-red); }
        .status-dot.market-open { background: var(--accent-green); }
        .status-dot.market-closed { background: var(--accent-yellow); }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 1rem;
            padding: 1rem;
        }
        
        .card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid #333;
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid #333;
        }
        
        .card-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .card-full {
            grid-column: span 3;
        }
        
        .account-stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
        }
        
        .stat {
            text-align: center;
            padding: 1rem;
            background: var(--bg-secondary);
            border-radius: 8px;
        }
        
        .stat-value {
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--accent-blue);
        }
        
        .stat-value.positive { color: var(--accent-green); }
        .stat-value.negative { color: var(--accent-red); }
        
        .stat-label {
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-top: 0.5rem;
        }
        
        .quote-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
        }
        
        .quote-card {
            background: var(--bg-secondary);
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
            transition: transform 0.2s;
        }
        
        .quote-card:hover {
            transform: translateY(-2px);
        }
        
        .quote-symbol {
            font-size: 1.2rem;
            font-weight: bold;
            color: var(--accent-purple);
        }
        
        .quote-price {
            font-size: 1.5rem;
            font-weight: bold;
            margin: 0.5rem 0;
        }
        
        .quote-change {
            font-size: 0.9rem;
        }
        
        .quote-change.positive { color: var(--accent-green); }
        .quote-change.negative { color: var(--accent-red); }
        
        .signal-list {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .signal-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            background: var(--bg-secondary);
            border-radius: 8px;
            border-left: 4px solid;
        }
        
        .signal-item.buy { border-left-color: var(--accent-green); }
        .signal-item.sell { border-left-color: var(--accent-red); }
        .signal-item.hold { border-left-color: var(--text-secondary); }
        
        .signal-info {
            flex: 1;
        }
        
        .signal-symbol {
            font-weight: bold;
        }
        
        .signal-type {
            font-size: 0.9rem;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            margin-left: 0.5rem;
        }
        
        .signal-type.buy { background: rgba(0, 255, 136, 0.2); color: var(--accent-green); }
        .signal-type.sell { background: rgba(255, 68, 68, 0.2); color: var(--accent-red); }
        
        .signal-confidence {
            font-size: 0.85rem;
            color: var(--text-secondary);
        }
        
        .signal-action {
            display: flex;
            gap: 0.5rem;
        }
        
        .btn {
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
        }
        
        .btn-buy {
            background: var(--accent-green);
            color: #000;
        }
        
        .btn-sell {
            background: var(--accent-red);
            color: #fff;
        }
        
        .btn:hover {
            transform: scale(1.05);
        }
        
        .position-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .position-table th,
        .position-table td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #333;
        }
        
        .position-table th {
            color: var(--text-secondary);
            font-weight: normal;
            font-size: 0.85rem;
        }
        
        /* Breaking Alert Modal */
        .alert-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }
        
        .alert-modal.active {
            display: flex;
        }
        
        .alert-content {
            background: var(--bg-card);
            border: 2px solid var(--accent-yellow);
            border-radius: 16px;
            padding: 2rem;
            max-width: 500px;
            text-align: center;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from { transform: translateY(-50px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        
        .alert-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        
        .alert-title {
            font-size: 1.5rem;
            color: var(--accent-yellow);
            margin-bottom: 1rem;
        }
        
        .alert-symbol {
            font-size: 2rem;
            font-weight: bold;
            color: var(--accent-purple);
        }
        
        .alert-message {
            margin: 1rem 0;
            color: var(--text-secondary);
        }
        
        .alert-actions {
            display: flex;
            gap: 1rem;
            justify-content: center;
            margin-top: 1.5rem;
        }
        
        .alert-btn {
            padding: 1rem 2rem;
            font-size: 1.2rem;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            font-weight: bold;
        }
        
        .alert-btn-execute {
            background: var(--accent-green);
            color: #000;
        }
        
        .alert-btn-dismiss {
            background: var(--bg-secondary);
            color: var(--text-primary);
            border: 1px solid #555;
        }
        
        /* Regime indicator */
        .regime-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: 600;
        }
        
        .regime-indicator.rising {
            background: rgba(0, 255, 136, 0.2);
            color: var(--accent-green);
        }
        
        .regime-indicator.falling {
            background: rgba(255, 68, 68, 0.2);
            color: var(--accent-red);
        }
        
        .regime-indicator.sideways {
            background: rgba(255, 204, 0, 0.2);
            color: var(--accent-yellow);
        }
        
        .refresh-time {
            color: var(--text-secondary);
            font-size: 0.85rem;
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="logo">HERMES <span>Quantum</span></div>
        <div class="status-bar">
            <div class="status-indicator">
                <div class="status-dot" id="connection-dot"></div>
                <span id="connection-status">Connecting...</span>
            </div>
            <div class="status-indicator">
                <div class="status-dot" id="market-dot"></div>
                <span id="market-status">Market Closed</span>
            </div>
            <div class="regime-indicator" id="regime-indicator">
                📊 Sideways
            </div>
            <span class="refresh-time" id="last-update">--</span>
        </div>
    </header>
    
    <main class="main-content">
        <!-- Account Summary -->
        <div class="card card-full">
            <div class="card-header">
                <span class="card-title">📊 Account Summary</span>
                <span id="mode-badge" style="padding: 0.3rem 0.8rem; background: #4488ff33; color: #4488ff; border-radius: 12px; font-size: 0.85rem;">PAPER</span>
            </div>
            <div class="account-stats">
                <div class="stat">
                    <div class="stat-value" id="net-liq">$0.00</div>
                    <div class="stat-label">Net Liquidation</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="available-funds">$0.00</div>
                    <div class="stat-label">Available Funds</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="daily-pnl">$0.00</div>
                    <div class="stat-label">Daily P&L</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="daily-pnl-pct">0.00%</div>
                    <div class="stat-label">Daily Return</div>
                </div>
            </div>
        </div>
        
        <!-- Watchlist Quotes -->
        <div class="card card-full">
            <div class="card-header">
                <span class="card-title">📈 Quantum Stocks</span>
            </div>
            <div class="quote-grid" id="quote-grid">
                <!-- Populated by JS -->
            </div>
        </div>
        
        <!-- Signals -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">🎯 Trading Signals</span>
            </div>
            <div class="signal-list" id="signal-list">
                <div style="color: var(--text-secondary); text-align: center; padding: 2rem;">
                    Waiting for signals...
                </div>
            </div>
        </div>
        
        <!-- Positions -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">💼 Positions</span>
            </div>
            <table class="position-table" id="position-table">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Qty</th>
                        <th>Avg Cost</th>
                        <th>P&L</th>
                    </tr>
                </thead>
                <tbody id="position-body">
                    <tr>
                        <td colspan="4" style="text-align: center; color: var(--text-secondary);">No positions</td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <!-- Open Orders -->
        <div class="card">
            <div class="card-header">
                <span class="card-title">📝 Open Orders</span>
            </div>
            <div id="orders-list" style="color: var(--text-secondary); text-align: center; padding: 2rem;">
                No open orders
            </div>
        </div>
    </main>
    
    <!-- Breaking Alert Modal -->
    <div class="alert-modal" id="alert-modal">
        <div class="alert-content">
            <div class="alert-icon">⚡</div>
            <div class="alert-title">BREAKING NEWS ALERT</div>
            <div class="alert-symbol" id="alert-symbol">QBTS</div>
            <div class="alert-message" id="alert-message">
                Major news event detected. Price spike expected.
            </div>
            <div style="margin: 1rem 0;">
                <span style="color: var(--accent-green);">Confidence: </span>
                <span id="alert-confidence">95%</span>
            </div>
            <div class="alert-actions">
                <button class="alert-btn alert-btn-execute" onclick="executeAlert()">
                    🚀 EXECUTE NOW
                </button>
                <button class="alert-btn alert-btn-dismiss" onclick="dismissAlert()">
                    Dismiss
                </button>
            </div>
        </div>
    </div>
    
    <script>
        // Polling interval
        const POLL_INTERVAL = 2000; // 2 seconds
        
        // Update dashboard with state
        function updateDashboard(state) {
            // Connection status
            const connDot = document.getElementById('connection-dot');
            const connStatus = document.getElementById('connection-status');
            if (state.connected) {
                connDot.className = 'status-dot connected';
                connStatus.textContent = 'Connected';
            } else {
                connDot.className = 'status-dot disconnected';
                connStatus.textContent = 'Disconnected';
            }
            
            // Market status
            const marketDot = document.getElementById('market-dot');
            const marketStatus = document.getElementById('market-status');
            if (state.market_open) {
                marketDot.className = 'status-dot market-open';
                marketStatus.textContent = 'Market Open';
            } else {
                marketDot.className = 'status-dot market-closed';
                marketStatus.textContent = 'Market Closed';
            }
            
            // Market regime
            const regimeIndicator = document.getElementById('regime-indicator');
            const regimeIcons = { rising: '📈', falling: '📉', sideways: '📊' };
            regimeIndicator.className = 'regime-indicator ' + state.market_regime;
            regimeIndicator.textContent = regimeIcons[state.market_regime] + ' ' + 
                state.market_regime.charAt(0).toUpperCase() + state.market_regime.slice(1);
            
            // Mode badge
            const modeBadge = document.getElementById('mode-badge');
            modeBadge.textContent = state.mode.toUpperCase();
            modeBadge.style.background = state.mode === 'live' ? '#ff444433' : '#4488ff33';
            modeBadge.style.color = state.mode === 'live' ? '#ff4444' : '#4488ff';
            
            // Account stats
            document.getElementById('net-liq').textContent = 
                '$' + state.account.net_liquidation.toLocaleString('en-US', {minimumFractionDigits: 2});
            document.getElementById('available-funds').textContent = 
                '$' + state.account.available_funds.toLocaleString('en-US', {minimumFractionDigits: 2});
            
            const dailyPnl = document.getElementById('daily-pnl');
            dailyPnl.textContent = '$' + state.account.daily_pnl.toLocaleString('en-US', {minimumFractionDigits: 2});
            dailyPnl.className = 'stat-value ' + (state.account.daily_pnl >= 0 ? 'positive' : 'negative');
            
            const dailyPnlPct = document.getElementById('daily-pnl-pct');
            dailyPnlPct.textContent = state.account.daily_pnl_pct.toFixed(2) + '%';
            dailyPnlPct.className = 'stat-value ' + (state.account.daily_pnl_pct >= 0 ? 'positive' : 'negative');
            
            // Quotes
            const quoteGrid = document.getElementById('quote-grid');
            quoteGrid.innerHTML = '';
            for (const [symbol, quote] of Object.entries(state.watchlist_quotes)) {
                const change = quote.change || 0;
                const changeClass = change >= 0 ? 'positive' : 'negative';
                quoteGrid.innerHTML += `
                    <div class="quote-card">
                        <div class="quote-symbol">${symbol}</div>
                        <div class="quote-price">$${quote.last.toFixed(2)}</div>
                        <div class="quote-change ${changeClass}">
                            ${change >= 0 ? '+' : ''}${change.toFixed(2)}%
                        </div>
                    </div>
                `;
            }
            
            // Signals
            const signalList = document.getElementById('signal-list');
            if (state.signals.length > 0) {
                signalList.innerHTML = '';
                for (const signal of state.signals.slice(-10).reverse()) {
                    const signalClass = signal.signal.includes('BUY') ? 'buy' : 
                                       signal.signal.includes('SELL') ? 'sell' : 'hold';
                    signalList.innerHTML += `
                        <div class="signal-item ${signalClass}">
                            <div class="signal-info">
                                <span class="signal-symbol">${signal.symbol}</span>
                                <span class="signal-type ${signalClass}">${signal.signal}</span>
                                <div class="signal-confidence">
                                    ${signal.confidence.toFixed(0)}% confidence • ${signal.reason}
                                </div>
                            </div>
                            ${signal.actionable ? `
                            <div class="signal-action">
                                <button class="btn btn-buy" onclick="executeSignal('${signal.symbol}', 'BUY')">Buy</button>
                                <button class="btn btn-sell" onclick="executeSignal('${signal.symbol}', 'SELL')">Sell</button>
                            </div>
                            ` : ''}
                        </div>
                    `;
                }
            }
            
            // Positions
            const positionBody = document.getElementById('position-body');
            if (state.positions.length > 0) {
                positionBody.innerHTML = '';
                for (const pos of state.positions) {
                    const pnl = pos.unrealized_pnl || 0;
                    const pnlClass = pnl >= 0 ? 'positive' : 'negative';
                    positionBody.innerHTML += `
                        <tr>
                            <td>${pos.symbol}</td>
                            <td>${pos.quantity}</td>
                            <td>$${pos.avg_cost.toFixed(2)}</td>
                            <td class="stat-value ${pnlClass}">$${pnl.toFixed(2)}</td>
                        </tr>
                    `;
                }
            } else {
                positionBody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--text-secondary);">No positions</td></tr>';
            }
            
            // Orders
            const ordersList = document.getElementById('orders-list');
            if (state.open_orders.length > 0) {
                ordersList.innerHTML = '';
                for (const order of state.open_orders) {
                    ordersList.innerHTML += `
                        <div class="signal-item ${order.side.toLowerCase()}">
                            <div class="signal-info">
                                <span class="signal-symbol">${order.symbol}</span>
                                <span class="signal-type ${order.side.toLowerCase()}">${order.side} ${order.quantity}</span>
                                <div class="signal-confidence">${order.status}</div>
                            </div>
                            <button class="btn btn-sell" onclick="cancelOrder(${order.order_id})">Cancel</button>
                        </div>
                    `;
                }
            } else {
                ordersList.innerHTML = '<div style="color: var(--text-secondary); text-align: center; padding: 2rem;">No open orders</div>';
            }
            
            // Breaking alerts
            if (state.breaking_alerts.length > 0) {
                const alert = state.breaking_alerts[0];
                document.getElementById('alert-symbol').textContent = alert.symbol;
                document.getElementById('alert-message').textContent = alert.message;
                document.getElementById('alert-confidence').textContent = alert.confidence + '%';
                document.getElementById('alert-modal').classList.add('active');
            }
            
            // Last update
            document.getElementById('last-update').textContent = 
                'Updated: ' + new Date().toLocaleTimeString();
        }
        
        // Fetch state from server
        async function fetchState() {
            try {
                const response = await fetch('/api/state');
                const state = await response.json();
                updateDashboard(state);
            } catch (error) {
                console.error('Failed to fetch state:', error);
            }
        }
        
        // Execute signal
        async function executeSignal(symbol, side) {
            try {
                const response = await fetch('/api/execute', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({symbol, side})
                });
                const result = await response.json();
                console.log('Execution result:', result);
                fetchState();
            } catch (error) {
                console.error('Execution failed:', error);
            }
        }
        
        // Cancel order
        async function cancelOrder(orderId) {
            try {
                await fetch('/api/cancel/' + orderId, {method: 'POST'});
                fetchState();
            } catch (error) {
                console.error('Cancel failed:', error);
            }
        }
        
        // Alert actions
        function executeAlert() {
            const symbol = document.getElementById('alert-symbol').textContent;
            executeSignal(symbol, 'BUY');
            dismissAlert();
        }
        
        function dismissAlert() {
            document.getElementById('alert-modal').classList.remove('active');
            fetch('/api/dismiss-alert', {method: 'POST'});
        }
        
        // Start polling
        fetchState();
        setInterval(fetchState, POLL_INTERVAL);
    </script>
</body>
</html>
"""


# =============================================================================
# API ROUTES
# =============================================================================

@app.route('/')
def index():
    """Serve the dashboard"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/state')
def get_state():
    """Get current dashboard state"""
    global dashboard_state
    return jsonify(dashboard_state)


@app.route('/api/execute', methods=['POST'])
def execute_trade():
    """Execute a manual trade"""
    data = request.get_json()
    symbol = data.get('symbol')
    side = data.get('side')
    
    logger.info(f"Manual execution: {side} {symbol}")
    
    # TODO: Execute via orchestrator
    return jsonify({"status": "submitted", "symbol": symbol, "side": side})


@app.route('/api/cancel/<int:order_id>', methods=['POST'])
def cancel_order(order_id):
    """Cancel an order"""
    logger.info(f"Cancel order: {order_id}")
    # TODO: Cancel via orchestrator
    return jsonify({"status": "cancelled", "order_id": order_id})


@app.route('/api/dismiss-alert', methods=['POST'])
def dismiss_alert():
    """Dismiss breaking alert"""
    global dashboard_state
    if dashboard_state['breaking_alerts']:
        dashboard_state['breaking_alerts'].pop(0)
    return jsonify({"status": "dismissed"})


@app.route('/api/scan', methods=['POST'])
def trigger_scan():
    """Trigger a manual scan"""
    global orchestrator
    if orchestrator:
        results = orchestrator.scan_watchlist()
        return jsonify({"status": "scanned", "trades": len(results)})
    return jsonify({"status": "error", "message": "Orchestrator not initialized"})


# =============================================================================
# BACKGROUND UPDATER
# =============================================================================

def update_state():
    """Background task to update dashboard state"""
    global dashboard_state, orchestrator
    
    while True:
        try:
            if orchestrator:
                status = orchestrator.get_status()
                
                dashboard_state['connected'] = status.get('connected', False)
                dashboard_state['mode'] = status.get('mode', 'simulated')
                dashboard_state['market_open'] = status.get('market_open', False)
                dashboard_state['positions'] = status.get('positions', [])
                dashboard_state['open_orders'] = status.get('open_orders', [])
                
                if 'portfolio' in status:
                    portfolio = status['portfolio']
                    dashboard_state['account'] = {
                        'net_liquidation': portfolio.get('total_equity', 0),
                        'cash': portfolio.get('available_cash', 0),
                        'available_funds': portfolio.get('settled_cash', 0),
                        'daily_pnl': portfolio.get('daily_pnl', {}).get('total', 0),
                        'daily_pnl_pct': portfolio.get('daily_pnl', {}).get('pct', 0)
                    }
                    dashboard_state['market_regime'] = portfolio.get('market_regime', 'sideways')
            
            # Update quotes
            try:
                from data_ingestion.data_sources import DataSourceManager
                with DataSourceManager() as dm:
                    quotes = dm.get_watchlist_quotes()
                    dashboard_state['watchlist_quotes'] = {
                        symbol: {
                            'last': quote.last,
                            'bid': quote.bid,
                            'ask': quote.ask,
                            'change': 0  # Would need previous close
                        }
                        for symbol, quote in quotes.items()
                    }
            except Exception as e:
                logger.debug(f"Quote update error: {e}")
            
            dashboard_state['last_update'] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"State update error: {e}")
        
        time.sleep(5)  # Update every 5 seconds


# =============================================================================
# MAIN
# =============================================================================

def start_dashboard(
    host: str = '0.0.0.0',
    port: int = 5000,
    debug: bool = False,
    initialize_orchestrator: bool = True
):
    """
    Start the trading dashboard.
    
    Args:
        host: Host to bind to
        port: Port to listen on
        debug: Enable Flask debug mode
        initialize_orchestrator: Initialize trading orchestrator
    """
    global orchestrator, dashboard_state
    
    print("=" * 60)
    print("HERMES Quantum - Trading Dashboard")
    print("=" * 60)
    
    if initialize_orchestrator:
        try:
            from core.execution_bridge import TradingOrchestrator, ExecutionConfig, ExecutionMode
            
            # Use simulated mode for safety
            config = ExecutionConfig(mode=ExecutionMode.SIMULATED)
            orchestrator = TradingOrchestrator(execution_config=config)
            
            if orchestrator.initialize():
                print("✅ Trading orchestrator initialized")
                
                # Set initial state
                dashboard_state['connected'] = True
                dashboard_state['mode'] = config.mode.value
            else:
                print("⚠️  Orchestrator initialization failed, running in view-only mode")
        except Exception as e:
            print(f"⚠️  Could not initialize orchestrator: {e}")
            print("   Running in view-only mode")
    
    # Start background updater
    updater_thread = threading.Thread(target=update_state, daemon=True)
    updater_thread.start()
    
    print(f"\n🌐 Dashboard available at: http://localhost:{port}")
    print("   Press Ctrl+C to stop\n")
    
    # Run Flask app
    app.run(host=host, port=port, debug=debug, use_reloader=False)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='HERMES Quantum Trading Dashboard')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to listen on')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--no-orchestrator', action='store_true', help='Run without trading orchestrator')
    
    args = parser.parse_args()
    
    start_dashboard(
        host=args.host,
        port=args.port,
        debug=args.debug,
        initialize_orchestrator=not args.no_orchestrator
    )
