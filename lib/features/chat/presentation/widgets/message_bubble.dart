import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../data/models/message_model.dart';
import 'trip_card.dart';

class MessageBubble extends StatelessWidget {
  final MessageModel message;
  const MessageBubble({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    final isUser = message.sender == MessageSender.user;

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Column(
        crossAxisAlignment:
        isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          Container(
            margin: const EdgeInsets.symmetric(vertical: 6),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            constraints: BoxConstraints(
              maxWidth: MediaQuery.of(context).size.width * 0.78,
            ),
            decoration: BoxDecoration(
              gradient: isUser
                  ? const LinearGradient(
                  colors: [AppColors.primary, AppColors.primaryLight])
                  : null,
              color: isUser ? null : AppColors.aiBubble,
              borderRadius: BorderRadius.only(
                topLeft: const Radius.circular(18),
                topRight: const Radius.circular(18),
                bottomLeft:
                isUser ? const Radius.circular(18) : const Radius.circular(4),
                bottomRight:
                isUser ? const Radius.circular(4) : const Radius.circular(18),
              ),
            ),
            child: Text(
              message.text,
              style: const TextStyle(
                  color: AppColors.textPrimary, fontSize: 15, height: 1.4),
            ),
          ),
          if (message.trip != null) TripCard(trip: message.trip!),
        ],
      ),
    )
        .animate()
        .fadeIn(duration: 300.ms)
        .slideY(begin: 0.15, end: 0, curve: Curves.easeOut);
  }
}