import 'package:dio/dio.dart';
import '../../core/constants/api_constants.dart';
import '../models/trip_model.dart';

class ChatReply {
  final String text;
  final TripModel? trip;
  const ChatReply({required this.text, this.trip});
}

class ChatRepository {
  final Dio _dio;
  ChatRepository(this._dio);

  Future<ChatReply> send(String message, String sessionId) async {
    if (ApiConstants.useMock) return _mockReply(message);

    final res = await _dio.post(
      ApiConstants.chat,
      data: {'message': message, 'session_id': sessionId},
    );
    final data = res.data as Map<String, dynamic>;
    return ChatReply(
      text: data['reply'] ?? '',
      trip: data['trip'] != null
          ? TripModel.fromJson(data['trip'] as Map<String, dynamic>)
          : null,
    );
  }

  // ---------- Fake data (demo/testing ke liye) ----------
  Future<ChatReply> _mockReply(String message) async {
    await Future.delayed(const Duration(milliseconds: 1800));
    final m = message.toLowerCase();

    if (m.contains('goa') || m.contains('beach') || m.contains('plan')) {
      return const ChatReply(
        text: "I've put together a perfect Goa plan for you! 🌴",
        trip: TripModel(
          destination: 'Goa',
          summary: 'The perfect mix of beaches, seafood and nightlife.',
          imageUrl:
          'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=800',
          days: 3,
          budget: 38000,
          itinerary: [
            DayPlanModel(day: 1, title: 'Arrival & North Goa', activities: [
              ActivityModel(
                  time: '10:00 AM',
                  title: 'Hotel Check-in',
                  description: 'Beach-facing hotel near Calangute',
                  cost: 6000),
              ActivityModel(
                  time: '03:00 PM',
                  title: 'Baga Beach',
                  description: 'Water sports and beach shacks',
                  cost: 2500),
              ActivityModel(
                  time: '08:00 PM',
                  title: 'Tito’s Lane',
                  description: 'Nightlife and live music',
                  cost: 3000),
            ]),
            DayPlanModel(day: 2, title: 'Heritage & Food', activities: [
              ActivityModel(
                  time: '09:00 AM',
                  title: 'Basilica of Bom Jesus',
                  description: 'UNESCO heritage site',
                  cost: 0),
              ActivityModel(
                  time: '01:00 PM',
                  title: 'Fontainhas Walk',
                  description: 'Latin quarter + Goan thali',
                  cost: 1200),
              ActivityModel(
                  time: '06:00 PM',
                  title: 'Mandovi River Cruise',
                  description: 'Sunset cruise with live music',
                  cost: 1000),
            ]),
            DayPlanModel(day: 3, title: 'South Goa Chill', activities: [
              ActivityModel(
                  time: '10:00 AM',
                  title: 'Palolem Beach',
                  description: 'Peaceful beach, kayaking',
                  cost: 1800),
              ActivityModel(
                  time: '05:00 PM',
                  title: 'Departure',
                  description: 'Airport drop',
                  cost: 800),
            ]),
          ],
        ),
      );
    }

    return const ChatReply(
      text: "Got it! Share your destination, dates and budget and I'll build the best plan for you. ✈️",
    );
  }
}