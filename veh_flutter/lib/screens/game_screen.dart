import 'dart:async';

import 'package:flutter/material.dart';
import 'package:audioplayers/audioplayers.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:google_fonts/google_fonts.dart';
import '../services/story_service.dart';
import '../models/scene.dart';
import '../models/choice.dart';
import '../core/api_client.dart';
import '../core/constants.dart';

/// Contexte audio commun aux deux lecteurs.
///
/// Par défaut chaque `AudioPlayer` réclame `AUDIOFOCUS_GAIN` sur Android : le
/// lecteur de narration vole alors le focus à la musique, qu'audioplayers met
/// en pause (`FocusManager.onLoss`) sans jamais la relancer. Avec
/// `AndroidAudioFocus.none` — et `mixWithOthers` côté iOS — les deux flux se
/// superposent, comme les deux balises <audio> de la version web.
final AudioContext _mixedAudioContext = AudioContext(
  android: const AudioContextAndroid(
    contentType: AndroidContentType.music,
    usageType: AndroidUsageType.media,
    audioFocus: AndroidAudioFocus.none,
  ),
  iOS: AudioContextIOS(
    category: AVAudioSessionCategory.playback,
    options: const {AVAudioSessionOptions.mixWithOthers},
  ),
);

class GameScreen extends StatefulWidget {
  final String storySlug;
  final String storyTitle;
  final String sceneKey;

  const GameScreen({
    super.key,
    required this.storySlug,
    required this.storyTitle,
    required this.sceneKey,
  });

  @override
  State<GameScreen> createState() => _GameScreenState();
}

