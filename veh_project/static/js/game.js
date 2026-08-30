/**
 * VEH — Vous Êtes le Héros
 * Musique de fond adaptative + narration automatique (TTS ou fichier audio).
 * Vanilla JS pur, aucun framework.
 */

'use strict';

// ═══════════════════════════════════════════════════════════
//  CLASSE AudioManager — Musique de fond
// ═══════════════════════════════════════════════════════════

class AudioManager {
    constructor(audioElement, staticUrl) {
        this.audioElement = audioElement;
        this.staticUrl    = staticUrl.endsWith('/') ? staticUrl : staticUrl + '/';
        this.currentTrack = null;
        this.isMuted      = false;
        this.targetVolume = 0.6;
        this._fadeInterval = null;

        const savedMute = localStorage.getItem('veh_muted');
        if (savedMute === 'true') {
            this.isMuted = true;
            this.audioElement.volume = 0;
        } else {
            this.audioElement.volume = this.targetVolume;
        }
    }

    _buildTrackUrl(t) { return `${this.staticUrl}music/${t}`; }

    _clearFade() {
        if (this._fadeInterval) { clearInterval(this._fadeInterval); this._fadeInterval = null; }
    }

    fadeOut() {
        return new Promise(resolve => {
            this._clearFade();
            const step = this.targetVolume / 16, delay = 50;
            this._fadeInterval = setInterval(() => {
                if (this.audioElement.volume > step) {
                    this.audioElement.volume = Math.max(0, this.audioElement.volume - step);
                } else {
                    this.audioElement.volume = 0;
                    this.audioElement.pause();
                    this._clearFade(); resolve();
                }
            }, delay);
        });
    }

    fadeIn() {
        return new Promise(resolve => {
            this._clearFade();
            if (this.isMuted) { resolve(); return; }
            this.audioElement.volume = 0;
            const step = this.targetVolume / 16, delay = 50;
            this._fadeInterval = setInterval(() => {
                if (this.audioElement.volume < this.targetVolume - step) {
                    this.audioElement.volume = Math.min(this.targetVolume, this.audioElement.volume + step);
                } else {
                    this.audioElement.volume = this.targetVolume; this._clearFade(); resolve();
                }
            }, delay);
        });
    }

    async playTrack(trackName, transition) {
        const newUrl = this._buildTrackUrl(trackName);
        if (transition === 'continuous') {
            if (this.currentTrack === trackName && !this.audioElement.paused) return;
            transition = 'fade';
        }
        if (transition === 'instant') {
            this._clearFade();
            this.audioElement.pause();
            this.audioElement.currentTime = 0;
            this.audioElement.src = newUrl;
            this.audioElement.volume = this.isMuted ? 0 : this.targetVolume;
            this.currentTrack = trackName;
            try { await this.audioElement.play(); }
            catch (_) { this._waitForInteraction(newUrl, trackName); }
            return;
        }
        if (this.currentTrack && !this.audioElement.paused) await this.fadeOut();
        this.audioElement.src = newUrl;
        this.audioElement.currentTime = 0;
        this.currentTrack = trackName;
        try { await this.audioElement.play(); await this.fadeIn(); }
        catch (_) { this._waitForInteraction(newUrl, trackName); }
    }

    _waitForInteraction(url, trackName) {
        const start = async () => {
            this.audioElement.src = url;
            this.currentTrack = trackName;
            this.audioElement.volume = this.isMuted ? 0 : this.targetVolume;
            try { await this.audioElement.play(); } catch (_) {}
            document.removeEventListener('click', start);
            document.removeEventListener('keydown', start);
        };
        document.addEventListener('click', start, { once: true });
        document.addEventListener('keydown', start, { once: true });
    }

    /** Baisser le volume progressivement pendant la narration */
    duck() {
        this._clearFade();
        if (this.isMuted) return;
        const target = 0.05;
        const step   = Math.max((this.audioElement.volume - target) / 10, 0.005);
        this._fadeInterval = setInterval(() => {
            if (this.audioElement.volume > target + step) {
                this.audioElement.volume = Math.max(target, this.audioElement.volume - step);
            } else {
                this.audioElement.volume = target;
                this._clearFade();
            }
        }, 30);
    }

