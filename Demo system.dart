// -------------------------------------------------------------------
// Enhanced Healthcare Management System Demo – Flutter v2.0
// -------------------------------------------------------------------
// • Responsive design with adaptive layouts
// • Modern material design with custom theme
// • Interactive dashboard with data visualization
// • Enhanced patient detail page with timeline
// • Improved navigation with app bar and drawer
// • Search functionality for patients, drugs and tests
// • Form validation and better user feedback
// -------------------------------------------------------------------
//  How to run:
//  flutter create healthcare_demo && cd healthcare_demo
//  replace lib/main.dart with this file, then:  flutter run -d chrome
// -------------------------------------------------------------------

import 'package:flutter/material.dart';

void main() => runApp(const HealthcareDemoApp());

/* ============================= Models ============================= */
class Visit {
  final int id;
  final DateTime date;
  final List<String> drugs;
  final List<String> tests;
  final String notes;
  final String outcome;
  final double temperature;
  final int heartRate;
  final int bloodPressureSystolic;
  final int bloodPressureDiastolic;

  Visit({
    required this.id,
    required this.date,
    this.drugs = const [],
    this.tests = const [],
    this.notes = '',
    this.outcome = '',
    this.temperature = 36.8,
    this.heartRate = 75,
    this.bloodPressureSystolic = 120,
    this.bloodPressureDiastolic = 80,
  });
}

class Patient {
  final int id;
  String name;
  int age;
  String gender;
  String phone;
  String email;
  String address;
  String bloodType;
  String avatar;
  List<Visit> visits;
  List<String> allergies;
  List<String> chronicConditions;

  Patient({
    required this.id,
    required this.name,
    required this.age,
    required this.gender,
    required this.phone,
    this.email = '',
    this.address = '',
    this.bloodType = '',
    required this.avatar,
    this.visits = const [],
    this.allergies = const [],
    this.chronicConditions = const [],
  });
}

/* ============================= Seed data ============================= */
final List<String> seedDrugs = [
  'Paracetamol 500 mg',
  'Amoxicillin 250 mg',
  'Ibuprofen 200 mg',
  'Metformin 850 mg',
  'Atorvastatin 20 mg',
  'Losartan 50 mg',
  'Aspirin 81 mg',
  'Omeprazole 20 mg',
  'Azithromycin 500 mg',
  'Vitamin D3 1000 IU',
  'Lisinopril 10 mg',
  'Levothyroxine 50 mcg',
  'Amlodipine 5 mg',
  'Simvastatin 20 mg',
  'Ciprofloxacin 500 mg',
];

final List<String> seedTests = [
  'Complete Blood Count (CBC)',
  'Liver Function Test',
  'HbA1c',
  'Lipid Profile',
  'Chest X‑Ray',
  'Thyroid (TSH)',
  'Electrolytes Panel',
  'Urinalysis',
  'Kidney Function Test',
  'ECG',
  'Ultrasound',
  'CT Scan',
  'MRI',
  'D-Dimer',
  'Troponin',
];

final List<String> bloodTypes = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

final List<Patient> seedPatients = [
  Patient(
    id: 1,
    name: 'Ahmed Mahdi',
    age: 32,
    gender: 'Male',
    phone: '0770‑123‑4567',
    email: 'ahmed.m@example.com',
    address: '123 Kindi Street, Baghdad',
    bloodType: 'O+',
    avatar: 'https://i.pravatar.cc/150?u=ahmed',
    visits: [
      Visit(
        id: 1,
        date: DateTime.parse('2025-04-01'),
        drugs: ['Paracetamol 500 mg'],
        tests: ['Complete Blood Count (CBC)'],
        notes: 'Mild fever, WBC 10 K/µL',
        outcome: 'Improved',
        temperature: 38.2,
      ),
    ],
    allergies: ['Penicillin'],
    chronicConditions: [],
  ),
  Patient(
    id: 2,
    name: 'Zainab Ali',
    age: 45,
    gender: 'Female',
    phone: '0781‑555‑9999',
    email: 'zainab.a@example.com',
    address: '456 Tigris View, Baghdad',
    bloodType: 'A+',
    avatar: 'https://i.pravatar.cc/150?u=zainab',
    visits: [
      Visit(
        id: 1,
        date: DateTime.parse('2025-03-28'),
        drugs: ['Metformin 850 mg'],
        tests: ['HbA1c'],
        notes: 'HbA1c = 7.8 %',
        outcome: 'Stable',
        bloodPressureSystolic: 135,
        bloodPressureDiastolic: 85,
      ),
      Visit(
        id: 2,
        date: DateTime.parse('2025-04-18'),
        drugs: ['Atorvastatin 20 mg'],
        tests: ['Lipid Profile'],
        notes: 'LDL = 165 mg/dL',
        outcome: 'Follow-up needed',
        bloodPressureSystolic: 130,
        bloodPressureDiastolic: 82,
      ),
    ],
    allergies: [],
    chronicConditions: ['Type 2 Diabetes', 'Hyperlipidemia'],
  ),
  Patient(
    id: 3,
    name: 'Hassan Farid',
    age: 60,
    gender: 'Male',
    phone: '0780‑888‑2222',
    email: 'hassan.f@example.com',
    address: '789 Euphrates Road, Basra',
    bloodType: 'B+',
    avatar: 'https://i.pravatar.cc/150?u=hassan',
    visits: [
      Visit(
        id: 1,
        date: DateTime.parse('2025-04-10'),
        drugs: ['Losartan 50 mg', 'Aspirin 81 mg'],
        tests: ['Chest X‑Ray', 'Electrolytes Panel'],
        notes: 'CXR → mild cardiomegaly',
        outcome: 'Stable',
        heartRate: 82,
        bloodPressureSystolic: 145,
        bloodPressureDiastolic: 90,
      ),
    ],
    allergies: ['Sulfa drugs'],
    chronicConditions: ['Hypertension', 'Coronary Artery Disease'],
  ),
  Patient(
    id: 4,
    name: 'Fatima Hussein',
    age: 28,
    gender: 'Female',
    phone: '0771‑444‑3333',
    email: 'fatima.h@example.com',
    address: '321 University Avenue, Mosul',
    bloodType: 'AB-',
    avatar: 'https://i.pravatar.cc/150?u=fatima',
    visits: [],
    allergies: ['Latex'],
    chronicConditions: ['Asthma'],
  ),
  Patient(
    id: 5,
    name: 'Omar Kareem',
    age: 52,
    gender: 'Male',
    phone: '0782‑777‑6666',
    email: 'omar.k@example.com',
    address: '654 Market Street, Erbil',
    bloodType: 'O-',
    avatar: 'https://i.pravatar.cc/150?u=omar',
    visits: [
      Visit(
        id: 1,
        date: DateTime.parse('2025-04-05'),
        drugs: ['Levothyroxine 50 mcg'],
        tests: ['Thyroid (TSH)'],
        notes: 'TSH = 5.8 mIU/L',
        outcome: 'Medication adjusted',
        temperature: 36.7,
      ),
    ],
    allergies: [],
    chronicConditions: ['Hypothyroidism'],
  ),
];

/* ============================= Main App ============================= */
class HealthcareDemoApp extends StatelessWidget {
  const HealthcareDemoApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Healthcare Demo',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF4355B9),
          brightness: Brightness.light,
        ),
        useMaterial3: true,
        fontFamily: 'Poppins',
        appBarTheme: const AppBarTheme(
          centerTitle: false,
          elevation: 0,
        ),
        cardTheme: CardTheme(
          elevation: 2,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          surfaceTintColor: Colors.white,
        ),
        dividerTheme: const DividerThemeData(),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: Colors.grey.shade50,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: Colors.grey.shade300),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: Colors.grey.shade300),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: Color(0xFF4355B9), width: 2),
          ),
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
        ),
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
        ),
        textButtonTheme: TextButtonThemeData(
          style: TextButton.styleFrom(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
        ),
        chipTheme: ChipThemeData(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(8),
          ),
        ),
      ),
      home: const _MainShell(),
    );
  }
}

