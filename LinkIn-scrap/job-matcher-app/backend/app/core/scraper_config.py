# scraper_config.py - Configuration du scraper
import os
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class ScrapingConfig:
    """Configuration pour le scraper LinkedIn"""
    
    # Paramètres de base
    MAX_PAGES_DEFAULT: int = 3
    MAX_PAGES_LIMIT: int = 10
    DELAY_MIN: float = 2.0
    DELAY_MAX: float = 5.0
    
    # Paramètres Selenium
    SELENIUM_TIMEOUT: int = 15
    SELENIUM_IMPLICIT_WAIT: int = 10
    PAGE_LOAD_TIMEOUT: int = 30
    
    # Paramètres de scraping
    MAX_SCROLLS: int = 3
    SCROLL_PAUSE: float = 1.0
    
    # Paramètres de base de données
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DB_NAME: str = os.getenv("DB_NAME", "linkedin_scraper")
    
    # Sélecteurs CSS (backup si les principaux échouent)
    BACKUP_SELECTORS: Dict[str, List[str]] = {
        'job_cards_fallback': [
            "div.job-search-card",
            "div.result-card",
            "li.job-result-card",
            "div[data-job-id]"
        ],
        'title_fallback': [
            "h3 a",
            ".job-title a",
            ".result-card__title a"
        ],
        'company_fallback': [
            "h4 a",
            ".job-search-card__subtitle-link",
            ".result-card__subtitle"
        ]
    }
    
    # User agents pour rotation
    USER_AGENTS: List[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
    ]
    
    # Mapping des filtres LinkedIn
    EXPERIENCE_LEVELS: Dict[str, str] = {
        'internship': '1',
        'entry': '2',
        'associate': '3', 
        'mid_senior': '4',
        'director': '5',
        'executive': '6'
    }
    
    JOB_TYPES: Dict[str, str] = {
        'full_time': 'F',
        'part_time': 'P',
        'contract': 'C', 
        'temporary': 'T',
        'internship': 'I',
        'volunteer': 'V',
        'other': 'O'
    }
    
    DATE_POSTED: Dict[str, str] = {
        'past_24h': 'r86400',
        'past_week': 'r604800', 
        'past_month': 'r2592000',
        'any_time': ''
    }
    
    COMPANY_SIZES: Dict[str, str] = {
        'startup': 'A,B',  # 1-10, 11-50
        'small': 'C',      # 51-200
        'medium': 'D',     # 201-500
        'large': 'E,F,G'   # 501-1000, 1001-5000, 5001-10000
    }