import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';

Future<bool> showConfirmDialog(
    BuildContext context, {
      required String title,
      required String message,
      String confirmText = 'Delete',
    }) async {
  final result = await showDialog<bool>(
    context: context,
    builder: (ctx) => AlertDialog(
      backgroundColor: AppColors.surface,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      title: Text(title, style: const TextStyle(fontWeight: FontWeight.w700)),
      content: Text(message,
          style: const TextStyle(color: AppColors.textSecondary)),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(ctx, false),
          child: const Text('Cancel'),
        ),
        TextButton(
          onPressed: () => Navigator.pop(ctx, true),
          child: Text(confirmText,
              style: const TextStyle(color: AppColors.error)),
        ),
      ],
    ),
  );
  return result ?? false;
}