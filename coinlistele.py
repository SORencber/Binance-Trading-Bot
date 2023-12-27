import os
from binance.client import Client
import pandas as pd
import teknikgosterge  # Teknik analiz için özel modül

# API ve Gizli Anahtarları Ayarla
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')
client = Client(api_key, api_secret)
X=  0.05

def get_trending_coins():
    tickers = client.get_ticker()
    # Sadece 'USDT' ile biten semboller üzerinde işlem yap
    trending = [ticker for ticker in tickers if ticker['symbol'].endswith('USDT') and float(ticker['priceChangePercent']) > X]
    #print(trending)
    return trending[:20]

def analyze_coins(coins):
    # Her bir coin için veriyi DataFrame'e dönüştür ve sözlüğe ekle
    coins_data = {}
    for coin in coins:
        symbol = coin['symbol']
        
        klines = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1HOUR, "30 days ago UTC")
        df = pd.DataFrame(klines, columns=['Open time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume', 'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'])
        # DataFrame'i düzenle ve coins_data sözlüğüne ekle
        coins_data[symbol] = df

    top_coins = teknikgosterge.analyzer(coins_data)
    filtered_coins = [coin for coin in top_coins if coin not in ["BTCUSDT", "ETHUSDT"]]

    print("En iyi performans gösteren coinler:", top_coins)
    return filtered_coins
    
def main():
    trending_coins = get_trending_coins()
    result=analyze_coins(trending_coins)
    return result

if __name__ == "__main__":
    main()