    /** Remonter le volume progressivement après la narration */
    unduck() {
        this._clearFade();
        if (this.isMuted) return;
        const target = this.targetVolume;
        const step   = Math.max((target - this.audioElement.volume) / 10, 0.005);
        this._fadeInterval = setInterval(() => {
            if (this.audioElement.volume < target - step) {
                this.audioElement.volume = Math.min(target, this.audioElement.volume + step);
            } else {
                this.audioElement.volume = target;
                this._clearFade();
            }
        }, 30);
    }

    toggleMute() {
        this.isMuted = !this.isMuted;
        localStorage.setItem('veh_muted', this.isMuted);
        if (this.isMuted) {
            this._clearFade(); this.audioElement.volume = 0;
        } else {
            if (this.audioElement.paused && this.currentTrack) this.audioElement.play().catch(() => {});
            this.audioElement.volume = this.targetVolume;
        }
        document.getElementById('icon-sound-on') ?.classList.toggle('hidden', this.isMuted);
        document.getElementById('icon-sound-off')?.classList.toggle('hidden', !this.isMuted);
    }
}


// ═══════════════════════════════════════════════════════════
//  CLASSE NarrationController
//  Lit le texte de la scène automatiquement.
//  Priorité : fichier audio uploadé → synthèse vocale (TTS)
// ═══════════════════════════════════════════════════════════

class NarrationController {
    /**
     * @param {HTMLAudioElement} audioEl        <audio id="narration-audio">
     * @param {AudioManager}     audioManager   Pour le ducking musique
     * @param {string}           narrativeText  Texte à lire en TTS
     */
    constructor(audioEl, audioManager, narrativeText) {
        this.audioEl   = audioEl;
        this.manager   = audioManager;
        this.text      = narrativeText;
        this.synth     = window.speechSynthesis || null;

        this.mode      = 'none';   // 'audio' | 'tts' | 'none'
        this.isPlaying = false;
        this.isPaused  = false;

        // Éléments UI
        this.btn        = document.getElementById('narration-btn');
        this.iconPlay   = document.getElementById('narration-icon-play');
        this.iconPause  = document.getElementById('narration-icon-pause');
        this.label      = document.getElementById('narration-label');

        // Fin naturelle du fichier audio
        this.audioEl?.addEventListener('ended', () => this._onEnded());
    }

    /**
     * Initialise le mode (audio ou TTS) et affiche le bouton.
     * @param {string|string[]} audioUrls  URL(s) candidates du fichier audio, testées dans l'ordre
     */
    init(audioUrls) {
        const candidates = (Array.isArray(audioUrls) ? audioUrls : [audioUrls])
            .filter(Boolean);

        if (candidates.length) {
            this.mode = 'audio';
            this._resolveAudioCandidate(candidates, 0);
        } else if (this.synth) {
            this.mode = 'tts';
        } else {
            return;
        }
        if (this.btn) {
            this.btn.classList.replace('hidden', 'flex');
            this.btn.addEventListener('click', () => this.toggle());
        }
    }

    /**
     * Teste les URLs candidates l'une après l'autre ; la première qui charge
     * devient la source. Si toutes échouent → repli sur la synthèse vocale (TTS).
     */
    _resolveAudioCandidate(candidates, idx) {
        if (idx >= candidates.length) {
            // Aucun fichier trouvé : repli silencieux sur TTS
            this.mode = this.synth ? 'tts' : 'none';
            if (this.mode === 'none') this.btn?.classList.replace('flex', 'hidden');
            return;
        }
        const url   = candidates[idx];
        const probe = new Audio();
        probe.preload = 'metadata';
        probe.addEventListener('loadedmetadata', () => {
            if (this.mode === 'audio') this.audioEl.src = url;
        }, { once: true });
        probe.addEventListener('error', () => {
            this._resolveAudioCandidate(candidates, idx + 1);
        }, { once: true });
        probe.src = url;
    }