class _GameScreenState extends State<GameScreen>
    with SingleTickerProviderStateMixin {
  final _service = StoryService();

  // ── Game state ──────────────────────────────────────────────────────────
  Scene?   _scene;
  bool     _loading  = true;
  bool     _choosing = false;
  String?  _error;

  // ── Fade animation ──────────────────────────────────────────────────────
  late final AnimationController _fadeCtrl;
  late final Animation<double>   _fade;

  // ── Background music (audioplayers) ────────────────────────────────────
  final _musicPlayer = AudioPlayer();
  bool   _musicMuted = false;
  String? _currentMusic;

  /// Volume « standard » de la musique, identique au web (static/js/game.js).
  static const double _musicVolumeFull = 0.6;

  /// Volume pendant la narration : la musique passe sous la voix sans
  /// disparaître. Le web descend à 0.05, inaudible sur un haut-parleur de
  /// téléphone — d'où un ducking plus doux ici.
  static const double _musicVolumeDucked = 0.3;

  /// Niveau courant hors mute, suivi côté Dart pour enchaîner les fondus.
  double _musicVolume = _musicVolumeFull;
  Timer? _volumeFade;

  /// Pose du contexte audio : `_playMusic` l'attend avant toute lecture.
  late final Future<void> _audioReady;

  // ── Text-to-Speech narration (flutter_tts) ──────────────────────────────
  final _tts        = FlutterTts();
  bool  _ttsReady   = false;
  bool  _ttsPlaying = false;
  bool  _ttsPaused  = false;

  // ── Narration audio file (if uploaded in admin) ─────────────────────────
  final _narrationPlayer = AudioPlayer();
  StreamSubscription<void>? _narrationDoneSub;
  bool  _narrationMode   = false; // true = use audio file, false = use TTS

  @override
  void initState() {
    super.initState();
    _fadeCtrl = AnimationController(
        vsync: this, duration: const Duration(milliseconds: 500));
    _fade = CurvedAnimation(parent: _fadeCtrl, curve: Curves.easeIn);

    _audioReady = _initAudio();
    _initTts();
    _loadScene(widget.sceneKey);
  }

  /// Configure les lecteurs avant la première lecture : sans cela le focus
  /// audio par défaut est déjà demandé et la musique se fait couper.
  Future<void> _initAudio() async {
    await _musicPlayer.setReleaseMode(ReleaseMode.loop);
    try {
      await AudioPlayer.global.setAudioContext(_mixedAudioContext);
      await _musicPlayer.setAudioContext(_mixedAudioContext);
      await _narrationPlayer.setAudioContext(_mixedAudioContext);
    } catch (_) {}

    // Un seul abonnement pour toute la partie : se réabonner à chaque scène
    // empilait les callbacks de fin de narration.
    _narrationDoneSub = _narrationPlayer.onPlayerComplete.listen((_) {
      _unduckMusic();
      if (mounted) setState(() { _ttsPlaying = false; _ttsPaused = false; });
    });
  }

  @override
  void dispose() {
    _volumeFade?.cancel();
    _narrationDoneSub?.cancel();
    _fadeCtrl.dispose();
    _musicPlayer.dispose();
    _narrationPlayer.dispose();
    _tts.stop();
    super.dispose();
  }

  // ─────────────────────────────────────────────────────────────────────────
  //  TTS
  // ─────────────────────────────────────────────────────────────────────────

  Future<void> _initTts() async {
    await _tts.setLanguage('fr-FR');
    await _tts.setSpeechRate(0.42);  // vitesse confortable
    await _tts.setVolume(1.0);
    await _tts.setPitch(1.0);

    _tts.setStartHandler(() {
      if (mounted) setState(() { _ttsPlaying = true; _ttsPaused = false; });
      _duckMusic();
    });
    _tts.setCompletionHandler(() {
      if (mounted) setState(() { _ttsPlaying = false; _ttsPaused = false; });
      _unduckMusic();
    });
    _tts.setCancelHandler(() {
      if (mounted) setState(() { _ttsPlaying = false; _ttsPaused = false; });
      _unduckMusic();
    });
    _tts.setPauseHandler(() {
      if (mounted) setState(() { _ttsPlaying = false; _ttsPaused = true; });
      _unduckMusic();
    });
    _tts.setContinueHandler(() {
      if (mounted) setState(() { _ttsPlaying = true; _ttsPaused = false; });
      _duckMusic();
    });

    // Vérifier que le français est disponible
    final langs = await _tts.getLanguages as List<dynamic>? ?? [];
    final frAvailable = langs.any((l) => l.toString().startsWith('fr'));
    if (!frAvailable) await _tts.setLanguage('en-US'); // fallback

    if (mounted) setState(() => _ttsReady = true);
  }

  Future<void> _speakScene(Scene scene) async {
    if (_narrationMode && scene.audioNarrationUrl != null) {
      // Fichier audio uploadé — prioritaire
      try {
        await _narrationPlayer.stop();
        if (mounted) setState(() { _ttsPlaying = true; _ttsPaused = false; });
        _duckMusic();
        await _narrationPlayer.play(UrlSource(scene.audioNarrationUrl!));
      } catch (_) {}
    } else {
      // TTS — lecture du texte narratif
      if (!_ttsReady) return;
      await _tts.stop();
      // Certains moteurs Android n'appellent pas le start handler : on baisse
      // la musique nous-mêmes plutôt que d'attendre le callback.
      _duckMusic();
      await _tts.speak(scene.narrative);
    }
  }

  Future<void> _pauseNarration() async {
    if (_narrationMode) {
      await _narrationPlayer.pause();
      _unduckMusic();
      if (mounted) setState(() { _ttsPlaying = false; _ttsPaused = true; });
    } else {
      await _tts.pause();
    }
  }

  Future<void> _resumeNarration() async {
    if (_narrationMode) {
      _duckMusic();
      await _narrationPlayer.resume();
      if (mounted) setState(() { _ttsPlaying = true; _ttsPaused = false; });
    } else {
      _duckMusic();
      await _tts.speak(_scene!.narrative); // TTS n'a pas de resume fiable sur Android
    }
  }

  Future<void> _stopNarration() async {
    await _tts.stop();
    await _narrationPlayer.stop();
    _unduckMusic();
    if (mounted) setState(() { _ttsPlaying = false; _ttsPaused = false; });
  }

  Future<void> _toggleNarration() async {
    if (_ttsPlaying) {
      await _pauseNarration();
    } else if (_ttsPaused) {
      await _resumeNarration();
    } else {
      if (_scene != null) await _speakScene(_scene!);
    }
  }

  // ─────────────────────────────────────────────────────────────────────────
  //  Background music
  // ─────────────────────────────────────────────────────────────────────────

  Future<void> _playMusic(String musicFile, String transition) async {
    await _audioReady;
    final url = '${AppConstants.baseUrl}/static/music/$musicFile';
    final sameTrack = _currentMusic == musicFile;

    // « continuous » garde la piste en cours — sauf si elle s'est arrêtée,
    // auquel cas il faut bien la relancer.
    if (transition == 'continuous' &&
        sameTrack &&
        _musicPlayer.state == PlayerState.playing) {
      return;
    }

    _volumeFade?.cancel();
    _volumeFade = null;
    // Si le narrateur parle déjà, la piste démarre directement en retrait.
    _musicVolume = _ttsPlaying ? _musicVolumeDucked : _musicVolumeFull;
    try {
      if (transition == 'instant' || !sameTrack) await _musicPlayer.stop();
      await _musicPlayer.play(UrlSource(url),
          volume: _musicMuted ? 0 : _musicVolume);
      _currentMusic = musicFile;
    } catch (_) {}
  }

  /// Fondu progressif vers [target], comme `duck()`/`unduck()` côté web : un
  /// saut de volume brutal s'entend bien plus qu'une descente en douceur.
  void _fadeMusicTo(double target) {
    _volumeFade?.cancel();
    _volumeFade = null;
    if (_musicMuted) {
      _musicVolume = target; // sera appliqué au démute
      return;
    }
    const steps = 12;
    final from  = _musicVolume;
    final delta = (target - from) / steps;
    if (delta.abs() < 0.005) {
      _musicVolume = target;
      _musicPlayer.setVolume(target);
      return;
    }
    var i = 0;
    _volumeFade = Timer.periodic(const Duration(milliseconds: 35), (t) {
      i++;
      _musicVolume = i >= steps ? target : from + delta * i;
      _musicPlayer.setVolume(_musicVolume);
      if (i >= steps) { t.cancel(); _volumeFade = null; }
    });
  }

  void _duckMusic()   => _fadeMusicTo(_musicVolumeDucked);
  void _unduckMusic() => _fadeMusicTo(_musicVolumeFull);

  Future<void> _toggleMute() async {
    setState(() => _musicMuted = !_musicMuted);
    _volumeFade?.cancel();
    _volumeFade = null;
    if (_musicMuted) {
      await _musicPlayer.setVolume(0);
    } else {
      // On revient au niveau qu'impose l'état courant de la narration.
      _musicVolume = _ttsPlaying ? _musicVolumeDucked : _musicVolumeFull;
      await _musicPlayer.setVolume(_musicVolume);
    }
  }

  // ─────────────────────────────────────────────────────────────────────────
  //  Scene loading
  // ─────────────────────────────────────────────────────────────────────────

  Future<void> _loadScene(String key) async {
    setState(() { _loading = true; _error = null; });
    await _stopNarration();
    try {
      final scene = await _service.fetchScene(widget.storySlug, key);
      if (!mounted) return;
      setState(() {
        _scene = scene;
        _loading = false;
        _narrationMode = scene.audioNarrationUrl != null;
      });
      _fadeCtrl.forward(from: 0);
      await _playMusic(scene.musicFile, scene.musicTransition);

      // Lecture automatique après la transition visuelle (600ms)
      Future.delayed(const Duration(milliseconds: 900), () {
        if (mounted && _scene == scene) _speakScene(scene);
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      if (e.statusCode == 401) { Navigator.pushReplacementNamed(context, '/login'); return; }
      setState(() { _error = e.message; _loading = false; });
    } catch (_) {
      if (mounted) setState(() { _error = 'Erreur de connexion.'; _loading = false; });
    }
  }

  // ─────────────────────────────────────────────────────────────────────────
  //  Choice
  // ─────────────────────────────────────────────────────────────────────────

  Future<void> _onChoice(Choice choice) async {
    if (_choosing) return;
    setState(() => _choosing = true);
    await _stopNarration();
    try {
      final result = await _service.makeChoice(widget.storySlug, choice.id);
      if (!mounted) return;

      final isCompleted = result['is_completed'] as bool? ?? false;
      final nextData    = result['next_scene'] as Map<String, dynamic>?;

      if (nextData == null) {
        Navigator.pushReplacementNamed(context, '/ending', arguments: {
          'storySlug': widget.storySlug, 'storyTitle': widget.storyTitle,
          'endingType': null, 'narrative': 'Votre aventure est terminée.',
        });
        return;
      }

      final nextScene = Scene.fromJson(nextData);
      if (isCompleted || nextScene.isEnding) {
        Navigator.pushReplacementNamed(context, '/ending', arguments: {
          'storySlug': widget.storySlug, 'storyTitle': widget.storyTitle,
          'endingType': nextScene.endingType, 'narrative': nextScene.narrative,
        });
        return;
      }

      setState(() {
        _scene = nextScene;
        _choosing = false;
        _narrationMode = nextScene.audioNarrationUrl != null;
      });
      _fadeCtrl.forward(from: 0);
      await _playMusic(nextScene.musicFile, nextScene.musicTransition);
      Future.delayed(const Duration(milliseconds: 900), () {
        if (mounted && _scene == nextScene) _speakScene(nextScene);
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() => _choosing = false);
      if (e.statusCode == 401) { Navigator.pushReplacementNamed(context, '/login'); return; }
      ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.message), backgroundColor: Colors.red.shade800));
    } catch (_) {
      if (mounted) {
        setState(() => _choosing = false);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text('Erreur de connexion.'), backgroundColor: Colors.red));
      }
    }
  }

  void _confirmQuit() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF141920),
        title: const Text('Quitter ?', style: TextStyle(color: Color(0xFF4A9EE8))),
        content: const Text('La progression est sauvegardée automatiquement.',
            style: TextStyle(color: Color(0xFFA8C4DC))),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx),
              child: const Text('Continuer', style: TextStyle(color: Color(0xFF4A9EE8)))),
          TextButton(
              onPressed: () {
                Navigator.pop(ctx);
                Navigator.pushReplacementNamed(context, '/home');
              },
              child: const Text('Accueil', style: TextStyle(color: Color(0xFF8AAEC8)))),
        ],
      ),
    );
  }

  // ─────────────────────────────────────────────────────────────────────────
  //  Build
  // ─────────────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) { if (!didPop) _confirmQuit(); },
      child: Scaffold(
        appBar: AppBar(
          leading: IconButton(icon: const Icon(Icons.home_outlined), onPressed: _confirmQuit),
          title: Text(widget.storyTitle,
              style: const TextStyle(fontSize: 15), overflow: TextOverflow.ellipsis),
          actions: [
            // ── Bouton narration ──────────────────────────
            if (!_loading && _error == null)
              IconButton(
                icon: AnimatedSwitcher(
                  duration: const Duration(milliseconds: 200),
                  child: _ttsPlaying
                      ? const Icon(Icons.pause_circle_outline,
                          key: ValueKey('pause'), color: Color(0xFF4A9EE8))
                      : _ttsPaused
                          ? const Icon(Icons.play_circle_outline,
                              key: ValueKey('resume'), color: Color(0xFF8AAEC8))
                          : const Icon(Icons.volume_up,
                              key: ValueKey('play'), color: Color(0xFF506070)),
                ),
                tooltip: _ttsPlaying
                    ? 'Pause narration'
                    : _ttsPaused ? 'Reprendre' : 'Lire le récit',
                onPressed: _toggleNarration,
              ),
            // ── Bouton mute musique ───────────────────────
            IconButton(
              icon: Icon(_musicMuted ? Icons.music_off : Icons.music_note,
                  color: const Color(0xFF506070)),
              tooltip: _musicMuted ? 'Activer musique' : 'Couper musique',
              onPressed: _toggleMute,
            ),
          ],
        ),
        body: _loading
            ? const Center(child: CircularProgressIndicator(color: Color(0xFF4A9EE8)))
            : _error != null
                ? _buildError()
                : _buildGame(),
      ),
    );
  }

  Widget _buildError() => Center(
    child: Padding(
      padding: const EdgeInsets.all(32),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        const Icon(Icons.signal_wifi_off, color: Color(0xFF2A6AAA), size: 56),
        const SizedBox(height: 16),
        Text(_error!, style: const TextStyle(color: Color(0xFF8AAEC8)),
            textAlign: TextAlign.center),
        const SizedBox(height: 24),
        ElevatedButton.icon(
            onPressed: () => _loadScene(widget.sceneKey),
            icon: const Icon(Icons.refresh),
            label: const Text('Réessayer')),
      ]),
    ),
  );

  Widget _buildGame() {
    final scene = _scene!;
    return FadeTransition(
      opacity: _fade,
      child: Stack(children: [
        // ── Background image ───────────────────────────────
        // Toutes les histoires n'ont pas d'illustrations : on retombe alors
        // sur un dégradé, comme le fait déjà le web (game.html / game.js).
        Positioned.fill(
          child: scene.imageUrl != null
              ? Image.network(
                  scene.imageUrl!,
                  fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => const _SceneFallback(),
                )
              : const _SceneFallback(),
        ),

        // ── Gradient overlay ───────────────────────────────
        Positioned.fill(
          child: DecoratedBox(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  Colors.black.withValues(alpha: scene.imageUrl != null ? 0.4 : 0.0),
                  Colors.black.withValues(alpha: scene.imageUrl != null ? 0.7 : 0.0),
                  const Color(0xFF0F1319),
                ],
                stops: const [0.0, 0.5, 1.0],
              ),
            ),
          ),
        ),

        // ── Content ────────────────────────────────────────
        Column(children: [
          Expanded(
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(22, 28, 22, 16),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                // Badges scène + état narration
                Row(children: [
                  _SceneBadge(label: scene.sceneKey.replaceAll('_', ' ').toUpperCase()),
                  if (_ttsPlaying) ...[
                    const SizedBox(width: 10),
                    _NarrationIndicator(isPaused: false),
                  ] else if (_ttsPaused) ...[
                    const SizedBox(width: 10),
                    _NarrationIndicator(isPaused: true),
                  ],
                ]),
                const SizedBox(height: 20),

                // Séparateur doré
                Container(height: 1, decoration: const BoxDecoration(
                  gradient: LinearGradient(colors: [
                    Colors.transparent, Color(0xFF4A9EE8), Colors.transparent,
                  ]),
                )),
                const SizedBox(height: 20),

                // Texte narratif
                // Serif pour la lecture longue — même choix que le web
                Text(scene.narrative, style: GoogleFonts.crimsonText(
                  color: Colors.white,
                  fontSize: 19, height: 1.85, letterSpacing: 0.2,
                  shadows: scene.imageUrl != null
                      ? [const Shadow(color: Colors.black, blurRadius: 8)]
                      : null,
                )),
                const SizedBox(height: 24),
                Container(height: 1, color: const Color(0xFF1A2130)),
              ]),
            ),
          ),

          // ── Choices ─────────────────────────────────────
          Container(
            decoration: const BoxDecoration(
              color: Color(0xCC0F1319),
              border: Border(top: BorderSide(color: Color(0xFF1A2130))),
            ),
            padding: const EdgeInsets.fromLTRB(14, 10, 14, 28),
            child: scene.choices.isEmpty
                ? Center(child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    child: OutlinedButton.icon(
                      onPressed: () => Navigator.pushReplacementNamed(context, '/home'),
                      icon: const Icon(Icons.home_outlined, color: Color(0xFF8AAEC8)),
                      label: const Text("Retour à l'accueil",
                          style: TextStyle(color: Color(0xFF8AAEC8))),
                      style: OutlinedButton.styleFrom(
                          side: const BorderSide(color: Color(0xFF1E3050))),
                    ),
                  ))
                : Column(mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Padding(
                        padding: EdgeInsets.only(left: 4, bottom: 8, top: 4),
                        child: Text('QUE FAITES-VOUS ?', style: TextStyle(
                          color: Color(0xFF2A6AAA), fontSize: 10,
                          letterSpacing: 2.5, fontWeight: FontWeight.bold,
                        )),
                      ),
                      // Rejouabilité : le joueur est déjà passé par cette scène,
                      // on lui explique ce que signale le contour jaune.
                      if (scene.isRevisit)
                        const Padding(
                          padding: EdgeInsets.fromLTRB(4, 0, 4, 10),
                          child: Row(children: [
                            Icon(Icons.auto_awesome, size: 13, color: _kNewPath),
                            SizedBox(width: 6),
                            Expanded(child: Text(
                              'Les choix au contour jaune mènent à des chemins '
                              'jamais explorés — tentez-en un pour découvrir '
                              'une autre fin.',
                              style: TextStyle(
                                  color: _kNewPath, fontSize: 11.5, height: 1.35),
                            )),
                          ]),
                        ),
                      ...scene.choices.map((c) => _ChoiceTile(
                        choice: c, enabled: !_choosing,
                        isLoading: _choosing,
                        // Contour jaune seulement en rejouée, et seulement sur
                        // les chemins encore vierges : rien ne clignote lors de
                        // la première partie.
                        highlight: scene.isRevisit && !c.isExplored,
                        onTap: () => _onChoice(c),
                      )),
                    ]),
          ),
        ]),
      ]),
    );
  }
}

