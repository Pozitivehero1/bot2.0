import os
import sys
import logging
import random
from typing import List, Optional
from datetime import datetime

from data import get_data
from indicators import calculate_multi_timeframe, MultiTimeframeIndicators
from filters import get_top_candidates, score_signal
from writer import generate_post_with_memory
from publisher import publish
from trend import get_trending_symbols, get_base_asset
from history import get_recently_published, add_published, cleanup_history
from chart import generate_chart
from memory import PostMemory
from quality import PostQualityEvaluator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    cleanup_history()
    
    symbols = get_trending_symbols(limit=100)
    logger.info(f"Trending symbols: {len(symbols)}")
    if not symbols:
        logger.error("No symbols found")
        return
    
    recent = get_recently_published(minutes=180)
    symbols = [s for s in symbols if s not in recent]
    logger.info(f"After filtering recently published: {len(symbols)}")
    if not symbols:
        logger.info("No new symbols to analyze")
        return
    
    candidates = []
    for sym in symbols:
        logger.info(f"Analyzing {sym}")
        try:
            timeframes = ['15m', '1h', '4h', '1d']
            dataframes = {}
            for tf in timeframes:
                df = get_data(sym, interval=tf, limit=200)
                if df is not None:
                    dataframes[tf] = df
            if not dataframes:
                logger.warning(f"No data for {sym}")
                continue
            
            mtf = calculate_multi_timeframe(sym, dataframes)
            if mtf.tf_15m is None:
                logger.warning(f"No 15m data for {sym}")
                continue
            candidates.append(mtf)
        except Exception as e:
            logger.error(f"Error analyzing {sym}: {e}")
            continue
    
    logger.info(f"Candidates with data: {len(candidates)}")
    if not candidates:
        logger.info("No candidates after analysis")
        return
    
    top = get_top_candidates(candidates, top_n=1)
    if not top:
        logger.info("No candidates passed the score threshold")
        return
    
    best_mtf, best_score = top[0]
    symbol = best_mtf.symbol
    basic = get_base_asset(symbol)
    logger.info(f"Best candidate: {symbol} with score {best_score.total:.1f}")
    
    # Получаем DataFrame для графика (передаём напрямую)
    raw_data = get_data(symbol, interval='15m', limit=200)
    if raw_data is None:
        logger.error("No raw data for chart")
        raw_data = None
    
    memory = PostMemory()
    
    post_text = generate_post_with_memory(
        symbol=symbol,
        basic=basic,
        mtf=best_mtf,
        score=best_score,
        memory=memory
    )
    
    evaluator = PostQualityEvaluator()
    quality = evaluator.evaluate(post_text)
    if quality < 70:
        logger.warning(f"Post quality low ({quality:.1f}), but continuing...")
    
    chart_path = generate_chart(symbol, raw_data, basic)  # передаём DataFrame
    if chart_path:
        logger.info(f"Chart generated: {chart_path}")
    else:
        logger.warning("Chart generation failed")
    
    success = publish(post_text, image_path=chart_path)
    if success:
        add_published(symbol)
        memory.add_post(symbol, post_text)
        logger.info(f"Published post for {symbol}")
    else:
        logger.error("Publication failed")
    
    if chart_path and os.path.exists(chart_path):
        os.remove(chart_path)
        logger.debug("Cleaned up chart file")

if __name__ == "__main__":
    main()