import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../../../data/models/profile_model.dart';

class ProfileNotifier extends StateNotifier<ProfileModel> {
  static const _key = 'user_profile';

  ProfileNotifier() : super(const ProfileModel()) {
    _load();
  }

  Future<void> _load() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(_key);
      if (raw != null) {
        state = ProfileModel.fromJson(jsonDecode(raw) as Map<String, dynamic>);
      }
    } catch (_) {
      // Ignore corrupted data
    }
  }

  Future<void> update(ProfileModel profile) async {
    state = profile;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_key, jsonEncode(profile.toJson()));
  }
}

final profileProvider =
StateNotifierProvider<ProfileNotifier, ProfileModel>(
      (ref) => ProfileNotifier(),
);