// ── Widgets utilitaires ───────────────────────────────────────────────────────

class _SceneBadge extends StatelessWidget {
  final String label;
  const _SceneBadge({required this.label});
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
    decoration: BoxDecoration(
      color: Colors.black.withValues(alpha: 0.5),
      borderRadius: BorderRadius.circular(20),
      border: Border.all(color: const Color(0xFF1E2838).withValues(alpha: 0.7)),
    ),
    child: Text(label, style: const TextStyle(
        color: Color(0xFF8AAEC8), fontSize: 9, letterSpacing: 1.5)),
  );
}

class _NarrationIndicator extends StatelessWidget {
  final bool isPaused;
  const _NarrationIndicator({required this.isPaused});
  @override
  Widget build(BuildContext context) => Row(mainAxisSize: MainAxisSize.min, children: [
    if (!isPaused)
      const SizedBox(width: 14, height: 14,
          child: CircularProgressIndicator(strokeWidth: 1.5, color: Color(0xFF4A9EE8)))
    else
      const Icon(Icons.pause, size: 14, color: Color(0xFF8AAEC8)),
    const SizedBox(width: 5),
    Text(isPaused ? 'En pause' : 'Lecture...',
        style: TextStyle(
          color: isPaused ? const Color(0xFF8AAEC8) : const Color(0xFF4A9EE8),
          fontSize: 11,
        )),
  ]);
}

