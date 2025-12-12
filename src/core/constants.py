"""
Constantes do AutoPost.

Define todas as constantes utilizadas pelo sistema.
"""

from pathlib import Path
from enum import Enum


# ============================================================
# CONSTANTES DE IMAGEM PARA INSTAGRAM
# ============================================================

# Tamanho máximo para carrossel (aspect ratio 4:5)
CAROUSEL_MAX_SIZE = (1080, 1350)

# Tamanho para story (aspect ratio 9:16)
STORY_SIZE = (1080, 1920)

# Tamanho para post único (quadrado)
SQUARE_SIZE = (1080, 1080)

# Qualidade JPEG (95 é o recomendado para Instagram)
JPEG_QUALITY = 95

# Tamanho mínimo de imagem que o Instagram aceita
MIN_IMAGE_SIZE = 320

# Tamanho máximo de arquivo (em bytes) - 8MB
MAX_FILE_SIZE = 8 * 1024 * 1024


# ============================================================
# PADRÕES DE ARQUIVO
# ============================================================

# Padrões para identificar slides (regex)
SLIDE_PATTERNS = [
    r"slide[-_]?(\d+)\.(jpg|jpeg|png)",
    r"(\d+)\.(jpg|jpeg|png)",
]

# Padrões para identificar stories
STORY_PATTERNS = [
    r"story[-_]?(\d+)\.(jpg|jpeg|png)",
]

# Nome do arquivo de legenda
CAPTION_FILE = "caption.txt"

# Extensões de imagem aceitas
VALID_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


# ============================================================
# TIPOS DE POST
# ============================================================

class PostType(Enum):
    """Tipos de post suportados."""
    CAROUSEL = "carousel"  # Múltiplas imagens (até 10)
    STORY = "story"        # Story (temporário 24h)
    SINGLE = "single"      # Imagem única


# ============================================================
# PATHS PADRÃO
# ============================================================

# Diretório raiz do projeto (será sobrescrito pela config)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Paths padrão (relativos à raiz)
DEFAULT_CONTENT_PATH = PROJECT_ROOT / "content" / "posts"
DEFAULT_DATA_PATH = PROJECT_ROOT / "data"
DEFAULT_CREDENTIALS_PATH = PROJECT_ROOT / "data" / "credentials"


# ============================================================
# CONFIGURAÇÕES DE SEGURANÇA
# ============================================================

# Delay mínimo e máximo entre ações (em segundos)
MIN_ACTION_DELAY = 2
MAX_ACTION_DELAY = 5

# Delay após login bem-sucedido
POST_LOGIN_DELAY = 5

# Delay entre uploads de múltiplas imagens
UPLOAD_DELAY = 1


# ============================================================
# CONFIGURAÇÕES DE AGENDAMENTO
# ============================================================

# Horários padrão de postagem
DEFAULT_POST_TIMES = ["09:00", "15:00", "21:00"]

# Timezone padrão
DEFAULT_TIMEZONE = "America/Sao_Paulo"

# Intervalo de sincronização com Drive (em minutos)
DRIVE_SYNC_INTERVAL = 30


# ============================================================
# LIMITES
# ============================================================

# Máximo de imagens em um carrossel
MAX_CAROUSEL_IMAGES = 10

# Máximo de stories por vez
MAX_STORIES = 10

# Máximo de posts por dia (recomendado)
MAX_POSTS_PER_DAY = 10

# Tamanho máximo da legenda
MAX_CAPTION_LENGTH = 2200

# Máximo de hashtags
MAX_HASHTAGS = 30
