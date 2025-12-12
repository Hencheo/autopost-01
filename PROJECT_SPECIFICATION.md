# 📱 AutoPost - Especificação Completa do Projeto

## 🎯 Objetivo
Sistema automatizado para postagem no Instagram que permite:
- Agendamento automático de posts em horários configuráveis
- Sincronização com Google Drive para conteúdo remoto
- Postagem manual de pastas locais sob demanda
- Interface web para gerenciamento e monitoramento

---

## 🏗️ Arquitetura Modular

```
autopost/
├── src/
│   ├── core/                    # Núcleo do sistema
│   │   ├── __init__.py
│   │   ├── config.py            # Configurações centralizadas
│   │   ├── exceptions.py        # Exceções customizadas
│   │   └── constants.py         # Constantes do projeto
│   │
│   ├── instagram/               # Módulo Instagram
│   │   ├── __init__.py
│   │   ├── client.py            # Cliente Instagram (instagrapi)
│   │   ├── auth.py              # Autenticação e sessão
│   │   └── poster.py            # Lógica de postagem
│   │
│   ├── content/                 # Módulo de Conteúdo
│   │   ├── __init__.py
│   │   ├── file_manager.py      # Gerenciamento de arquivos
│   │   ├── image_processor.py   # Processamento de imagens
│   │   └── folder_parser.py     # Parser de pastas (slides, caption)
│   │
│   ├── storage/                 # Módulo de Armazenamento
│   │   ├── __init__.py
│   │   ├── local.py             # Storage local
│   │   ├── drive_sync.py        # Sincronização Google Drive
│   │   └── state.py             # Persistência de estado (JSON)
│   │
│   ├── scheduler/               # Módulo Agendador
│   │   ├── __init__.py
│   │   ├── scheduler.py         # Lógica de agendamento
│   │   ├── time_slots.py        # Gerenciamento de horários
│   │   └── queue.py             # Fila de posts
│   │
│   └── api/                     # Módulo API/Dashboard
│       ├── __init__.py
│       ├── app.py               # FastAPI app
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── dashboard.py     # Rotas do dashboard
│       │   ├── actions.py       # Ações (post now, cleanup, etc)
│       │   └── settings.py      # Configurações via API
│       ├── services/
│       │   ├── __init__.py
│       │   └── scheduler_service.py
│       ├── templates/
│       │   └── dashboard.html
│       └── static/
│           ├── css/
│           └── js/
│
├── data/                        # Dados persistentes
│   ├── state.json               # Estado do scheduler
│   ├── posted.json              # Histórico de posts
│   └── session.json             # Sessão Instagram
│
├── content/                     # Conteúdo local para postar
│   └── posts/                   # Pastas de posts
│       ├── meu-post-1/
│       │   ├── slide-1.jpg
│       │   ├── slide-2.jpg
│       │   └── caption.txt
│       └── meu-post-2/
│           └── ...
│
├── main.py                      # Entry point
├── requirements.txt
├── .env                         # Variáveis de ambiente
└── README.md
```

---

## 📦 Módulos Detalhados

### 1. Core (`src/core/`)

#### `config.py`
```python
# Responsabilidades:
# - Carregar variáveis de ambiente
# - Validar configurações obrigatórias
# - Fornecer defaults sensatos

class Config:
    # Instagram
    INSTAGRAM_USERNAME: str
    INSTAGRAM_PASSWORD: str
    
    # Google Drive
    DRIVE_FOLDER_ID: str
    DRIVE_CREDENTIALS_PATH: str
    
    # Agendamento
    POST_TIMES: list[str]  # ["09:00", "15:00", "21:00"]
    TIMEZONE: str          # "America/Sao_Paulo"
    
    # Paths
    LOCAL_CONTENT_PATH: str
    DATA_PATH: str
```

#### `constants.py`
```python
# Constantes de imagem para Instagram
IMAGE_MAX_SIZE = (1080, 1350)      # Carrossel 4:5
STORY_SIZE = (1080, 1920)          # Story 9:16
JPEG_QUALITY = 95
MIN_IMAGE_SIZE = 320

# Padrões de arquivo
SLIDE_PATTERN = "slide-*.jpg"
STORY_PATTERN = "story-*.jpg"
CAPTION_FILE = "caption.txt"
```

---

### 2. Instagram (`src/instagram/`)

