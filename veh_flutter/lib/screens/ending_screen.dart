import 'package:flutter/material.dart';

class EndingScreen extends StatelessWidget {
  final String storySlug;
  final String storyTitle;
  final String? endingType;
  final String narrative;

  const EndingScreen({
    super.key,
    required this.storySlug,
    required this.storyTitle,
    required this.endingType,
    required this.narrative,
  });

  Color get _color {
    switch (endingType) {
      case 'good':    return const Color(0xFF2E9E6C);
      case 'bad':     return const Color(0xFFA83A3A);
      default:        return const Color(0xFF9C8038);
    }
  }

  IconData get _icon {
    switch (endingType) {
      case 'good':  return Icons.military_tech;
      case 'bad':   return Icons.sentiment_very_dissatisfied;
      default:      return Icons.hourglass_bottom;
    }
  }

  String get _label {
    switch (endingType) {
      case 'good':  return 'BONNE FIN';
      case 'bad':   return 'MAUVAISE FIN';
      default:      return 'FIN NEUTRE';
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = _color;

    return Scaffold(
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              color.withValues(alpha: 0.25),
              const Color(0xFF0F1319),
              const Color(0xFF0F1319),
            ],
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              // ── Header ──────────────────────────────────────────
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 28, 20, 0),
                child: Column(
                  children: [
                    Container(
                      width: 80,
                      height: 80,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: color.withValues(alpha: 0.15),
                        border: Border.all(color: color.withValues(alpha: 0.6), width: 2),
                      ),
                      child: Icon(_icon, size: 40, color: color),
                    ),
                    const SizedBox(height: 16),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 20, vertical: 7),
                      decoration: BoxDecoration(
                        color: color.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: color.withValues(alpha: 0.7)),
                      ),
                      child: Text(
                        _label,
                        style: TextStyle(
                          color: color,
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                          letterSpacing: 2.5,
                        ),
                      ),
                    ),
                    const SizedBox(height: 10),
                    Text(
                      storyTitle,
                      style: const TextStyle(
                          color: Color(0xFF8AAEC8), fontSize: 13),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 20),
                    Container(
                      height: 1,
                      decoration: BoxDecoration(
                        gradient: LinearGradient(colors: [
                          Colors.transparent,
                          color.withValues(alpha: 0.5),
                          Colors.transparent,
                        ]),
                      ),
                    ),
                  ],
                ),
              ),

              // ── Narrative ────────────────────────────────────────
              Expanded(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 24, vertical: 24),
                  child: Text(
                    narrative,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 17,
                      height: 1.85,
                      letterSpacing: 0.2,
                    ),
                    textAlign: TextAlign.justify,
                  ),
                ),
              ),

              // ── Actions ──────────────────────────────────────────
              Container(
                padding: const EdgeInsets.fromLTRB(20, 12, 20, 32),
                decoration: const BoxDecoration(
                  border: Border(top: BorderSide(color: Color(0xFF1A2130))),
                ),
                child: Column(
                  children: [
                    SizedBox(
                      width: double.infinity,
                      height: 50,
                      child: ElevatedButton.icon(
                        onPressed: () =>
                            Navigator.pushReplacementNamed(context, '/game',
                                arguments: {
                              'storySlug': storySlug,
                              'storyTitle': storyTitle,
                              'sceneKey': 'auto',
                            }),
                        icon: const Icon(Icons.replay_rounded),
                        label: const Text('Rejouer l\'aventure',
                            style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold)),
                      ),
                    ),
                    const SizedBox(height: 10),
                    SizedBox(
                      width: double.infinity,
                      height: 46,
                      child: OutlinedButton.icon(
                        onPressed: () =>
                            Navigator.pushReplacementNamed(context, '/home'),
                        icon: const Icon(Icons.home_outlined,
                            color: Color(0xFF8AAEC8), size: 20),
                        label: const Text('Choisir une autre histoire',
                            style: TextStyle(color: Color(0xFF8AAEC8))),
                        style: OutlinedButton.styleFrom(
                          side:
                              const BorderSide(color: Color(0xFF1E3050)),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
