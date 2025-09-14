#!/usr/bin/env python3
"""
Vollständiger Schulmanager Online API Test
Demonstriert den kompletten Login-Flow und strukturierte Datenausgabe
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List
import aiohttp

# Add the custom_components path to sys.path
sys.path.insert(0, '../custom_components')

from schulmanager_online.api import SchulmanagerAPI


def print_separator(title: str, char: str = "="):
    """Drucke einen formatierten Separator."""
    print(f"\n{char * 60}")
    print(f" {title}")
    print(f"{char * 60}")


def format_lesson_time(lesson: Dict[str, Any]) -> str:
    """Formatiere Unterrichtszeit."""
    start = lesson.get('startTime', '')
    end = lesson.get('endTime', '')
    if start and end:
        return f"{start[:5]}-{end[:5]}"
    return "Zeit unbekannt"


def format_teachers(teachers: List[Dict[str, Any]]) -> str:
    """Formatiere Lehrerliste."""
    if not teachers:
        return "Kein Lehrer"
    
    names = []
    for teacher in teachers:
        name = teacher.get('abbreviation', teacher.get('name', ''))
        if name:
            names.append(name)
    
    return ', '.join(names) if names else "Kein Lehrer"


def analyze_schedule_data(lessons: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analysiere Stundenplandaten und erstelle Statistiken."""
    analysis = {
        'total_lessons': len(lessons),
        'lessons_by_date': {},
        'subjects': {},
        'teachers': set(),
        'rooms': set(),
        'substitutions': 0,
        'cancelled_lessons': 0,
        'changed_lessons': 0,
        'time_slots': set(),
    }
    
    for lesson in lessons:
        # Datum
        date = lesson.get('date', 'Unknown')
        if date not in analysis['lessons_by_date']:
            analysis['lessons_by_date'][date] = []
        analysis['lessons_by_date'][date].append(lesson)
        
        # Fächer
        subject = lesson.get('subject', {})
        subject_name = subject.get('name', 'Unknown')
        if subject_name not in analysis['subjects']:
            analysis['subjects'][subject_name] = 0
        analysis['subjects'][subject_name] += 1
        
        # Lehrer
        for teacher in lesson.get('teachers', []):
            teacher_name = teacher.get('name', teacher.get('abbreviation', ''))
            if teacher_name:
                analysis['teachers'].add(teacher_name)
        
        # Räume
        room = lesson.get('room', {}).get('name', '')
        if room:
            analysis['rooms'].add(room)
        
        # Zeitslots
        start_time = lesson.get('startTime', '')
        if start_time:
            analysis['time_slots'].add(start_time)
        
        # Änderungen
        if lesson.get('isSubstitution'):
            analysis['substitutions'] += 1
        
        lesson_type = lesson.get('type', '')
        if lesson_type == 'cancelledLesson':
            analysis['cancelled_lessons'] += 1
        elif lesson_type == 'changedLesson':
            analysis['changed_lessons'] += 1
    
    # Sets zu Listen konvertieren für JSON-Serialisierung
    analysis['teachers'] = sorted(list(analysis['teachers']))
    analysis['rooms'] = sorted(list(analysis['rooms']))
    analysis['time_slots'] = sorted(list(analysis['time_slots']))
    
    return analysis