enum AppPage { home, dashboard, drugs, tests, settings, patient }

class _MainShell extends StatefulWidget {
  const _MainShell({super.key});

  @override
  State<_MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<_MainShell> {
  AppPage _page = AppPage.home;
  Patient? _selectedPatient;
  String _searchQuery = '';
  bool _isSearching = false;

  final List<Patient> _patients = [...seedPatients];
  final List<String> _drugs = [...seedDrugs];
  final List<String> _tests = [...seedTests];

  // Controller for search functionality
  final TextEditingController _searchController = TextEditingController();

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  /* -------------------- Computed helpers -------------------- */
  List<Visit> get _allVisits => _patients.expand((p) => p.visits).toList();

  List<Patient> get _filteredPatients {
    if (_searchQuery.isEmpty) return _patients;
    return _patients.where((p) => 
      p.name.toLowerCase().contains(_searchQuery.toLowerCase()) ||
      p.phone.toLowerCase().contains(_searchQuery.toLowerCase()) ||
      p.email.toLowerCase().contains(_searchQuery.toLowerCase())
    ).toList();
  }

  List<String> get _filteredDrugs {
    if (_searchQuery.isEmpty) return _drugs;
    return _drugs.where((d) => 
      d.toLowerCase().contains(_searchQuery.toLowerCase())
    ).toList();
  }

  List<String> get _filteredTests {
    if (_searchQuery.isEmpty) return _tests;
    return _tests.where((t) => 
      t.toLowerCase().contains(_searchQuery.toLowerCase())
    ).toList();
  }

  List<MapEntry<String, int>> _topX(String type, [int n = 5]) {
    final Map<String, int> count = {};
    for (final v in _allVisits) {
      final items = type == 'drugs' ? v.drugs : v.tests;
      for (final i in items) {
        count.update(i, (value) => value + 1, ifAbsent: () => 1);
      }
    }
    final entries = count.entries.toList()..sort((a, b) => b.value.compareTo(a.value));
    return entries.take(n).toList();
  }

  /* -------------------- Dialog helpers -------------------- */
  Future<void> _showAddPatientDialog() async {
    final _PatientForm form = _PatientForm();
    final result = await showDialog<Patient>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add New Patient'),
        content: SizedBox(
          width: 400,
          child: form,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context), 
            child: const Text('Cancel')
          ),
          FilledButton(
            onPressed: () {
              if (form.isValid) Navigator.pop(context, form.toPatient());
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
    if (result != null) {
      setState(() => _patients.add(result));
      _showSnackBar('Patient ${result.name} added successfully');
    }
  }

  Future<void> _showAddDrugDialog() async {
    final controller = TextEditingController();
    final formKey = GlobalKey<FormState>();
    
    final result = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add Medication'),
        content: Form(
          key: formKey,
          child: TextFormField(
            controller: controller, 
            decoration: const InputDecoration(
              labelText: 'Medication name',
              hintText: 'e.g. Paracetamol 500 mg',
              prefixIcon: Icon(Icons.medication_outlined),
            ),
            validator: (value) {
              if (value == null || value.trim().isEmpty) {
                return 'Please enter medication name';
              }
              if (_drugs.contains(value.trim())) {
                return 'This medication already exists';
              }
              return null;
            },
            autofocus: true,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context), 
            child: const Text('Cancel')
          ),
          FilledButton(
            onPressed: () {
              if (formKey.currentState!.validate()) {
                Navigator.pop(context, controller.text.trim());
              }
            }, 
            child: const Text('Add')
          ),
        ],
      ),
    );
    
