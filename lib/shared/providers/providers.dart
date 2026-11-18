import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../core/network/dio_client.dart';
import '../../data/models/trip_model.dart';
import '../../data/repositories/chat_repository.dart';

final dioProvider = Provider((ref) => createDio());

final chatRepositoryProvider =
Provider((ref) => ChatRepository(ref.read(dioProvider)));

// Current bottom navigation tab
final navIndexProvider = StateProvider<int>((ref) => 0);

// Saved trips (persisted on device)
class SavedTripsNotifier extends StateNotifier<List<TripModel>> {
  static const _key = 'saved_trips';

  SavedTripsNotifier() : super([]) {
    _load();
  }

  Future<void> _load() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getStringList(_key) ?? [];
      state = raw
          .map((e) => TripModel.fromJson(jsonDecode(e) as Map<String, dynamic>))
          .toList();
    } catch (_) {
      // Ignore corrupted data
    }
  }

  Future<void> _persist() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList(
      _key,
      state.map((t) => jsonEncode(t.toJson())).toList(),
    );
  }

  Future<void> add(TripModel trip) async {
    if (state.contains(trip)) return;
    state = [...state, trip];
    await _persist();
  }

  Future<void> remove(TripModel trip) async {
    state = state.where((t) => t != trip).toList();
    await _persist();
  }

  Future<void> clear() async {
    state = [];
    await _persist();
  }
}

final savedTripsProvider =
StateNotifierProvider<SavedTripsNotifier, List<TripModel>>(
      (ref) => SavedTripsNotifier(),
);