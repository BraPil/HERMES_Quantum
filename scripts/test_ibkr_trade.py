#!/usr/bin/env python3
"""
IBKR TWS Paper Trade Test - QBTS
=================================
Places a test paper trade for QBTS (D-Wave Quantum).

Author: HERMES Development Team
"""

import asyncio
import sys
import time

# Python 3.14+ requires event loop to be set before importing ib_insync
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from ib_insync import IB, Stock, MarketOrder, LimitOrder, util


def test_qbts_trade():
    """Test placing a paper trade for QBTS"""
    print("=" * 60)
    print("IBKR Paper Trade Test - QBTS")
    print("=" * 60)
    
    ib = IB()
    
    try:
        # Connect to paper trading (port 7497)
        print("\n📡 Connecting to TWS on localhost:7497...")
        ib.connect('127.0.0.1', 7497, clientId=2)
        print("✅ Connected!")
        
        # Define QBTS stock
        qbts = Stock('QBTS', 'SMART', 'USD')
        
        # Qualify the contract (verify it exists)
        print("\n🔍 Qualifying QBTS contract...")
        ib.qualifyContracts(qbts)
        print(f"   Contract: {qbts}")
        print(f"   ConId: {qbts.conId}")
        
        # Request delayed market data (free, 15-min delayed)
        print("\n📊 Requesting delayed market data...")
        ib.reqMarketDataType(3)  # 3 = Delayed data
        
        ticker = ib.reqMktData(qbts, '', False, False)
        
        # Wait for data
        print("   Waiting for market data...")
        for _ in range(10):
            ib.sleep(1)
            if ticker.last or ticker.close:
                break
        
        # Get current price info
        last_price = ticker.last if ticker.last else ticker.close
        bid = ticker.bid if ticker.bid else 0
        ask = ticker.ask if ticker.ask else 0
        
        print(f"\n   QBTS Market Data (Delayed):")
        print(f"   Last: ${last_price:.2f}" if last_price else "   Last: N/A")
        print(f"   Bid: ${bid:.2f}" if bid > 0 else "   Bid: N/A")
        print(f"   Ask: ${ask:.2f}" if ask > 0 else "   Ask: N/A")
        
        # Cancel market data subscription
        ib.cancelMktData(qbts)
        
        # ==========================================
        # PLACE TEST ORDER - BUY 10 SHARES OF QBTS
        # ==========================================
        print("\n" + "-" * 40)
        print("PLACING TEST ORDER")
        print("-" * 40)
        
        quantity = 10  # Small test order
        
        # Use market order for simplicity
        order = MarketOrder('BUY', quantity)
        
        print(f"\n📝 Submitting order: BUY {quantity} QBTS @ MARKET")
        
        # Place the order
        trade = ib.placeOrder(qbts, order)
        
        # Wait for order to be processed
        print("   Waiting for order status...")
        for _ in range(10):
            ib.sleep(1)
            if trade.orderStatus.status in ['Filled', 'Cancelled', 'ApiCancelled']:
                break
            print(f"   Status: {trade.orderStatus.status}")
        
        # Check final status
        print(f"\n📋 Order Status: {trade.orderStatus.status}")
        
        if trade.orderStatus.status == 'Filled':
            fill_price = trade.orderStatus.avgFillPrice
            print(f"   ✅ FILLED!")
            print(f"   Quantity: {quantity}")
            print(f"   Fill Price: ${fill_price:.2f}")
            print(f"   Total Cost: ${fill_price * quantity:.2f}")
        elif trade.orderStatus.status == 'Submitted':
            print("   ⏳ Order submitted, waiting for fill...")
            print("   (Market may be closed)")
        else:
            print(f"   Status: {trade.orderStatus.status}")
            if trade.log:
                for log_entry in trade.log[-3:]:
                    print(f"   Log: {log_entry}")
        
        # Show updated positions
        print("\n" + "-" * 40)
        print("UPDATED POSITIONS")
        print("-" * 40)
        
        positions = ib.positions()
        if positions:
            for pos in positions:
                if pos.contract.symbol == 'QBTS':
                    print(f"   {pos.contract.symbol}: {pos.position} shares @ ${pos.avgCost:.2f}")
        else:
            print("   No positions yet (order may be pending)")
        
        # Show account summary
        print("\n" + "-" * 40)
        print("ACCOUNT SUMMARY")
        print("-" * 40)
        
        account_values = ib.accountSummary()
        for av in account_values:
            if av.tag in ['NetLiquidation', 'TotalCashValue', 'AvailableFunds']:
                print(f"   {av.tag}: ${float(av.value):,.2f}")
        
        print("\n" + "=" * 60)
        print("🎉 Test trade complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n📴 Disconnecting from TWS...")
        ib.disconnect()


if __name__ == "__main__":
    test_qbts_trade()
