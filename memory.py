import json
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path

MEMORY_FILE = Path("post_memory.json")

class PostMemory:
    """Хранит историю опубликованных постов: заголовки, первые предложения, CTA, стили."""
    
    def __init__(self, max_items: int = 100):
        self.max_items = max_items
        self.data = self._load()
    
    def _load(self) -> Dict:
        if MEMORY_FILE.exists():
            try:
                with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"posts": [], "titles": [], "first_sentences": [], "ctas": [], "styles": []}
        return {"posts": [], "titles": [], "first_sentences": [], "ctas": [], "styles": []}
    
    def _save(self):
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def add_post(self, symbol: str, text: str):
        """Добавляет пост в память, извлекая заголовок, первое предложение, CTA, стиль."""
        lines = text.strip().split('\n')
        title = lines[0] if lines else ""
        first_sentence = lines[1] if len(lines) > 1 else ""
        # CTA ищем в последних 3 строках
        ctas = [l for l in lines[-3:] if '?' in l or '!' in l]
        cta = ctas[0] if ctas else ""
        # Стиль (условно: определяем по наличию эмодзи, длине предложений)
        style = self._detect_style(text)
        
        self.data["posts"].append({"symbol": symbol, "text": text, "timestamp": datetime.now().isoformat()})
        self.data["titles"].append(title)
        self.data["first_sentences"].append(first_sentence)
        self.data["ctas"].append(cta)
        self.data["styles"].append(style)
        
        # Ограничиваем размер
        for key in self.data:
            if len(self.data[key]) > self.max_items:
                self.data[key] = self.data[key][-self.max_items:]
        self._save()
    
    def _detect_style(self, text: str) -> str:
        """Определяет стиль текста (для избегания повторов)."""
        # Упрощённо: анализируем длину предложений, количество эмодзи, знаков препинания
        # Для простоты возвращаем хеш первых 100 символов
        import hashlib
        return hashlib.md5(text[:100].encode()).hexdigest()[:8]
    
    def get_last_titles(self, n: int = 10) -> List[str]:
        return self.data["titles"][-n:]
    
    def get_last_first_sentences(self, n: int = 10) -> List[str]:
        return self.data["first_sentences"][-n:]
    
    def get_last_ctas(self, n: int = 10) -> List[str]:
        return self.data["ctas"][-n:]
    
    def get_last_styles(self, n: int = 10) -> List[str]:
        return self.data["styles"][-n:]
    
    def is_similar(self, text: str, threshold: float = 0.6) -> bool:
        """Проверяет, похож ли новый текст на уже опубликованные (простейшая проверка)."""
        # Для простоты используем сравнение первых 50 символов
        sample = text[:50].lower()
        for post in self.data["posts"][-10:]:
            if post["text"][:50].lower() == sample:
                return True
        return False