import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/utils/time_utils.dart';
import '../../../../data/models/chat_session_model.dart';
import '../../../../shared/providers/providers.dart';
import '../../../../shared/widgets/confirm_dialog.dart';
import '../../../chat/presentation/viewmodel/chat_viewmodel.dart';
import '../viewmodel/history_viewmodel.dart';

class HistoryScreen extends ConsumerStatefulWidget {
  const HistoryScreen({super.key});

  @override
  ConsumerState<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends ConsumerState<HistoryScreen> {
  String _query = '';

  void _open(ChatSessionModel session) {
    final ok = ref.read(chatViewModelProvider.notifier).loadSession(session);
    if (ok) {
      ref.read(navIndexProvider.notifier).state = 1; // AI Agent tab
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please wait for the AI to finish')),
      );
    }
  }

  Future<void> _clearAll() async {
    final ok = await showConfirmDialog(
      context,
      title: 'Clear all history?',
      message: 'All your past chats will be removed from this device.',
      confirmText: 'Clear all',
    );
    if (ok) ref.read(historyProvider.notifier).clear();
  }

  @override
  Widget build(BuildContext context) {
    final all = ref.watch(historyProvider);
    final q = _query.trim().toLowerCase();
    final sessions = q.isEmpty
        ? all
        : all
        .where((s) =>
    s.title.toLowerCase().contains(q) ||
        s.destinations.any((d) => d.toLowerCase().contains(q)))
        .toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('History'),
        actions: [
          if (all.isNotEmpty)
            IconButton(
              tooltip: 'Clear all',
              onPressed: _clearAll,
              icon: const Icon(Icons.delete_sweep_rounded),
            ),
        ],
      ),
      body: all.isEmpty
          ? const _EmptyState()
          : Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
            child: TextField(
              onChanged: (v) => setState(() => _query = v),
              decoration: const InputDecoration(
                hintText: 'Search chats or destinations...',
                prefixIcon: Icon(Icons.search_rounded,
                    color: AppColors.textMuted),
              ),
            ),
          ),
          Expanded(
            child: sessions.isEmpty
                ? const Center(
              child: Text('No matching chats',
                  style:
                  TextStyle(color: AppColors.textSecondary)),
            )
                : ListView.builder(
              padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
              itemCount: sessions.length,
              itemBuilder: (_, i) {
                final s = sessions[i];
                return Dismissible(
                  key: ValueKey(s.id),
                  direction: DismissDirection.endToStart,
                  background: Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: const EdgeInsets.only(right: 24),
                    alignment: Alignment.centerRight,
                    decoration: BoxDecoration(
                      color: AppColors.error.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(18),
                    ),
                    child: const Icon(Icons.delete_rounded,
                        color: AppColors.error),
                  ),
                  onDismissed: (_) => ref
                      .read(historyProvider.notifier)
                      .delete(s.id),
                  child: _SessionTile(
                    session: s,
                    onTap: () => _open(s),
                  ),
                ).animate().fadeIn(delay: (50 * i).ms);
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _SessionTile extends StatelessWidget {
  final ChatSessionModel session;
  final VoidCallback onTap;
  const _SessionTile({required this.session, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final dests = session.destinations;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      child: Material(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(18),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: AppColors.primary.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(Icons.chat_bubble_rounded,
                      color: AppColors.primaryLight, size: 20),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(session.title,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                              fontSize: 15, fontWeight: FontWeight.w700)),
                      const SizedBox(height: 3),
                      Text(session.preview,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                              color: AppColors.textSecondary, fontSize: 13)),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 6,
                        runSpacing: 6,
                        crossAxisAlignment: WrapCrossAlignment.center,
                        children: [
                          Text(timeAgo(session.updatedAt),
                              style: const TextStyle(
                                  color: AppColors.textMuted, fontSize: 11)),
                          ...dests.map((d) => Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: AppColors.accent.withOpacity(0.12),
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const Icon(Icons.place_rounded,
                                    size: 11, color: AppColors.accent),
                                const SizedBox(width: 3),
                                Text(d,
                                    style: const TextStyle(
                                        color: AppColors.accent,
                                        fontSize: 11,
                                        fontWeight: FontWeight.w600)),
                              ],
                            ),
                          )),
                        ],
                      ),
                    ],
                  ),
                ),
                const Icon(Icons.chevron_right_rounded,
                    color: AppColors.textMuted),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.history_rounded, size: 64, color: AppColors.textMuted),
          SizedBox(height: 12),
          Text('No chat history yet',
              style: TextStyle(color: AppColors.textSecondary)),
          SizedBox(height: 4),
          Text('Your conversations with the AI agent will appear here',
              style: TextStyle(color: AppColors.textMuted, fontSize: 12)),
        ],
      ),
    );
  }
}