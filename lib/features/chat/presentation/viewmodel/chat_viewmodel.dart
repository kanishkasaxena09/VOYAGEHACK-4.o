import 'package:equatable/equatable.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';
import '../../../../data/models/chat_session_model.dart';
import '../../../../data/models/message_model.dart';
import '../../../../data/models/trip_model.dart';
import '../../../../data/repositories/chat_repository.dart';
import '../../../../shared/providers/providers.dart';
import '../../../history/presentation/viewmodel/history_viewmodel.dart';

class ChatState extends Equatable {
  final List<MessageModel> messages;
  final bool isTyping;

  const ChatState({this.messages = const [], this.isTyping = false});

  ChatState copyWith({List<MessageModel>? messages, bool? isTyping}) =>
      ChatState(
        messages: messages ?? this.messages,
        isTyping: isTyping ?? this.isTyping,
      );

  @override
  List<Object?> get props => [messages, isTyping];
}

class ChatViewModel extends StateNotifier<ChatState> {
  final ChatRepository _repo;
  final HistoryNotifier _history;
  String _sessionId = const Uuid().v4();

  ChatViewModel(this._repo, this._history)
      : super(ChatState(messages: [_welcome()]));

  static MessageModel _welcome() => MessageModel(
    id: const Uuid().v4(),
    text:
    "Hi! I'm your AI Travel Agent. Tell me about your trip — destination, dates, budget, or interests.",
    sender: MessageSender.ai,
    timestamp: DateTime.now(),
  );

  MessageModel _msg(String text, MessageSender s, {TripModel? trip}) =>
      MessageModel(
        id: const Uuid().v4(),
        text: text,
        sender: s,
        timestamp: DateTime.now(),
        trip: trip,
      );

  // Save the current conversation to history
  void _saveSession() {
    final userMsgs =
    state.messages.where((m) => m.sender == MessageSender.user);
    if (userMsgs.isEmpty) return;

    var title = userMsgs.first.text;
    if (title.length > 42) title = '${title.substring(0, 42)}...';

    _history.upsert(ChatSessionModel(
      id: _sessionId,
      title: title,
      updatedAt: DateTime.now(),
      messages: state.messages,
    ));
  }

  // Start a fresh conversation
  void newChat() {
    if (state.isTyping) return;
    _sessionId = const Uuid().v4();
    state = ChatState(messages: [_welcome()]);
  }

  // Open an old conversation from history. Returns false if busy.
  bool loadSession(ChatSessionModel session) {
    if (state.isTyping) return false;
    _sessionId = session.id;
    state = ChatState(messages: session.messages);
    return true;
  }

  Future<void> sendMessage(String text) async {
    final clean = text.trim();
    if (clean.isEmpty || state.isTyping) return;

    state = state.copyWith(
      messages: [...state.messages, _msg(clean, MessageSender.user)],
      isTyping: true,
    );
    _saveSession();

    try {
      final reply = await _repo.send(clean, _sessionId);
      state = state.copyWith(
        messages: [
          ...state.messages,
          _msg(reply.text, MessageSender.ai, trip: reply.trip),
        ],
        isTyping: false,
      );
    } catch (_) {
      state = state.copyWith(
        messages: [
          ...state.messages,
          _msg("Oops! Couldn't reach the server. Please try again. 🙏",
              MessageSender.ai),
        ],
        isTyping: false,
      );
    }
    _saveSession();
  }
}

final chatViewModelProvider =
StateNotifierProvider<ChatViewModel, ChatState>((ref) {
  return ChatViewModel(
    ref.read(chatRepositoryProvider),
    ref.read(historyProvider.notifier),
  );
});