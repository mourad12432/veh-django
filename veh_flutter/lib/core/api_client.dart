import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiException implements Exception {
  final String message;
  final int statusCode;
  const ApiException(this.message, this.statusCode);
  @override
  String toString() => message;
}

class ApiClient {
  static const _kAccess   = 'access_token';
  static const _kRefresh  = 'refresh_token';
  static const _kUsername = 'username';

  final _http = http.Client();

  Future<String?> getAccessToken() async =>
      (await SharedPreferences.getInstance()).getString(_kAccess);

  Future<String?> getUsername() async =>
      (await SharedPreferences.getInstance()).getString(_kUsername);

  Future<void> saveTokens(String access, String refresh, String username) async {
    final p = await SharedPreferences.getInstance();
    await p.setString(_kAccess, access);
    await p.setString(_kRefresh, refresh);
    await p.setString(_kUsername, username);
  }

  Future<void> clearSession() async {
    final p = await SharedPreferences.getInstance();
    await p.remove(_kAccess);
    await p.remove(_kRefresh);
    await p.remove(_kUsername);
  }

  Future<Map<String, String>> _headers() async {
    final token = await getAccessToken();
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  Future<http.Response> get(String url) async =>
      _http.get(Uri.parse(url), headers: await _headers());

  Future<http.Response> post(String url, Map<String, dynamic> body) async =>
      _http.post(Uri.parse(url),
          headers: await _headers(), body: jsonEncode(body));

  Future<dynamic> parseResponse(http.Response response) async {
    final decoded = jsonDecode(utf8.decode(response.bodyBytes));
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return decoded;
    }
    String message;
    if (decoded is Map) {
      message = decoded['detail']?.toString() ??
                decoded['error']?.toString() ??
                decoded['message']?.toString() ??
                'Erreur ${response.statusCode}';
    } else {
      message = 'Erreur ${response.statusCode}';
    }
    throw ApiException(message, response.statusCode);
  }
}
