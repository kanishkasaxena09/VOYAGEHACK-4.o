import 'package:dio/dio.dart';
import '../constants/api_constants.dart';

Dio createDio() {
  final dio = Dio(
    BaseOptions(
      baseUrl: ApiConstants.baseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 60), // AI slow ho sakta hai
      headers: {'Content-Type': 'application/json'},
    ),
  );
  dio.interceptors.add(LogInterceptor(requestBody: true, responseBody: true));
  return dio;
}