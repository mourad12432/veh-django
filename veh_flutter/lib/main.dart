import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import 'services/auth_service.dart';
import 'screens/splash_screen.dart';
import 'screens/login_screen.dart';
import 'screens/register_screen.dart';
import 'screens/home_screen.dart';
import 'screens/game_screen.dart';
import 'screens/ending_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final auth = AuthService();
  await auth.init();
  runApp(
    ChangeNotifierProvider.value(value: auth, child: const VehApp()),
  );
}

class VehApp extends StatelessWidget {
  const VehApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Vous Êtes le Héros',
      debugShowCheckedModeBanner: false,
      theme: _theme(),
      initialRoute: '/',
      routes: {
        '/':        (ctx) => const SplashScreen(),
        '/login':   (ctx) => const LoginScreen(),
        '/register':(ctx) => const RegisterScreen(),
        '/home':    (ctx) => const HomeScreen(),
      },
      onGenerateRoute: (settings) {
        if (settings.name == '/game') {
          final args = settings.arguments as Map<String, dynamic>;
          return MaterialPageRoute(
            builder: (ctx) => GameScreen(
              storySlug:  args['storySlug']  as String,
              storyTitle: args['storyTitle'] as String,
              sceneKey:   args['sceneKey']   as String? ?? 'auto',
            ),
          );
        }
        if (settings.name == '/ending') {
          final args = settings.arguments as Map<String, dynamic>;
          return MaterialPageRoute(
            builder: (ctx) => EndingScreen(
              storySlug:  args['storySlug']  as String,
              storyTitle: args['storyTitle'] as String,
              endingType: args['endingType'] as String?,
              narrative:  args['narrative']  as String,
            ),
          );
        }
        return null;
      },
    );
  }

  // ── Charte « NovaPay » — mêmes jetons que le web (templates/base.html) ──
  static const _bg    = Color(0xFF0F1319);  // fond
  static const _bg2   = Color(0xFF141920);  // surface
  static const _sky   = Color(0xFF4A9EE8);  // accent
  static const _text  = Color(0xFFE4EEF8);  // texte principal
  static const _text2 = Color(0xFF8AAEC8);  // texte secondaire
  static const _text3 = Color(0xFF506070);  // texte tertiaire / icônes
  static const _line  = Color(0xFF1E3050);  // bordures

  ThemeData _theme() {
    // DM Sans pour l'interface, Outfit pour les titres — comme sur le web.
    final base = ThemeData(useMaterial3: true, brightness: Brightness.dark);
    final textTheme = GoogleFonts.dmSansTextTheme(base.textTheme)
        .apply(bodyColor: _text, displayColor: _text)
        .copyWith(
          displayLarge:  GoogleFonts.outfit(fontWeight: FontWeight.w800, letterSpacing: -1.2, color: _text),
          displayMedium: GoogleFonts.outfit(fontWeight: FontWeight.w800, letterSpacing: -1.0, color: _text),
          displaySmall:  GoogleFonts.outfit(fontWeight: FontWeight.w700, letterSpacing: -0.8, color: _text),
          headlineLarge: GoogleFonts.outfit(fontWeight: FontWeight.w700, letterSpacing: -0.8, color: _text),
          headlineMedium:GoogleFonts.outfit(fontWeight: FontWeight.w700, letterSpacing: -0.6, color: _text),
          headlineSmall: GoogleFonts.outfit(fontWeight: FontWeight.w700, letterSpacing: -0.5, color: _text),
          titleLarge:    GoogleFonts.outfit(fontWeight: FontWeight.w600, letterSpacing: -0.4, color: _text),
          titleMedium:   GoogleFonts.outfit(fontWeight: FontWeight.w600, letterSpacing: -0.2, color: _text),
        );

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: _bg,
      textTheme: textTheme,
      colorScheme: const ColorScheme.dark(
        primary:   _sky,
        secondary: Color(0xFFE85A5A),
        surface:   _bg2,
        onPrimary: Colors.white,
        onSurface: _text,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: _bg,
        foregroundColor: _sky,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: GoogleFonts.outfit(
          fontSize: 18, fontWeight: FontWeight.w600,
          letterSpacing: -0.4, color: _sky,
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color(0xFF2A6AAA),
          foregroundColor: Colors.white,
          elevation: 0,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          // 12 px : le contenu doit tenir dans les boutons à hauteur fixe (44–50 px)
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
          textStyle: GoogleFonts.outfit(fontSize: 15, fontWeight: FontWeight.w600),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: _bg,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: _line),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: _line),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFF2A6AAA), width: 2),
        ),
        labelStyle: TextStyle(color: _text2),
        hintStyle:  TextStyle(color: _text3),
        prefixIconColor: _text3,
        suffixIconColor: _text3,
      ),
    );
  }
}
