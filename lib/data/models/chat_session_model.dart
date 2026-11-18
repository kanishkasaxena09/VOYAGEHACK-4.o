import 'package:equatable/equatable.dart';
import 'message_model.dart';

class ChatSessionModel extends Equatable {
  final String id;
  final String title;
  final DateTime updatedAt;
  final List<MessageModel> messages;

  const ChatSessionModel({
    required this.id,
    required this.title,
    required this.updatedAt,
    required this.messages,
  });

  String get preview => messages.isEmpty ? '' : messages.last.text;

  List<String> get destinations => messages
      .where((m) => m.trip != null)
      .map((m) => m.trip!.destination)
      .toSet()
      .toList();

  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'updated_at': updatedAt.toIso8601String(),
    'messages': messages.map((m) => m.toJson()).toList(),
  };

  factory ChatSessionModel.fromJson(Map<String, dynamic> j) =>
      ChatSessionModel(
        id: j['id'] ?? '',
        title: j['title'] ?? 'Chat',
        updatedAt: DateTime.tryParse(j['updated_at'] ?? '') ?? DateTime.now(),
        messages: ((j['messages'] as List?) ?? [])
            .map((e) => MessageModel.fromJson(e as Map<String, dynamic>))
            .toList(),
      );

  @override
  List<Object?> get props => [id, title, updatedAt, messages];
}