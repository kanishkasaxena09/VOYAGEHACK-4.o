import 'dart:math' as math;
import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../data/models/trip_model.dart';

class BudgetChart extends StatelessWidget {
  final TripModel trip;
  const BudgetChart({super.key, required this.trip});

  static const _palette = [
    AppColors.primaryLight,
    AppColors.accent,
    Color(0xFF8B5CF6),
    Color(0xFFEC4899),
    Color(0xFF3B82F6),
    Color(0xFF22C55E),
    Color(0xFFF97316),
  ];

  @override
  Widget build(BuildContext context) {
    final dayTotals = trip.itinerary
        .map((d) => d.activities.fold<int>(0, (sum, a) => sum + a.cost))
        .toList();
    final planned = dayTotals.fold<int>(0, (a, b) => a + b);
    final remaining = trip.budget - planned;

    if (planned == 0) return const SizedBox.shrink();

    return Container(
      margin: const EdgeInsets.fromLTRB(16, 6, 16, 10),
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Budget Breakdown',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
          const SizedBox(height: 16),
          Row(
            children: [
              SizedBox(
                width: 130,
                height: 130,
                child: TweenAnimationBuilder<double>(
                  tween: Tween(begin: 0, end: 1),
                  duration: const Duration(milliseconds: 1200),
                  curve: Curves.easeOutCubic,
                  builder: (context, progress, _) => CustomPaint(
                    painter: _DonutPainter(
                      values: dayTotals.map((e) => e.toDouble()).toList(),
                      colors: List.generate(dayTotals.length,
                              (i) => _palette[i % _palette.length]),
                      progress: progress,
                    ),
                    child: Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Text('Planned',
                              style: TextStyle(
                                  fontSize: 11, color: AppColors.textMuted)),
                          Text('₹$planned',
                              style: const TextStyle(
                                  fontSize: 16, fontWeight: FontWeight.w800)),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 20),
              Expanded(
                child: Column(
                  children: List.generate(dayTotals.length, (i) {
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 4),
                      child: Row(
                        children: [
                          Container(
                            width: 10,
                            height: 10,
                            decoration: BoxDecoration(
                              color: _palette[i % _palette.length],
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text('Day ${trip.itinerary[i].day}',
                              style: const TextStyle(
                                  color: AppColors.textSecondary,
                                  fontSize: 13)),
                          const Spacer(),
                          Text('₹${dayTotals[i]}',
                              style: const TextStyle(
                                  fontWeight: FontWeight.w600, fontSize: 13)),
                        ],
                      ),
                    );
                  }),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: (remaining >= 0 ? AppColors.success : AppColors.error)
                  .withOpacity(0.12),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                Icon(
                  remaining >= 0
                      ? Icons.savings_rounded
                      : Icons.warning_amber_rounded,
                  size: 18,
                  color: remaining >= 0 ? AppColors.success : AppColors.error,
                ),
                const SizedBox(width: 8),
                Text(
                  remaining >= 0
                      ? '₹$remaining left in your budget'
                      : '₹${remaining.abs()} over budget',
                  style: TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color:
                    remaining >= 0 ? AppColors.success : AppColors.error,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _DonutPainter extends CustomPainter {
  final List<double> values;
  final List<Color> colors;
  final double progress;

  _DonutPainter({
    required this.values,
    required this.colors,
    required this.progress,
  });

  @override
  void paint(Canvas canvas, Size size) {
    const stroke = 16.0;
    final rect = Rect.fromLTWH(stroke / 2, stroke / 2, size.width - stroke,
        size.height - stroke);
    final total = values.fold<double>(0, (a, b) => a + b);
    if (total == 0) return;

    final paint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = stroke
      ..strokeCap = StrokeCap.butt;

    double start = -math.pi / 2;
    const gap = 0.04;
    for (var i = 0; i < values.length; i++) {
      final sweep = (values[i] / total) * 2 * math.pi * progress;
      paint.color = colors[i];
      canvas.drawArc(rect, start, math.max(sweep - gap, 0.01), false, paint);
      start += sweep;
    }
  }

  @override
  bool shouldRepaint(covariant _DonutPainter old) => old.progress != progress;
}