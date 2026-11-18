import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_colors.dart';
import '../viewmodel/chat_viewmodel.dart';
import '../widgets/message_bubble.dart';
import '../widgets/chat_input_bar.dart';
import '../widgets/suggestion_chips.dart';
import '../widgets/typing_indicator.dart';

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _send(String text) {
    ref.read(chatViewModelProvider.notifier).sendMessage(text);
    _controller.clear();
  }

  @override
  Widget build(BuildContext context) {
    final chat = ref.watch(chatViewModelProvider);
    ref.listen(chatViewModelProvider, (_, __) => _scrollToBottom());

    final itemCount = chat.messages.length + (chat.isTyping ? 1 : 0);

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                    colors: [AppColors.primary, AppColors.primaryLight]),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.flight_takeoff_rounded,
                  size: 18, color: Colors.white),
            ),
            const SizedBox(width: 12),
            const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text("Voyage AI",
                    style: TextStyle(fontWeight: FontWeight.w600)),
                Text("Online • Your personal travel agent",
                    style: TextStyle(
                        fontSize: 11, color: AppColors.textSecondary)),
              ],
            ),
          ],
        ),

        actions: [
          IconButton(
            tooltip: 'New chat',
            onPressed: () =>
                ref.read(chatViewModelProvider.notifier).newChat(),
            icon: const Icon(Icons.add_comment_rounded),
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              itemCount: itemCount,
              itemBuilder: (context, index) {
                if (index == chat.messages.length) {
                  return const TypingIndicator();
                }
                return MessageBubble(message: chat.messages[index]);
              },
            ),
          ),
          SuggestionChips(onSelected: _send),
          ChatInputBar(
            controller: _controller,
            onSend: () => _send(_controller.text),
          ),
        ],
      ),
    );
  }
}