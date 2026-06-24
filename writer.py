import requests
import os
import random
import logging
from typing import List, Dict, Optional
from memory import PostMemory
from indicators import MultiTimeframeIndicators, IndicatorResult
from filters import SignalScore

logger = logging.getLogger(__name__)

MISTRAL_API = os.getenv("MISTRAL_API")
if not MISTRAL_API:
    logger.warning("MISTRAL_API environment variable not set")

# Большой набор хуков (более 300 комбинаций)
HOOKS = [
    "Внимание! {symbol} резко вырос/упал – что дальше?",
    "Только что произошло нечто важное для {symbol}",
    "Этот сигнал по {symbol} я ждал неделю",
    "Как заработать на движении {symbol}?",
    "Крупные игроки начали скупать {symbol}",
    "Технический анализ {symbol} – бычий разворот?",
    "Осторожно: {symbol} готовится к сильному движению",
    "Не упусти момент с {symbol}",
    "Что скрывает график {symbol}?",
    "Прибыльная возможность на {symbol}",
    "Как я нашел эту точку входа на {symbol}",
    "Почему я выбираю {symbol} сегодня",
    "Важное предупреждение по {symbol}",
    "История повторяется: {symbol} снова на уровне",
    "Мой прогноз по {symbol} на сегодня",
    "Смотрите, что происходит с {symbol}",
    "Кто следует за {symbol}?",
    "Этот паттерн на {symbol} предвещает рост",
    "Сегодня особенный день для {symbol}",
    "Как я использую {symbol} для заработка",
    "Топ-причина следить за {symbol}",
    "Разбор {symbol} – отличный момент",
    "Необычная активность на {symbol}",
    "Почему все говорят о {symbol}?",
    "Мой опыт торговли {symbol}",
    "Готовьтесь: {symbol} может удивить",
    "На что обратить внимание по {symbol}",
    "Движение {symbol} – что дальше?",
    "Сигнал для входа в {symbol}",
    "Рынок {symbol} подает знаки",
    "Взгляд на {symbol} от профессионала",
    "Как я анализирую {symbol}",
    "Этот инструмент показывает рост {symbol}",
    "Не пропустите движение {symbol}",
    "Что говорят индикаторы о {symbol}",
    "Критический момент для {symbol}",
    "Мой прогноз по {symbol} на неделю",
    "Как {symbol} может принести прибыль",
    "Следуй за ликвидностью – {symbol}",
    "Почему я не продаю {symbol}",
    "Идеальная точка входа в {symbol}",
    "Как {symbol} бьет рекорды",
    "Анализ настроений по {symbol}",
    "Используй шанс с {symbol}",
    "Что скрывается за движением {symbol}?",
    "Почему {symbol} недооценен",
    "Как я заработал на {symbol}",
    "Важный уровень на {symbol}",
    "Пора обратить внимание на {symbol}",
    "Сигнал для выхода из {symbol}",
    "Куда пойдет {symbol} сегодня?",
    "Обзор {symbol} – все детали",
    "Этот график говорит о росте {symbol}",
    "Как использовать {symbol} в портфеле",
    "Редкая возможность с {symbol}",
    "Почему {symbol} может обвалиться",
    "Как я защищаю свои позиции по {symbol}",
    "Прогноз {symbol} от эксперта",
    "Что будет, если {symbol} пробьет уровень?",
    "Мой секрет по {symbol}",
    "Время покупать {symbol}?",
    "Как {symbol} влияет на рынок",
    "Трейдеры выбирают {symbol}",
    "Этот сигнал по {symbol} – 90% точности",
    "Активность {symbol} зашкаливает",
    "Как {symbol} изменит ваш день",
    "Почему я ждал именно этого движения {symbol}",
    "Что делать с {symbol} сейчас",
    "История {symbol} повторяется",
    "Как я оцениваю {symbol}",
    "Ваш шанс с {symbol}",
    "Разбор движения {symbol}",
    "Как {symbol} обманывает многих",
    "Почему я ставлю на {symbol}",
    "Смотрите на {symbol} внимательнее",
    "Как {symbol} может стать вашим фаворитом",
    "Прогноз по {symbol} на день",
    "Кто управляет {symbol}?",
    "Как {symbol} удивил рынок",
    "Используйте момент с {symbol}",
    "Что важно знать о {symbol}",
    "Как я определяю тренд {symbol}",
    "Неожиданный поворот {symbol}",
    "Почему {symbol} в центре внимания",
    "Сигнал для сделки с {symbol}",
    "Анализ движения {symbol}",
    "Как {symbol} достиг максимума",
    "Секрет успеха {symbol}",
    "Что говорят киты о {symbol}",
    "Почему я держу {symbol}",
    "Лучший момент для {symbol}",
    "Как {symbol} обгоняет рынок",
    "Почему {symbol} опасен для слабых",
    "Как я читаю график {symbol}",
    "Этот паттерн на {symbol} – ключ",
    "Время действовать с {symbol}",
    "Прогноз {symbol} на ближайшие часы",
    "Что ждет {symbol} дальше",
    "Я покупаю {symbol} – вот почему",
    "Не упустите {symbol}",
    "Как {symbol} изменит правила игры",
    "Сигнал для входа в {symbol} сегодня",
    "Почему {symbol} стоит вашего внимания",
    "Как я зарабатываю на {symbol}",
]