    if (result != null && result.isNotEmpty) {
      setState(() => _drugs.add(result));
      _showSnackBar('Medication $result added successfully');
    }
  }

  Future<void> _showAddTestDialog() async {
    final controller = TextEditingController();
    final formKey = GlobalKey<FormState>();
    
    final result = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add Lab Test'),
        content: Form(
          key: formKey,
          child: TextFormField(
            controller: controller, 
            decoration: const InputDecoration(
              labelText: 'Test name',
              hintText: 'e.g. Complete Blood Count',
              prefixIcon: Icon(Icons.science_outlined),
            ),
            validator: (value) {
              if (value == null || value.trim().isEmpty) {
                return 'Please enter test name';
              }
              if (_tests.contains(value.trim())) {
                return 'This test already exists';
              }
              return null;
            },
            autofocus: true,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context), 
            child: const Text('Cancel')
          ),
          FilledButton(
            onPressed: () {
              if (formKey.currentState!.validate()) {
                Navigator.pop(context, controller.text.trim());
              }
            }, 
            child: const Text('Add')
          ),
        ],
      ),
    );
    
    if (result != null && result.isNotEmpty) {
      setState(() => _tests.add(result));
      _showSnackBar('Lab test $result added successfully');
    }
  }

  Future<void> _showNewVisitDialog(Patient patient) async {
    final form = VisitForm(drugs: _drugs, tests: _tests);
    final visit = await showDialog<Visit>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Record New Visit'),
        content: SizedBox(
          width: 500,
          child: form,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context), 
            child: const Text('Cancel')
          ),
          FilledButton(
            onPressed: () {
              if (form.isValid) Navigator.pop(context, form.toVisit());
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
    
    if (visit != null) {
      setState(() => patient.visits = [...patient.visits, visit]);
      _showSnackBar('Visit recorded successfully');
    }
  }

  Future<void> _showDeleteConfirmation(Function() onConfirm, String title, String content) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: Text(content),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false), 
            child: const Text('Cancel')
          ),
          FilledButton(
            style: FilledButton.styleFrom(
              backgroundColor: Colors.red,
            ),
            onPressed: () => Navigator.pop(context, true), 
            child: const Text('Delete')
          ),
        ],
      ),
    );
    
    if (confirmed == true) {
      onConfirm();
    }
  }

  void _showSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(10),
        ),
        action: SnackBarAction(
          label: 'Dismiss',
          onPressed: () {
            ScaffoldMessenger.of(context).hideCurrentSnackBar();
          },
        ),
      ),
    );
  }

  /* -------------------- Search functionality -------------------- */
  void _startSearch() {
    setState(() {
      _isSearching = true;
      _searchQuery = '';
    });
  }

  void _stopSearch() {
    setState(() {
      _isSearching = false;
      _searchQuery = '';
      _searchController.clear();
    });
  }

  void _updateSearchQuery(String query) {
    setState(() {
      _searchQuery = query;
    });
  }

  /* -------------------- Pages -------------------- */
  Widget _buildHome() {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              const Text(
                'Patients', 
                style: TextStyle(
                  fontSize: 24, 
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(width: 16),
              Chip(
                label: Text('${_patients.length} total'),
                backgroundColor: Colors.grey.shade100,
              ),
              const Spacer(),
              FilledButton.icon(
                onPressed: _showAddPatientDialog,
                icon: const Icon(Icons.person_add_alt_1),
                label: const Text('Add Patient'),
              ),
            ],
          ),
        ),
        if (_filteredPatients.isEmpty)
          Expanded(
            child: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.search_off_rounded,
                    size: 80,
                    color: Colors.grey.shade400,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    _searchQuery.isEmpty 
                      ? 'No patients found' 
                      : 'No patients match "${_searchQuery}"',
                    style: TextStyle(
                      fontSize: 16,
                      color: Colors.grey.shade700,
                    ),
                  ),
                  if (_searchQuery.isNotEmpty)
                    TextButton(
                      onPressed: _stopSearch,
                      child: const Text('Clear search'),
                    ),
                ],
              ),
            ),
          )
        else
          Expanded(
            child: AnimatedSwitcher(
              duration: const Duration(milliseconds: 300),
              child: LayoutBuilder(
                key: ValueKey<String>(_searchQuery),
                builder: (context, constraints) {
                  final isWideScreen = constraints.maxWidth > 700;
                  
                  if (isWideScreen) {
                    // Grid view for wide screens
                    return GridView.builder(
                      padding: const EdgeInsets.all(16),
                      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 2,
                        childAspectRatio: 3,
                        crossAxisSpacing: 16,
                        mainAxisSpacing: 16,
                      ),
                      itemCount: _filteredPatients.length,
                      itemBuilder: (context, i) {
                        final p = _filteredPatients[i];
                        return _PatientCard(
                          patient: p,
                          onTap: () => setState(() {
                            _selectedPatient = p;
                            _page = AppPage.patient;
                          }),
                        );
                      },
                    );
                  } else {
                    // List view for narrow screens
                    return ListView.separated(
                      padding: const EdgeInsets.all(16),
                      itemCount: _filteredPatients.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 12),
                      itemBuilder: (context, i) {
                        final p = _filteredPatients[i];
                        return _PatientListTile(
                          patient: p,
                          onTap: () => setState(() {
                            _selectedPatient = p;
                            _page = AppPage.patient;
                          }),
                        );
                      },
                    );
                  }
                },
              ),
            ),
          ),
      ],
    );
  }

  Widget _buildDashboard() {
    final topDrugs = _topX('drugs');
    final topTests = _topX('tests');
    final hasData = _allVisits.isNotEmpty;
    
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Dashboard', 
            style: TextStyle(
              fontSize: 24, 
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 24),
          
          // Statistics cards
          LayoutBuilder(
            builder: (context, constraints) {
              final isWideScreen = constraints.maxWidth > 700;
              
              return Wrap(
                spacing: 16,
                runSpacing: 16,
                children: [
                  _StatCard(
                    icon: Icons.people_alt_outlined,
                    title: 'Total Patients',
                    value: _patients.length.toString(),
                    color: Colors.blue,
                    width: isWideScreen ? (constraints.maxWidth - 48) / 2 : constraints.maxWidth,
                  ),
                  _StatCard(
                    icon: Icons.calendar_month_outlined,
                    title: 'Total Visits',
                    value: _allVisits.length.toString(),
                    color: Colors.green,
                    width: isWideScreen ? (constraints.maxWidth - 48) / 2 : constraints.maxWidth,
                  ),
                ],
              );
            },
          ),
          
          const SizedBox(height: 32),
          
          if (!hasData)
            _EmptyStateWidget(
              icon: Icons.analytics_outlined,
              title: 'No visit data',
              description: 'Add patient visits to see analytics and trends.',
            )
          else
            LayoutBuilder(
              builder: (context, constraints) {
                final isWideScreen = constraints.maxWidth > 700;
                
                return Column(
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Card(
                            child: Padding(
                              padding: const EdgeInsets.all(16),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    children: [
                                      Icon(
                                        Icons.medication_outlined, 
                                        color: Theme.of(context).colorScheme.primary,
                                      ),
                                      const SizedBox(width: 8),
                                      Text(
                                        'Top Medications',
                                        style: Theme.of(context).textTheme.titleMedium!.copyWith(
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 16),
                                  ...topDrugs.asMap().entries.map((entry) {
                                    final i = entry.key;
                                    final e = entry.value;
                                    return Padding(
                                      padding: const EdgeInsets.only(bottom: 8),
                                      child: _ProgressBar(
                                        label: e.key,
                                        value: e.value,
                                        maxValue: topDrugs.isNotEmpty ? topDrugs.first.value : 1,
                                        color: Colors.blue.shade700,
                                        rank: i + 1,
                                      ),
                                    );
                                  }),
                                ],
                              ),
                            ),
                          ),
                        ),
                        if (isWideScreen) const SizedBox(width: 16),
                        if (isWideScreen)
                          Expanded(
                            child: Card(
                              child: Padding(
                                padding: const EdgeInsets.all(16),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      children: [
                                        Icon(
                                          Icons.science_outlined, 
                                          color: Theme.of(context).colorScheme.primary,
                                        ),
                                        const SizedBox(width: 8),
                                        Text(
                                          'Top Lab Tests',
                                          style: Theme.of(context).textTheme.titleMedium!.copyWith(
                                            fontWeight: FontWeight.bold,
                                          ),
                                        ),
                                      ],
                                    ),
                                    const SizedBox(height: 16),
                                    ...topTests.asMap().entries.map((entry) {
                                      final i = entry.key;
                                      final e = entry.value;
                                      return Padding(
                                        padding: const EdgeInsets.only(bottom: 8),
                                        child: _ProgressBar(
                                          label: e.key,
                                          value: e.value,
                                          maxValue: topTests.isNotEmpty ? topTests.first.value : 1,
                                          color: Colors.green.shade700,
                                          rank: i + 1,
                                        ),
                                      );
                                    }),
                                  ],
                                ),
                              ),
                            ),
                          ),
                      ],
                    ),
                    
                    if (!isWideScreen) const SizedBox(height: 16),
                    if (!isWideScreen)
                      Card(
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Icon(
                                    Icons.science_outlined, 
                                    color: Theme.of(context).colorScheme.primary,
                                  ),
                                  const SizedBox(width: 8),
                                  Text(
                                    'Top Lab Tests',
                                    style: Theme.of(context).textTheme.titleMedium!.copyWith(
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 16),
                              ...topTests.asMap().entries.map((entry) {
                                final i = entry.key;
                                final e = entry.value;
                                return Padding(
                                  padding: const EdgeInsets.only(bottom: 8),
                                  child: _ProgressBar(
                                    label: e.key,
                                    value: e.value,
                                    maxValue: topTests.isNotEmpty ? topTests.first.value : 1,
                                    color: Colors.green.shade700,
                                    rank: i + 1,
                                  ),
                                );
                              }),
                            ],
                          ),
                        ),
                      ),
                  ],
                );
              },
            ),
            
          const SizedBox(height: 32),
          
          // Recent activity
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        Icons.history_outlined, 
                        color: Theme.of(context).colorScheme.primary,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        'Recent Activity',
                        style: Theme.of(context).textTheme.titleMedium!.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  if (!hasData)
                    const Padding(
                      padding: EdgeInsets.all(16),
                      child: Center(
                        child: Text('No recent activity'),
                      ),
                    )
                  else
                    ..._getRecentVisits(),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
  
  List<Widget> _getRecentVisits() {
    final visitsSorted = [..._allVisits]..sort((a, b) => b.date.compareTo(a.date));
    final recentVisits = visitsSorted.take(5).toList();
    
    return recentVisits.map((visit) {
      final patient = _patients.firstWhere(
        (p) => p.visits.any((v) => v.id == visit.id),
      );
      return _RecentActivityItem(
        date: visit.date,
        patientName: patient.name,
        patientAvatar: patient.avatar,
        description: '${visit.drugs.isEmpty ? "No medications" : visit.drugs.join(", ")}\n'
            '${visit.tests.isEmpty ? "No tests" : visit.tests.join(", ")}',
        onTap: () => setState(() {
          _selectedPatient = patient;
          _page = AppPage.patient;
        }),
      );
    }).toList();
  }

  Widget _buildSimpleListPage(String title, List<String> items, VoidCallback onAdd) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Text(
                title, 
                style: const TextStyle(
                  fontSize: 24, 
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(width: 16),
              Chip(
                label: Text('${items.length} total'),
                backgroundColor: Colors.grey.shade100,
              ),
              const Spacer(),
              FilledButton.icon(
                onPressed: onAdd, 
                icon: const Icon(Icons.add), 
                label: const Text('Add'),
              ),
            ],
          ),
        ),
        if (items.isEmpty || (items.isEmpty && _searchQuery.isNotEmpty))
          Expanded(
            child: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    _searchQuery.isNotEmpty ? Icons.search_off_rounded : Icons.pending_actions,
                    size: 80,
                    color: Colors.grey.shade400,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    _searchQuery.isNotEmpty
                        ? 'No matches found for "${_searchQuery}"'
                        : 'No ${title.toLowerCase()} available',
                    style: TextStyle(
                      fontSize: 16,
                      color: Colors.grey.shade700,
                    ),
                  ),
                  const SizedBox(height: 8),
                  FilledButton.icon(
                    onPressed: onAdd,
                    icon: const Icon(Icons.add),
                    label: Text('Add ${title.substring(0, title.length - 1)}'),
                  ),
                ],
              ),
            ),
          )
        else
          Expanded(
            child: ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: items.length,
              separatorBuilder: (_, __) => const Divider(height: 1),
              itemBuilder: (context, i) => Card(
                margin: const EdgeInsets.symmetric(vertical: 4),
                child: ListTile(
                  title: Text(items[i]),
                  leading: title == 'Drugs'
                      ? const Icon(Icons.medication_outlined, color: Colors.blue)
                      : const Icon(Icons.science_outlined, color: Colors.green),
                  trailing: IconButton(
                    icon: const Icon(Icons.delete_outline, color: Colors.red),
                    onPressed: () {
                      _showDeleteConfirmation(
                        () => setState(() => items.removeAt(i)),
                        'Delete ${title.substring(0, title.length - 1)}',
                        'Are you sure you want to delete "${items[i]}"?',
                      );
                    },
                  ),
                ),
              ),
            ),
          ),
      ],
    );
  }

  Widget _buildPatientPage(Patient p) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final isWideScreen = constraints.maxWidth > 800;
        
        if (isWideScreen) {
          // Desktop layout - side by side
          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Patient info sidebar
              SizedBox(
                width: 300,
                child: Card(
                  margin: const EdgeInsets.all(16),
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        CircleAvatar(
                          backgroundImage: NetworkImage(p.avatar),
                          radius: 60,
                        ),
                        const SizedBox(height: 16),
                        Text(
                          p.name,
                          style: const TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                          ),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 8),
                        Text(
                          '${p.gender} • ${p.age} years',
                          style: TextStyle(
                            fontSize: 16,
                            color: Colors.grey.shade600,
                          ),
                        ),
                        const SizedBox(height: 4),
                        if (p.bloodType.isNotEmpty)
                          Chip(
                            label: Text('Blood: ${p.bloodType}'),
                            backgroundColor: Colors.red.shade50,
                          ),
                        const Divider(height: 32),
                        _PatientInfoItem(
                          icon: Icons.phone_outlined,
                          title: 'Phone',
                          value: p.phone,
                        ),
                        if (p.email.isNotEmpty)
                          _PatientInfoItem(
                            icon: Icons.email_outlined,
                            title: 'Email',
                            value: p.email,
                          ),
                        if (p.address.isNotEmpty)
                          _PatientInfoItem(
                            icon: Icons.location_on_outlined,
                            title: 'Address',
                            value: p.address,
                          ),
                        const Divider(height: 32),
                        
                        // Allergies
                        Row(
                          children: [
                            Icon(
                              Icons.warning_amber_rounded,
                              color: Theme.of(context).colorScheme.error,
                              size: 20,
                            ),
                            const SizedBox(width: 8),
                            Text(
                              'Allergies',
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                color: Theme.of(context).colorScheme.error,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        p.allergies.isEmpty
                            ? const Text('No known allergies')
                            : Wrap(
                                spacing: 8,
                                runSpacing: 8,
                                children: p.allergies.map((allergy) => Chip(
                                  label: Text(allergy),
                                  backgroundColor: Colors.red.shade50,
                                )).toList(),
                              ),
                        
                        const SizedBox(height: 16),
                        
                        // Chronic conditions
                        Row(
                          children: [
                            Icon(
                              Icons.monitor_heart_outlined,
                              color: Theme.of(context).colorScheme.secondary,
                              size: 20,
                            ),
                            const SizedBox(width: 8),
                            Text(
                              'Chronic Conditions',
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                color: Theme.of(context).colorScheme.secondary,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        p.chronicConditions.isEmpty
                            ? const Text('No chronic conditions')
                            : Wrap(
                                spacing: 8,
                                runSpacing: 8,
                                children: p.chronicConditions.map((condition) => Chip(
                                  label: Text(condition),
                                  backgroundColor: Colors.purple.shade50,
                                )).toList(),
                              ),
                      ],
                    ),
                  ),
                ),
              ),
              
              // Visits section
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.only(top: 16, right: 16, bottom: 16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Text(
                            'Patient History',
                            style: Theme.of(context).textTheme.headlineSmall!.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const Spacer(),
                          FilledButton.icon(
                            onPressed: () => _showNewVisitDialog(p),
                            icon: const Icon(Icons.add),
                            label: const Text('New Visit'),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      
                      Expanded(
                        child: p.visits.isEmpty
                            ? _EmptyStateWidget(
                                icon: Icons.calendar_month_outlined,
                                title: 'No visits recorded',
                                description: 'Add a new visit to start tracking patient history.',
                                action: FilledButton.icon(
                                  onPressed: () => _showNewVisitDialog(p),
                                  icon: const Icon(Icons.add),
                                  label: const Text('Add First Visit'),
                                ),
                              )
                            : _VisitTimeline(visits: p.visits),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          );
        } else {
          // Mobile layout - stacked
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Patient header
              Card(
                margin: const EdgeInsets.all(16),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      Row(
                        children: [
                          CircleAvatar(
                            backgroundImage: NetworkImage(p.avatar),
                            radius: 30,
                          ),
                          const SizedBox(width: 16),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  p.name,
                                  style: const TextStyle(
                                    fontSize: 20,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                                Text(
                                  '${p.gender} • ${p.age} yrs • ${p.bloodType}',
                                  style: TextStyle(
                                    color: Colors.grey.shade600,
                                  ),
                                ),
                                Text(
                                  p.phone,
                                  style: TextStyle(
                                    color: Colors.grey.shade600,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                      
                      if (p.allergies.isNotEmpty) ...[
                        const Divider(height: 24),
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Icon(
                              Icons.warning_amber_rounded, 
                              color: Theme.of(context).colorScheme.error,
                              size: 18,
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'Allergies:',
                                    style: TextStyle(
                                      fontWeight: FontWeight.bold,
                                      color: Theme.of(context).colorScheme.error,
                                    ),
                                  ),
                                  Text(p.allergies.join(', ')),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ],
                      
                      if (p.chronicConditions.isNotEmpty) ...[
                        const Divider(height: 24),
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Icon(
                              Icons.monitor_heart_outlined, 
                              color: Theme.of(context).colorScheme.secondary,
                              size: 18,
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'Chronic Conditions:',
                                    style: TextStyle(
                                      fontWeight: FontWeight.bold,
                                      color: Theme.of(context).colorScheme.secondary,
                                    ),
                                  ),
                                  Text(p.chronicConditions.join(', ')),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ],
                    ],
                  ),
                ),
              ),
              
              // Visits header
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: Row(
                  children: [
                    const Text(
                      'Visits',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const Spacer(),
                    FilledButton.icon(
                      onPressed: () => _showNewVisitDialog(p),
                      icon: const Icon(Icons.add),
                      label: const Text('New Visit'),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 8),
              
              // Visits list
              Expanded(
                child: p.visits.isEmpty
                    ? _EmptyStateWidget(
                        icon: Icons.calendar_month_outlined,
                        title: 'No visits recorded',
                        description: 'Add a new visit to start tracking patient history.',
                        action: FilledButton.icon(
                          onPressed: () => _showNewVisitDialog(p),
                          icon: const Icon(Icons.add),
                          label: const Text('Add First Visit'),
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: p.visits.length,
                        itemBuilder: (context, i) {
                          final visits = [...p.visits]..sort((a, b) => b.date.compareTo(a.date));
                          return _VisitCard(visit: visits[i]);
                        },
                      ),
              ),
            ],
          );
        }
      },
    );
  }

  Widget _buildSettings() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Settings', 
            style: TextStyle(
              fontSize: 24, 
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 24),
          
          LayoutBuilder(
            builder: (context, constraints) {
              final isWideScreen = constraints.maxWidth > 700;
              
              if (isWideScreen) {
                // Two-column layout
                return Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Profile settings
                    Expanded(
                      child: Card(
                        child: Padding(
                          padding: const EdgeInsets.all(24),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Icon(
                                    Icons.person_outline,
                                    color: Theme.of(context).colorScheme.primary,
                                  ),
                                  const SizedBox(width: 8),
                                  Text(
                                    'Profile Information',
                                    style: Theme.of(context).textTheme.titleMedium!.copyWith(
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 24),
                              TextField(
                                decoration: const InputDecoration(
                                  labelText: 'Name',
                                  hintText: 'Your full name',
                                  prefixIcon: Icon(Icons.person_outline),
                                ),
                                controller: TextEditingController(text: 'Dr. Noor Ahmed'),
                              ),
                              const SizedBox(height: 16),
                              TextField(
                                decoration: const InputDecoration(
                                  labelText: 'Specialty',
                                  hintText: 'Your medical specialty',
                                  prefixIcon: Icon(Icons.medical_services_outlined),
                                ),
                                controller: TextEditingController(text: 'General Practitioner'),
                              ),
                              const SizedBox(height: 16),
                              TextField(
                                decoration: const InputDecoration(
                                  labelText: 'License Number',
                                  hintText: 'Your medical license number',
                                  prefixIcon: Icon(Icons.badge_outlined),
                                ),
                                controller: TextEditingController(text: 'MED-2025-1234'),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                    
                    const SizedBox(width: 16),
                    
                    // Contact settings
                    Expanded(
                      child: Card(
                        child: Padding(
                          padding: const EdgeInsets.all(24),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Icon(
                                    Icons.contact_phone_outlined,
                                    color: Theme.of(context).colorScheme.primary,
                                  ),
                                  const SizedBox(width: 8),
                                  Text(
                                    'Contact Information',
                                    style: Theme.of(context).textTheme.titleMedium!.copyWith(
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 24),
                              TextField(
                                decoration: const InputDecoration(
                                  labelText: 'Email',
                                  hintText: 'Your email address',
                                  prefixIcon: Icon(Icons.email_outlined),
                                ),
                                controller: TextEditingController(text: 'noor@example.com'),
                              ),
                              const SizedBox(height: 16),
                              TextField(
                                decoration: const InputDecoration(
                                  labelText: 'Phone',
                                  hintText: 'Your phone number',
                                  prefixIcon: Icon(Icons.phone_outlined),
                                ),
                                controller: TextEditingController(text: '0770‑000‑0000'),
                              ),
                              const SizedBox(height: 16),
                              TextField(
                                decoration: const InputDecoration(
                                  labelText: 'Address',
                                  hintText: 'Your practice address',
                                  prefixIcon: Icon(Icons.location_on_outlined),
                                ),
                                controller: TextEditingController(text: 'Basra, Iraq'),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ],
                );
              } else {
                // Single column layout
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Profile settings
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Icon(
                                  Icons.person_outline,
                                  color: Theme.of(context).colorScheme.primary,
                                ),
                                const SizedBox(width: 8),
                                Text(
                                  'Profile Information',
                                  style: Theme.of(context).textTheme.titleMedium!.copyWith(
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 16),
                            TextField(
                              decoration: const InputDecoration(
                                labelText: 'Name',
                                hintText: 'Your full name',
                                prefixIcon: Icon(Icons.person_outline),
                              ),
                              controller: TextEditingController(text: 'Dr. Noor Ahmed'),
                            ),
                            const SizedBox(height: 12),
                            TextField(
                              decoration: const InputDecoration(
                                labelText: 'Specialty',
                                hintText: 'Your medical specialty',
                                prefixIcon: Icon(Icons.medical_services_outlined),
                              ),
                              controller: TextEditingController(text: 'General Practitioner'),
                            ),
                            const SizedBox(height: 12),
                            TextField(
                              decoration: const InputDecoration(
                                labelText: 'License Number',
                                hintText: 'Your medical license number',
                                prefixIcon: Icon(Icons.badge_outlined),
                              ),
                              controller: TextEditingController(text: 'MED-2025-1234'),
                            ),
                          ],
                        ),
                      ),
                    ),
                    
                    const SizedBox(height: 16),
                    
                    // Contact settings
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Icon(
                                  Icons.contact_phone_outlined,
                                  color: Theme.of(context).colorScheme.primary,
                                ),
                                const SizedBox(width: 8),
                                Text(
                                  'Contact Information',
                                  style: Theme.of(context).textTheme.titleMedium!.copyWith(
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 16),
                            TextField(
                              decoration: const InputDecoration(
                                labelText: 'Email',
                                hintText: 'Your email address',
                                prefixIcon: Icon(Icons.email_outlined),
                              ),
                              controller: TextEditingController(text: 'noor@example.com'),
                            ),
                            const SizedBox(height: 12),
                            TextField(
                              decoration: const InputDecoration(
                                labelText: 'Phone',
                                hintText: 'Your phone number',
                                prefixIcon: Icon(Icons.phone_outlined),
                              ),
                              controller: TextEditingController(text: '0770‑000‑0000'),
                            ),
                            const SizedBox(height: 12),
                            TextField(
                              decoration: const InputDecoration(
                                labelText: 'Address',
                                hintText: 'Your practice address',
                                prefixIcon: Icon(Icons.location_on_outlined),
                              ),
                              controller: TextEditingController(text: 'Basra, Iraq'),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                );
              }
            },
          ),
          
          const SizedBox(height: 24),
          
          // App settings
          Card(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        Icons.settings_outlined,
                        color: Theme.of(context).colorScheme.primary,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        'Application Settings',
                        style: Theme.of(context).textTheme.titleMedium!.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  
                  // Toggle switches
                  SwitchListTile(
                    title: const Text('Dark Mode'),
                    subtitle: const Text('Use dark theme for the application'),
                    value: false,
                    onChanged: (value) {},
                  ),
                  const Divider(),
                  SwitchListTile(
                    title: const Text('Notifications'),
                    subtitle: const Text('Enable push notifications'),
                    value: true,
                    onChanged: (value) {},
                  ),
                  const Divider(),
                  SwitchListTile(
                    title: const Text('Data Backup'),
                    subtitle: const Text('Automatically backup data to cloud'),
                    value: true,
                    onChanged: (value) {},
                  ),
                ],
              ),
            ),
          ),
          
          const SizedBox(height: 24),
          Center(
            child: FilledButton.icon(
              onPressed: () {
                _showSnackBar('Settings saved successfully');
              },
              icon: const Icon(Icons.save),
              label: const Text('Save All Settings'),
            ),
          ),
        ],
      ),
    );
  }

  /* -------------------- Build -------------------- */
  @override
  Widget build(BuildContext context) {
    final String pageTitle = () {
      switch (_page) {
        case AppPage.home:
          return 'Patients';
        case AppPage.dashboard:
          return 'Dashboard';
        case AppPage.drugs:
          return 'Medications';
        case AppPage.tests:
          return 'Lab Tests';
        case AppPage.settings:
          return 'Settings';
        case AppPage.patient:
          return _selectedPatient != null ? _selectedPatient!.name : 'Patient Details';
      }
    }();

    final List<NavigationRailDestination> destinations = [
      const NavigationRailDestination(
        icon: Icon(Icons.home_outlined),
        selectedIcon: Icon(Icons.home),
        label: Text('Home'),
      ),
      const NavigationRailDestination(
        icon: Icon(Icons.dashboard_outlined),
        selectedIcon: Icon(Icons.dashboard),
        label: Text('Dashboard'),
      ),
      const NavigationRailDestination(
        icon: Icon(Icons.medication_outlined),
        selectedIcon: Icon(Icons.medication),
        label: Text('Drugs'),
      ),
      const NavigationRailDestination(
        icon: Icon(Icons.science_outlined),
        selectedIcon: Icon(Icons.science),
        label: Text('Lab Tests'),
      ),
      const NavigationRailDestination(
        icon: Icon(Icons.settings_outlined),
        selectedIcon: Icon(Icons.settings),
        label: Text('Settings'),
      ),
    ];

    Widget body;
    switch (_page) {
      case AppPage.home:
        body = _buildHome();
        break;
      case AppPage.dashboard:
        body = _buildDashboard();
        break;
      case AppPage.drugs:
        body = _buildSimpleListPage(
          'Drugs', 
          _filteredDrugs, 
          _showAddDrugDialog,
        );
        break;
      case AppPage.tests:
        body = _buildSimpleListPage(
          'Lab Tests', 
          _filteredTests, 
          _showAddTestDialog,
        );
        break;
      case AppPage.settings:
        body = _buildSettings();
        break;
      case AppPage.patient:
        body = _selectedPatient != null 
            ? _buildPatientPage(_selectedPatient!)
            : const SizedBox();
        break;
    }

    // Check if we should show search on this page
    final bool canSearch = [AppPage.home, AppPage.drugs, AppPage.tests].contains(_page);

    return Scaffold(
      appBar: AppBar(
        leading: _page == AppPage.patient
            ? IconButton(
                icon: const Icon(Icons.arrow_back),
                onPressed: () => setState(() => _page = AppPage.home),
              )
            : null,
        title: _isSearching
            ? TextField(
                controller: _searchController,
                autofocus: true,
                decoration: InputDecoration(
                  hintText: 'Search ${pageTitle.toLowerCase()}...',
                  border: InputBorder.none,
                ),
                onChanged: _updateSearchQuery,
              )
            : Text(pageTitle),
        actions: [
          if (canSearch) ...[
            // Search button
            IconButton(
              icon: Icon(_isSearching ? Icons.close : Icons.search),
              onPressed: _isSearching ? _stopSearch : _startSearch,
              tooltip: _isSearching ? 'Clear search' : 'Search',
            ),
          ],
          
          // User account button
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 16),
            child: CircleAvatar(
              backgroundImage: NetworkImage('https://i.pravatar.cc/150?u=doctor'),
              radius: 18,
            ),
          ),
        ],
      ),
      body: Row(
        children: [
          // NavigationRail that expands on hover
          NavigationRail(
            selectedIndex: _page.index.clamp(0, 4),
            onDestinationSelected: (i) => setState(() {
              _page = AppPage.values[i];
              _stopSearch();
            }),
            extended: MediaQuery.of(context).size.width > 1000,
            labelType: NavigationRailLabelType.selected,
            useIndicator: true,
            destinations: destinations,
          ),
          const VerticalDivider(width: 1),
          Expanded(child: body),
        ],
      ),
      drawer: MediaQuery.of(context).size.width < 600
          ? Drawer(
              child: Column(
                children: [
                  UserAccountsDrawerHeader(
                    accountName: const Text('Dr. Noor Ahmed'),
                    accountEmail: const Text('noor@example.com'),
                    currentAccountPicture: const CircleAvatar(
                      backgroundImage: NetworkImage('https://i.pravatar.cc/150?u=doctor'),
                    ),
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.primary,
                    ),
                  ),
                  ...destinations.asMap().entries.map((entry) {
                    final i = entry.key;
                    final d = entry.value;
                    return ListTile(
                      leading: Icon(
                        Icons.circle,
                        color: _page.index == i
                            ? Theme.of(context).colorScheme.primary
                            : null,
                      ),
                      title: d.label,
                      selected: _page.index == i,
                      onTap: () {
                        setState(() => _page = AppPage.values[i]);
                        Navigator.pop(context);
                      },
                    );
                  }).toList(),
                ],
              ),
            )
          : null,
      floatingActionButton: _page == AppPage.patient && _selectedPatient != null
          ? FloatingActionButton.extended(
              onPressed: () => _showNewVisitDialog(_selectedPatient!),
              icon: const Icon(Icons.add),
              label: const Text('New Visit'),
            )
          : null,
    );
  }
}

/* ============================= Enhanced Widgets ============================= */

// Timeline widget for patient visits
class _VisitTimeline extends StatelessWidget {
  final List<Visit> visits;
  
  const _VisitTimeline({required this.visits});
  
  @override
  Widget build(BuildContext context) {
    final sortedVisits = [...visits]..sort((a, b) => b.date.compareTo(a.date));
    
    return ListView.builder(
      padding: const EdgeInsets.symmetric(vertical: 8),
      itemCount: sortedVisits.length,
      itemBuilder: (context, index) {
        final visit = sortedVisits[index];
        final isFirst = index == 0;
        final isLast = index == sortedVisits.length - 1;
        
        return IntrinsicHeight(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Timeline line and dot
              SizedBox(
                width: 60,
                child: Column(
                  children: [
                    // Line above
                    if (!isFirst)
                      Expanded(
                        flex: 1,
                        child: VerticalDivider(
                          color: Theme.of(context).colorScheme.primary.withOpacity(0.5),
                          thickness: 2,
                          width: 40,
                        ),
                      ),
                    
                    // Dot
                    Container(
                      width: 20,
                      height: 20,
                      decoration: BoxDecoration(
                        color: Theme.of(context).colorScheme.primary,
                        shape: BoxShape.circle,
                      ),
                    ),
                    
                    // Line below
                    if (!isLast)
                      Expanded(
                        flex: 3,
                        child: VerticalDivider(
                          color: Theme.of(context).colorScheme.primary.withOpacity(0.5),
                          thickness: 2,
                          width: 40,
                        ),
                      ),
                  ],
                ),
              ),
              
              // Date
              SizedBox(
                width: 100,
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        "${visit.date.month}/${visit.date.day}",
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                      Text(
                        "${visit.date.year}",
                        style: TextStyle(
                          color: Colors.grey.shade600,
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              
              // Visit content
              Expanded(
                child: Card(
                  margin: const EdgeInsets.only(right: 16, bottom: 16),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Vitals
                        Row(
                          children: [
                            Icon(
                              Icons.favorite_outline,
                              size: 14,
                              color: Theme.of(context).colorScheme.primary,
                            ),
                            const SizedBox(width: 4),
                            Text(
                              'Vitals:',
                              style: TextStyle(
                                fontWeight: FontWeight.bold,
                                color: Theme.of(context).colorScheme.primary,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 4),
                        Wrap(
                          spacing: 16,
                          children: [
                            Text('BP: ${visit.bloodPressureSystolic}/${visit.bloodPressureDiastolic}'),
                            Text('HR: ${visit.heartRate} bpm'),
                            Text('Temp: ${visit.temperature.toStringAsFixed(1)}°C'),
                          ],
                        ),
                        
                        if (visit.drugs.isNotEmpty) ...[
                          const Divider(),
                          Row(
                            children: [
                              Icon(
                                Icons.medication_outlined,
                                size: 14,
                                color: Colors.blue.shade700,
                              ),
                              const SizedBox(width: 4),
                              Text(
                                'Medications:',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: Colors.blue.shade700,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 4),
                          Wrap(
                            spacing: 8,
                            runSpacing: 4,
                            children: visit.drugs.map((drug) => Chip(
                              label: Text(drug, style: const TextStyle(fontSize: 12)),
                              backgroundColor: Colors.blue.shade50,
                              padding: EdgeInsets.zero,
                            )).toList(),
                          ),
                        ],
                        
                        if (visit.tests.isNotEmpty) ...[
                          const Divider(),
                          Row(
                            children: [
                              Icon(
                                Icons.science_outlined,
                                size: 14,
                                color: Colors.green.shade700,
                              ),
                              const SizedBox(width: 4),
                              Text(
                                'Lab Tests:',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: Colors.green.shade700,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 4),
                          Wrap(
                            spacing: 8,
                            runSpacing: 4,
                            children: visit.tests.map((test) => Chip(
                              label: Text(test, style: const TextStyle(fontSize: 12)),
                              backgroundColor: Colors.green.shade50,
                              padding: EdgeInsets.zero,
                            )).toList(),
                          ),
                        ],
                        
                        if (visit.notes.isNotEmpty) ...[
                          const Divider(),
                          Row(
                            children: [
                              Icon(
                                Icons.note_outlined,
                                size: 14,
                                color: Colors.orange.shade700,
                              ),
                              const SizedBox(width: 4),
                              Text(
                                'Notes:',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: Colors.orange.shade700,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 4),
                          Text(visit.notes),
                        ],
                        
                        if (visit.outcome.isNotEmpty) ...[
                          const Divider(),
                          Row(
                            children: [
                              Icon(
                                Icons.check_circle_outline,
                                size: 14,
                                color: Colors.purple.shade700,
                              ),
                              const SizedBox(width: 4),
                              Text(
                                'Outcome:',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: Colors.purple.shade700,
                                ),
                              ),
                              const SizedBox(width: 4),
                              Text(visit.outcome),
                            ],
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

// Visit card for mobile layout
class _VisitCard extends StatelessWidget {
  final Visit visit;
  
  const _VisitCard({required this.visit});
  
  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  Icons.event_outlined,
                  color: Theme.of(context).colorScheme.primary,
                ),
                const SizedBox(width: 8),
                Text(
                  "${visit.date.month}/${visit.date.day}/${visit.date.year}",
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: visit.outcome.isNotEmpty 
                        ? _getOutcomeColor(visit.outcome) 
                        : Colors.grey.shade200,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    visit.outcome.isNotEmpty ? visit.outcome : 'No outcome',
                    style: TextStyle(
                      fontSize: 12,
                      color: visit.outcome.isNotEmpty 
                          ? _getOutcomeColor(visit.outcome).shade800 
                          : Colors.grey.shade800,
                    ),
                  ),
                ),
              ],
            ),
            const Divider(),
            
            // Vitals
            Text(
              'Vitals',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: Theme.of(context).colorScheme.primary,
              ),
            ),
            const SizedBox(height: 4),
            Wrap(
              spacing: 16,
              children: [
                Text('BP: ${visit.bloodPressureSystolic}/${visit.bloodPressureDiastolic}'),
                Text('HR: ${visit.heartRate} bpm'),
                Text('Temp: ${visit.temperature.toStringAsFixed(1)}°C'),
              ],
            ),
            
            const SizedBox(height: 8),
            
            // Drugs and tests
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                ...visit.drugs.map((drug) => Chip(
                  avatar: const Icon(Icons.medication_outlined, size: 16),
                  label: Text(drug),
                  backgroundColor: Colors.blue.shade50,
                )),
                ...visit.tests.map((test) => Chip(
                  avatar: const Icon(Icons.science_outlined, size: 16),
                  label: Text(test),
                  backgroundColor: Colors.green.shade50,
                )),
              ],
            ),
            
            if (visit.notes.isNotEmpty) ...[
              const SizedBox(height: 8),
              const Divider(),
              const SizedBox(height: 8),
              Text(
                'Notes',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  color: Theme.of(context).colorScheme.secondary,
                ),
              ),
              const SizedBox(height: 4),
              Text(visit.notes),
            ],
          ],
        ),
      ),
    );
  }
  
  MaterialColor _getOutcomeColor(String outcome) {
    if (outcome.toLowerCase().contains('improved') || 
        outcome.toLowerCase().contains('stable')) {
      return Colors.green;
    } else if (outcome.toLowerCase().contains('follow-up') || 
               outcome.toLowerCase().contains('adjusted')) {
      return Colors.orange;
    } else if (outcome.toLowerCase().contains('critical') || 
               outcome.toLowerCase().contains('worsened')) {
      return Colors.red;
    }
    return Colors.blue;
  }
}

// Enhanced statistics card
class _StatCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String value;
  final MaterialColor color;
  final double width;
  
  const _StatCard({
    required this.icon,
    required this.title,
    required this.value,
    this.color = Colors.blue,
    this.width = double.infinity,
  });
  
  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: width,
      child: Card(
        elevation: 2,
        shadowColor: color.withOpacity(0.3),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Row(
            children: [
              Container(
                width: 60,
                height: 60,
                decoration: BoxDecoration(
                  color: color.shade50,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  icon,
                  color: color.shade700,
                  size: 30,
                ),
              ),
              const SizedBox(width: 20),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      color: Colors.grey.shade600,
                      fontSize: 14,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    value,
                    style: TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.bold,
                      color: color.shade700,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// Data visualization progress bar
class _ProgressBar extends StatelessWidget {
  final String label;
  final int value;
  final int maxValue;
  final Color color;
  final int rank;
  
  const _ProgressBar({
    required this.label,
    required this.value,
    required this.maxValue,
    required this.color,
    required this.rank,
  });
  
  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 24,
          height: 24,
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            shape: BoxShape.circle,
          ),
          child: Center(
            child: Text(
              '$rank',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: color,
                fontSize: 12,
              ),
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Flexible(
                    child: Text(
                      label,
                      style: const TextStyle(fontWeight: FontWeight.w500),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  Text(
                    '$value',
                    style: TextStyle(
                      color: color,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: value / maxValue,
                  backgroundColor: Colors.grey.shade200,
                  valueColor: AlwaysStoppedAnimation<Color>(color),
                  minHeight: 8,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

// Patient info item
class _PatientInfoItem extends StatelessWidget {
  final IconData icon;
  final String title;
  final String value;
  
  const _PatientInfoItem({
    required this.icon,
    required this.title,
    required this.value,
  });
  
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            icon,
            color: Theme.of(context).colorScheme.primary,
            size: 18,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey.shade600,
                  ),
                ),
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 14,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// Enhanced patient card for grid view
class _PatientCard extends StatelessWidget {
  final Patient patient;
  final VoidCallback onTap;
  
  const _PatientCard({
    required this.patient,
    required this.onTap,
  });
  
  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              CircleAvatar(
                backgroundImage: NetworkImage(patient.avatar),
                radius: 30,
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      patient.name,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      '${patient.gender} • ${patient.age} years',
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey.shade600,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Icon(
                          Icons.calendar_month_outlined,
                          size: 14,
                          color: Theme.of(context).colorScheme.primary,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          '${patient.visits.length} visits',
                          style: TextStyle(
                            fontSize: 14,
                            color: Theme.of(context).colorScheme.primary,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              if (patient.chronicConditions.isNotEmpty)
                Chip(
                  label: Text(
                    patient.chronicConditions.length > 1
                        ? '${patient.chronicConditions.length} conditions'
                        : patient.chronicConditions.first,
                    style: const TextStyle(fontSize: 12),
                  ),
                  backgroundColor: Colors.purple.shade50,
                ),
              const SizedBox(width: 8),
              const Icon(Icons.chevron_right),
            ],
          ),
        ),
      ),
    );
  }
}

// Patient list tile for mobile view
class _PatientListTile extends StatelessWidget {
  final Patient patient;
  final VoidCallback onTap;
  
  const _PatientListTile({
    required this.patient,
    required this.onTap,
  });
  
  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        onTap: onTap,
        leading: CircleAvatar(
          backgroundImage: NetworkImage(patient.avatar),
        ),
        title: Text(patient.name),
        subtitle: Text('${patient.gender} • ${patient.age} yrs • ${patient.visits.length} visits'),
        trailing: const Icon(Icons.chevron_right),
      ),
    );
  }
}

// Recent activity item
class _RecentActivityItem extends StatelessWidget {
  final DateTime date;
  final String patientName;
  final String patientAvatar;
  final String description;
  final VoidCallback onTap;
  
  const _RecentActivityItem({
    required this.date,
    required this.patientName,
    required this.patientAvatar,
    required this.description,
    required this.onTap,
  });
  
  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            CircleAvatar(
              backgroundImage: NetworkImage(patientAvatar),
              radius: 20,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(
                        patientName,
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const Spacer(),
                      Text(
                        "${date.month}/${date.day}/${date.year}",
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey.shade600,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    description,
                    style: TextStyle(
                      fontSize: 13,
                      color: Colors.grey.shade700,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// Empty state widget
class _EmptyStateWidget extends StatelessWidget {
  final IconData icon;
  final String title;
  final String description;
  final Widget? action;
  
  const _EmptyStateWidget({
    required this.icon,
    required this.title,
    required this.description,
    this.action,
  });
  
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            icon,
            size: 80,
            color: Colors.grey.shade400,
          ),
          const SizedBox(height: 16),
          Text(
            title,
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: Colors.grey.shade800,
            ),
          ),
          const SizedBox(height: 8),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 32),
            child: Text(
              description,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey.shade600,
              ),
            ),
          ),
          if (action != null) ...[
            const SizedBox(height: 24),
            action!,
          ],
        ],
      ),
    );
  }
}

/* -------------------- Form Widgets -------------------- */

// Patient form widget
class _PatientForm extends StatefulWidget {
  const _PatientForm({Key? key}) : super(key: key);

  @override
  _PatientFormState createState() => _PatientFormState();
  
  bool get isValid => true; // Simplified for demo
  
  Patient toPatient() {
    // Simplified for demo
    return Patient(
      id: DateTime.now().millisecondsSinceEpoch,
      name: 'New Patient',
      age: 30,
      gender: 'Male',
      phone: '0770-000-0000',
      avatar: 'https://i.pravatar.cc/150?u=${DateTime.now().millisecondsSinceEpoch}',
    );
  }
}

class _PatientFormState extends State<_PatientForm> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _ageController = TextEditingController();
  String _gender = 'Male';
  final _phoneController = TextEditingController();
  final _emailController = TextEditingController();
  final _addressController = TextEditingController();
  String _bloodType = bloodTypes.first;
  final List<String> _allergies = [];
  final List<String> _chronicConditions = [];

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: SingleChildScrollView(
        child: Column(
          children: [
            // Basic Info
            TextField(
              controller: _nameController,
              decoration: const InputDecoration(
                labelText: 'Full Name',
                prefixIcon: Icon(Icons.person),
              ),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _ageController,
                    decoration: const InputDecoration(
                      labelText: 'Age',
                      prefixIcon: Icon(Icons.calendar_today),
                    ),
                    keyboardType: TextInputType.number,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: DropdownButtonFormField<String>(
                    value: _gender,
                    decoration: const InputDecoration(
                      labelText: 'Gender',
                      prefixIcon: Icon(Icons.people),
                    ),
                    items: const [
                      DropdownMenuItem(value: 'Male', child: Text('Male')),
                      DropdownMenuItem(value: 'Female', child: Text('Female')),
                      DropdownMenuItem(value: 'Other', child: Text('Other')),
                    ],
                    onChanged: (value) {
                      if (value != null) {
                        setState(() {
                          _gender = value;
                        });
                      }
                    },
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _phoneController,
              decoration: const InputDecoration(
                labelText: 'Phone',
                prefixIcon: Icon(Icons.phone),
              ),
              keyboardType: TextInputType.phone,
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _emailController,
              decoration: const InputDecoration(
                labelText: 'Email (Optional)',
                prefixIcon: Icon(Icons.email),
              ),
              keyboardType: TextInputType.emailAddress,
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              value: _bloodType,
              decoration: const InputDecoration(
                labelText: 'Blood Type',
                prefixIcon: Icon(Icons.bloodtype),
              ),
              items: bloodTypes
                  .map((type) => DropdownMenuItem(value: type, child: Text(type)))
                  .toList(),
              onChanged: (value) {
                if (value != null) {
                  setState(() {
                    _bloodType = value;
                  });
                }
              },
            ),
          ],
        ),
      ),
    );
  }
}

// Visit form widget
class VisitForm extends StatefulWidget {
  final List<String> drugs;
  final List<String> tests;
  
  const VisitForm({Key? key, required this.drugs, required this.tests}) : super(key: key);

  @override
  VisitFormState createState() => VisitFormState();
  
  bool get isValid => true; // Simplified for demo
  
  Visit toVisit() {
    // Simplified for demo
    return Visit(
      id: DateTime.now().millisecondsSinceEpoch,
      date: DateTime.now(),
      drugs: const ['Paracetamol 500 mg'],
      tests: const ['Complete Blood Count (CBC)'],
      notes: 'Patient visit notes',
      outcome: 'Stable',
    );
  }
}

class VisitFormState extends State<VisitForm> {
  final _formKey = GlobalKey<FormState>();
  final _notesController = TextEditingController();
  final _outcomeController = TextEditingController();
  final _temperatureController = TextEditingController(text: '36.8');
  final _heartRateController = TextEditingController(text: '75');
  final _bpSystolicController = TextEditingController(text: '120');
  final _bpDiastolicController = TextEditingController(text: '80');
  
  DateTime _visitDate = DateTime.now();
  final Set<String> _selectedDrugs = {};
  final Set<String> _selectedTests = {};

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _formKey,
      child: SingleChildScrollView(
        child: Column(
          children: [
            // Date selection
            ListTile(
              title: const Text('Visit Date'),
              subtitle: Text('${_visitDate.month}/${_visitDate.day}/${_visitDate.year}'),
              trailing: IconButton(
                icon: const Icon(Icons.calendar_today),
                onPressed: () async {
                  final date = await showDatePicker(
                    context: context,
                    initialDate: _visitDate,
                    firstDate: DateTime(2000),
                    lastDate: DateTime(2100),
                  );
                  if (date != null) {
                    setState(() {
                      _visitDate = date;
                    });
                  }
                },
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Vital signs
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Vital Signs',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _temperatureController,
                            decoration: const InputDecoration(
                              labelText: 'Temperature (°C)',
                              prefixIcon: Icon(Icons.thermostat),
                            ),
                            keyboardType: TextInputType.number,
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: TextField(
                            controller: _heartRateController,
                            decoration: const InputDecoration(
                              labelText: 'Heart Rate (bpm)',
                              prefixIcon: Icon(Icons.favorite),
                            ),
                            keyboardType: TextInputType.number,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _bpSystolicController,
                            decoration: const InputDecoration(
                              labelText: 'Systolic (mmHg)',
                              prefixIcon: Icon(Icons.trending_up),
                            ),
                            keyboardType: TextInputType.number,
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: TextField(
                            controller: _bpDiastolicController,
                            decoration: const InputDecoration(
                              labelText: 'Diastolic (mmHg)',
                              prefixIcon: Icon(Icons.trending_down),
                            ),
                            keyboardType: TextInputType.number,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Medications
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Medications',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: widget.drugs.map((drug) => FilterChip(
                        label: Text(drug),
                        selected: _selectedDrugs.contains(drug),
                        onSelected: (selected) {
                          setState(() {
                            if (selected) {
                              _selectedDrugs.add(drug);
                            } else {
                              _selectedDrugs.remove(drug);
                            }
                          });
                        },
                      )).toList(),
                    ),
                  ],
                ),
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Lab tests
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Lab Tests',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: widget.tests.map((test) => FilterChip(
                        label: Text(test),
                        selected: _selectedTests.contains(test),
                        onSelected: (selected) {
                          setState(() {
                            if (selected) {
                              _selectedTests.add(test);
                            } else {
                              _selectedTests.remove(test);
                            }
                          });
                        },
                      )).toList(),
                    ),
                  ],
                ),
              ),
            ),
            
            const SizedBox(height: 16),
            
            // Notes and outcome
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Notes & Outcome',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: _notesController,
                      decoration: const InputDecoration(
                        labelText: 'Clinical Notes',
                        hintText: 'Enter observations, findings, etc.',
                      ),
                      maxLines: 3,
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: _outcomeController,
                      decoration: const InputDecoration(
                        labelText: 'Visit Outcome',
                        hintText: 'e.g. Stable, Improved, Follow-up needed',
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}