import os
import time
from binance.client import Client
import pandas as pd
import numpy as np
import threading
import teknikgosterge
from datetime import datetime
from math import floor


# Binance API ve Gizli Anahtarları
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')

# Binance Client'ını başlat
client = Client(api_key, api_secret)
server_time = client.get_server_time()
client.timestamp_offset = server_time['serverTime'] - int(time.time() * 1000)
stop_loss_percentage = 0.05  # %5 stop-loss
take_profit_percentage = 0.10  # %10 take-profit

def log_to_file(message):
    with open("bot_log.txt", "a+", encoding='utf-8') as file:  # UTF-8 kodlaması ile dosya açma
        file.write(message + "\n")  # Mesajı dosyaya yaz

def run_bot(symbol, interval):

    i = 0
    asset = split_symbol(symbol)
   
    balance = get_balance(asset)
   
    formatted_symbol = symbol.replace('/', '')
    get_trade_history(formatted_symbol)
    stop_loss_price = None
    take_profit_price = None
    while True:
        try:
           
            i += 1
            print(f"AI Bot {symbol} {interval} -> Çalışma #{i}")
            print(f"{time.strftime('%Y-%m-%d %H:%M:%S')}-{asset} Bakiyesi:", balance)
           # print(f"{asset}-Gecmisi :", history)
            open_orders = client.get_open_orders(symbol=formatted_symbol)
            for order in open_orders:
             print(order)
            # Verileri çek
            klines = client.get_historical_klines(formatted_symbol, interval, "5000 minutes ago UTC")
            df = pd.DataFrame(klines, columns=['Open time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume', 'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'])
            #current_price = df['Close'].iloc[-1]
            current_time = datetime.now()
           
            ticker = client.get_symbol_ticker(symbol=formatted_symbol)
            current_price = float(ticker['price'])

          
            action, current_price, fibonacci_levels =  teknikgosterge.start_model(df)
            # Alım/Satım işlemleri için gelişmiş karar mekanizması
            free_balance = float(balance['free'])
       
            if stop_loss_price is not None and take_profit_price is not None:
                            if current_price <= stop_loss_price or current_price >= take_profit_price:
                                action = 'sell'
        
        
            if action == 'buy':
                print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {symbol} {interval} -> Güçlü Alım Sinyali ( {current_price})")                     
                last_buy = get_last_trade_details(formatted_symbol, True)  # En son alım işlemi için
                if(len(last_buy)>0):     
                    print("En son alım:", last_buy)
                    my_last_buy_price = float(last_buy['price'])
                    my_last_buy_quantity = float(last_buy['quantity'])
                    my_last_buy_time = last_buy['time']
                    
                stop_loss_price, take_profit_price =execute_buy_order(symbol, client,current_price, float(last_buy['price']))

                  
                   

            elif action == 'sell':

                print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {symbol} {interval} -> Güçlü Satım Sinyali ( { current_price})")
                last_buy = get_last_trade_details(formatted_symbol, True)  # En son alım işlemi için
                if(len(last_buy)>0):     
                    print("En son alım:", last_buy)
                    my_last_buy_price = float(last_buy['price'])
                    my_last_buy_quantity = float(last_buy['quantity'])
                    my_last_buy_time = last_buy['time']
                    
                    profit =my_last_buy_price+ (my_last_buy_price*0.010)
                    free_balance = float(balance['free'])
                    print("Beklenen Miktar",profit)
                    if(float(current_price)>profit and free_balance>0):
                        
                        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {symbol} {interval} -> Satım gerceklesiyor ( { current_price})")
                        log_message = f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {symbol} {interval} ->  Satım gerceklesiyor: {current_price}"
                        log_to_file(log_message)  # Log mesajını dosyaya yaz
                        order = sell(formatted_symbol, free_balance)
                        print(order)
                    
                        #return order
                        #for order in open_orders:
                        #  client.cancel_order(symbol=formatted_symbol, orderId=order['orderId'])
                        #   balance_info = get_balance(asset)
                        #  free_balance = float(balance_info['free'])  
                            #  print(f"{asset} Free Quantity:", balance_info)
                            #  sell(symbol, free_balance)
                    else:
                        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {symbol} {interval} -> Güçlü Satım Sinyali icin son yüksek alimlara bak  ( { current_price})")
                        log_message = f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {symbol} {interval} -> Güçlü Satım Sinyali: {current_price}"
                        log_to_file(log_message)  # Log mesajını dosyaya yaz
                        execute_sell_orders(symbol, client,my_last_buy_price)
                    
            else:
                # Bekleme aksiyonu
                print("Şu an için bir işlem yapılmasına gerek yok.")         
                    
            time.sleep(10)  # 5 dakika bekle

        except Exception as e:
            error_message = f"{time.strftime('%Y-%m-%d %H:%M:%S')} - Hata: {str(e)}, Satır: {e.__traceback__.tb_lineno}"
            log_to_file(error_message)  # Hata mesajını dosyaya yaz
            print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} Bir hata oluştu: {e}, Satır: {e.__traceback__.tb_lineno}")
            time.sleep(60)  # Hata durumunda 1 dakika bekle

def start_bot(psymbol, pinterval):
    bot_thread = threading.Thread(target=run_bot, args=(psymbol, pinterval))
    bot_thread.start()
    return {"message": f"AI Bot {psymbol} {pinterval} için başlatıldı"}

def buy(symbol, quantity):
    # Burada alım işlemi için Binance API çağrısı yapılacak
    order = client.order_market_buy(symbol=symbol, quantity=quantity)
    return order