CTA_LIST = [
    "А вы уже зашли в позицию?",
    "Что думаете по этому сигналу?",
    "Поделитесь своим мнением в комментариях",
    "Кто тоже торгует эту монету?",
    "Ждёте рост или падение?",
    "Какой у вас стоп-лосс?",
    "Кто уже в сделке?",
    "Какой ваш прогноз?",
    "Стоит ли брать этот сигнал?",
    "А вы согласны с анализом?",
    "Кто еще видит этот паттерн?",
    "Как думаете, пробьет уровень?",
    "Что по этому поводу думают трейдеры?",
    "Ждём комментариев!",
    "А у вас есть эта монета?",
    "Ставьте лайк, если тоже следите",
    "Ваше мнение очень важно!",
    "Какой таймфрейм вы используете?",
    "Согласны с целью?",
    "Может быть, я ошибаюсь?",
    "А вы как считаете?",
    "Ждем вашего фидбека!",
    "Кто уже взял?",
    "Какой ваш take-profit?",
    "Когда вы выйдете из сделки?",
    "У кого похожий анализ?",
    "Какие у вас риски?",
    "Какой процент вы рискуете?",
    "Это ваш фаворит?",
    "Кого еще анализируете?",
    "Как считаете, стоит докупить?",
    "Верите в рост?",
    "Что говорят ваши индикаторы?",
    "Какой новостной фон?",
    "Что скажете по этому уровню?",
]

STYLES = [
    "энергичный, с короткими предложениями, много эмодзи",
    "спокойный, аналитический, с цифрами",
    "разговорный, обращение к читателю, вопросы",
    "ироничный, с юмором, нестандартные сравнения",
    "вдохновляющий, с мотивацией",
    "с тревожным подтекстом, предупреждающий",
    "детальный, с объяснением каждого индикатора",
    "лаконичный, только суть, без воды",
    "эмоциональный, с восклицаниями",
    "уверенный, авторитетный, с фактами",
    "скептический, с сомнениями",
    "прогнозирующий, с конкретными цифрами",
]

STRUCTURES = [
    "hook → проблема → решение → вход → цели → стоп → вывод → CTA",
    "hook → анализ → сигнал → риск → цель → CTA",
    "hook → индикаторы → уровень → вход → цели → стоп → вывод → CTA",
    "hook → сценарий → вход → TP1/TP2/TP3 → стоп → вывод → CTA",
    "hook → новости → техника → вход → управление риском → CTA",
    "hook → эмоции → факты → вход → цели → стоп → вывод → CTA",
    "hook → вопрос → ответ → сигнал → риск → прибыль → CTA",
    "hook → история → паттерн → вход → цели → стоп → CTA",
]

