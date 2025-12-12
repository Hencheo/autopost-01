"""
Lógica de postagem no Instagram.

Responsável por postar carrossel, story e imagem única.
"""

from pathlib import Path
from typing import List, Optional

from .client import get_instagram_client, InstagramClient
from .auth import humanized_delay
from ..core.exceptions import PostError
from ..core.constants import MAX_CAROUSEL_IMAGES, MAX_STORIES


class InstagramPoster:
    """
    Gerenciador de postagens no Instagram.
    
    Suporta:
    - Carrossel (múltiplas imagens)
    - Story
    - Imagem única
    """
    
    def __init__(self, client: Optional[InstagramClient] = None):
        """
        Inicializa o poster.
        
        Args:
            client: Cliente Instagram. Se None, usa o singleton.
        """
        self._instagram = client or get_instagram_client()
    
    def _ensure_logged_in(self) -> None:
        """Garante que está logado antes de postar."""
        if not self._instagram.is_logged_in():
            self._instagram.login()
    
    def post_carousel(self, images: List[Path], caption: str) -> dict:
        """
        Posta um carrossel (álbum) de imagens.
        
        Args:
            images: Lista de paths das imagens (2-10 imagens).
            caption: Legenda do post.
            
        Returns:
            Dict com informações do post criado.
            
        Raises:
            PostError: Se houver erro na postagem.
        """
        self._ensure_logged_in()
        
        # Validações
        if len(images) < 1:
            raise PostError("Carrossel precisa de pelo menos 1 imagem")
        
        if len(images) > MAX_CAROUSEL_IMAGES:
            raise PostError(f"Carrossel suporta no máximo {MAX_CAROUSEL_IMAGES} imagens")
        
        # Verificar se arquivos existem
        for img in images:
            if not img.exists():
                raise PostError(f"Imagem não encontrada: {img}")
        
        print(f"📸 Postando carrossel com {len(images)} imagens...")
        humanized_delay()
        
        try:
            # Se é apenas 1 imagem, posta como single
            if len(images) == 1:
                result = self._instagram.client.photo_upload(
                    path=str(images[0]),
                    caption=caption
                )
            else:
                # Converter paths para strings
                image_paths = [str(img) for img in images]
                
                result = self._instagram.client.album_upload(
                    paths=image_paths,
                    caption=caption
                )
            
            post_info = {
                "id": result.pk,
                "code": result.code,
                "type": "carousel" if len(images) > 1 else "single",
                "images_count": len(images),
                "caption_preview": caption[:100] + "..." if len(caption) > 100 else caption,
            }
            
            print(f"✅ Carrossel postado! ID: {result.pk}")
            return post_info
            
        except Exception as e:
            raise PostError(f"Erro ao postar carrossel: {e}")
    
    def post_story(self, images: List[Path]) -> List[dict]:
        """
        Posta uma ou mais imagens como Story.
        
        Args:
            images: Lista de paths das imagens.
            
        Returns:
            Lista de dicts com informações de cada story.
            
        Raises:
            PostError: Se houver erro na postagem.
        """
        self._ensure_logged_in()
        
        if len(images) > MAX_STORIES:
            raise PostError(f"Máximo de {MAX_STORIES} stories por vez")
        
        results = []
        
        for i, img in enumerate(images):
            if not img.exists():
                raise PostError(f"Imagem não encontrada: {img}")
            
            print(f"📱 Postando story {i + 1}/{len(images)}...")
            humanized_delay()
            
            try:
                result = self._instagram.client.photo_upload_to_story(
                    path=str(img)
                )
                
                results.append({
                    "id": result.pk,
                    "type": "story",
                    "index": i + 1,
                })
                
                print(f"✅ Story {i + 1} postado!")
                
            except Exception as e:
                raise PostError(f"Erro ao postar story {i + 1}: {e}")
        
        return results
    
    def post_single(self, image: Path, caption: str) -> dict:
        """
        Posta uma única imagem.
        
        Args:
            image: Path da imagem.
            caption: Legenda do post.
            
        Returns:
            Dict com informações do post.
            
        Raises:
            PostError: Se houver erro na postagem.
        """
        self._ensure_logged_in()
        
        if not image.exists():
            raise PostError(f"Imagem não encontrada: {image}")
        
        print(f"📷 Postando imagem única...")
        humanized_delay()
        
        try:
            result = self._instagram.client.photo_upload(
                path=str(image),
                caption=caption
            )
            
            post_info = {
                "id": result.pk,
                "code": result.code,
                "type": "single",
                "caption_preview": caption[:100] + "..." if len(caption) > 100 else caption,
            }
            
            print(f"✅ Imagem postada! ID: {result.pk}")
            return post_info
            
        except Exception as e:
            raise PostError(f"Erro ao postar imagem: {e}")


# Função utilitária
def get_poster() -> InstagramPoster:
    """Retorna uma instância do poster."""
    return InstagramPoster()
