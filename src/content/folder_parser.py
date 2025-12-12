"""
Parser de pastas de conteúdo.

Analisa a estrutura de pastas para detectar tipo de post,
extrair slides e ler legendas.
"""

import re
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass

from ..core.constants import (
    PostType,
    SLIDE_PATTERNS,
    STORY_PATTERNS,
    CAPTION_FILE,
    VALID_IMAGE_EXTENSIONS
)
from ..core.exceptions import FolderParseError


@dataclass
class PostContent:
    """
    Representa o conteúdo de uma pasta de post.
    
    Attributes:
        folder: Path da pasta original.
        post_type: Tipo do post (carousel, story, single).
        slides: Lista de paths das imagens.
        caption: Legenda do post.
    """
    folder: Path
    post_type: PostType
    slides: List[Path]
    caption: str
    
    @property
    def folder_name(self) -> str:
        """Nome da pasta."""
        return self.folder.name
    
    @property
    def slide_count(self) -> int:
        """Quantidade de slides."""
        return len(self.slides)


class FolderParser:
    """
    Parser de pastas de conteúdo para Instagram.
    
    Detecta automaticamente o tipo de post baseado nos arquivos
    presentes na pasta.
    """
    
    def parse(self, folder: Path) -> PostContent:
        """
        Analisa uma pasta e extrai seu conteúdo.
        
        Args:
            folder: Path da pasta a ser analisada.
            
        Returns:
            PostContent com todas as informações extraídas.
            
        Raises:
            FolderParseError: Se a pasta for inválida.
        """
        if not folder.exists():
            raise FolderParseError(f"Pasta não encontrada: {folder}")
        
        if not folder.is_dir():
            raise FolderParseError(f"Não é uma pasta: {folder}")
        
        post_type = self.detect_type(folder)
        slides = self.get_slides(folder, post_type)
        caption = self.get_caption(folder)
        
        if not slides:
            raise FolderParseError(f"Nenhuma imagem válida encontrada em: {folder}")
        
        return PostContent(
            folder=folder,
            post_type=post_type,
            slides=slides,
            caption=caption
        )
    
    def detect_type(self, folder: Path) -> PostType:
        """
        Detecta o tipo de post baseado nos arquivos.
        
        Prioridade:
        1. Se tem arquivos story-*.jpg -> STORY
        2. Se tem múltiplos slide-*.jpg -> CAROUSEL
        3. Se tem apenas 1 imagem -> SINGLE
        
        Args:
            folder: Path da pasta.
            
        Returns:
            PostType detectado.
        """
        # Verificar se é story
        stories = self._find_stories(folder)
        if stories:
            return PostType.STORY
        
        # Verificar slides
        slides = self._find_slides(folder)
        if len(slides) > 1:
            return PostType.CAROUSEL
        
        # Se tem pelo menos 1 imagem, é single
        if slides or self._find_any_image(folder):
            return PostType.SINGLE
        
        return PostType.SINGLE
    
    def get_slides(self, folder: Path, post_type: Optional[PostType] = None) -> List[Path]:
        """
        Obtém a lista de slides ordenados.
        
        Args:
            folder: Path da pasta.
            post_type: Tipo do post (opcional).
            
        Returns:
            Lista de paths ordenados por número.
        """
        if post_type is None:
            post_type = self.detect_type(folder)
        
        if post_type == PostType.STORY:
            return self._find_stories(folder)
        
        # Tentar encontrar slides nomeados
        slides = self._find_slides(folder)
        
        if slides:
            return slides
        
        # Fallback: qualquer imagem válida, ordenada por nome
        return sorted(self._find_any_image(folder))
    
    def get_caption(self, folder: Path) -> str:
        """
        Lê a legenda do arquivo caption.txt.
        
        Args:
            folder: Path da pasta.
            
        Returns:
            Texto da legenda ou string vazia.
        """
        caption_path = folder / CAPTION_FILE
        
        if not caption_path.exists():
            # Tentar variações
            for alt_name in ["Caption.txt", "CAPTION.txt", "legenda.txt"]:
                alt_path = folder / alt_name
                if alt_path.exists():
                    caption_path = alt_path
                    break
        
        if not caption_path.exists():
            return ""
        
        try:
            return caption_path.read_text(encoding="utf-8").strip()
        except Exception:
            try:
                return caption_path.read_text(encoding="latin-1").strip()
            except Exception:
                return ""
    
    def _find_slides(self, folder: Path) -> List[Path]:
        """
        Encontra slides nomeados (slide-1.jpg, slide-2.jpg, etc).
        
        Returns:
            Lista ordenada de paths.
        """
        slides = []
        
        for file in folder.iterdir():
            if not file.is_file():
                continue
            
            for pattern in SLIDE_PATTERNS:
                match = re.match(pattern, file.name, re.IGNORECASE)
                if match:
                    number = int(match.group(1))
                    slides.append((number, file))
                    break
        
        # Ordenar por número e retornar apenas os paths
        slides.sort(key=lambda x: x[0])
        return [slide[1] for slide in slides]
    
    def _find_stories(self, folder: Path) -> List[Path]:
        """
        Encontra stories nomeados (story-1.jpg, story-2.jpg, etc).
        
        Returns:
            Lista ordenada de paths.
        """
        stories = []
        
        for file in folder.iterdir():
            if not file.is_file():
                continue
            
            for pattern in STORY_PATTERNS:
                match = re.match(pattern, file.name, re.IGNORECASE)
                if match:
                    number = int(match.group(1))
                    stories.append((number, file))
                    break
        
        stories.sort(key=lambda x: x[0])
        return [story[1] for story in stories]
    
    def _find_any_image(self, folder: Path) -> List[Path]:
        """
        Encontra qualquer imagem válida na pasta.
        
        Returns:
            Lista de paths de imagens.
        """
        images = []
        
        for file in folder.iterdir():
            if file.is_file() and file.suffix.lower() in VALID_IMAGE_EXTENSIONS:
                images.append(file)
        
        return images
    
    def is_valid_folder(self, folder: Path) -> Tuple[bool, str]:
        """
        Verifica se uma pasta é válida para postagem.
        
        Args:
            folder: Path da pasta.
            
        Returns:
            Tupla (is_valid, message).
        """
        if not folder.exists():
            return False, "Pasta não existe"
        
        if not folder.is_dir():
            return False, "Não é uma pasta"
        
        images = self._find_any_image(folder)
        if not images:
            return False, "Nenhuma imagem encontrada"
        
        return True, "OK"


# Instância global
_parser: Optional[FolderParser] = None


def get_folder_parser() -> FolderParser:
    """Retorna o parser singleton."""
    global _parser
    if _parser is None:
        _parser = FolderParser()
    return _parser
