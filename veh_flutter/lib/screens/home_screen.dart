import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import '../services/story_service.dart';
import '../models/story.dart';
import '../core/api_client.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _service = StoryService();
  List<Story>? _stories;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadStories();
  }

  Future<void> _loadStories() async {
    setState(() { _loading = true; _error = null; });
    try {
      final stories = await _service.fetchStories();
      if (mounted) setState(() { _stories = stories; _loading = false; });
    } on ApiException catch (e) {
      if (mounted) setState(() { _error = e.message; _loading = false; });
    } catch (_) {
      if (mounted) setState(() { _error = 'Impossible de charger les histoires.'; _loading = false; });
    }
  }

  void _playStory(Story story) {
    Navigator.pushNamed(context, '/game', arguments: {
      'storySlug': story.slug,
      'storyTitle': story.title,
      'sceneKey': 'auto',
    });
  }

  Future<void> _logout() async {
    await context.read<AuthService>().logout();
    if (mounted) Navigator.pushReplacementNamed(context, '/login');
  }

  @override
  Widget build(BuildContext context) {
    final username = context.watch<AuthService>().username ?? 'Héros';

    return Scaffold(
      appBar: AppBar(
        title: const Text('Vous Êtes le Héros',
            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 17)),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Déconnexion',
            onPressed: _logout,
          ),
        ],
      ),
      body: RefreshIndicator(
        color: const Color(0xFF4A9EE8),
        onRefresh: _loadStories,
        child: CustomScrollView(
          slivers: [
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 24, 20, 4),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Bienvenue, $username',
                      style: const TextStyle(
                        color: Color(0xFF4A9EE8),
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    const Text(
                      'Choisissez votre aventure',
                      style: TextStyle(color: Color(0xFF8AAEC8), fontSize: 14),
                    ),
                    const SizedBox(height: 20),
                    const Divider(color: Color(0xFF1A2130)),
                    const SizedBox(height: 12),
                  ],
                ),
              ),
            ),
            if (_loading)
              const SliverFillRemaining(
                child: Center(
                  child: CircularProgressIndicator(color: Color(0xFF4A9EE8)),
                ),
              )
            else if (_error != null)
              SliverFillRemaining(
                child: Center(
                  child: Padding(
                    padding: const EdgeInsets.all(32),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.wifi_off,
                            color: Color(0xFF2A6AAA), size: 56),
                        const SizedBox(height: 16),
                        Text(_error!,
                            style: const TextStyle(color: Color(0xFF8AAEC8)),
                            textAlign: TextAlign.center),
                        const SizedBox(height: 20),
                        ElevatedButton.icon(
                          onPressed: _loadStories,
                          icon: const Icon(Icons.refresh),
                          label: const Text('Réessayer'),
                        ),
                      ],
                    ),
                  ),
                ),
              )
            else if (_stories!.isEmpty)
              const SliverFillRemaining(
                child: Center(
                  child: Text('Aucune histoire disponible.',
                      style: TextStyle(color: Color(0xFF8AAEC8))),
                ),
              )
            else
              SliverPadding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                sliver: SliverList(
                  delegate: SliverChildBuilderDelegate(
                    (ctx, i) => _StoryCard(
                      story: _stories![i],
                      onPlay: () => _playStory(_stories![i]),
                    ),
                    childCount: _stories!.length,
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _StoryCard extends StatelessWidget {
  final Story story;
  final VoidCallback onPlay;

  const _StoryCard({required this.story, required this.onPlay});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: const Color(0xFF141920),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF1E3050)),
        boxShadow: [
          BoxShadow(
              color: Colors.black.withValues(alpha: 0.4),
              blurRadius: 8,
              offset: const Offset(0, 4)),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(16),
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: onPlay,
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(
                        color: const Color(0xFF4A9EE8).withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                            color: const Color(0xFF4A9EE8).withValues(alpha: 0.4)),
                      ),
                      child: const Icon(Icons.auto_stories,
                          color: Color(0xFF4A9EE8), size: 26),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Text(
                        story.title,
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                          height: 1.3,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                Text(
                  story.description,
                  style: const TextStyle(
                    color: Color(0xFFA8C4DC),
                    fontSize: 14,
                    height: 1.55,
                  ),
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 18),
                SizedBox(
                  width: double.infinity,
                  height: 48,
                  child: ElevatedButton.icon(
                    onPressed: onPlay,
                    icon: const Icon(Icons.play_arrow_rounded, size: 22),
                    label: const Text('Commencer / Continuer'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