#### `client.py`
```python
# Responsabilidades:
# - Singleton do cliente instagrapi
# - Gerenciar conexão e reconexão
# - Rate limiting e delays humanizados

class InstagramClient:
    def __init__(self, config: Config)
    def login(self) -> bool
    def logout(self) -> None
    def is_logged_in(self) -> bool
```

#### `poster.py`
```python
# Responsabilidades:
# - Postar carrossel
# - Postar story
# - Postar imagem única

class InstagramPoster:
    def post_carousel(self, images: list[Path], caption: str) -> bool
    def post_story(self, images: list[Path]) -> bool
    def post_single(self, image: Path, caption: str) -> bool
```

---

### 3. Content (`src/content/`)

#### `folder_parser.py`
```python
# Responsabilidades:
# - Analisar estrutura de pasta
# - Detectar tipo de post (carrossel, story, single)
# - Extrair slides e caption

class FolderParser:
    def parse(self, folder: Path) -> PostContent
    def detect_type(self, folder: Path) -> PostType  # CAROUSEL, STORY, SINGLE
    def get_slides(self, folder: Path) -> list[Path]
    def get_caption(self, folder: Path) -> str
```

#### `image_processor.py`
```python
# Responsabilidades:
# - Converter para JPEG RGB
# - Redimensionar se necessário
# - Validar formato para Instagram

class ImageProcessor:
    def process_folder(self, folder: Path) -> list[Path]
    def convert_to_rgb_jpeg(self, image: Path) -> Path
    def validate_for_instagram(self, image: Path) -> tuple[bool, str]
    def resize_if_needed(self, image: Path, max_size: tuple) -> Path
```

---

### 4. Storage (`src/storage/`)

#### `local.py`
```python
# Responsabilidades:
# - Listar pastas pendentes
# - Mover pastas para "posted"
# - Gerenciar estrutura local

class LocalStorage:
    def get_pending_folders(self) -> list[Path]
    def mark_as_posted(self, folder: Path) -> None
    def cleanup_posted(self, days: int = 30) -> None
```

#### `drive_sync.py`
```python
# Responsabilidades:
# - Autenticar com Google Drive
# - Baixar pastas de conteúdo
# - Sincronizar periodicamente

class DriveSync:
    def sync(self) -> list[Path]
    def download_folder(self, folder_id: str) -> Path
    def list_remote_folders(self) -> list[dict]
```

#### `state.py`
```python
# Responsabilidades:
# - Persistir estado do scheduler
# - Histórico de posts
# - Recuperação após reinício

class StateManager:
    def save_state(self, state: dict) -> None
    def load_state(self) -> dict
    def add_to_history(self, post_info: dict) -> None
    def get_history(self, limit: int = 50) -> list[dict]
```

---

### 5. Scheduler (`src/scheduler/`)

#### `scheduler.py`
```python
# Responsabilidades:
# - Agendar posts nos horários configurados
# - Executar posts automaticamente
# - Lidar com falhas e retry

class PostScheduler:
    def start(self) -> None
    def stop(self) -> None
    def add_time_slot(self, time: str) -> None
    def remove_time_slot(self, time: str) -> None
    def get_next_post_time(self) -> datetime
```

#### `time_slots.py`
```python
# Responsabilidades:
# - Gerenciar horários de postagem
# - Calcular próximo horário
# - Validar formato de horário

class TimeSlotManager:
    def set_slots(self, times: list[str]) -> None
    def get_next_slot(self) -> datetime
    def is_valid_time(self, time_str: str) -> bool
```

---

### 6. API (`src/api/`)

#### `app.py`
```python
# FastAPI app principal

app = FastAPI(title="AutoPost Dashboard")

# Middleware, CORS, etc.
```

#### `routes/dashboard.py`
```python
# Rotas do dashboard

GET  /                    # Dashboard principal
GET  /api/status          # Status do scheduler
GET  /api/history         # Histórico de posts
GET  /api/pending         # Posts pendentes
```

#### `routes/actions.py`
```python
# Ações manuais

POST /api/post-now              # Postar próximo da fila
POST /api/post-folder           # Postar pasta específica
POST /api/sync-drive            # Sincronizar Drive
POST /api/cleanup               # Limpar posts antigos
POST /api/reset                 # Resetar estado
```

#### `routes/settings.py`
```python
# Configurações

GET  /api/settings              # Obter configurações
POST /api/settings/times        # Atualizar horários
POST /api/settings/toggle       # Liga/desliga scheduler
```