/// Couleur des chemins jamais empruntés : un jaune franc, lisible sur le fond
/// sombre du jeu et impossible à confondre avec le bleu de l'interface.
const Color _kNewPath = Color(0xFFFFC53D);

/// Étiquette d'état d'un choix (« NOUVEAU » / « DÉJÀ VU »).
class _ChoiceTag extends StatelessWidget {
  final String label;
  final Color color;
  const _ChoiceTag({required this.label, required this.color});

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
    decoration: BoxDecoration(
      color: color.withValues(alpha: 0.14),
      borderRadius: BorderRadius.circular(20),
      border: Border.all(color: color.withValues(alpha: 0.5)),
    ),
    child: Text(label, style: TextStyle(
        color: color, fontSize: 8.5, letterSpacing: 1.1,
        fontWeight: FontWeight.bold)),
  );
}

class _ChoiceTile extends StatefulWidget {
  final Choice choice;
  final bool enabled;
  final bool isLoading;

  /// Chemin jamais emprunté lors d'une partie précédente : contour jaune
  /// pulsant, pour suggérer au joueur d'essayer une autre branche.
  final bool highlight;

  final VoidCallback onTap;

  const _ChoiceTile({
    required this.choice, required this.enabled,
    required this.isLoading, required this.highlight, required this.onTap,
  });

