import '../core/api_client.dart';
import '../core/constants.dart';
import '../models/story.dart';
import '../models/scene.dart';

class StoryService {
  final _api = ApiClient();

  Future<List<Story>> fetchStories() async {
    final res = await _api.get('${AppConstants.storiesEndpoint}/');
    final data = await _api.parseResponse(res);
    final list = data as List<dynamic>;
    return list.map((j) => Story.fromJson(j as Map<String, dynamic>)).toList();
  }

  Future<Scene> fetchScene(String storySlug, String sceneKey) async {
    final res = await _api.get(
      '${AppConstants.playEndpoint}/$storySlug/scene/$sceneKey/',
    );
    final data = await _api.parseResponse(res) as Map<String, dynamic>;
    return Scene.fromJson(data);
  }

  Future<Map<String, dynamic>> makeChoice(
      String storySlug, int choiceId) async {
    final res = await _api.post(
      '${AppConstants.playEndpoint}/$storySlug/choose/',
      {'choice_id': choiceId},
    );
    return await _api.parseResponse(res) as Map<String, dynamic>;
  }
}
