import 'package:equatable/equatable.dart';

class ProfileModel extends Equatable {
  final String name;
  final String email;
  final String homeCity;
  final String travelStyle; // Budget | Comfort | Luxury
  final bool notifications;

  const ProfileModel({
    this.name = 'Traveller',
    this.email = '',
    this.homeCity = 'Delhi',
    this.travelStyle = 'Comfort',
    this.notifications = true,
  });

  ProfileModel copyWith({
    String? name,
    String? email,
    String? homeCity,
    String? travelStyle,
    bool? notifications,
  }) =>
      ProfileModel(
        name: name ?? this.name,
        email: email ?? this.email,
        homeCity: homeCity ?? this.homeCity,
        travelStyle: travelStyle ?? this.travelStyle,
        notifications: notifications ?? this.notifications,
      );

  Map<String, dynamic> toJson() => {
    'name': name,
    'email': email,
    'home_city': homeCity,
    'travel_style': travelStyle,
    'notifications': notifications,
  };

  factory ProfileModel.fromJson(Map<String, dynamic> j) => ProfileModel(
    name: j['name'] ?? 'Traveller',
    email: j['email'] ?? '',
    homeCity: j['home_city'] ?? 'Delhi',
    travelStyle: j['travel_style'] ?? 'Comfort',
    notifications: j['notifications'] ?? true,
  );

  @override
  List<Object?> get props =>
      [name, email, homeCity, travelStyle, notifications];
}