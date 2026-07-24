import 'package:flutter_test/flutter_test.dart';
import 'package:fitlens_mobile/main.dart';

void main() {
  testWidgets('FitLensApp smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const FitLensApp());
    expect(find.text('FitLens AI'), findsOneWidget);
  });
}
