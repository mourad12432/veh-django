class Choice {
  final int id;
  final String text;
  final String? nextSceneKey;
  final int order;

  const Choice({
    required this.id,
    required this.text,
    this.nextSceneKey,
    required this.order,
  });

  factory Choice.fromJson(Map<String, dynamic> json) => Choice(
        id: json['id'] as int,
        text: json['text'] as String,
        nextSceneKey: json['next_scene_key'] as String?,
        order: json['order'] as int,
      );
}
