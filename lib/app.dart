import 'package:flutter/material.dart';
import 'package:voyage_app/features/splash/presentation/view/splash_screen.dart';
import 'core/theme/app_theme.dart';

class VoyageApp extends StatelessWidget {
  const VoyageApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Voyage AI',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      home: const SplashScreen(),
    );
  }
}