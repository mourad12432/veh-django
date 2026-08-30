class AppConstants {
  // Émulateur Android  → 10.0.2.2  (= localhost de la machine hôte)
  // Simulateur iPhone  → localhost
  // Vrai appareil      → IP locale de ton PC (ex: 192.168.1.X)
  static const String baseUrl = 'http://10.0.2.2:8000';

  static const String authEndpoint    = '$baseUrl/api/auth';
  static const String storiesEndpoint = '$baseUrl/api/stories';
  static const String playEndpoint    = '$baseUrl/api/play';
  static const String sessionsEndpoint = '$baseUrl/api/sessions';
}