def generate_post_with_memory(
    symbol: str,
    basic: str,
    mtf: MultiTimeframeIndicators,
    score: SignalScore,
    memory: PostMemory
) -> str:
    """Генерирует уникальный пост с использованием памяти и множества шаблонов."""
    
    # Извлекаем основные данные
    ind = mtf.tf_15m
    price = ind.price
    change = ind.change_1h
    rsi = ind.rsi
    ema20 = ind.ema20
    ema50 = ind.ema50
    ema200 = ind.ema200
    atr = ind.atr
    adx = ind.adx
    macd = ind.macd
    macd_signal = ind.macd_signal
    macd_hist = ind.macd_hist
    vwap = ind.vwap
    bb_high = ind.bb_high
    bb_low = ind.bb_low
    bb_mid = ind.bb_mid
    stoch_k = ind.stoch_rsi_k
    stoch_d = ind.stoch_rsi_d
    vol_rel = ind.volume_relative
    swing_high = ind.swing_high
    swing_low = ind.swing_low
    support = ind.support
    resistance = ind.resistance
    breakout_up = ind.breakout_up
    breakout_down = ind.breakout_down
    liquidity_sweep = ind.liquidity_sweep
    pullback = ind.pullback
    trend_cont = ind.trend_continuation
    false_breakout = ind.false_breakout
    atr_stop = ind.atr_stop
    risk_reward = ind.risk_reward
    confidence = score.confidence
    
    # Выбираем уникальные элементы на основе памяти
    used_hooks = memory.get_last_titles(20)  # заголовки как хуки
    used_ctas = memory.get_last_ctas(20)
    used_styles = memory.get_last_styles(20)
    
    # Фильтруем хуки, чтобы избежать повторов
    available_hooks = [h for h in HOOKS if h not in used_hooks]
    if not available_hooks:
        available_hooks = HOOKS
    hook_template = random.choice(available_hooks)
    hook = hook_template.format(symbol=f"${basic}")
    
    # Стиль
    available_styles = [s for s in STYLES if s not in used_styles]
    if not available_styles:
        available_styles = STYLES
    style = random.choice(available_styles)
    
    # CTA
    available_ctas = [c for c in CTA_LIST if c not in used_ctas]
    if not available_ctas:
        available_ctas = CTA_LIST
    cta = random.choice(available_ctas)
    
    # Структура
    structure = random.choice(STRUCTURES)
    
    # Определяем направление (бычий/медвежий)
    if ema20 > ema50 and price > ema20:
        direction = "бычий"
        emoji_up = "🚀"
        emoji_down = "📉"
    else:
        direction = "медвежий"
        emoji_up = "📈"
        emoji_down = "🔻"
    
    # Формируем динамический контент
    entry_price = price
    tp1 = resistance if resistance > price else price * 1.02
    tp2 = swing_high if swing_high > price else price * 1.05
    tp3 = price * 1.10 if direction == "бычий" else price * 0.90
    stop_loss = atr_stop if direction == "бычий" else price + atr * 2
    
    # Генерация пояснения
    signal_reason = []
    if pullback:
        signal_reason.append("откат к EMA20")
    if breakout_up:
        signal_reason.append("пробой сопротивления")
    if liquidity_sweep:
        signal_reason.append("свип ликвидности")
    if trend_cont:
        signal_reason.append("продолжение тренда")
    if not signal_reason:
        signal_reason.append("смешанные сигналы, но индикаторы указывают на движение")
    
    reason_text = ", ".join(signal_reason)
    
    # Сборка поста в зависимости от структуры
    # Создаём части
    parts = {
        "hook": hook,
        "problem": f"На {basic} сформировался сигнал, который нельзя игнорировать.",
        "analysis": f"Цена {price:.4f} USDT, изменение за час {change:+.2f}%. RSI {rsi:.1f}, EMA20 {ema20:.2f}, EMA50 {ema50:.2f}. ADX {adx:.1f} указывает на {'сильный' if adx > 25 else 'слабый'} тренд.",
        "signal": f"Основная причина: {reason_text}.",
        "entry": f"Вход по текущей цене {entry_price:.4f} USDT.",
        "tp1": f"TP1: {tp1:.4f} USDT",
        "tp2": f"TP2: {tp2:.4f} USDT",
        "tp3": f"TP3: {tp3:.4f} USDT",
        "stop": f"Стоп-лосс: {stop_loss:.4f} USDT",
        "risk": f"Риск/прибыль: {risk_reward:.1f}",
        "conclusion": f"Итог: {'Бычий' if direction == 'бычий' else 'Медвежий'} сценарий. Уровень уверенности: {confidence:.1f}%.",
        "cta": cta
    }
    
    # Сборка по структуре
    order = structure.split(" → ")
    text_lines = []
    for item in order:
        if item in parts:
            text_lines.append(parts[item])
    
    # Добавляем случайные эмодзи и форматирование
    emojis = ["🔥", "💰", "💎", "📊", "⚡", "🎯", "💡", "🚨", "🟢", "🔴"]
    # Вставляем эмодзи в некоторые строки
    for i, line in enumerate(text_lines):
        if random.random() > 0.5:
            emoji = random.choice(emojis)
            text_lines[i] = f"{emoji} {line}"
    
    # Соединяем
    post = "\n".join(text_lines)
    
    # Добавляем реферальную ссылку (если есть)
    ref_link = os.getenv("REFERRAL_LINK")
    if ref_link:
        post += f"\n\nТоргуйте на Binance по моей ссылке: {ref_link}"
    
    # Проверка уникальности (если похоже на недавние, заменяем некоторые части)
    if memory.is_similar(post):
        # Заменяем хуки и некоторые фразы
        new_hook = random.choice([h for h in HOOKS if h != hook_template]).format(symbol=f"${basic}")
        post = post.replace(hook, new_hook, 1)
        # Заменяем CTA
        new_cta = random.choice([c for c in CTA_LIST if c != cta])
        post = post.replace(cta, new_cta, 1)
    
    # Ограничиваем длину (500-700 символов)
    if len(post) > 700:
        post = post[:700]
    elif len(post) < 500:
        # Добавляем дополнительный анализ
        extra = f" Дополнительно: цена выше VWAP ({vwap:.4f}), что подтверждает бычий настрой. Объём в {vol_rel:.1f}x выше среднего."
        post += extra
    
    # Убираем двойные пробелы и лишние переносы
    import re
    post = re.sub(r'\n{2,}', '\n\n', post)
    
    # Вызов AI для финальной шлифовки (опционально)
    if MISTRAL_API:
        try:
            post = _polish_with_ai(post, basic, style)
        except Exception as e:
            logger.error(f"AI polish failed: {e}")
    
    return post

def _polish_with_ai(text: str, basic: str, style: str) -> str:
    """Отправляет черновик в Mistral для улучшения стиля."""
    prompt = f"""
Ты — опытный крипто-журналист. Перепиши следующий пост в стиле: {style}.
Сохрани все ключевые цифры и факты. Сделай текст живым, человечным, без шаблонов.
Используй смайлы где уместно. Убери любые маркеры списков. Длина 300-500 символов.
Пост должен начинаться с заголовка, затем идти анализ, сигнал, вход, цели, стоп, вывод и CTA.
Все упоминания монеты делай строго как ${basic}.

Текст для переработки:
{text}
"""
    r = requests.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {MISTRAL_API}",
            "Content-Type": "application/json"
        },
        json={
            "model": "mistral-small",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8,
            "max_tokens": 400
        },
        timeout=60
    )
    r.raise_for_status()
    data = r.json()
    polished = data["choices"][0]["message"]["content"]
    # Убираем лишние символы
    for ch in ['*', '_', '`', '#']:
        polished = polished.replace(ch, '')
    return polished.strip()
