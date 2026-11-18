import 'package:flutter/material.dart';
import '../../../../core/theme/app_colors.dart';

class SuggestionChips extends StatelessWidget {
  final Function(String) onSelected;

  const SuggestionChips({super.key, required this.onSelected});

  final List<String> suggestions = const [
    "Goa for 5 days",
    "Budget under ₹40,000",
    "Honeymoon trip",
    "Family trip with kids",
    "Beach + Food",
    "Adventure trip",
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 50,
      margin: const EdgeInsets.only(bottom: 8),
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: suggestions.length,
        separatorBuilder: (_, __) => const SizedBox(width: 10),
        itemBuilder: (context, index) {
          return GestureDetector(
            onTap: () => onSelected(suggestions[index]),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: AppColors.primary.withOpacity(0.4)),
              ),
              child: Text(
                suggestions[index],
                style: const TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}