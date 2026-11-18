
import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../data/models/trip_model.dart';

class BookingScreen extends StatelessWidget {
  final TripModel trip;
  const BookingScreen({super.key, required this.trip});

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: Text('Book ${trip.destination}'),
          bottom: const TabBar(
            indicatorColor: AppColors.primaryLight,
            labelColor: AppColors.primaryLight,
            unselectedLabelColor: AppColors.textMuted,
            tabs: [
              Tab(icon: Icon(Icons.flight_rounded), text: 'Flights'),
              Tab(icon: Icon(Icons.hotel_rounded), text: 'Hotels'),
            ],
          ),
        ),
        body: TabBarView(
          children: [_FlightsTab(trip: trip), _HotelsTab(trip: trip)],
        ),
      ),
    );
  }
}

// ---------------- Flights ----------------
class _FlightsTab extends StatelessWidget {
  final TripModel trip;
  const _FlightsTab({required this.trip});

  static const _flights = [
    ('IndiGo', '06:15', '08:40', '2h 25m', 5400),
    ('Air India', '11:30', '14:05', '2h 35m', 6900),
    ('Vistara', '18:45', '21:10', '2h 25m', 7600),
  ];

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _flights.length,
      itemBuilder: (context, i) {
        final f = _flights[i];
        return _BookingTile(
          icon: Icons.flight_takeoff_rounded,
          title: f.$1,
          subtitle: 'Delhi → ${trip.destination}',
          meta: '${f.$2} - ${f.$3}  •  ${f.$4}',
          price: f.$5,
          priceSuffix: '/ person',
          onBook: () => _confirm(
            context,
            '${f.$1} flight booked',
            'Delhi → ${trip.destination}  •  ${f.$2}',
          ),
        ).animate().fadeIn(delay: (100 * i).ms).slideY(begin: 0.1, end: 0);
      },
    );
  }
}

// ---------------- Hotels ----------------
class _HotelsTab extends StatelessWidget {
  final TripModel trip;
  const _HotelsTab({required this.trip});

  static const _hotels = [
    ('Seaside Resort & Spa', '4.8', 6500),
    ('Palm Grove Hotel', '4.5', 4200),
    ('Backpackers Hostel', '4.2', 1500),
  ];

  @override
  Widget build(BuildContext context) {
    final nights = trip.days > 1 ? trip.days - 1 : 1;

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _hotels.length,
      itemBuilder: (context, i) {
        final h = _hotels[i];
        final total = h.$3 * nights;
        return _BookingTile(
          icon: Icons.hotel_rounded,
          title: h.$1,
          subtitle: '${trip.destination}  •  ⭐ ${h.$2}',
          meta: '$nights nights  •  ₹${h.$3} / night',
          price: total,
          priceSuffix: 'total',
          onBook: () => _confirm(
            context,
            '${h.$1} booked',
            '$nights nights in ${trip.destination}',
          ),
        ).animate().fadeIn(delay: (100 * i).ms).slideY(begin: 0.1, end: 0);
      },
    );
  }
}

// ---------------- Shared tile ----------------
class _BookingTile extends StatelessWidget {
  final IconData icon;
  final String title, subtitle, meta, priceSuffix;
  final int price;
  final VoidCallback onBook;

  const _BookingTile({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.meta,
    required this.price,
    required this.priceSuffix,
    required this.onBook,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
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
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: AppColors.primary.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: AppColors.primaryLight),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title,
                        style: const TextStyle(
                            fontSize: 16, fontWeight: FontWeight.w700)),
                    const SizedBox(height: 2),
                    Text(subtitle,
                        style: const TextStyle(
                            color: AppColors.textSecondary, fontSize: 13)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(meta,
              style:
              const TextStyle(color: AppColors.textMuted, fontSize: 12)),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text('₹$price',
                      style: const TextStyle(
                          color: AppColors.accent,
                          fontSize: 20,
                          fontWeight: FontWeight.w800)),
                  const SizedBox(width: 4),
                  Text(priceSuffix,
                      style: const TextStyle(
                          color: AppColors.textMuted, fontSize: 12)),
                ],
              ),
              ElevatedButton(onPressed: onBook, child: const Text('Book')),
            ],
          ),
        ],
      ),
    );
  }
}

// ---------------- Confirmation sheet ----------------
void _confirm(BuildContext context, String title, String subtitle) {
  showModalBottomSheet(
    context: context,
    backgroundColor: AppColors.surface,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
    ),
    builder: (sheetContext) => Padding(
      padding: const EdgeInsets.fromLTRB(24, 28, 24, 32),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.success.withOpacity(0.15),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.check_rounded,
                color: AppColors.success, size: 44),
          ).animate().scale(
              begin: const Offset(0.3, 0.3),
              duration: 500.ms,
              curve: Curves.elasticOut),
          const SizedBox(height: 18),
          const Text('Booking Confirmed!',
              style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
          const SizedBox(height: 8),
          Text(title,
              style: const TextStyle(fontWeight: FontWeight.w600)),
          const SizedBox(height: 4),
          Text(subtitle,
              style: const TextStyle(color: AppColors.textSecondary)),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () => Navigator.pop(sheetContext),
              child: const Text('Done'),
            ),
          ),
        ],
      ),
    ),
  );
}