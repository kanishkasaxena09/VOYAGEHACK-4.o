import 'package:equatable/equatable.dart';
import 'trip_model.dart';

enum MessageSender { user, ai }

class MessageModel extends Equatable {
  final String id;
  final String text;
  final MessageSender sender;
  final DateTime timestamp;
  final TripModel? trip;

  const MessageModel({
    required this.id,
    required this.text,
    required this.sender,
    required this.timestamp,
    this.trip,
  });

  Map<String, dynamic> toJson() => {
    'id': id,
    'text': text,
    'sender': sender.name,
    'timestamp': timestamp.toIso8601String(),
    'trip': trip?.toJson(),
  };

  factory MessageModel.fromJson(Map<String, dynamic> j) => MessageModel(
    id: j['id'] ?? '',
    text: j['text'] ?? '',
    sender: j['sender'] == 'user' ? MessageSender.user : MessageSender.ai,
    timestamp: DateTime.tryParse(j['timestamp'] ?? '') ?? DateTime.now(),
    trip: j['trip'] != null
        ? TripModel.fromJson(j['trip'] as Map<String, dynamic>)
        : null,
  );

  @override
  List<Object?> get props => [id, text, sender, timestamp, trip];
}