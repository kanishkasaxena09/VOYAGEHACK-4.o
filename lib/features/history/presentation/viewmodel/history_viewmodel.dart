import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../../data/models/chat_session_model.dart';

class HistoryNotifier extends StateNotifier<List<ChatSessionModel>> {
  static const _key = 'chat_history';
  late final Future<void> _ready;

  HistoryNotifier() : super([]) {
    _ready = _load();
  }

  Future<void> _load() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getStringList(_key) ?? [];
      final list = raw
          .map((e) =>
          ChatSessionModel.fromJson(jsonDecode(e) as Map<String, dynamic>))
          .toList()
        ..sort((a, b) => b.updatedAt.compareTo(a.updatedAt));
      state = list;
    } catch (_) {
      // Ignore corrupted data
    }
  }

  Future<void> _persist() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(
      _key,
      state.map((s) => jsonEncode(s.toJson())).toList(),
    );
  }

  Future<void> upsert(ChatSessionModel session) async {
    await _ready;
    final others = state.where((s) => s.id != session.id).toList();
    state = [session, ...others];
    await _persist();
  }

  Future<void> delete(String id) async {
    state = state.where((s) => s.id != id).toList();
    await _persist();
  }

  Future<void> clear() async {
    state = [];
    await _persist();
  }
}

final historyProvider =
StateNotifierProvider<HistoryNotifier, List<ChatSessionModel>>(
      (ref) => HistoryNotifier(),
);