    /** Lance ou reprend la lecture */
    play() {
        if (this.mode === 'audio') {
            // La source n'est pas encore résolue (probe en cours) : on abandonne proprement
            if (!this.audioEl.src) return;
            if (!this.isPaused) this.audioEl.currentTime = 0;
            // Si la lecture échoue (autoplay bloqué, fichier absent), on annule l'état
            this.audioEl.play().catch(() => {
                this.manager.unduck();
                this.isPlaying = false;
                this._updateUI();
            });
        } else if (this.mode === 'tts') {
            if (this.isPaused && this.synth.paused) {
                this.synth.resume();
            } else {
                this._speakTTS();
            }
        } else return;

        this.manager.duck();
        this.isPlaying = true;
        this.isPaused  = false;
        this._updateUI();
    }

    /** Met en pause */
    pause() {
        if (this.mode === 'audio') {
            this.audioEl.pause();
        } else if (this.mode === 'tts') {
            this.synth?.pause();
        }
        this.manager.unduck();
        this.isPlaying = false;
        this.isPaused  = true;
        this._updateUI();
    }

    /** Arrête complètement et remet à zéro */
    stop() {
        if (this.mode === 'audio') {
            this.audioEl.pause();
            this.audioEl.currentTime = 0;
        } else if (this.mode === 'tts') {
            this.synth?.cancel();
        }
        this.manager.unduck();
        this.isPlaying = false;
        this.isPaused  = false;
        this._updateUI();
    }

    /** Bascule lecture / pause */
    toggle() {
        this.isPlaying ? this.pause() : this.play();
    }

    /**
     * Démarre automatiquement après un délai (post-transition de scène).
     * @param {number} delay  ms
     */
    autoPlay(delay = 1000) {
        setTimeout(() => {
            if (!this.isPlaying) this.play();
        }, delay);
    }

    // ── Privé ──────────────────────────────────────────────

    _speakTTS() {
        this.synth.cancel();
        const utter = new SpeechSynthesisUtterance(this.text);
        utter.lang   = 'fr-FR';
        utter.rate   = 0.88;   // légèrement plus lent pour la compréhension
        utter.pitch  = 1.0;
        utter.volume = 1.0;

        // Choisir la meilleure voix française disponible
        const voices = this.synth.getVoices();
        const pick = voices.find(v => v.lang === 'fr-FR' && v.localService)
                  || voices.find(v => v.lang.startsWith('fr') && v.localService)
                  || voices.find(v => v.lang.startsWith('fr'));
        if (pick) utter.voice = pick;

        utter.onend   = () => this._onEnded();
        utter.onerror = (e) => {
            if (e.error !== 'interrupted') { this._onEnded(); }
        };

        this.synth.speak(utter);
    }

    _onEnded() {
        this.manager.unduck();
        this.isPlaying = false;
        this.isPaused  = false;
        this._updateUI();
    }

    _updateUI() {
        if (!this.btn) return;
        this.iconPlay ?.classList.toggle('hidden',  this.isPlaying);
        this.iconPause?.classList.toggle('hidden', !this.isPlaying);
        if (this.label) {
            this.label.textContent = this.isPlaying
                ? 'Pause'
                : (this.isPaused ? 'Reprendre' : 'Lire');
        }
        // Couleur du bouton selon l'état
        this.btn.classList.toggle('text-yellow-300', this.isPlaying);
        this.btn.classList.toggle('text-purple-400', !this.isPlaying);
    }
}


