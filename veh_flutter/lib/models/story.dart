class Story {
  final int id;
  final String title;
  final String slug;
  final String description;
  final String? coverImageUrl;
  final String? startingSceneKey;

  const Story({
    required this.id,
    required this.title,
    required this.slug,
    required this.description,
    this.coverImageUrl,
    this.startingSceneKey,
  });

  factory Story.fromJson(Map<String, dynamic> json) => Story(
        id: json['id'] as int,
        title: json['title'] as String,
        slug: json['slug'] as String,
        description: json['description'] as String,
        coverImageUrl: json['cover_image_url'] as String?,
        startingSceneKey: json['starting_scene_key'] as String?,
      );
}
