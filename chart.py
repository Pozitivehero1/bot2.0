import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import tempfile
import os
import logging

logger = logging.getLogger(__name__)

def generate_chart(symbol, raw_data, basic):
    """
    Генерирует свечной график с EMA20/EMA50 и сохраняет во временный PNG-файл.
    raw_data может быть DataFrame или список списков.
    Возвращает путь к файлу.
    """
    if raw_data is None:
        return None
    
    try:
        # Если raw_data - DataFrame, используем его
        if isinstance(raw_data, pd.DataFrame):
            df = raw_data.copy()
            # Убедимся, что индекс - datetime
            if not isinstance(df.index, pd.DatetimeIndex):
                if 'timestamp' in df.columns:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
                else:
                    logger.error("DataFrame must have DatetimeIndex or 'timestamp' column")
                    return None
        else:
            # Предполагаем список списков, как раньше
            df = pd.DataFrame(raw_data)
            df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume',
                          'close_time', 'quote_asset_volume', 'number_of_trades',
                          'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore']
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
        
        # Берём последние 100 свечей
        df = df.tail(100)
        if len(df) < 10:
            logger.warning("Not enough data for chart")
            return None
        
        # Добавляем EMA
        df['EMA20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['EMA50'] = df['close'].ewm(span=50, adjust=False).mean()
        
        # Строим график
        apds = [
            mpf.make_addplot(df['EMA20'], color='orange', width=0.7),
            mpf.make_addplot(df['EMA50'], color='blue', width=0.7),
        ]
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        mpf.plot(df, type='candle', style='charles',
                 addplot=apds, volume=True,
                 title=f'{basic} (USDT) 15m Chart',
                 ylabel='Price (USDT)',
                 savefig=temp_path,
                 figsize=(10, 6))
        return temp_path
    except Exception as e:
        logger.error(f"Chart generation error: {e}")
        return None