// ═══════════════════════════════════════════════════════════
//  INITIALISATION
// ═══════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    const gameData = document.getElementById('game-data');
    if (!gameData) return;

    const musicFile    = gameData.dataset.music      || 'calm_ambient.mp3';
    const transition   = gameData.dataset.transition || 'fade';
    const staticUrl    = gameData.dataset.staticUrl  || '/static/';
    const sceneKey     = gameData.dataset.sceneKey   || '';
    const ttsEndpoint  = gameData.dataset.narrationEndpoint || '';
    // Priorité : fichier uploadé (admin) → fichier statique (.mp3/.wav) →
    //            Gemini TTS à la demande (serveur) → synthèse vocale navigateur.
    const uploaded     = gameData.dataset.narration || '';
    const narrationUrls = uploaded
        ? [uploaded]
        : [
            ...(sceneKey ? [
                `${staticUrl}narrations/${sceneKey}.mp3`,
                `${staticUrl}narrations/${sceneKey}.wav`,
            ] : []),
            ...(ttsEndpoint ? [ttsEndpoint] : []),
          ];

    // Lire le texte narratif depuis le JSON caché
    const narrativeEl  = document.getElementById('veh-narrative');
    const narrativeText = narrativeEl ? JSON.parse(narrativeEl.textContent) : '';

    // ── Musique de fond ─────────────────────────────────────
    const bgAudio = document.getElementById('bg-music');
    if (!bgAudio) return;
    const audio = new AudioManager(bgAudio, staticUrl);

    // Sync icône mute au chargement
    document.getElementById('icon-sound-on') ?.classList.toggle('hidden', audio.isMuted);
    document.getElementById('icon-sound-off')?.classList.toggle('hidden', !audio.isMuted);

    // Lancer la piste musicale
    audio.playTrack(musicFile, transition);
    document.getElementById('mute-btn')?.addEventListener('click', () => audio.toggleMute());

    // ── Narration (TTS ou fichier audio) ────────────────────
    const narrationAudio = document.getElementById('narration-audio');
    const narration = new NarrationController(narrationAudio, audio, narrativeText);

    // Attendre que les voix TTS soient chargées (Chrome les charge async)
    const initNarration = () => {
        narration.init(narrationUrls);
        // Lecture automatique après la transition de la scène
        if (narration.mode !== 'none') {
            narration.autoPlay(1100);
        }
    };

    if (window.speechSynthesis && window.speechSynthesis.getVoices().length === 0) {
        window.speechSynthesis.onvoiceschanged = () => {
            window.speechSynthesis.onvoiceschanged = null;
            initNarration();
        };
    } else {
        initNarration();
    }

    // ── Transitions lors des choix ──────────────────────────
    document.querySelectorAll('.choice-form').forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            narration.stop();  // Arrêt narration avant de changer de scène

            document.querySelectorAll('.choice-form button').forEach(b => b.disabled = true);

            const sceneBg = document.getElementById('scene-bg');
            const content = document.getElementById('game-content');
            if (sceneBg) { sceneBg.style.transition = 'opacity 0.4s ease'; sceneBg.style.opacity = '0'; }
            if (content) { content.style.transition = 'opacity 0.4s ease'; content.style.opacity = '0.3'; }

            await new Promise(r => setTimeout(r, 400));
            form.submit();
        });
    });

    // ── Image de fond statique (fallback si pas d'image uploadée) ──
    const sceneBg = document.getElementById('scene-bg');
    if (sceneBg) {
        const hasUploadedImage = sceneBg.dataset.hasImage === '1';
        if (!hasUploadedImage && sceneKey) {
            _tryLoadSceneImage(staticUrl, sceneKey, sceneBg);
        }
        // Fade-in
        sceneBg.style.opacity = '0';
        requestAnimationFrame(() => {
            sceneBg.style.transition = 'opacity 0.8s ease';
            sceneBg.style.opacity    = '1';
        });
    }
});

/**
 * Essaie de charger une image statique pour la scène dans l'ordre :
 * png, jpg, jpeg, jfif, webp. Si trouvée, l'applique en background-image.
 * (.jfif est un JPEG déguisé, pris en charge par tous les navigateurs.)
 */
function _tryLoadSceneImage(staticUrl, sceneKey, element) {
    const formats = ['png', 'jpg', 'jpeg', 'jfif', 'webp'];
    let idx = 0;
    function tryNext() {
        if (idx >= formats.length) return;
        const url = `${staticUrl}scenes/${sceneKey}.${formats[idx++]}`;
        const img = new Image();
        img.onload  = () => { element.style.backgroundImage = `url(${url})`; };
        img.onerror = tryNext;
        img.src     = url;
    }
    tryNext();
}
