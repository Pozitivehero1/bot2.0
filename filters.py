import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from indicators import MultiTimeframeIndicators, IndicatorResult

logger = logging.getLogger(__name__)

@dataclass
class SignalScore:
    total: float          # общий скор (0-100)
    trend: float          # трендовые индикаторы
    momentum: float       # моментум
    volatility: float     # волатильность
    volume: float         # объём
    pattern: float        # паттерны (пробои, свипы и т.д.)
    multi_tf: float       # согласованность таймфреймов
    confidence: float     # уверенность (из индикаторов)
    risk_reward: float    # риск/прибыль

class SignalFilter:
    def __init__(self, min_score: float = 25.0):
        self.min_score = min_score
    
    def evaluate(self, mtf: MultiTimeframeIndicators) -> Optional[SignalScore]:
        if not mtf.tf_15m:
            logger.warning(f"No 15m data for {mtf.symbol}, cannot evaluate")
            return None
        
        ind = mtf.tf_15m
        tf1h = mtf.tf_1h
        tf4h = mtf.tf_4h
        tfd = mtf.tf_1d
        
        score_trend = self._score_trend(ind, tf1h, tf4h, tfd)
        score_momentum = self._score_momentum(ind, tf1h, tf4h, tfd)
        score_volatility = self._score_volatility(ind)
        score_volume = self._score_volume(ind)
        score_pattern = self._score_pattern(ind)
        score_multi_tf = self._score_multi_tf(ind, tf1h, tf4h, tfd)
        score_confidence = mtf.confidence_score / 100.0 * 100.0
        score_rr = self._score_risk_reward(ind)
        
        total = (score_trend * 0.25 +
                 score_momentum * 0.20 +
                 score_volatility * 0.10 +
                 score_volume * 0.10 +
                 score_pattern * 0.15 +
                 score_multi_tf * 0.10 +
                 score_confidence * 0.05 +
                 score_rr * 0.05)
        
        return SignalScore(
            total=total,
            trend=score_trend,
            momentum=score_momentum,
            volatility=score_volatility,
            volume=score_volume,
            pattern=score_pattern,
            multi_tf=score_multi_tf,
            confidence=score_confidence,
            risk_reward=score_rr
        )
    
    def _score_trend(self, ind: IndicatorResult, tf1h, tf4h, tfd) -> float:
        score = 0.0
        if ind.ema20 > ind.ema50:
            score += 25
        if ind.ema50 > ind.ema200:
            score += 20
        if ind.adx > 25:
            score += 20
        if ind.macd > ind.macd_signal:
            score += 20
        if ind.price > ind.ema20:
            score += 15
        return min(score, 100.0)
    
    def _score_momentum(self, ind: IndicatorResult, tf1h, tf4h, tfd) -> float:
        score = 0.0
        if 50 <= ind.rsi <= 70:
            score += 30
        elif ind.rsi > 70:
            score += 10
        elif ind.rsi < 30:
            score += 5
        if ind.cci > 0:
            score += 20
        if ind.stoch_rsi_k > ind.stoch_rsi_d:
            score += 20
        if ind.change_1h > 0:
            score += 15
        if ind.change_4h > 0:
            score += 15
        return min(score, 100.0)
    
    def _score_volatility(self, ind: IndicatorResult) -> float:
        score = 0.0
        atr_pct = ind.atr / ind.price * 100
        if atr_pct > 0.5:
            score += 40
        elif atr_pct > 0.3:
            score += 20
        if ind.price < ind.bb_low * 1.02:
            score += 30
        elif ind.price > ind.bb_high * 0.98:
            score += 30
        else:
            score += 15
        return min(score, 100.0)
    
    def _score_volume(self, ind: IndicatorResult) -> float:
        score = 0.0
        if ind.volume_relative > 1.5:
            score += 50
        elif ind.volume_relative > 1.2:
            score += 30
        else:
            score += 10
        if ind.volume_relative > 1.0:
            score += 30
        return min(score, 100.0)
    
    def _score_pattern(self, ind: IndicatorResult) -> float:
        score = 0.0
        if ind.breakout_up:
            score += 30
        elif ind.breakout_down:
            score += 20
        if ind.liquidity_sweep:
            score += 25
        if ind.pullback:
            score += 25
        if ind.trend_continuation:
            score += 20
        if ind.false_breakout:
            score += 10
        return min(score, 100.0)
    
    def _score_multi_tf(self, ind: IndicatorResult, tf1h, tf4h, tfd) -> float:
        trend_15m = ind.ema20 > ind.ema50
        aligns = 0
        total = 0
        if tf1h is not None:
            total += 1
            if trend_15m == (tf1h.ema20 > tf1h.ema50):
                aligns += 1
        if tf4h is not None:
            total += 1
            if trend_15m == (tf4h.ema20 > tf4h.ema50):
                aligns += 1
        if tfd is not None:
            total += 1
            if trend_15m == (tfd.ema20 > tfd.ema50):
                aligns += 1
        if total > 0:
            return (aligns / total) * 100
        return 50.0
    
    def _score_risk_reward(self, ind: IndicatorResult) -> float:
        rr = ind.risk_reward
        if rr >= 3.0:
            return 100
        elif rr >= 2.0:
            return 70
        elif rr >= 1.5:
            return 50
        elif rr >= 1.0:
            return 30
        else:
            return 10

