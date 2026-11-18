import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../../core/theme/app_colors.dart';
import '../../../../../shared/providers/providers.dart';
import '../../../chat/presentation/viewmodel/chat_viewmodel.dart';
import '../../../profile/presentation/viewmodel/profile_viewmodel.dart';

class _Dest {
  final String name, tagline, image;
  const _Dest(this.name, this.tagline, this.image);
}

const _destinations = [
  _Dest('Goa', 'Beaches & Nightlife',
      'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=600'),
  _Dest('Manali', 'Snow & Adventure',
      'https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=600'),
  _Dest('Jaipur', 'Royal Heritage',
      'https://images.unsplash.com/photo-1477587458883-47145ed94245?w=600'),
  _Dest('Kerala', 'Backwaters & Calm',
      'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=600'),
];

const _categories = [
  (Icons.beach_access_rounded, 'Beach'),
  (Icons.terrain_rounded, 'Mountains'),
  (Icons.favorite_rounded, 'Honeymoon'),
  (Icons.family_restroom_rounded, 'Family'),
  (Icons.hiking_rounded, 'Adventure'),
];

const _pickPrices = [22000, 18000, 15000, 25000];
const _pickDays = [4, 5, 3, 5];

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  void _plan(WidgetRef ref, String prompt) {
    ref.read(navIndexProvider.notifier).state = 1; // Chat tab
    ref.read(chatViewModelProvider.notifier).sendMessage(prompt);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Text('Hello, ${ref.watch(profileProvider).name} 👋',
                style: const TextStyle(color: AppColors.textSecondary, fontSize: 15)),
            const SizedBox(height: 4),
            const Text('Where do you want\nto go next?',
                style: TextStyle(
                    fontSize: 30, fontWeight: FontWeight.w800, height: 1.2))
                .animate()
                .fadeIn()
                .slideX(begin: -0.1, end: 0),
            const SizedBox(height: 20),

            // Search bar -> chat
            GestureDetector(
              onTap: () => ref.read(navIndexProvider.notifier).state = 1,
              child: Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.surface,
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(color: AppColors.primary.withOpacity(0.3)),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.auto_awesome_rounded,
                        color: AppColors.primaryLight),
                    SizedBox(width: 12),
                    Expanded(
                      child: Text('Ask AI to plan your trip...',
                          style: TextStyle(color: AppColors.textMuted)),
                    ),
                    Icon(Icons.mic_rounded, color: AppColors.textMuted),
                  ],
                ),
              ),
            ),

            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [AppColors.primary, Color(0xFF0F766E)],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(24),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Plan a trip in 30 seconds',
                            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
                        const SizedBox(height: 6),
                        const Text(
                          'Tell our AI your budget and mood. Get a full itinerary instantly.',
                          style: TextStyle(fontSize: 13, color: Colors.white70, height: 1.4),
                        ),
                        const SizedBox(height: 14),
                        ElevatedButton(
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.white,
                            foregroundColor: AppColors.primary,
                            padding:
                            const EdgeInsets.symmetric(horizontal: 18, vertical: 10),
                          ),
                          onPressed: () => ref.read(navIndexProvider.notifier).state = 1,
                          child: const Text('Start Planning',
                              style: TextStyle(fontWeight: FontWeight.w700)),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 12),
                  const Icon(Icons.auto_awesome_rounded, size: 64, color: Colors.white24),
                ],
              ),
            ).animate().fadeIn(delay: 200.ms).slideY(begin: 0.15, end: 0),

            const SizedBox(height: 24),
            SizedBox(
              height: 90,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: _categories.length,
                separatorBuilder: (_, __) => const SizedBox(width: 14),
                itemBuilder: (_, i) {
                  final c = _categories[i];
                  return GestureDetector(
                    onTap: () => _plan(ref, 'Plan a ${c.$2} trip for me'),
                    child: Column(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: AppColors.surfaceLight,
                            borderRadius: BorderRadius.circular(18),
                          ),
                          child: Icon(c.$1, color: AppColors.accent),
                        ),
                        const SizedBox(height: 6),
                        Text(c.$2, style: const TextStyle(fontSize: 12)),
                      ],
                    ),
                  );
                },
              ),
            ),

            const SizedBox(height: 16),
            const Text('Popular Destinations',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            const SizedBox(height: 14),
            SizedBox(
              height: 260,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: _destinations.length,
                separatorBuilder: (_, __) => const SizedBox(width: 14),
                itemBuilder: (_, i) {
                  final d = _destinations[i];
                  return GestureDetector(
                    onTap: () => _plan(ref, 'Plan a 3 day trip to ${d.name}'),
                    child: Container(
                      width: 190,
                      decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(24)),
                      clipBehavior: Clip.antiAlias,
                      child: Stack(
                        fit: StackFit.expand,
                        children: [
                          CachedNetworkImage(
                            imageUrl: d.image,
                            fit: BoxFit.cover,
                            errorWidget: (_, __, ___) => Container(
                                color: AppColors.surfaceLight),
                          ),
                          Container(
                            decoration: BoxDecoration(
                              gradient: LinearGradient(
                                begin: Alignment.topCenter,
                                end: Alignment.bottomCenter,
                                colors: [
                                  Colors.transparent,
                                  Colors.black.withOpacity(0.8)
                                ],
                              ),
                            ),
                          ),
                          Positioned(
                            left: 16,
                            bottom: 16,
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(d.name,
                                    style: const TextStyle(
                                        fontSize: 22,
                                        fontWeight: FontWeight.w800,
                                        color: Colors.white)),
                                Text(d.tagline,
                                    style: const TextStyle(
                                        fontSize: 12, color: Colors.white70)),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ).animate().fadeIn(delay: (100 * i).ms).slideX(begin: 0.2);
                },
              ),
            ),

            const SizedBox(height: 24),
            const Text('Top Picks For You',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            const SizedBox(height: 14),
            ...List.generate(_destinations.length, (i) {
              final d = _destinations[i];
              return GestureDetector(
                onTap: () => _plan(ref,
                    'Plan a ${_pickDays[i]} day trip to ${d.name} under ₹${_pickPrices[i]}'),
                child: Container(
                  margin: const EdgeInsets.only(bottom: 12),
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: AppColors.surface,
                    borderRadius: BorderRadius.circular(18),
                  ),
                  child: Row(
                    children: [
                      ClipRRect(
                        borderRadius: BorderRadius.circular(14),
                        child: SizedBox(
                          width: 80,
                          height: 80,
                          child: CachedNetworkImage(
                            imageUrl: d.image,
                            fit: BoxFit.cover,
                            errorWidget: (_, __, ___) =>
                                Container(color: AppColors.surfaceLight),
                          ),
                        ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(d.name,
                                style: const TextStyle(
                                    fontSize: 16, fontWeight: FontWeight.w700)),
                            const SizedBox(height: 2),
                            Text('${_pickDays[i]} days • ${d.tagline}',
                                style: const TextStyle(
                                    color: AppColors.textSecondary, fontSize: 12)),
                            const SizedBox(height: 6),
                            Text('From ₹${_pickPrices[i]}',
                                style: const TextStyle(
                                    color: AppColors.accent,
                                    fontWeight: FontWeight.w700)),
                          ],
                        ),
                      ),
                      const Icon(Icons.arrow_forward_ios_rounded,
                          size: 16, color: AppColors.textMuted),
                    ],
                  ),
                ).animate().fadeIn(delay: (80 * i).ms),
              );
            }),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }
}