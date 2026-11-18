import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../../core/theme/app_colors.dart';
import '../../../../../data/models/trip_model.dart';
import '../../../../../shared/providers/providers.dart';
import '../../../booking/presentation/view/booking_screen.dart';
import '../widgets/budget_chart.dart';

class ItineraryScreen extends ConsumerWidget {
  final TripModel trip;
  const ItineraryScreen({super.key, required this.trip});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final saved = ref.watch(savedTripsProvider).contains(trip);

    return Scaffold(
      backgroundColor: AppColors.background,
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: saved ? AppColors.success : AppColors.primary,
        onPressed: () {
          if (!saved) {
            ref.read(savedTripsProvider.notifier).add(trip);
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Trip saved! ✅')),
            );
          }
        },
        icon: Icon(saved ? Icons.check_rounded : Icons.bookmark_add_rounded,
            color: Colors.white),
        label: Text(saved ? 'Saved' : 'Save Trip',
            style: const TextStyle(color: Colors.white)),
      ),
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            expandedHeight: 260,
            pinned: true,
            backgroundColor: AppColors.background,
            flexibleSpace: FlexibleSpaceBar(
              title: Text(trip.destination,
                  style: const TextStyle(fontWeight: FontWeight.w700)),
              background: Stack(
                fit: StackFit.expand,
                children: [
                  CachedNetworkImage(
                    imageUrl: trip.imageUrl,
                    fit: BoxFit.cover,
                    errorWidget: (_, __, ___) => Container(
                      decoration: const BoxDecoration(
                        gradient: LinearGradient(
                            colors: [AppColors.primary, AppColors.surfaceLight]),
                      ),
                    ),
                  ),
                  Container(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: [
                          Colors.transparent,
                          AppColors.background.withOpacity(0.95)
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(trip.summary,
                      style: const TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 15,
                          height: 1.5)),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      _Stat(Icons.calendar_month_rounded, '${trip.days}', 'Days'),
                      const SizedBox(width: 12),
                      _Stat(Icons.currency_rupee_rounded, '${trip.budget}',
                          'Budget',
                          color: AppColors.accent),
                    ],
                  ),

                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton.icon(
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppColors.primaryLight,
                        side: const BorderSide(color: AppColors.primary),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(14)),
                      ),
                      onPressed: () => Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => BookingScreen(trip: trip)),
                      ),
                      icon: const Icon(Icons.confirmation_number_rounded),
                      label: const Text('Book Flights & Hotels'),
                    ),
                  ),
                ],
              ),
            ),
          ),
          SliverToBoxAdapter(child: BudgetChart(trip: trip)),
          SliverList(
            delegate: SliverChildBuilderDelegate(
                  (context, i) => _DayCard(day: trip.itinerary[i])
                  .animate()
                  .fadeIn(delay: (120 * i).ms)
                  .slideY(begin: 0.1, end: 0),
              childCount: trip.itinerary.length,
            ),
          ),
          const SliverToBoxAdapter(child: SizedBox(height: 100)),
        ],
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  final IconData icon;
  final String value;
  final String label;
  final Color color;
  const _Stat(this.icon, this.value, this.label,
      {this.color = AppColors.primaryLight});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Row(
          children: [
            Icon(icon, color: color),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(value,
                    style: const TextStyle(
                        fontSize: 18, fontWeight: FontWeight.w700)),
                Text(label,
                    style: const TextStyle(
                        fontSize: 12, color: AppColors.textMuted)),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _DayCard extends StatelessWidget {
  final DayPlanModel day;
  const _DayCard({required this.day});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 6, 16, 10),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding:
                const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                      colors: [AppColors.primary, AppColors.primaryLight]),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text('Day ${day.day}',
                    style: const TextStyle(
                        fontWeight: FontWeight.w700, fontSize: 13)),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(day.title,
                    style: const TextStyle(
                        fontSize: 16, fontWeight: FontWeight.w600)),
              ),
            ],
          ),
          const SizedBox(height: 14),
          ...day.activities.map((a) => Container(
            margin: const EdgeInsets.only(left: 8, bottom: 4),
            padding: const EdgeInsets.only(left: 16, bottom: 14),
            decoration: BoxDecoration(
              border: Border(
                left: BorderSide(
                    color: AppColors.primary.withOpacity(0.5), width: 2),
              ),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(a.time,
                          style: const TextStyle(
                              color: AppColors.primaryLight,
                              fontSize: 12,
                              fontWeight: FontWeight.w600)),
                      const SizedBox(height: 2),
                      Text(a.title,
                          style: const TextStyle(
                              fontSize: 15, fontWeight: FontWeight.w600)),
                      const SizedBox(height: 2),
                      Text(a.description,
                          style: const TextStyle(
                              color: AppColors.textSecondary,
                              fontSize: 13)),
                    ],
                  ),
                ),
                Text(a.cost == 0 ? 'Free' : '₹${a.cost}',
                    style: const TextStyle(
                        color: AppColors.accent,
                        fontWeight: FontWeight.w600)),
              ],
            ),
          )),
        ],
      ),
    );
  }
}