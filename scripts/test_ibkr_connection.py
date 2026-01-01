#!/usr/bin/env python3
"""
IBKR TWS API Connection Test
=============================
Tests connection to Interactive Brokers TWS paper trading account.

Requirements:
- TWS running with API enabled
- Port 7497 for paper trading
- "Enable ActiveX and Socket Clients" checked
- "Download open orders on connection" checked

Author: HERMES Development Team
"""

import asyncio
import sys

# Python 3.14+ requires event loop to be set before importing ib_insync
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from ib_insync import IB, Stock, util


def test_connection():
    """Test connection to IBKR TWS"""
    print("=" * 60)
    print("IBKR TWS Connection Test")
    print("=" * 60)
    
    ib = IB()
    
    try:
        # Connect to paper trading (port 7497)
        print("\n📡 Connecting to TWS on localhost:7497...")
        ib.connect('127.0.0.1', 7497, clientId=1)
        
        if ib.isConnected():
            print("✅ Connected successfully!\n")
        else:
            print("❌ Connection failed")
            return False
        
        # Get account info
        print("-" * 40)
        print("ACCOUNT INFORMATION")
        print("-" * 40)
        
        accounts = ib.managedAccounts()
        print(f"Managed Accounts: {accounts}")
        
        # Get account values
        account_values = ib.accountSummary()
        
        # Find key metrics
        net_liq = None
        cash = None
        for av in account_values:
            if av.tag == 'NetLiquidation':
                net_liq = f"${float(av.value):,.2f}"
            elif av.tag == 'TotalCashValue':
                cash = f"${float(av.value):,.2f}"
        
        print(f"Net Liquidation Value: {net_liq or 'N/A'}")
        print(f"Total Cash: {cash or 'N/A'}")
        
        # Get positions
        print("\n" + "-" * 40)
        print("CURRENT POSITIONS")
        print("-" * 40)
        
        positions = ib.positions()
        if positions:
            for pos in positions:
                print(f"  {pos.contract.symbol}: {pos.position} shares @ ${pos.avgCost:.2f}")
        else:
            print("  No open positions")
        
        # Get open orders
        print("\n" + "-" * 40)
        print("OPEN ORDERS")
        print("-" * 40)
        
        open_trades = ib.openTrades()
        if open_trades:
            for trade in open_trades:
                print(f"  {trade.order.action} {trade.order.totalQuantity} "
                      f"{trade.contract.symbol} @ {trade.order.lmtPrice}")
        else:
            print("  No open orders")
        
        # Test market data (delayed)
        print("\n" + "-" * 40)
        print("MARKET DATA TEST")
        print("-" * 40)
        
        # Request delayed data (doesn't require market data subscription)
        ib.reqMarketDataType(4)  # 4 = delayed frozen
        
        contract = Stock('AAPL', 'SMART', 'USD')
        ib.qualifyContracts(contract)
        
        ticker = ib.reqMktData(contract)
        ib.sleep(2)  # Wait for data
        
        print(f"  AAPL - Bid: {ticker.bid}, Ask: {ticker.ask}, Last: {ticker.last}")
        
        ib.cancelMktData(contract)
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED! IBKR connection is working.")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Is TWS running and logged in?")
        print("  2. Is API enabled? (Configure → API → Settings)")
        print("  3. Is port 7497 correct for paper trading?")
        print("  4. Did you allow the API connection when prompted?")
        return False
        
    finally:
        if ib.isConnected():
            ib.disconnect()
            print("\n📴 Disconnected from TWS")


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
