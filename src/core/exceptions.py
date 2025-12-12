"""
Exceções customizadas do AutoPost.

Define todas as exceções do sistema para tratamento de erros organizado.
"""


class AutoPostError(Exception):
    """Exceção base do AutoPost."""
    pass


class ConfigError(AutoPostError):
    """Erro de configuração - variáveis de ambiente ausentes ou inválidas."""
    pass


class InstagramError(AutoPostError):
    """Erro relacionado ao Instagram - login, postagem, etc."""
    pass


class LoginError(InstagramError):
    """Erro específico de login no Instagram."""
    pass


class PostError(InstagramError):
    """Erro ao tentar postar conteúdo no Instagram."""
    pass


class ContentError(AutoPostError):
    """Erro relacionado ao conteúdo - pasta inválida, imagem corrompida, etc."""
    pass


class FolderParseError(ContentError):
    """Erro ao analisar estrutura de pasta."""
    pass


class ImageProcessError(ContentError):
    """Erro ao processar imagem."""
    pass


class StorageError(AutoPostError):
    """Erro relacionado ao armazenamento - local ou Drive."""
    pass


class DriveError(StorageError):
    """Erro específico do Google Drive."""
    pass


class StateError(StorageError):
    """Erro ao salvar/carregar estado."""
    pass


class SchedulerError(AutoPostError):
    """Erro relacionado ao agendamento."""
    pass
