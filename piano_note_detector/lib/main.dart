import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() {
  runApp(const PianoNoteDetectorApp());
}

class PianoNoteDetectorApp extends StatelessWidget {
  const PianoNoteDetectorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Piano Note Detector',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const HomePage(),
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  HomePageState createState() => HomePageState();
}

class HomePageState extends State<HomePage> {
  List<String> detectedNotes = [];
  bool isRecording = false;

  Future<void> startRecording() async {
    setState(() {
      isRecording = true;
      detectedNotes = [];
    });

    try {
      // iOS Simulator için 127.0.0.1, gerçek cihaz için bilgisayarınızın IP adresi
      final response = await http.post(
        Uri.parse('http://127.0.0.1:5000/record'),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['success']) {
          setState(() {
            detectedNotes = List<String>.from(data['notes']);
          });
        }
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Bağlantı hatası: $e'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      setState(() {
        isRecording = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Piano Note Detector'),
        backgroundColor: Colors.blue,
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const SizedBox(height: 20),
            if (isRecording)
              Column(
                children: const [
                  CircularProgressIndicator(),
                  SizedBox(height: 10),
                  Text('Ses kaydediliyor...'),
                ],
              )
            else
              ElevatedButton.icon(
                onPressed: startRecording,
                icon: const Icon(Icons.mic),
                label: const Text('Kayda Başla'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 30, vertical: 15),
                ),
              ),
            const SizedBox(height: 40),
            if (detectedNotes.isNotEmpty) ...[
              const Text(
                'Tespit Edilen Notalar:',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 20),
              Wrap(
                spacing: 10,
                runSpacing: 10,
                alignment: WrapAlignment.center,
                children: detectedNotes.map((note) => NoteCard(note: note)).toList(),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class NoteCard extends StatelessWidget {
  final String note;

  const NoteCard({super.key, required this.note});

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 4,
      child: Container(
        padding: const EdgeInsets.all(15),
        child: Text(
          note,
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }
}
