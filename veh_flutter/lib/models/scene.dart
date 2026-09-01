import 'choice.dart';

class Scene {
  final int id;
  final String sceneKey;
  final String narrative;
  final String? imageUrl;
  final String musicFile;
  final String musicTransition;
  final bool isEnding;
  final String? endingType;
  final List<Choice> choices;
  final String? audioNarrationUrl;

  /// Le joueur est déjà passé par cette scène dans une partie précédente :
  /// on peut alors lui signaler les choix qu'il n'a jamais tentés.
  final bool isRevisit;

  const Scene({
    required this.id,
    required this.sceneKey,
    required this.narrative,
    this.imageUrl,
    required this.musicFile,
    required this.musicTransition,
    required this.isEnding,
    this.endingType,
    required this.choices,
    this.audioNarrationUrl,
    this.isRevisit = false,
  });

  factory Scene.fromJson(Map<String, dynamic> json) => Scene(
        id: json['id'] as int,
        sceneKey: json['scene_key'] as String,
        narrative: json['narrative'] as String,
        imageUrl: json['image_url'] as String?,
        musicFile: json['music_file'] as String? ?? 'calm_ambient.mp3',
        musicTransition: json['music_transition'] as String? ?? 'fade',
        isEnding: json['is_ending'] as bool? ?? false,
        endingType: json['ending_type'] as String?,
        audioNarrationUrl: json['audio_narration_url'] as String?,
        isRevisit: json['is_revisit'] as bool? ?? false,
        choices: (json['choices'] as List<dynamic>? ?? [])
            .map((c) => Choice.fromJson(c as Map<String, dynamic>))
            .toList(),
      );
}
