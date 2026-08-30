"""
Service TTS Gemini partagé — synthèse vocale des narrations de scènes.

Utilisé par les commandes :
    - generate_narrations       (toutes les scènes)
    - generate_narrations_demo  (uniquement le chemin des premiers choix)

La sortie de Gemini TTS est du PCM brut (16 bits, mono). On l'enveloppe dans
un fichier WAV valide sans aucune dépendance externe (module `wave` standard).
Le taux d'échantillonnage est lu depuis le mime_type de la réponse pour éviter
tout décalage de vitesse si Google change le format.
"""

import os
import wave
from pathlib import Path


# Paramètres audio par défaut de Gemini TTS
DEFAULT_SAMPLE_RATE = 24000
SAMPLE_WIDTH        = 2   # 16 bits = 2 octets
CHANNELS            = 1

# Modèle et voix par défaut
DEFAULT_MODEL = 'gemini-2.5-flash-preview-tts'
DEFAULT_VOICE = 'Charon'   # voix grave, adaptée à un thriller narratif


class TTSError(RuntimeError):
    """Erreur de configuration ou d'appel du service TTS."""


def get_client():
    """
    Instancie le client Gemini à partir de GEMINI_API_KEY.
    Lève TTSError avec un message clair si la clé ou le SDK manque.
    """
    api_key = os.environ.get('GEMINI_API_KEY', '')
    if not api_key:
        raise TTSError(
            "GEMINI_API_KEY n'est pas configurée. "
            "Ajoutez-la dans votre .env (la même que celle du jeu)."
        )
    try:
        from google import genai
    except ImportError:
        raise TTSError(
            "Le SDK google-genai n'est pas installé.\n"
            "Lancez : pip install google-genai"
        )
    return genai.Client(api_key=api_key)


def build_prompt(narrative: str, style: str = '') -> str:
    """Ajoute une éventuelle consigne de style devant le texte à lire."""
    narrative = (narrative or '').strip()
    if style:
        return f"Lis le texte suivant {style} :\n\n{narrative}"
    return narrative


def parse_rate(mime_type: str) -> int:
    """Extrait le taux d'échantillonnage du mime_type (ex: audio/L16;rate=24000)."""
    for token in (mime_type or '').split(';'):
        token = token.strip()
        if token.startswith('rate='):
            try:
                return int(token.split('=', 1)[1])
            except (ValueError, IndexError):
                break
    return DEFAULT_SAMPLE_RATE


def synthesize(client, text: str, voice: str = DEFAULT_VOICE, model: str = DEFAULT_MODEL):
    """
    Appelle Gemini TTS et retourne (octets PCM bruts, taux d'échantillonnage).
    Lève TTSError si la réponse ne contient pas d'audio.
    """
    from google.genai import types

    response = client.models.generate_content(
        model=model,
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=['AUDIO'],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice,
                    )
                )
            ),
        ),
    )
    try:
        part = response.candidates[0].content.parts[0]
        data = part.inline_data.data
        mime = part.inline_data.mime_type or ''
    except (AttributeError, IndexError, TypeError):
        raise TTSError("Réponse Gemini sans données audio (quota ou modèle invalide ?).")
    if not data:
        raise TTSError("Réponse audio vide.")
    return data, parse_rate(mime)


def write_wav(path: Path, pcm: bytes, rate: int = DEFAULT_SAMPLE_RATE):
    """Enveloppe le PCM brut dans un fichier WAV valide (aucune dépendance)."""
    with wave.open(str(path), 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(rate)
        wf.writeframes(pcm)
