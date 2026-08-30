"""
Service Google Gemini pour enrichir les textes narratifs du jeu VEH.
Utilise le modèle Gemini Flash pour des réponses rapides et immersives.
"""

import os
import logging

logger = logging.getLogger(__name__)


class GeminiService:
    """
    Service d'enrichissement narratif via l'API Google Gemini.
    En cas d'erreur, retourne toujours le texte original (fallback silencieux).
    """

    # Prompt système — rôle de l'auteur
    SYSTEM_PROMPT = (
        "Tu es un auteur de romans noirs et thrillers. "
        "Enrichis ce texte narratif de jeu en gardant exactement "
        "le même sens et les mêmes faits. Rends-le plus immersif, "
        "plus atmosphérique. Maximum 4 phrases. Réponds uniquement "
        "avec le texte enrichi, rien d'autre."
    )

    def __init__(self):
        self.api_key = os.environ.get('GEMINI_API_KEY', '')
        self._client = None

    def _get_client(self):
        """Initialise le client Gemini de façon lazy."""
        if not self._client and self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel('gemini-1.5-flash')
            except ImportError:
                logger.warning("google-generativeai n'est pas installé. Enrichissement désactivé.")
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation de Gemini : {e}")
        return self._client

    def enrich_narrative(
        self,
        scene_narrative: str,
        story_title: str,
        previous_choice: str = None
    ) -> str:
        """
        Enrichit un texte narratif de scène avec l'IA Gemini.

        Args:
            scene_narrative: Le texte original de la scène
            story_title: Le titre de l'histoire (contexte)
            previous_choice: Le choix précédent du joueur (contexte, optionnel)

        Returns:
            Le texte enrichi, ou le texte original en cas d'erreur
        """
        if not self.api_key:
            logger.debug("GEMINI_API_KEY non configurée, retour du texte original.")
            return scene_narrative

        client = self._get_client()
        if not client:
            return scene_narrative

        try:
            # Construire le prompt avec contexte
            context_parts = [f"Histoire : {story_title}"]
            if previous_choice:
                context_parts.append(f"Choix précédent du joueur : {previous_choice}")
            context_parts.append(f"Texte à enrichir : {scene_narrative}")

            full_prompt = f"{self.SYSTEM_PROMPT}\n\n" + "\n".join(context_parts)

            response = client.generate_content(full_prompt)
            enriched = response.text.strip()

            # Vérification de sécurité : si la réponse est vide, utiliser l'original
            if not enriched:
                return scene_narrative

            return enriched

        except Exception as e:
            logger.error(f"Erreur Gemini lors de l'enrichissement narratif : {e}")
            # Fallback silencieux — le jeu continue avec le texte original
            return scene_narrative
