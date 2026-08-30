import 'package:flutter/foundation.dart';
import '../core/api_client.dart';
import '../core/constants.dart';

class AuthService extends ChangeNotifier {
  final _api = ApiClient();

  bool _isAuthenticated = false;
  String? _username;

  bool get isAuthenticated => _isAuthenticated;
  String? get username => _username;

  Future<void> init() async {
    final token = await _api.getAccessToken();
    if (token != null) {
      _isAuthenticated = true;
      _username = await _api.getUsername();
    }
  }

  Future<void> login(String username, String password) async {
    final res = await _api.post(
      '${AppConstants.authEndpoint}/login/',
      {'username': username, 'password': password},
    );
    final data = await _api.parseResponse(res) as Map<String, dynamic>;
    await _api.saveTokens(
      data['access'] as String,
      data['refresh'] as String,
      username,
    );
    _username = username;
    _isAuthenticated = true;
    notifyListeners();
  }

  Future<void> register(String username, String email, String password) async {
    final res = await _api.post(
      '${AppConstants.authEndpoint}/register/',
      {
        'username': username,
        'email': email,
        'password': password,
        'password2': password, // le serializer Django exige la confirmation
      },
    );
    await _api.parseResponse(res);
    await login(username, password);
  }

  Future<void> logout() async {
    await _api.clearSession();
    _isAuthenticated = false;
    _username = null;
    notifyListeners();
  }
}
