import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../shared/providers/providers.dart';
import '../../../itinerary/presentation/view/itinerary_screen.dart';

class TripsScreen extends ConsumerWidget {
  const TripsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final trips = ref.watch(savedTripsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('My Trips')),
      body: trips.isEmpty
          ? const Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.luggage_rounded,
                size: 64, color: AppColors.textMuted),
            SizedBox(height: 12),
            Text('No saved trips yet',
                style: TextStyle(color: AppColors.textSecondary)),
            SizedBox(height: 4),
            Text('Plan a trip with the AI agent and save it here',
                style: TextStyle(
                    color: AppColors.textMuted, fontSize: 12)),
          ],
        ),
      )
          : ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: trips.length,
        itemBuilder: (_, i) {
          final t = trips[i];
          return Dismissible(
            key: ValueKey('${t.destination}-${t.days}-${t.budget}'),
            direction: DismissDirection.endToStart,
            background: Container(
              margin: const EdgeInsets.only(bottom: 12),
              padding: const EdgeInsets.only(right: 24),
              alignment: Alignment.centerRight,
              decoration: BoxDecoration(
                color: AppColors.error.withOpacity(0.2),
                borderRadius: BorderRadius.circular(16),
              ),
              child: const Icon(Icons.delete_rounded,
                  color: AppColors.error),
            ),
            onDismissed: (_) =>
                ref.read(savedTripsProvider.notifier).remove(t),
            child: Card(
              color: AppColors.surface,
              margin: const EdgeInsets.only(bottom: 12),
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(16)),
              child: ListTile(
                contentPadding: const EdgeInsets.all(16),
                title: Text(t.destination,
                    style:
                    const TextStyle(fontWeight: FontWeight.w700)),
                subtitle: Text('${t.days} days • ₹${t.budget}'),
                trailing: const Icon(Icons.chevron_right_rounded),
                onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                      builder: (_) => ItineraryScreen(trip: t)),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}