def sell(symbol, quantity):
    # Burada satım işlemi için Binance API çağrısı yapılacak
    order = client.order_market_sell(symbol=symbol, quantity=quantity)
    return order
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


def execute_buy_order(symbol, client,current_price,my_last_price):
    base_asset, quote_asset = symbol.split('/')  # Örneğin 'BTC/USDT' için 'BTC' ve 'USDT'
    formatted_symbol = symbol.replace('/', '')

    # Hassasiyet bilgilerini al
    info = client.get_exchange_info()
    symbol_info = [s for s in info['symbols'] if s['symbol'] == formatted_symbol][0]
    price_filter = [f for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER'][0]
    lot_size_filter = [f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'][0]

    price_precision = int(price_filter['tickSize'].find('1') - 1)
    quantity_precision = int(lot_size_filter['stepSize'].find('1') - 1)

    while True:
        # Piyasa derinliğini al ve değerleri yuvarla
        depth = client.get_order_book(symbol=formatted_symbol)
        best_ask_price = format_value(float(depth['asks'][0][0]), price_precision)
        best_ask_quantity = format_value(float(depth['asks'][0][1]), quantity_precision)
        #bid_price = format_value(float(depth['bids'][0]), price_precision)
        highest_bid = max(depth['bids'], key=lambda x: float(x[0]))
         
        highest_bid_price = float(highest_bid[0])
        highest_bid_quantity = float(highest_bid[1])

        print(f"En yüksek alım emri: Fiyat: {highest_bid_price}, Miktar: {highest_bid_quantity}")
        print("Son ticker fiyat",current_price)
        print("EN düsük satis miktari", best_ask_price)
        print("EN düsük satisin  adedi", best_ask_quantity)

        # Hesap bakiyesini kontrol et
        balance = float(client.get_asset_balance(asset=quote_asset)['free'])
        print("Balance", balance)
        # Alabileceğiniz maksimum miktarı hesapla ve yuvarla
        max_buy_quantity = format_value(balance / best_ask_price, quantity_precision)
       
        # Alım yapılacak miktarı belirle
        buy_quantity = min(best_ask_quantity, max_buy_quantity)
        Icanthis= my_last_price-(my_last_price*0.02)
       
        if Icanthis>best_ask_price and buy_quantity * best_ask_price > balance or buy_quantity == 0:
            print("Yeterli bakiye yok veya alınacak miktar 0. Alım işlemi gerçekleştirilemiyor.")
            break  # Döngüden çık, ama fonksiyonu tamamen bitir

        # Alım emrini ver
        order = client.order_limit_buy(symbol=formatted_symbol, quantity=buy_quantity, price=best_ask_price)
        print(f"Alım emri verildi: Fiyat: {best_ask_price}, Miktar: {buy_quantity}")
        
        stop_loss_price = best_ask_price * (1 - stop_loss_percentage)
        take_profit_price = current_price * (1 + take_profit_percentage)

        return stop_loss_price,take_profit_price
        # Emrin tamamlanmasını bekle (veya belirli bir süre)
        time.sleep(60)  # 60 saniye bekle


def execute_sell_orders(symbol, client,my_last_buy_price):
    base_asset, quote_asset = symbol.split('/')  # Örneğin 'BTC/USDT' için 'BTC' ve 'USDT'
    formatted_symbol = symbol.replace('/', '')

    # Hassasiyet bilgilerini al
    info = client.get_exchange_info()
    symbol_info = [s for s in info['symbols'] if s['symbol'] == formatted_symbol][0]
    price_filter = [f for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER'][0]
    lot_size_filter = [f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE'][0]

    price_precision = int(price_filter['tickSize'].find('1') - 1)
    quantity_precision = int(lot_size_filter['stepSize'].find('1') - 1)

    # Hesap bakiyesini kontrol et
    balance = float(client.get_asset_balance(asset=base_asset)['free'])

    # Eğer satılacak coin yoksa işlemi sonlandır
    if balance <= 0:
        print("Satılacak coin yok.")
        return

    # Piyasa derinliğini al
    depth = client.get_order_book(symbol=formatted_symbol)
    profit =my_last_buy_price+ (my_last_buy_price*0.005)
    highest_bid = max(depth['bids'], key=lambda x: float(x[0]))
    highest_bid_price = float(highest_bid[0])
    highest_bid_quantity = float(highest_bid[1])
    print("en yüksek alim:",highest_bid_price)
    print("beklenen miktar:",profit)
    # Bakiyenizdeki miktarı satana kadar en yüksek alım emirlerini incele
    for bid in depth['bids']:
        bid_price = format_value(float(bid[0]), price_precision)
        bid_quantity = format_value(float(bid[1]), quantity_precision)
      
        if(bid_price>profit):
            # Satılacak miktarı belirle ve yuvarla
            sell_quantity = format_value(min(balance, bid_quantity), quantity_precision)

            # Satış emrini ver
            order = client.order_limit_sell(symbol=formatted_symbol, quantity=sell_quantity, price=bid_price)
            print(f"Satış emri verildi: Fiyat: {bid_price}, Miktar: {sell_quantity}")

            # Güncel bakiyeyi güncelle
            balance -= sell_quantity

            if balance <= 0:
                break  # Bakiye bittiğinde döngüyü sonlandır

            # Emrin tamamlanmasını bekle (veya belirli bir süre)
            time.sleep(60)  # 60 saniye bekle
