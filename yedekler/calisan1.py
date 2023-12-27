import os
import time
from binance.client import Client
from datetime import datetime
from math import floor
import coinlistele
from binance.exceptions import BinanceAPIException

# Binance API ve Gizli Anahtarları
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')

# Binance Client'ını başlat
client = Client(api_key, api_secret)
server_time = client.get_server_time()
client.timestamp_offset = server_time['serverTime'] - int(time.time() * 1000)
stop_loss_percentage = 0.02  # %2 stop-loss
take_profit_percentage = 0.02  # %2 kar
investment_percentage =0.25 # bosta kalan parayi 4 esit parcada coin aldir
def log_to_file(message):
    with open("bot_log.txt", "a+", encoding='utf-8') as file:  # UTF-8 kodlaması ile dosya açma
        file.write(message + "\n")  # Mesajı dosyaya yaz
        
def is_asset_available(best_coin, client):
    """Belirtilen coini kullanıcının assetleri arasında kontrol eder."""
    account = client.get_account()
    asset_list = [asset['asset'] for asset in account['balances']]
    return best_coin in asset_list

def has_sufficient_balance(asset, required_amount):
    try:
        balance = client.get_asset_balance(asset=asset)
        if balance is not None:
            return float(balance['free']) >= required_amount
        else:
            print(f"Balance query failed for {asset}.")
            return False
    except Exception as e:
        print(f"An error occurred while checking balance for {asset}: {e}")
        return False

def get_total_balance(client, quote_asset="USDT"):
    """Toplam bakiyeyi belirtilen quote asset cinsinden döndürür."""
    account = client.get_account()
    total_balance = 0.0
    for asset in account['balances']:
        if asset['asset'] == quote_asset:
            total_balance += float(asset['free'])
        else:
            symbol = asset['asset'] + quote_asset
            if is_valid_symbol(symbol, client):
                try:
                    ticker = client.get_symbol_ticker(symbol=symbol)
                    total_balance += float(asset['free']) * float(ticker['price'])
                except Exception as e:
                    print(f"Error converting {asset['asset']} to {quote_asset}: {e}")
    return total_balance
def check_assets_and_last_trades(client, first_ten_coins):
    """Mevcut varlıkları ve son alım miktarlarını kontrol eder."""
    account = client.get_account()
    assets = account['balances']

    for asset in assets:
        asset_quantity = float(asset['free'])
        if asset_quantity >= 1.0:  # Varlık miktarı 1 veya daha büyükse işlem yap
            symbol = asset['asset'] + 'USDT'
            if is_valid_symbol(symbol, client):
                last_trade = get_last_trade_details(symbol, True)
                if last_trade:
                    current_price = float(client.get_symbol_ticker(symbol=symbol)['price'])
                    purchase_price = float(last_trade['price'])
                    profit_ratio = (current_price - purchase_price) / purchase_price
                    
                    if profit_ratio >= take_profit_percentage or purchase_price >= current_price:
                        if symbol not in first_ten_coins:
                            print(f"Ilk 10 coin arasinda degil satiliyor: {symbol}")
                            execute_sell_orders(symbol)
                        else:
                            print(f"Hala ilk 10 coin arasinda {symbol}")
                    elif current_price <= purchase_price * (1 - stop_loss_percentage):
                        print(f"Stop-loss sınırına ulaşıldı. Satış yapılıyor: {symbol}")
                        execute_sell_orders(symbol)
                   
def check_coin():
    first_ten_coins  = coinlistele.main()

    symbol=check_assets_and_last_trades(client,first_ten_coins)
    if(symbol):
       best_coin=symbol
       #print(symbol)

       total_balance = get_balance(split_USDT(symbol))
       #print(total_balance)

       current_price = float(client.get_symbol_ticker(symbol=symbol)['price'])

       stop_loss_price = current_price * (1 - stop_loss_percentage)
       take_profit_price = current_price * (1 + take_profit_percentage)
       return best_coin,stop_loss_price,take_profit_price,total_balance
    else:
        check_and_execute_buy_orders(first_ten_coins, investment_percentage)
        

def check_and_execute_buy_orders(first_ten_coins, investment_percentage):
    quote_asset = "USDT"
    total_balance = get_balance(quote_asset)
    available_balance = float(total_balance['free'])

    for coin in first_ten_coins:
        # Eğer varlık miktarı 1'den büyükse alım yapma
        if has_sufficient_balance(coin, 1):
            print(f"{coin} zaten yeterli miktarda mevcut. Alım yapılmayacak.")
            continue

        # Alım için gerekli miktarı hesapla
        required_amount = available_balance * investment_percentage

        # Yeterli bakiye varsa alım yap
        if available_balance >= required_amount:
            print(f"{coin} için yeterli bakiye mevcut. Alım yapılıyor.")
            ticker = client.get_symbol_ticker(symbol=coin)
            current_price = float(ticker['price'])
            stop_loss_price, take_profit_price = execute_buy_order(coin, current_price, required_amount)
            if stop_loss_price is not None and take_profit_price is not None:
                print(f"Alım işlemi tamamlandı: {coin}")
            else:
                print(f"Alım işlemi başarısız: {coin}")
        else:
            print(f"{coin} için yeterli bakiye yok. Alım yapılmayacak.")
            continue

        # Alınan miktarı toplam bakiyeden çıkar
        available_balance -= required_amount
           
def run_bot():
    
        i = 0
           
        while True:
            check_coin()

            try:          

                
                i += 1
                print(f"AI Bot  -> Çalışma #{i}")
           
                
                time.sleep(30)  # 5 dakika bekle

            except Exception as e:
                error_message = f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Hata: {str(e)}, Satır: {e.__traceback__.tb_lineno}"
                log_to_file(error_message)  # Hata mesajını dosyaya yaz
                print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} Bir hata oluştu: {e}, Satır: {e.__traceback__.tb_lineno}")
                time.sleep(60)  # Hata durumunda 1 dakika bekle

