import os

# API Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
EXAMPLES_DIR = os.path.join(BASE_DIR, "examples")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Classification Settings
DEFAULT_CATEGORIES = ["إيجابي", "سلبي", "محايد"]
DEFAULT_BATCH_SIZE = 25
DEFAULT_SEPARATOR = "\n"

# UI Configuration
CUSTOM_COLORS = ['#2ecc71', '#e74c3c', '#3498db', '#f1c40f', '#9b59b6', '#1abc9c']

# Arabic Stop Words
STOP_WORDS = {
    'في', 'من', 'على', 'إلى', 'عن', 'مع', 'هذا', 'هذه', 'تم', 'فيه', 'أن', 'كان',
    'كانت', 'لم', 'لن', 'ما', 'هل', 'قد', 'لا', 'إن', 'كل', 'بعد', 'قبل', 'حتى', 'إذا',
    'كيف', 'هو', 'هي', 'نحن', 'هم', 'هن', 'أنت', 'أنتم', 'أنتن', 'أنا', 'به', 'لها',
    'لهم', 'لنا', 'له', 'منه', 'منها', 'منهم', 'عنه', 'عنها', 'عنهم', 'فيها', 'فيهم',
    'بها', 'بهم', 'لك', 'لكم', 'لكن', 'ثم', 'أو', 'أم', 'بل', 'لا', 'و', 'ف', 'ب', 'ل', 'ك', 'و'
}

# File Settings
SEPARATOR_OPTIONS = [
    ("\n", "سطر جديد (↵)"),
    (",", "فاصلة (,)"),
    (".", "نقطة (.)"),
    (";", "فاصلة منقوطة (;)"),
    ("custom", "فاصل مخصص ✏️")
]

# Privacy Settings
SETTINGS_FILE = os.path.join(CONFIG_DIR, "privacy_settings.json")
PRIVACY_CACHE_KEY = "privacy_patterns_cache" 