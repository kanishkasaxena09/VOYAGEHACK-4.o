import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../shared/widgets/main_shell.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../onboarding/presentation/view/onboarding_screen.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    Future.delayed(const Duration(milliseconds: 2800), () async {
      final prefs = await SharedPreferences.getInstance();
      final done = prefs.getBool('onboarding_done') ?? false;
      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        PageRouteBuilder(
          transitionDuration: const Duration(milliseconds: 600),
          pageBuilder: (_, __, ___) =>
          done ? const MainShell() : const OnboardingScreen(),
          transitionsBuilder: (_, anim, __, child) =>
              FadeTransition(opacity: anim, child: child),
        ),
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        width: double.infinity,
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFF0B0F14), Color(0xFF0F2A2E)],
          ),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(26),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: const LinearGradient(
                    colors: [AppColors.primary, AppColors.primaryLight]),
                boxShadow: [
                  BoxShadow(
                    color: AppColors.primaryLight.withOpacity(0.45),
                    blurRadius: 40,
                    spreadRadius: 4,
                  ),
                ],
              ),
              child: const Icon(Icons.flight_takeoff_rounded,
                  size: 54, color: Colors.white),
            )
                .animate()
                .scale(
                begin: const Offset(0.4, 0.4),
                duration: 700.ms,
                curve: Curves.elasticOut)
                .fadeIn(duration: 400.ms),
            const SizedBox(height: 28),
            const Text(
              'Voyage AI',
              style: TextStyle(
                  fontSize: 34, fontWeight: FontWeight.w800, letterSpacing: 1),
            ).animate().fadeIn(delay: 500.ms).slideY(begin: 0.4, end: 0),
            const SizedBox(height: 8),
            const Text(
              'Your personal AI travel agent',
              style: TextStyle(color: AppColors.textSecondary, fontSize: 15),
            ).animate().fadeIn(delay: 900.ms),
            const SizedBox(height: 48),
            const SizedBox(
              width: 26,
              height: 26,
              child: CircularProgressIndicator(
                  strokeWidth: 2.5, color: AppColors.primaryLight),
            ).animate().fadeIn(delay: 1200.ms),
          ],
        ),
      ),
    );
  }
}