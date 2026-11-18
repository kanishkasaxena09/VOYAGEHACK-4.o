import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../data/models/profile_model.dart';
import '../../../../shared/providers/providers.dart';
import '../../../../shared/widgets/confirm_dialog.dart';
import '../../../history/presentation/viewmodel/history_viewmodel.dart';
import '../viewmodel/profile_viewmodel.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  void _edit(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      builder: (_) => const _EditProfileSheet(),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final p = ref.watch(profileProvider);
    final trips = ref.watch(savedTripsProvider);
    final chats = ref.watch(historyProvider);
    final places = trips.map((t) => t.destination).toSet().length;
    final initial = p.name.trim().isEmpty ? 'T' : p.name.trim()[0].toUpperCase();

    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
        children: [
          // ---------- Header ----------
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [AppColors.primary, Color(0xFF0F766E)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(24),
            ),
            child: Row(
              children: [
                CircleAvatar(
                  radius: 34,
                  backgroundColor: Colors.white,
                  child: Text(initial,
                      style: const TextStyle(
                          fontSize: 30,
                          fontWeight: FontWeight.w800,
                          color: AppColors.primary)),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(p.name,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                              fontSize: 22, fontWeight: FontWeight.w800)),
                      const SizedBox(height: 2),
                      Text(p.email.isEmpty ? 'Add your email' : p.email,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                              color: Colors.white70, fontSize: 13)),
                      const SizedBox(height: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 10, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.white.withOpacity(0.18),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text('${p.travelStyle} traveller',
                            style: const TextStyle(
                                fontSize: 12, fontWeight: FontWeight.w600)),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  onPressed: () => _edit(context),
                  icon: const Icon(Icons.edit_rounded),
                ),
              ],
            ),
          ).animate().fadeIn().slideY(begin: 0.1, end: 0),

          const SizedBox(height: 16),

          // ---------- Stats ----------
          Row(
            children: [
              _Stat('${trips.length}', 'Saved trips', Icons.luggage_rounded),
              const SizedBox(width: 10),
              _Stat('${chats.length}', 'Chats', Icons.chat_bubble_rounded),
              const SizedBox(width: 10),
              _Stat('$places', 'Places', Icons.place_rounded),
            ],
          ).animate().fadeIn(delay: 150.ms),

          // ---------- Preferences ----------
          const _SectionTitle('Travel preferences'),
          _Group(children: [
            ListTile(
              leading: const Icon(Icons.home_rounded,
                  color: AppColors.primaryLight),
              title: const Text('Home city'),
              subtitle: Text(p.homeCity,
                  style: const TextStyle(color: AppColors.textSecondary)),
              trailing: const Icon(Icons.chevron_right_rounded,
                  color: AppColors.textMuted),
              onTap: () => _edit(context),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.diamond_rounded,
                          color: AppColors.primaryLight, size: 22),
                      SizedBox(width: 16),
                      Text('Travel style', style: TextStyle(fontSize: 16)),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Wrap(
                    spacing: 8,
                    children: ['Budget', 'Comfort', 'Luxury'].map((s) {
                      final selected = p.travelStyle == s;
                      return ChoiceChip(
                        label: Text(s),
                        selected: selected,
                        showCheckmark: false,
                        selectedColor: AppColors.primary,
                        backgroundColor: AppColors.surfaceLight,
                        side: BorderSide.none,
                        labelStyle: TextStyle(
                          color: selected
                              ? Colors.white
                              : AppColors.textSecondary,
                          fontWeight: FontWeight.w600,
                        ),
                        onSelected: (_) => ref
                            .read(profileProvider.notifier)
                            .update(p.copyWith(travelStyle: s)),
                      );
                    }).toList(),
                  ),
                ],
              ),
            ),
            SwitchListTile(
              secondary: const Icon(Icons.notifications_rounded,
                  color: AppColors.primaryLight),
              title: const Text('Trip notifications'),
              value: p.notifications,
              activeColor: AppColors.primaryLight,
              onChanged: (v) => ref
                  .read(profileProvider.notifier)
                  .update(p.copyWith(notifications: v)),
            ),
          ]),

          // ---------- Data ----------
          const _SectionTitle('Data'),
          _Group(children: [
            ListTile(
              leading:
              const Icon(Icons.history_rounded, color: AppColors.accent),
              title: const Text('Clear chat history'),
              onTap: () async {
                final ok = await showConfirmDialog(
                  context,
                  title: 'Clear chat history?',
                  message: 'All past chats will be removed.',
                  confirmText: 'Clear',
                );
                if (ok) ref.read(historyProvider.notifier).clear();
              },
            ),
            ListTile(
              leading: const Icon(Icons.delete_outline_rounded,
                  color: AppColors.error),
              title: const Text('Remove all saved trips'),
              onTap: () async {
                final ok = await showConfirmDialog(
                  context,
                  title: 'Remove saved trips?',
                  message: 'All saved trips will be deleted.',
                  confirmText: 'Remove',
                );
                if (ok) ref.read(savedTripsProvider.notifier).clear();
              },
            ),
          ]),

          // ---------- About ----------
          const _SectionTitle('About'),
          _Group(children: [
            ListTile(
              leading: const Icon(Icons.info_outline_rounded,
                  color: AppColors.primaryLight),
              title: const Text('Voyage AI'),
              subtitle: const Text('Version 1.0.0',
                  style: TextStyle(color: AppColors.textSecondary)),
              onTap: () => showAboutDialog(
                context: context,
                applicationName: 'Voyage AI',
                applicationVersion: '1.0.0',
                children: const [
                  Text('Your personal AI travel agent. Built for VoyageHack 4.0.'),
                ],
              ),
            ),
          ]),
        ],
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  final String value, label;
  final IconData icon;
  const _Stat(this.value, this.label, this.icon);

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(18),
        ),
        child: Column(
          children: [
            Icon(icon, color: AppColors.accent, size: 22),
            const SizedBox(height: 8),
            Text(value,
                style:
                const TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
            Text(label,
                style: const TextStyle(
                    color: AppColors.textMuted, fontSize: 12)),
          ],
        ),
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String text;
  const _SectionTitle(this.text);

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.fromLTRB(4, 24, 4, 10),
    child: Text(text,
        style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w700,
            color: AppColors.textSecondary,
            letterSpacing: 0.5)),
  );
}