---

## 🔄 Fluxos Principais

### Fluxo 1: Post Automático Agendado
```
1. Scheduler detecta horário de post
2. DriveSync.sync() baixa novos conteúdos
3. LocalStorage.get_pending_folders() lista pendentes
4. FolderParser.parse() analisa próxima pasta
5. ImageProcessor.process_folder() processa imagens
6. InstagramPoster.post_carousel() posta no Instagram
7. LocalStorage.mark_as_posted() move para posted
8. StateManager.add_to_history() registra no histórico
```

### Fluxo 2: Post Manual de Pasta Local
```
1. Usuário clica "Post Now" no dashboard (ou envia comando)
2. API recebe POST /api/post-folder com path da pasta
3. FolderParser.parse() analisa pasta
4. ImageProcessor.process_folder() processa imagens
5. InstagramPoster.post_carousel() posta
6. StateManager.add_to_history() registra
```

### Fluxo 3: Sincronização com Drive
```
1. Scheduler executa sync periódico (ou manual via API)
2. DriveSync.list_remote_folders() lista pastas no Drive
3. Para cada pasta nova:
   - DriveSync.download_folder() baixa conteúdo
   - Salva em content/posts/
4. Pastas ficam disponíveis para agendamento
```

---

## 📋 Requisitos de Pasta de Conteúdo

### Estrutura de uma pasta de post:
```
meu-post-legal/
├── slide-1.jpg      # Obrigatório: pelo menos 1 slide
├── slide-2.jpg      # Opcional: mais slides (até 10)
├── slide-3.jpg
└── caption.txt      # Obrigatório: legenda do post
```

### Regras:
- **Slides**: Nomeados como `slide-{N}.jpg` ou `slide-{N}.png`
- **Ordem**: Numérica (slide-1, slide-2, ...)
- **Formato ideal**: JPEG RGB, 1080x1350px
- **Caption**: Arquivo `caption.txt` com a legenda (UTF-8)

---

## ⚙️ Variáveis de Ambiente (.env)

```env
# Instagram
INSTAGRAM_USERNAME=seu_usuario
INSTAGRAM_PASSWORD=sua_senha
INSTAGRAM_SESSION_ID=opcional_session_hijack

# Google Drive
DRIVE_FOLDER_ID=id_da_pasta_no_drive
GOOGLE_CREDENTIALS_JSON={"type":"service_account",...}

# Agendamento
POST_TIMES=09:00,15:00,21:00
TIMEZONE=America/Sao_Paulo

# API
API_PORT=8000
API_HOST=0.0.0.0

# Storage
LOCAL_CONTENT_PATH=./content/posts
DATA_PATH=./data
```

---

## 🚀 Comandos de Uso

### Desenvolvimento Local
```bash
# Instalar dependências
pip install -r requirements.txt

# Rodar localmente
python main.py

# Acessar dashboard
http://localhost:8000
```

### Deploy (Render/Railway)
```bash
# Start command
python main.py

# Variáveis de ambiente: configurar no painel
```

---

## 📊 Dashboard - Funcionalidades

| Seção | Descrição |
|-------|-----------|
| **Status** | Estado atual do scheduler (ativo/parado) |
| **Próximo Post** | Horário e conteúdo do próximo post |
| **Fila** | Lista de pastas pendentes |
| **Histórico** | Últimos posts realizados |
| **Ações** | Post Now, Sync Drive, Cleanup, Reset |
| **Configurações** | Horários de postagem, toggle on/off |

---

## 🔒 Segurança

1. **Session Hijacking**: Usar session_id do navegador logado
2. **Device ID persistente**: Salvar e reutilizar device_id
3. **Delays humanizados**: Intervalos aleatórios entre ações
4. **Rate limiting**: Respeitar limites do Instagram
5. **Credenciais**: Nunca commitar no git, usar .env

---

## 📝 Notas Importantes

1. **Instagram não tem API oficial** - Usamos instagrapi (não oficial)
2. **Risco de bloqueio** - Delays e comportamento humano são essenciais
3. **Backup de sessão** - Sempre salvar session após login bem-sucedido
4. **Formato de imagem** - JPEG RGB é obrigatório (sem transparência!)
5. **Google Drive** - Service account precisa de acesso à pasta

---

*Especificação criada em: 2025-12-11*
*Versão: 2.0 - Arquitetura Modular*