  @override
  State<_ChoiceTile> createState() => _ChoiceTileState();
}

class _ChoiceTileState extends State<_ChoiceTile>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulse = AnimationController(
      vsync: this, duration: const Duration(milliseconds: 1300));

  /// Le halo ne pulse pas si le système demande de limiter les animations.
  bool _reduceMotion = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _reduceMotion = MediaQuery.of(context).disableAnimations;
    _syncPulse();
  }

  @override
  void didUpdateWidget(covariant _ChoiceTile old) {
    super.didUpdateWidget(old);
    if (old.highlight != widget.highlight) _syncPulse();
  }

  void _syncPulse() {
    if (widget.highlight && !_reduceMotion) {
      if (!_pulse.isAnimating) _pulse.repeat(reverse: true);
    } else {
      _pulse.stop();
      _pulse.value = 0;
    }
  }

  @override
  void dispose() {
    _pulse.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final choice   = widget.choice;
    final enabled  = widget.enabled;
    final glow     = widget.highlight;
    final explored = choice.isExplored;
    final accent   = glow ? _kNewPath : const Color(0xFF4A9EE8);

    // Contenu figé : il ne dépend pas de l'animation, donc il n'est pas
    // reconstruit à chaque image du halo.
    final content = Row(children: [
      Container(
        width: 28, height: 28,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: accent.withValues(alpha: 0.12),
          border: Border.all(
              color: accent.withValues(
                  alpha: !enabled ? 0.2 : explored ? 0.3 : 0.6)),
        ),
        child: Center(child: Text('${choice.order + 1}',
            style: TextStyle(
              color: accent.withValues(
                  alpha: !enabled ? 0.3 : explored ? 0.5 : 1.0),
              fontSize: 12, fontWeight: FontWeight.bold,
            ))),
      ),
      const SizedBox(width: 12),
      Expanded(child: Text(choice.text, style: TextStyle(
          color: !enabled
              ? Colors.white30
              : explored ? Colors.white.withValues(alpha: 0.55) : Colors.white,
          fontSize: 15, height: 1.4))),
      if (glow) ...[
        const SizedBox(width: 8),
        const _ChoiceTag(label: 'NOUVEAU', color: _kNewPath),
      ] else if (explored) ...[
        const SizedBox(width: 8),
        const _ChoiceTag(label: 'DÉJÀ VU', color: Color(0xFF64788C)),
      ],
      const SizedBox(width: 8),
      if (widget.isLoading)
        const SizedBox(width: 16, height: 16,
            child: CircularProgressIndicator(strokeWidth: 1.5, color: Color(0xFF4A9EE8)))
      else
        Icon(Icons.chevron_right_rounded, size: 20,
            color: !enabled
                ? Colors.white12
                : glow ? _kNewPath : const Color(0xFF4A9EE8)),
    ]);

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: enabled ? widget.onTap : null,
          borderRadius: BorderRadius.circular(10),
          child: AnimatedBuilder(
            animation: _pulse,
            builder: (context, child) {
              // t = 0 : contour jaune sobre ; t = 1 : halo large.
              final t = glow ? (_reduceMotion ? 0.6 : _pulse.value) : 0.0;
              return DecoratedBox(
                decoration: BoxDecoration(
                  color: !enabled
                      ? const Color(0xAA0F1319)
                      : explored ? const Color(0x990F1319) : const Color(0xCC141920),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(
                    color: glow
                        ? _kNewPath.withValues(alpha: 0.65 + 0.35 * t)
                        : enabled
                            ? const Color(0xFF1E3050)
                            : const Color(0xFF1A2130),
                    width: glow ? 1.8 : 1,
                  ),
                  boxShadow: glow
                      ? [BoxShadow(
                          color: _kNewPath.withValues(alpha: 0.10 + 0.30 * t),
                          blurRadius: 6 + 14 * t,
                          spreadRadius: 0.5 * t)]
                      : null,
                ),
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 13),
                  child: child,
                ),
              );
            },
            child: content,
          ),
        ),
      ),
    );
  }
}

/// Fond de repli quand la scène n'a pas d'illustration (ou qu'elle échoue à
/// charger). Reprend le dégradé de la version web, en charte NovaPay.
class _SceneFallback extends StatelessWidget {
  const _SceneFallback();

  @override
  Widget build(BuildContext context) {
    return const DecoratedBox(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFF0F1319), Color(0xFF16263A), Color(0xFF0F1319)],
          stops: [0.0, 0.5, 1.0],
        ),
      ),
    );
  }
}