def is_valid_symbol(symbol, client):
    try:
        ticker=client.get_symbol_ticker(symbol=symbol)
        print(ticker)
        return True
    except Exception as e:
        print(f"{symbol} için hata: {e}")
        return False
def split_USDT(symbol):
    # 'USDT' ile biten sembolü ayır
    if symbol.endswith('USDT'):
        return symbol[:-4]  # Son 4 karakteri ('USDT') çıkar
    return symbol

def buy(symbol, quantity):
    # Burada alım işlemi için Binance API çağrısı yapılacak
    order = client.order_market_buy(symbol=symbol, quantity=quantity)
    return order

def sell(symbol, quantity):
   
    try:
        order = client.order_market_sell(symbol=symbol, quantity=quantity)
        return order
    except Exception as e:
        print(f"Satış işlemi sırasında bir hata oluştu: {e}",symbol)
        # Hata mesajını log dosyasına yazabilirsiniz.
        log_to_file(f"Satış işlemi hatası: {e}")
        # Burada ek hata yönetimi kodları olabilir.
        # Örneğin, hatanın türüne bağlı olarak farklı aksiyonlar alabilirsiniz.
        return None
def get_balance(asset):
    # 'asset' parametresi, bakiyesini almak istediğiniz varlığın sembolüdür (örneğin 'BTC').
    balance = client.get_asset_balance(asset=asset)
    return balance
def get_trade_history(symbol):
    trades = client.get_my_trades(symbol=symbol)
    for trade in trades:
        print(f"Time: {trade['time']}, Symbol: {trade['symbol']}, Quantity: {trade['qty']}, Price: {trade['price']}, Is Buyer: {trade['isBuyer']}")

def get_last_trade_details(symbol, is_buyer):
    trades = client.get_my_trades(symbol=symbol)
    last_trade = None

    for trade in reversed(trades):
        if trade['isBuyer'] == is_buyer:
            last_trade = trade
            break

    if last_trade is not None:
        return {"time":last_trade['time'],"quantity": last_trade['qty'], "price": last_trade['price']}
    else:
        return ''


def split_symbol(symbol):
    asset, _ = symbol.split('/')
    return asset

def format_value(value, precision):
    """ Verilen değeri, belirtilen hassasiyet değerine göre yuvarlar """
    factor = 10 ** precision
    return floor(value * factor) / factor


def execute_buy_order(symbol, current_price, required_amount):
    quote_asset = "USDT"
    formatted_symbol = symbol

    # Hassasiyet bilgilerini al
    info = client.get_exchange_info()
    symbol_info = [s for s in info['symbols'] if s['symbol'] == formatted_symbol][0]
    price_filter = [f for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER'][0]
    lot_size_filter = [f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'][0]

    price_precision = int(price_filter['tickSize'].find('1') - 1)
    quantity_precision = int(lot_size_filter['stepSize'].find('1') - 1)

    # Alım yapılacak miktarı belirle
    buy_quantity = format_value(required_amount / current_price, quantity_precision)

    if buy_quantity == 0:
        print("Yeterli bakiye yok veya alınacak miktar 0. Alım işlemi gerçekleştirilemiyor.")
        return None, None

    try:
        # Alım emrini ver
        order = client.order_limit_buy(symbol=formatted_symbol, quantity=buy_quantity, price=current_price)
        print(f"Alım emri verildi: Fiyat: {current_price}, Miktar: {buy_quantity}")
        
        stop_loss_price = current_price * (1 - stop_loss_percentage)
        take_profit_price = current_price * (1 + take_profit_percentage)

        # Emrin tamamlanmasını bekle (veya belirli bir süre)
        time.sleep(30)  # 30 saniye bekle
        return stop_loss_price, take_profit_price
    except BinanceAPIException as e:
        print(f"Alım işlemi sırasında hata oluştu: {e}")
        return None, None
   
        


def execute_sell_orders(symbol):
    base_asset = split_USDT(symbol)
    formatted_symbol = symbol

    try:
        # Get exchange information
        info = client.get_exchange_info()
        symbol_info = [s for s in info['symbols'] if s['symbol'] == formatted_symbol][0]
        lot_size_filter = [f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'][0]
        min_lot_size = float(lot_size_filter['minQty'])
        quantity_precision = int(lot_size_filter['stepSize'].find('1') - 1)

        # Check account balance
        balance = float(client.get_asset_balance(asset=base_asset)['free'])
        if balance < min_lot_size:
            print("Insufficient balance to place a sell order.")
            return

        # Get order book and determine sell quantity
        depth = client.get_order_book(symbol=formatted_symbol)
        for bid in depth['bids']:
            bid_price = float(bid[0])
            bid_quantity = float(bid[1])
            sell_quantity = min(balance, bid_quantity)
            sell_quantity = format_value(sell_quantity, quantity_precision)

            if sell_quantity >= min_lot_size:
                # Place sell order
                order = client.order_limit_sell(symbol=formatted_symbol, quantity=sell_quantity, price=bid_price)
                print(f"Placed sell order: Price = {bid_price}, Quantity = {sell_quantity}")
                balance -= sell_quantity
                if balance < min_lot_size:
                    break
            else:
                print("Sell quantity below minimum lot size.")
        
        time.sleep(60)  # Wait for 60 seconds
    except BinanceAPIException as e:
        print(f"Error during sell order: {e}")
        log_to_file(f"Error during sell order: {symbol},{e}")  # Hata mesajını dosyaya yaz
