# 📱 AutoPost

Sistema modular de postagem automatizada para Instagram com sincronização Google Drive.

## 🚀 Início Rápido

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar .env
```bash
# Já configurado com suas credenciais
# Edite se necessário
```

### 3. Executar
```bash
python main.py
```

### 4. Acessar Dashboard
```
http://localhost:8000
```

---

## 📁 Estrutura

```
autopost/
├── src/
│   ├── core/           # Configurações e constantes
│   ├── instagram/      # Cliente Instagram
│   ├── content/        # Parser e processador de imagens
│   ├── storage/        # Storage local e Drive
│   ├── scheduler/      # Agendamento de posts
│   └── api/            # Dashboard FastAPI
├── data/               # Estado e sessão
├── content/posts/      # Pastas de conteúdo
├── main.py             # Entry point
└── .env                # Configurações
```

---

## 📋 Formato de Pasta de Post

```
meu-post/
├── slide-1.jpg    # Slides numerados
├── slide-2.jpg
├── slide-3.jpg
└── caption.txt    # Legenda do post
```

---

## 🔧 Features

- ✅ Postagem automática em horários configuráveis
- ✅ Sync com Google Drive
- ✅ Dashboard web responsivo
- ✅ Postar imediatamente (Post Now)
- ✅ Session hijacking para login seguro
- ✅ Processamento automático de imagens (RGB, dimensões)
- ✅ Fila de posts com priorização

---

## 🌐 Deploy

Para deploy em Render/Railway:

1. Configure as variáveis de ambiente no painel
2. Use `GOOGLE_CREDENTIALS_JSON` com o JSON completo
3. Start command: `python main.py`

---

*AutoPost v2.0 - Arquitetura Modular*