class _Group extends StatelessWidget {
  final List<Widget> children;
  const _Group({required this.children});

  @override
  Widget build(BuildContext context) => Material(
    color: AppColors.surface,
    borderRadius: BorderRadius.circular(18),
    clipBehavior: Clip.antiAlias,
    child: Column(children: children),
  );
}

// ---------------- Edit sheet ----------------
class _EditProfileSheet extends ConsumerStatefulWidget {
  const _EditProfileSheet();

  @override
  ConsumerState<_EditProfileSheet> createState() => _EditProfileSheetState();
}

class _EditProfileSheetState extends ConsumerState<_EditProfileSheet> {
  late final TextEditingController _name;
  late final TextEditingController _email;
  late final TextEditingController _city;

  @override
  void initState() {
    super.initState();
    final p = ref.read(profileProvider);
    _name = TextEditingController(text: p.name);
    _email = TextEditingController(text: p.email);
    _city = TextEditingController(text: p.homeCity);
  }

  @override
  void dispose() {
    _name.dispose();
    _email.dispose();
    _city.dispose();
    super.dispose();
  }

  void _save() {
    final p = ref.read(profileProvider);
    ref.read(profileProvider.notifier).update(
      p.copyWith(
        name: _name.text.trim().isEmpty ? 'Traveller' : _name.text.trim(),
        email: _email.text.trim(),
        homeCity:
        _city.text.trim().isEmpty ? 'Delhi' : _city.text.trim(),
      ),
    );
    Navigator.pop(context);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Profile updated ✅')),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(
          24, 24, 24, 24 + MediaQuery.of(context).viewInsets.bottom),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Edit profile',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
            const SizedBox(height: 20),
            TextField(
              controller: _name,
              textCapitalization: TextCapitalization.words,
              decoration: const InputDecoration(
                  hintText: 'Your name',
                  prefixIcon: Icon(Icons.person_rounded)),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _email,
              keyboardType: TextInputType.emailAddress,
              decoration: const InputDecoration(
                  hintText: 'Email', prefixIcon: Icon(Icons.email_rounded)),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _city,
              textCapitalization: TextCapitalization.words,
              decoration: const InputDecoration(
                  hintText: 'Home city', prefixIcon: Icon(Icons.home_rounded)),
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _save,
                child: const Text('Save changes'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}