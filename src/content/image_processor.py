"""
Processamento de imagens para Instagram.

Converte, redimensiona e valida imagens para o formato ideal do Instagram.
"""

import os
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image

from ..core.constants import (
    CAROUSEL_MAX_SIZE,
    STORY_SIZE,
    SQUARE_SIZE,
    JPEG_QUALITY,
    MIN_IMAGE_SIZE,
    MAX_FILE_SIZE,
    PostType
)
from ..core.exceptions import ImageProcessError


class ImageProcessor:
    """
    Processador de imagens para Instagram.
    
    Garante que todas as imagens estejam no formato correto:
    - JPEG RGB (sem transparência)
    - Dimensões adequadas
    - Tamanho de arquivo dentro do limite
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Inicializa o processador.
        
        Args:
            output_dir: Diretório para imagens processadas.
                       Se None, usa diretório temporário.
        """
        self.output_dir = output_dir
    
    def process_folder(self, images: List[Path], 
                       post_type: PostType = PostType.CAROUSEL) -> List[Path]:
        """
        Processa todas as imagens de uma pasta.
        
        Args:
            images: Lista de paths das imagens originais.
            post_type: Tipo do post para determinar dimensões.
            
        Returns:
            Lista de paths das imagens processadas.
        """
        processed = []
        
        # Determinar tamanho máximo baseado no tipo
        max_size = self._get_max_size(post_type)
        
        for img_path in images:
            try:
                processed_path = self.process_image(img_path, max_size)
                processed.append(processed_path)
            except ImageProcessError as e:
                print(f"⚠️ Erro ao processar {img_path.name}: {e}")
                raise
        
        return processed
    
    def process_image(self, image_path: Path, 
                      max_size: Tuple[int, int] = CAROUSEL_MAX_SIZE) -> Path:
        """
        Processa uma única imagem.
        
        Args:
            image_path: Path da imagem original.
            max_size: Tamanho máximo (width, height).
            
        Returns:
            Path da imagem processada.
        """
        if not image_path.exists():
            raise ImageProcessError(f"Imagem não encontrada: {image_path}")
        
        try:
            with Image.open(image_path) as img:
                # Converter para RGB (remove transparência)
                if img.mode in ("RGBA", "P", "LA"):
                    img = self._convert_to_rgb(img)
                elif img.mode != "RGB":
                    img = img.convert("RGB")
                
                # Redimensionar se necessário
                img = self._resize_if_needed(img, max_size)
                
                # Salvar como JPEG
                output_path = self._get_output_path(image_path)
                
                img.save(
                    output_path,
                    "JPEG",
                    quality=JPEG_QUALITY,
                    optimize=True
                )
                
                # Verificar tamanho do arquivo
                if output_path.stat().st_size > MAX_FILE_SIZE:
                    # Recomprimir com qualidade menor
                    self._compress_to_size(img, output_path, MAX_FILE_SIZE)
                
                return output_path
                
        except Exception as e:
            raise ImageProcessError(f"Erro ao processar {image_path}: {e}")
    
    def convert_to_rgb_jpeg(self, image_path: Path) -> Path:
        """
        Converte uma imagem para JPEG RGB.
        
        Args:
            image_path: Path da imagem.
            
        Returns:
            Path da imagem convertida.
        """
        return self.process_image(image_path)
    
    def validate_for_instagram(self, image_path: Path) -> Tuple[bool, str]:
        """
        Valida se uma imagem está OK para o Instagram.
        
        Args:
            image_path: Path da imagem.
            
        Returns:
            Tupla (is_valid, message).
        """
        if not image_path.exists():
            return False, "Arquivo não existe"
        
        try:
            with Image.open(image_path) as img:
                # Verificar modo
                if img.mode not in ("RGB", "RGBA", "P", "L", "LA"):
                    return False, f"Modo de cor não suportado: {img.mode}"
                
                # Verificar dimensões mínimas
                if img.width < MIN_IMAGE_SIZE or img.height < MIN_IMAGE_SIZE:
                    return False, f"Imagem muito pequena: {img.width}x{img.height}"
                
                # Verificar tamanho do arquivo
                file_size = image_path.stat().st_size
                if file_size > MAX_FILE_SIZE:
                    return False, f"Arquivo muito grande: {file_size / 1024 / 1024:.1f}MB"
                
                return True, "OK"
                
        except Exception as e:
            return False, f"Erro ao abrir imagem: {e}"
    
    def resize_if_needed(self, image_path: Path, 
                         max_size: Tuple[int, int]) -> Path:
        """
        Redimensiona imagem se exceder o tamanho máximo.
        
        Args:
            image_path: Path da imagem.
            max_size: Tamanho máximo (width, height).
            
        Returns:
            Path da imagem (original ou redimensionada).
        """
        with Image.open(image_path) as img:
            if img.width <= max_size[0] and img.height <= max_size[1]:
                return image_path
        
        return self.process_image(image_path, max_size)
    
    def _convert_to_rgb(self, img: Image.Image) -> Image.Image:
        """
        Converte imagem com transparência para RGB.
        
        Remove o canal alfa colocando fundo branco.
        """
        # Criar fundo branco
        background = Image.new("RGB", img.size, (255, 255, 255))
        
        # Se tem canal alfa, usar como máscara
        if img.mode == "RGBA":
            background.paste(img, mask=img.split()[3])
        elif img.mode == "P" and "transparency" in img.info:
            img = img.convert("RGBA")
            background.paste(img, mask=img.split()[3])
        elif img.mode == "LA":
            background.paste(img.convert("RGBA"), mask=img.split()[1])
        else:
            background.paste(img)
        
        return background
    
    def _resize_if_needed(self, img: Image.Image, 
                          max_size: Tuple[int, int]) -> Image.Image:
        """
        Redimensiona mantendo aspect ratio.
        """
        if img.width <= max_size[0] and img.height <= max_size[1]:
            return img
        
        # Calcular novo tamanho mantendo proporção
        ratio = min(max_size[0] / img.width, max_size[1] / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        
        return img.resize(new_size, Image.Resampling.LANCZOS)
    
    def _get_output_path(self, original_path: Path) -> Path:
        """
        Gera o path de saída para a imagem processada.
        """
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            return self.output_dir / f"{original_path.stem}_processed.jpg"
        
        # Usar diretório temporário
        temp_dir = Path(tempfile.gettempdir()) / "autopost"
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir / f"{original_path.stem}_processed.jpg"
    
    def _compress_to_size(self, img: Image.Image, 
                          output_path: Path, 
                          max_size: int) -> None:
        """
        Comprime imagem até atingir o tamanho máximo.
        """
        quality = JPEG_QUALITY
        
        while quality > 30:
            img.save(output_path, "JPEG", quality=quality, optimize=True)
            
            if output_path.stat().st_size <= max_size:
                break
            
            quality -= 10
    
    def _get_max_size(self, post_type: PostType) -> Tuple[int, int]:
        """
        Retorna o tamanho máximo baseado no tipo de post.
        """
        if post_type == PostType.STORY:
            return STORY_SIZE
        elif post_type == PostType.SINGLE:
            return SQUARE_SIZE
        return CAROUSEL_MAX_SIZE


# Instância global
_processor: Optional[ImageProcessor] = None


def get_image_processor() -> ImageProcessor:
    """Retorna o processador singleton."""
    global _processor
    if _processor is None:
        _processor = ImageProcessor()
    return _processor