def score_signal(mtf: MultiTimeframeIndicators) -> float:
    filter_obj = SignalFilter()
    score = filter_obj.evaluate(mtf)
    return score.total if score else 0.0

def get_top_candidates(mtf_list: List[MultiTimeframeIndicators], top_n: int = 5) -> List[Tuple[MultiTimeframeIndicators, SignalScore]]:
    filter_obj = SignalFilter()
    scored = []
    for mtf in mtf_list:
        s = filter_obj.evaluate(mtf)
        if s and s.total >= filter_obj.min_score:
            scored.append((mtf, s))
    scored.sort(key=lambda x: x[1].total, reverse=True)
    return scored[:top_n] 

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from indicators import MultiTimeframeIndicators, IndicatorResult

logger = logging.getLogger(__name__)

@dataclass
class SignalScore:
    total: float          # общий скор (0-100)
    trend: float          # трендовые индикаторы
    momentum: float       # моментум
    volatility: float     # волатильность
    volume: float         # объём
    pattern: float        # паттерны (пробои, свипы и т.д.)
    multi_tf: float       # согласованность таймфреймов
    confidence: float     # уверенность (из индикаторов)
    risk_reward: float    # риск/прибыль

class SignalFilter:
    def __init__(self, min_score: float = 25.0):
        self.min_score = min_score
    
    def evaluate(self, mtf: MultiTimeframeIndicators) -> Optional[SignalScore]:
        if not mtf.tf_15m:
            logger.warning(f"No 15m data for {mtf.symbol}, cannot evaluate")
            return None
        
        ind = mtf.tf_15m
        tf1h = mtf.tf_1h
        tf4h = mtf.tf_4h
        tfd = mtf.tf_1d
        
        score_trend = self._score_trend(ind, tf1h, tf4h, tfd)
        score_momentum = self._score_momentum(ind, tf1h, tf4h, tfd)
        score_volatility = self._score_volatility(ind)
        score_volume = self._score_volume(ind)
        score_pattern = self._score_pattern(ind)
        score_multi_tf = self._score_multi_tf(ind, tf1h, tf4h, tfd)
        score_confidence = mtf.confidence_score / 100.0 * 100.0
        score_rr = self._score_risk_reward(ind)
        
        total = (score_trend * 0.25 +
                 score_momentum * 0.20 +
                 score_volatility * 0.10 +
                 score_volume * 0.10 +
                 score_pattern * 0.15 +
                 score_multi_tf * 0.10 +
                 score_confidence * 0.05 +
                 score_rr * 0.05)
        
        return SignalScore(
            total=total,
            trend=score_trend,
            momentum=score_momentum,
            volatility=score_volatility,
            volume=score_volume,
            pattern=score_pattern,
            multi_tf=score_multi_tf,
            confidence=score_confidence,
            risk_reward=score_rr
        )
    
    def _score_trend(self, ind: IndicatorResult, tf1h, tf4h, tfd) -> float:
        score = 0.0
        if ind.ema20 > ind.ema50:
            score += 25
        if ind.ema50 > ind.ema200:
            score += 20
        if ind.adx > 25:
            score += 20
        if ind.macd > ind.macd_signal:
            score += 20
        if ind.price > ind.ema20:
            score += 15
        return min(score, 100.0)
    
    def _score_momentum(self, ind: IndicatorResult, tf1h, tf4h, tfd) -> float:
        score = 0.0
        if 50 <= ind.rsi <= 70:
            score += 30
        elif ind.rsi > 70:
            score += 10
        elif ind.rsi < 30:
            score += 5
        if ind.cci > 0:
            score += 20
        if ind.stoch_rsi_k > ind.stoch_rsi_d:
            score += 20
        if ind.change_1h > 0:
            score += 15
        if ind.change_4h > 0:
            score += 15
        return min(score, 100.0)
    
    def _score_volatility(self, ind: IndicatorResult) -> float:
        score = 0.0
        atr_pct = ind.atr / ind.price * 100
        if atr_pct > 0.5:
            score += 40
        elif atr_pct > 0.3:
            score += 20
        if ind.price < ind.bb_low * 1.02:
            score += 30
        elif ind.price > ind.bb_high * 0.98:
            score += 30
        else:
            score += 15
        return min(score, 100.0)
    
    def _score_volume(self, ind: IndicatorResult) -> float:
        score = 0.0
        if ind.volume_relative > 1.5:
            score += 50
        elif ind.volume_relative > 1.2:
            score += 30
        else:
            score += 10
        if ind.volume_relative > 1.0:
            score += 30
        return min(score, 100.0)
    
    def _score_pattern(self, ind: IndicatorResult) -> float:
        score = 0.0
        if ind.breakout_up:
            score += 30
        elif ind.breakout_down:
            score += 20
        if ind.liquidity_sweep:
            score += 25
        if ind.pullback:
            score += 25
        if ind.trend_continuation:
            score += 20
        if ind.false_breakout:
            score += 10
        return min(score, 100.0)
    
    def _score_multi_tf(self, ind: IndicatorResult, tf1h, tf4h, tfd) -> float:
        trend_15m = ind.ema20 > ind.ema50
        aligns = 0
        total = 0
        if tf1h is not None:
            total += 1
            if trend_15m == (tf1h.ema20 > tf1h.ema50):
                aligns += 1
        if tf4h is not None:
            total += 1
            if trend_15m == (tf4h.ema20 > tf4h.ema50):
                aligns += 1
        if tfd is not None:
            total += 1
            if trend_15m == (tfd.ema20 > tfd.ema50):
                aligns += 1
        if total > 0:
            return (aligns / total) * 100
        return 50.0
    
    def _score_risk_reward(self, ind: IndicatorResult) -> float:
        rr = ind.risk_reward
        if rr >= 3.0:
            return 100
        elif rr >= 2.0:
            return 70
        elif rr >= 1.5:
            return 50
        elif rr >= 1.0:
            return 30
        else:
            return 10

def score_signal(mtf: MultiTimeframeIndicators) -> float:
    filter_obj = SignalFilter()
    score = filter_obj.evaluate(mtf)
    return score.total if score else 0.0

def get_top_candidates(mtf_list: List[MultiTimeframeIndicators], top_n: int = 5) -> List[Tuple[MultiTimeframeIndicators, SignalScore]]:
    filter_obj = SignalFilter()
    scored = []
    for mtf in mtf_list:
        s = filter_obj.evaluate(mtf)
        if s and s.total >= filter_obj.min_score:
            scored.append((mtf, s))
    scored.sort(key=lambda x: x[1].total, reverse=True)
    return scored[:top_n]
