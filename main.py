from ib_insync import IB, MarketOrder
import time

class IBKRTradeCopierPolling:
    def __init__(self, source_host='127.0.0.1', source_port=7496, 
                 dest_host='127.0.0.1', dest_port=7498, 
                 source_client_id=1, dest_client_id=2,
                 poll_interval=2):

        self.source_ib = IB()
        self.dest_ib = IB()
        self.source_host = source_host
        self.source_port = source_port
        self.dest_host = dest_host
        self.dest_port = dest_port
        self.source_client_id = source_client_id
        self.dest_client_id = dest_client_id
        self.poll_interval = poll_interval
        
        # Track processed fills to avoid duplicates
        self.processed_exec_ids = set()
    
    def connect(self):
        """Connect to both IBKR accounts"""
        try:
            print(f"Connecting to source account at {self.source_host}:{self.source_port}...")
            self.source_ib.connect(self.source_host, self.source_port, clientId=self.source_client_id)
            print("✓ Source account connected")
            
            print(f"Connecting to destination account at {self.dest_host}:{self.dest_port}...")
            self.dest_ib.connect(self.dest_host, self.dest_port, clientId=self.dest_client_id)
            print("✓ Destination account connected")
            
            print("\n⚠️  NOTE: Will copy ALL existing fills from today on startup")
            print("    Then monitor for new trades going forward\n")
            
            return True
        except Exception as e:
            print(f"✗ Connection error: {e}")
            return False
    
    def check_for_new_trades(self):
        """Check for new trades and copy them"""
        try:
            # Get all current fills
            current_fills = self.source_ib.fills()
            
            # Find new fills
            new_fills = []
            for fill in current_fills:
                if fill.execution.execId not in self.processed_exec_ids:
                    new_fills.append(fill)
                    self.processed_exec_ids.add(fill.execution.execId)
            
            # Process new fills
            for fill in new_fills:
                print(f"\n{'='*60}")
                print(f"🔔 NEW TRADE DETECTED in Source Account:")
                print(f"Symbol: {fill.contract.symbol}")
                print(f"Action: {fill.execution.side}")
                print(f"Quantity: {fill.execution.shares}")
                print(f"Price: ${fill.execution.price}")
                print(f"Time: {fill.execution.time}")
                print(f"{'='*60}")
                
                # Copy the trade
                self.copy_trade(fill.contract, fill.execution)
                
        except Exception as e:
            print(f"✗ Error checking for trades: {e}")
    
    def copy_trade(self, contract, execution):
        try:
            # Determine the action (BUY/SELL)
            action = execution.side  # 'BOT' (bought) or 'SLD' (sold)
            if action == 'BOT':
                order_action = 'BUY'
            elif action == 'SLD':
                order_action = 'SELL'
            else:
                print(f"Unknown action: {action}")
                return
            
            quantity = execution.shares
            
            # Create market order for destination account
            order = MarketOrder(order_action, quantity)
            
            print(f"\n📤 Placing order in Destination Account:")
            print(f"  Contract: {contract.symbol}")
            print(f"  Action: {order_action}")
            print(f"  Quantity: {quantity}")
            
            # Place the order
            trade = self.dest_ib.placeOrder(contract, order)
            
            print(f"✓ Order placed successfully!")
            print(f"  Order ID: {trade.order.orderId}")
            
        except Exception as e:
            print(f"✗ Error copying trade: {e}")
    
    def start_monitoring(self):
        """Start monitoring trades by polling"""
        print("\n" + "="*60)
        print("TRADE COPIER STARTED - Polling every", self.poll_interval, "seconds")
        print("="*60)
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                self.check_for_new_trades()
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            print("\n\nStopping trade copier...")
            self.disconnect()
    
    def disconnect(self):
        """Disconnect from both accounts"""
        print("Disconnecting from accounts...")
        self.source_ib.disconnect()
        self.dest_ib.disconnect()
        print("✓ Disconnected")


def main():
    """
    Main function to run the polling-based trade copier
    """
    
    # Configuration - TWO PC SETUP
    SOURCE_HOST = '127.0.0.1'      # This PC (local)
    SOURCE_PORT = 7496              # Port for source account
    
    DEST_HOST = '10.53.109.247'    # Other PC IP address
    DEST_PORT = 7497                # Port for destination account
    
    SOURCE_CLIENT_ID = 100          # Unique ID for source connection
    DEST_CLIENT_ID = 200            # Unique ID for destination connection
    
    POLL_INTERVAL = 2               # Check for new trades every 2 seconds
    
    print("="*60)
    print("IBKR TRADE COPIER - POLLING VERSION")
    print("="*60)
    print(f"Source Account:      {SOURCE_HOST}:{SOURCE_PORT} (This PC)")
    print(f"Destination Account: {DEST_HOST}:{DEST_PORT}")
    print(f"Poll Interval:       {POLL_INTERVAL} seconds")
    print("="*60)
    
    # Create copier instance
    copier = IBKRTradeCopierPolling(
        source_host=SOURCE_HOST,
        source_port=SOURCE_PORT,
        dest_host=DEST_HOST,
        dest_port=DEST_PORT,
        source_client_id=SOURCE_CLIENT_ID,
        dest_client_id=DEST_CLIENT_ID,
        poll_interval=POLL_INTERVAL
    )
    
    # Connect to both accounts
    if copier.connect():
        # Start monitoring
        copier.start_monitoring()
    else:
        print("\nFailed to connect. Troubleshooting:")
        print("1. Is TWS/Gateway running on BOTH PCs?")
        print("2. Is API enabled on BOTH accounts?")
        print(f"3. On destination PC ({DEST_HOST}), have you added this PC's IP to trusted IPs?")
        print("4. Check firewalls on both PCs - port needs to be open")


if __name__ == "__main__":
    main()