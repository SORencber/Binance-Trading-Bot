import pandas as pd
import talib


def start_model(df):
            if 'Close' not in df.columns:
                # Hata mesajı yazdır ve fonksiyonu sonlandır
                print(f"'Close' column not found in DataFrame.")
                return None, None, None
            # Diğer işlemler...

            df['Close'] = pd.to_numeric(df['Close'])
            df['High'] = pd.to_numeric(df['High'])
            df['Low'] = pd.to_numeric(df['Low'])
            #print(df['Low'])

            # Teknik Göstergeleri Hesapla
           
            upper_band, middle_band, lower_band = talib.BBANDS(df['Close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
           # print(upper_band, middle_band, lower_band)
            df['upper_band'] = upper_band
            df['middle_band'] = middle_band
            df['lower_band'] = lower_band
            # RSI, MACD ve Bollinger Bantları ayarları
            df['RSI'] = talib.RSI(df['Close'], timeperiod=10)
            df['MACD'], df['MACD_Signal'], df['MACD_Hist'] = talib.MACD(df['Close'], fastperiod=9, slowperiod=19, signalperiod=9)

            # RSI ve MACD sinyallerini değerlendirme
            rsi_buy_signal = df['RSI'] < 20
            rsi_sell_signal = df['RSI'] > 80
            macd_buy_signal = (df['MACD'] > df['MACD_Signal'])
            macd_sell_signal = (df['MACD'] < df['MACD_Signal'])

            # Bollinger Bantlarına göre alım/satım sinyalleri
            bollinger_buy_signal = df['Close'] < df['lower_band']
            bollinger_sell_signal = df['Close'] > df['upper_band'] 
            current_price = df['Close'].iloc[-1]
            high_price = df['High'].max()
            low_price = df['Low'].min()
            fibonacci_levels = calculate_fibonacci_levels(high_price, low_price)
            # Fiyatın Fibonacci seviyelerine göre konumu
            fibonacci_buy_signal = df['Close'].iloc[-1] < fibonacci_levels['Level 23.6%']
            fibonacci_sell_signal = df['Close'].iloc[-1] > fibonacci_levels['Level 23.6%']

            # Sinyallerin kombinasyonu
            combined_buy_signal = rsi_buy_signal & macd_buy_signal & bollinger_buy_signal
            combined_sell_signal = rsi_sell_signal & macd_sell_signal & bollinger_sell_signal

            # Kombine sinyalleri güncelle
            combined_buy_signal = combined_buy_signal & fibonacci_buy_signal
            combined_sell_signal = combined_sell_signal & fibonacci_sell_signal
             # Alım veya satım kararını belirle
            if combined_buy_signal.iloc[-1]:
                action = 'buy'
            elif combined_sell_signal.iloc[-1]:
                action = 'sell'
            else:
                action = 'hold'
            # print(action, current_price,  {
            #                                 'current_price': current_price,
            #                                 'Bollinger Bands': {
            #                                     'upper_band': upper_band,
            #                                     'middle_band': middle_band,
            #                                     'lower_band': lower_band
            #                                 },
            #                                 'RSI': df['RSI'],
            #                                 'MACD': {
            #                                     'MACD': df['MACD'],
            #                                     'MACD_Signal': df['MACD_Signal'],
            #                                     'MACD_Hist': df['MACD_Hist']
            #                                 },
            #                                 'Fibonacci Levels': calculate_fibonacci_levels(high_price, low_price)
            #                             })
            return action, current_price,  {
                                            'current_price': current_price,
                                            'Bollinger Bands': {
                                                'upper_band': upper_band,
                                                'middle_band': middle_band,
                                                'lower_band': lower_band
                                            },
                                            'RSI': df['RSI'],
                                            'MACD': {
                                                'MACD': df['MACD'],
                                                'MACD_Signal': df['MACD_Signal'],
                                                'MACD_Hist': df['MACD_Hist']
                                            },
                                            'Fibonacci Levels': calculate_fibonacci_levels(high_price, low_price)
                                        }


def calculate_fibonacci_levels(high, low):
    difference = high - low
    return {
        'Level 23.6%': high - difference * 0.236,
        'Level 38.2%': high - difference * 0.382,
        'Level 50%': high - difference * 0.5,
        'Level 61.8%': high - difference * 0.618
    }
def analyzer(coins_data):
    best_coin = None
    best_score = float('-inf')  # Initialize with a very low score
    scored_coins = {}
    for coin, df in coins_data.items():
        #print(coin)
        action, current_price, indicators = start_model(df)
        #print(coin,action, current_price, indicators)
        
        # Evaluate the coin based on its indicators and action
        # The scoring system can be adjusted based on your strategy
        
        score = evaluate_coin(indicators, action)
        scored_coins[coin] = score
        # Sort and get top 10 coins
    top_coins = sorted(scored_coins, key=scored_coins.get, reverse=True)[:10]
    #print(top_coins)
    return top_coins

    #return best_coin

def evaluate_coin(indicators, action):
    score = 0   
    some_threshold = 0.01  # Örnek eşik değeri, ihtiyacınıza göre ayarlayın

    if action == 'buy':
        score += 1  # Basit puanlama
    # Bollinger Bantlarına göre puanlama
    if (indicators['Bollinger Bands']['lower_band'].iloc[-1] - indicators['current_price']) > some_threshold:
        score += 1
    # RSI'ya göre puanlama
    if indicators['RSI'].iloc[-1] < 30:
        score += 1
    # MACD'ye göre puanlama
    if indicators['MACD']['MACD_Hist'].iloc[-1] > 0:
        score += 1
    # Benzer şekilde diğer göstergeler için de puanlama yapılabilir
    return score

