class Choice {
  final int id;
  final String text;
  final String? nextSceneKey;
  final int order;

  /// Ce chemin a déjà été emprunté par le joueur lors d'une partie précédente.
  /// Renseigné par l'API (`is_explored`) — sert à mettre en avant les choix
  /// jamais essayés, qui mènent aux autres fins.
  final bool isExplored;

  const Choice({
    required this.id,
    required this.text,
    this.nextSceneKey,
    required this.order,
    this.isExplored = false,
  });

  factory Choice.fromJson(Map<String, dynamic> json) => Choice(
        id: json['id'] as int,
        text: json['text'] as String,
        nextSceneKey: json['next_scene_key'] as String?,
        order: json['order'] as int,
        isExplored: json['is_explored'] as bool? ?? false,
      );
}
