import 'package:equatable/equatable.dart';

class ActivityModel extends Equatable {
  final String time;
  final String title;
  final String description;
  final int cost;

  const ActivityModel({
    required this.time,
    required this.title,
    required this.description,
    required this.cost,
  });

  factory ActivityModel.fromJson(Map<String, dynamic> j) => ActivityModel(
    time: j['time'] ?? '',
    title: j['title'] ?? '',
    description: j['description'] ?? '',
    cost: ((j['cost'] ?? 0) as num).toInt(),
  );

  Map<String, dynamic> toJson() => {
    'time': time,
    'title': title,
    'description': description,
    'cost': cost,
  };

  @override
  List<Object?> get props => [time, title, description, cost];
}

class DayPlanModel extends Equatable {
  final int day;
  final String title;
  final List<ActivityModel> activities;

  const DayPlanModel({
    required this.day,
    required this.title,
    required this.activities,
  });

  factory DayPlanModel.fromJson(Map<String, dynamic> j) => DayPlanModel(
    day: ((j['day'] ?? 1) as num).toInt(),
    title: j['title'] ?? '',
    activities: ((j['activities'] as List?) ?? [])
        .map((e) => ActivityModel.fromJson(e as Map<String, dynamic>))
        .toList(),
  );

  Map<String, dynamic> toJson() => {
    'day': day,
    'title': title,
    'activities': activities.map((a) => a.toJson()).toList(),
  };

  @override
  List<Object?> get props => [day, title, activities];
}

class TripModel extends Equatable {
  final String destination;
  final String summary;
  final String imageUrl;
  final int days;
  final int budget;
  final List<DayPlanModel> itinerary;

  const TripModel({
    required this.destination,
    required this.summary,
    required this.imageUrl,
    required this.days,
    required this.budget,
    required this.itinerary,
  });

  factory TripModel.fromJson(Map<String, dynamic> j) => TripModel(
    destination: j['destination'] ?? '',
    summary: j['summary'] ?? '',
    imageUrl: j['image_url'] ?? '',
    days: ((j['days'] ?? 0) as num).toInt(),
    budget: ((j['budget'] ?? 0) as num).toInt(),
    itinerary: ((j['itinerary'] as List?) ?? [])
        .map((e) => DayPlanModel.fromJson(e as Map<String, dynamic>))
        .toList(),
  );

  Map<String, dynamic> toJson() => {
    'destination': destination,
    'summary': summary,
    'image_url': imageUrl,
    'days': days,
    'budget': budget,
    'itinerary': itinerary.map((d) => d.toJson()).toList(),
  };

  @override
  List<Object?> get props => [destination, days, budget, itinerary];
}