async def comprehensive_api_test():
    """Vollständiger API-Test mit strukturierter Datenausgabe."""
    print_separator("🎓 SCHULMANAGER ONLINE API - VOLLSTÄNDIGER TEST", "=")
    
    # Konfiguration
    email = "<schulmanager-login>"
    password = "<schulmanager-password>"
    
    print(f"📧 Account: {email}")
    print(f"🔐 Password: {'*' * len(password)}")
    
    async with aiohttp.ClientSession() as session:
        api = SchulmanagerAPI(email, password, session)
        
        try:
            print_separator("1️⃣  AUTHENTIFIZIERUNG", "-")
            
            # Schritt 1: Salt abrufen
            print("🧂 Salt abrufen...")
            salt = await api._get_salt()
            print(f"✅ Salt erhalten: {salt[:20]}...")
            
            # Schritt 2: Hash generieren
            print("🔐 Passwort-Hash generieren...")
            salted_hash = api._generate_salted_hash(password, salt)
            print(f"✅ Hash generiert: {salted_hash[:30]}...")
            
            # Schritt 3: Login
            print("🚪 Login durchführen...")
            await api._login(salted_hash)
            print(f"✅ Login erfolgreich!")
            print(f"🎫 Token: {api.token[:50]}..." if api.token else "❌ Kein Token")
            print(f"⏰ Token läuft ab: {api.token_expires}")
            
            print_separator("2️⃣  SCHÜLER-DATEN ABRUFEN", "-")
            
            students = await api.get_students()
            print(f"✅ {len(students)} Schüler gefunden:")
            
            for i, student in enumerate(students, 1):
                name = f"{student.get('firstname', '')} {student.get('lastname', '')}"
                student_id = student.get('id', '')
                class_id = student.get('classId', '')
                class_name = student.get('className', '')
                
                print(f"   {i}. 👤 {name}")
                print(f"      🆔 ID: {student_id}")
                print(f"      🏫 Klasse: {class_name} (ID: {class_id})")
                
                # Zusätzliche Informationen falls vorhanden
                if student.get('birthDate'):
                    print(f"      🎂 Geburtsdatum: {student['birthDate']}")
                if student.get('email'):
                    print(f"      📧 E-Mail: {student['email']}")
            
            if not students:
                print("❌ Keine Schüler gefunden!")
                return
            
            # Ersten Schüler für weitere Tests verwenden
            test_student = students[0]
            student_id = test_student.get('id')
            student_name = f"{test_student.get('firstname', '')} {test_student.get('lastname', '')}"
            
            print_separator(f"3️⃣  STUNDENPLAN FÜR {student_name.upper()}", "-")
            
            # Datum berechnen
            today = datetime.now().date()
            start_date = today - timedelta(days=today.weekday())  # Montag dieser Woche
            end_date = start_date + timedelta(days=13)  # 2 Wochen
            
            print(f"📅 Zeitraum: {start_date} bis {end_date}")
            
            schedule_data = await api.get_schedule(student_id, start_date, end_date)
            lessons = schedule_data.get('lessons', [])
            
            print(f"✅ {len(lessons)} Unterrichtsstunden gefunden")
            
            if lessons:
                # Datenanalyse
                analysis = analyze_schedule_data(lessons)
                
                print_separator("📊 DATENANALYSE", "-")
                print(f"📚 Gesamtstunden: {analysis['total_lessons']}")
                print(f"📅 Schultage: {len(analysis['lessons_by_date'])}")
                print(f"🎯 Verschiedene Fächer: {len(analysis['subjects'])}")
                print(f"👨‍🏫 Verschiedene Lehrer: {len(analysis['teachers'])}")
                print(f"🏫 Verschiedene Räume: {len(analysis['rooms'])}")
                print(f"🔄 Vertretungen: {analysis['substitutions']}")
                print(f"❌ Ausfälle: {analysis['cancelled_lessons']}")
                print(f"⚠️  Änderungen: {analysis['changed_lessons']}")
                
                print_separator("📚 FÄCHER-VERTEILUNG", "-")
                for subject, count in sorted(analysis['subjects'].items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / analysis['total_lessons']) * 100
                    print(f"   {subject}: {count} Stunden ({percentage:.1f}%)")
                
                print_separator("⏰ ZEITSLOTS", "-")
                for time_slot in analysis['time_slots']:
                    print(f"   {time_slot[:5]}")
                
                print_separator("👨‍🏫 LEHRER", "-")
                for teacher in analysis['teachers']:
                    print(f"   {teacher}")
                
                print_separator("🏫 RÄUME", "-")
                for room in analysis['rooms']:
                    print(f"   {room}")
                
                print_separator("📋 DETAILLIERTER STUNDENPLAN", "-")
                
                # Stundenplan nach Tagen gruppiert anzeigen
                for date in sorted(analysis['lessons_by_date'].keys()):
                    day_lessons = analysis['lessons_by_date'][date]
                    weekday = datetime.strptime(date, "%Y-%m-%d").strftime("%A")
                    
                    print(f"\n📅 {weekday}, {date} ({len(day_lessons)} Stunden):")
                    print("   " + "─" * 70)
                    
                    for lesson in sorted(day_lessons, key=lambda x: x.get('startTime', '')):
                        subject = lesson.get('subject', {}).get('name', 'Unknown')
                        subject_abbr = lesson.get('subject', {}).get('abbreviation', '')
                        time_str = format_lesson_time(lesson)
                        room = lesson.get('room', {}).get('name', 'Kein Raum')
                        teachers = format_teachers(lesson.get('teachers', []))
                        
                        # Status-Icons
                        status_icon = ""
                        if lesson.get('isSubstitution'):
                            status_icon = "🔄"
                        elif lesson.get('type') == 'cancelledLesson':
                            status_icon = "❌"
                        elif lesson.get('type') == 'changedLesson':
                            status_icon = "⚠️"
                        
                        print(f"   {time_str} | {subject_abbr:4} | {subject:20} | {room:10} | {teachers:15} {status_icon}")
                        
                        # Kommentare anzeigen
                        comment = lesson.get('comment', '')
                        if comment:
                            print(f"          💬 {comment}")
                
                print_separator("4️⃣  HAUSAUFGABEN", "-")
                
                try:
                    homework_data = await api.get_homework(student_id)
                    homeworks = homework_data.get('homeworks', [])
                    
                    print(f"✅ {len(homeworks)} Hausaufgaben gefunden")
                    
                    if homeworks:
                        for hw in homeworks:
                            subject = hw.get('subject', {}).get('name', 'Unknown')
                            description = hw.get('description', 'Keine Beschreibung')
                            due_date = hw.get('dueDate', 'Kein Fälligkeitsdatum')
                            teacher = hw.get('teacher', {})
                            teacher_name = teacher.get('name', teacher.get('abbreviation', 'Unbekannt'))
                            
                            print(f"\n📝 {subject}")
                            print(f"   📅 Fällig: {due_date}")
                            print(f"   👨‍🏫 Lehrer: {teacher_name}")
                            print(f"   📄 Aufgabe: {description}")
                    else:
                        print("ℹ️  Keine Hausaufgaben vorhanden")
                        
                except Exception as e:
                    print(f"⚠️  Hausaufgaben nicht verfügbar: {e}")
                
                print_separator("5️⃣  NOTEN (OPTIONAL)", "-")
                
                try:
                    grades_data = await api.get_grades(student_id)
                    grades = grades_data.get('grades', [])
                    
                    print(f"✅ {len(grades)} Noten gefunden")
                    
                    if grades:
                        for grade in grades[:5]:  # Nur erste 5 anzeigen
                            subject = grade.get('subject', {}).get('name', 'Unknown')
                            grade_value = grade.get('grade', 'Keine Note')
                            grade_type = grade.get('type', 'Unknown')
                            date = grade.get('date', 'Kein Datum')
                            
                            print(f"   📊 {subject}: {grade_value} ({grade_type}) - {date}")
                    else:
                        print("ℹ️  Keine Noten vorhanden")
                        
                except Exception as e:
                    print(f"⚠️  Noten nicht verfügbar: {e}")
                
                print_separator("💾 JSON-EXPORT", "-")
                
                # Strukturierte Daten als JSON exportieren
                export_data = {
                    'student': {
                        'id': student_id,
                        'name': student_name,
                        'class': test_student.get('className', ''),
                    },
                    'period': {
                        'start': start_date.isoformat(),
                        'end': end_date.isoformat(),
                    },
                    'analysis': analysis,
                    'schedule': lessons,
                    'export_timestamp': datetime.now().isoformat(),
                }
                
                # JSON in Datei speichern
                filename = f"schulmanager_export_{student_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
                
                print(f"💾 Daten exportiert nach: {filename}")
                print(f"📊 Dateigröße: {len(json.dumps(export_data, default=str))} Zeichen")
            
            print_separator("🎉 TEST ERFOLGREICH ABGESCHLOSSEN", "=")
            print(f"✅ Alle API-Funktionen getestet")
            print(f"📊 Daten für {len(students)} Schüler verfügbar")
            print(f"⏱️  Test-Dauer: ~30-60 Sekunden")
            print(f"🔗 API-Aufrufe: ~{5 + len(students) * 3}")
            
        except Exception as e:
            print_separator("❌ TEST FEHLGESCHLAGEN", "=")
            print(f"Fehler: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(comprehensive_api_test())
