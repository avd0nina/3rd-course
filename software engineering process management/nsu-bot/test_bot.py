import unittest
import json
from datetime import datetime, date
from unittest.mock import patch
from controllers import (
    GroupController, ScheduleController, HomeworkController, 
    QueueController, NotificationController
)
from storage import (
    GroupStorage, ScheduleStorage, HomeworkStorage,
    QueueStorage, NotificationStorage, DiffStorage, EventStorage, LogStorage
)
from nsu_integration import NSUIntegrationService, ParsedScheduleEntry
from database import get_db, ScheduleEntry, ScheduleDiff, ScheduleUpdatedEvent, EventLog, Student, Group, GroupChatMembership
from notifier import EventPublisher, Notifier
from analytics import AnalyticsTracker

class TestGroupController(unittest.TestCase):
    def setUp(self):
        """
        Clean E4 test data before every TestGroupController test.
        This makes auto-invite tests repeatable after multiple local runs.
        """
        db = get_db()
        try:
            e4_user_ids = [55551, 55552, 55553, 55554, 55555]

            db.query(GroupChatMembership).filter(
                GroupChatMembership.user_id.in_(e4_user_ids)
            ).delete(synchronize_session=False)

            db.query(Student).filter(
                Student.user_id.in_(e4_user_ids)
            ).delete(synchronize_session=False)

            db.query(Group).filter(
                Group.number.like("%E4-TEST%")
            ).delete(synchronize_session=False)

            db.commit()
        finally:
            db.close()
    def test_connect_student_to_group(self):
        user_id = 12345
        group_number = "CS-101"
        result = GroupController.connect_student_to_group(user_id, group_number)
        self.assertTrue(result, "Failed to connect student to group")
    
    def test_create_academic_group_default_type(self):
        """Test that default group type is 'academic'"""
        group = GroupStorage.create_group_if_not_exists("TEST-ACADEMIC-001")
        self.assertEqual(group.group_type, "academic", "Default group type should be 'academic'")
    
    def test_create_subject_chat_group(self):
        """Test creating a group with 'subject_chat' type"""
        group = GroupStorage.create_group_if_not_exists("TEST-CHAT-001", group_type="subject_chat")
        self.assertEqual(group.group_type, "subject_chat", "Group type should be 'subject_chat'")
    
    def test_get_groups_by_type(self):
        """Test filtering groups by type"""
        GroupStorage.create_group_if_not_exists("TEST-ACADEMIC-002", group_type="academic")
        GroupStorage.create_group_if_not_exists("TEST-CHAT-002", group_type="subject_chat")
        GroupStorage.create_group_if_not_exists("TEST-CHAT-003", group_type="subject_chat")
        
        academic_groups = GroupStorage.get_groups_by_type("academic")
        chat_groups = GroupStorage.get_groups_by_type("subject_chat")
        
        # Check that chat_groups contains both subject_chat groups we created
        chat_numbers = [g.number for g in chat_groups if g.number.startswith("TEST-CHAT-")]
        self.assertGreaterEqual(len(chat_numbers), 2, "Should have at least 2 subject_chat groups")

    def test_link_telegram_chat_to_subject_group(self):
        """E3: Test linking Telegram chat to subject_chat group"""
        # Create a subject_chat group
        subject_group = GroupStorage.create_group_if_not_exists("E3-TEST-MATH", group_type="subject_chat")
        
        # Link Telegram chat
        result = GroupController.link_telegram_chat_to_subject_group(subject_group.id, "-1001234567890")
        
        # Verify result
        self.assertEqual(result["status"], "success", "Link should succeed")
        self.assertIn("Telegram-чат привязан", result["message"], "Message should confirm linking")
        
        # Verify chat ID was saved
        updated_group = GroupStorage.get_group_by_id(subject_group.id)
        self.assertEqual(updated_group.telegram_chat_id, "-1001234567890", "Chat ID should be saved")

    def test_link_telegram_chat_fails_for_academic_group(self):
        """E3: Test that linking chat fails for academic group"""
        # Create an academic group
        academic_group = GroupStorage.create_group_if_not_exists("E3-TEST-ACADEMIC")
        
        # Try to link Telegram chat (should fail)
        result = GroupController.link_telegram_chat_to_subject_group(academic_group.id, "-1001234567890")
        
        # Verify error
        self.assertEqual(result["status"], "error", "Should fail for academic group")
        self.assertIn("не является чатом", result["message"], "Should indicate wrong group type")

    def test_get_user_subject_chats(self):
        """E3/E7: Test getting subject chats for user"""
        user_id = 99999
        GroupController.connect_student_to_group(user_id, "TEST-E3")
        
        # Get user's group and create subject chats
        user_group = GroupStorage.get_student_group(user_id)
        subject_group1 = GroupStorage.create_group_if_not_exists(f"[{user_group.number}] Mathematics", group_type="subject_chat")
        subject_group2 = GroupStorage.create_group_if_not_exists(f"[{user_group.number}] Physics", group_type="subject_chat")
        
        # Link one chat
        GroupController.link_telegram_chat_to_subject_group(subject_group1.id, "-1001111111111")
        
        # Get user's chats
        result = GroupController.get_user_subject_chats(user_id)
        
        # Verify
        self.assertEqual(result["status"], "success", "Should succeed")
        chats = result["chats"]
        self.assertGreaterEqual(len(chats), 2, "Should have at least 2 subject chats")
        
        # Check that one has telegram and one doesn't
        chat_with_telegram = [c for c in chats if c["has_telegram"]]
        chat_without_telegram = [c for c in chats if not c["has_telegram"]]
        self.assertGreaterEqual(len(chat_with_telegram), 1, "Should have at least 1 chat with telegram")
        self.assertGreaterEqual(len(chat_without_telegram), 1, "Should have at least 1 chat without telegram")

    def test_auto_invite_group_members_to_chat(self):
        """E4: Test auto-inviting group members to a subject chat"""
        # Create academic group with multiple members
        academic_user1 = 55551
        academic_user2 = 55552
        academic_user3 = 55553
        
        GroupController.connect_student_to_group(academic_user1, "E4-TEST-GROUP")
        GroupController.connect_student_to_group(academic_user2, "E4-TEST-GROUP")
        GroupController.connect_student_to_group(academic_user3, "E4-TEST-GROUP")
        
        # Get the academic group
        academic_group = GroupStorage.get_student_group(academic_user1)
        
        # Create and link subject_chat
        subject_chat = GroupStorage.create_group_if_not_exists(f"[{academic_group.number}] Physics", group_type="subject_chat")
        GroupController.link_telegram_chat_to_subject_group(subject_chat.id, "-999888777666")
        
        # Auto-invite members
        result = GroupController.auto_invite_group_members_to_chat(academic_group.id, subject_chat.id)
        
        # Verify
        self.assertEqual(result["status"], "success", "Should succeed")
        self.assertEqual(result["invited_count"], 3, "Should invite 3 members")
        
        # Verify memberships were saved
        members = GroupStorage.get_chat_members(subject_chat.id)
        self.assertEqual(len(members), 3, "Should have 3 members in chat")
        self.assertIn(academic_user1, members)
        self.assertIn(academic_user2, members)
        self.assertIn(academic_user3, members)

    def test_auto_invite_no_duplicates(self):
        """E4: Test that auto-invite doesn't add duplicates"""
        user_id = 55554
        GroupController.connect_student_to_group(user_id, "E4-TEST-DUP")
        academic_group = GroupStorage.get_student_group(user_id)
        
        # Create and link chat
        chat = GroupStorage.create_group_if_not_exists(f"[{academic_group.number}] Math", group_type="subject_chat")
        GroupController.link_telegram_chat_to_subject_group(chat.id, "-111222333444")
        
        # Invite once
        result1 = GroupController.auto_invite_group_members_to_chat(academic_group.id, chat.id)
        invited_first = result1["invited_count"]
        
        # Invite again (should not add duplicates)
        result2 = GroupController.auto_invite_group_members_to_chat(academic_group.id, chat.id)
        invited_second = result2["invited_count"]
        
        # Second invite should be 0
        self.assertEqual(invited_second, 0, "Second invite should not add duplicates")
        
        # Total members should be same
        members = GroupStorage.get_chat_members(chat.id)
        self.assertEqual(len(members), invited_first, "Should not create duplicates")

    def test_auto_invite_all_subject_chats(self):
        """E4: Test inviting members to all subject chats"""
        user_id = 55555
        GroupController.connect_student_to_group(user_id, "E4-TEST-ALL")
        academic_group = GroupStorage.get_student_group(user_id)
        
        # Create multiple subject chats
        chat1 = GroupStorage.create_group_if_not_exists(f"[{academic_group.number}] Biology", group_type="subject_chat")
        chat2 = GroupStorage.create_group_if_not_exists(f"[{academic_group.number}] Chemistry", group_type="subject_chat")
        GroupController.link_telegram_chat_to_subject_group(chat1.id, "-333444555666")
        GroupController.link_telegram_chat_to_subject_group(chat2.id, "-777888999000")
        
        # Auto-invite to all
        result = GroupController.auto_invite_all_subject_chats(academic_group.id)
        
        # Verify
        self.assertEqual(result["status"], "success", "Should succeed")
        self.assertEqual(result["chats_processed"], 2, "Should process 2 chats")
        self.assertEqual(result["total_invited"], 2, "Should invite 1 member to 2 chats")

    def test_create_subject_chat_allowed(self):
        """E5: Test creating subject chat when user has permission"""
        user_id = 65551
        GroupController.connect_student_to_group(user_id, "E5-TEST-CREATE")
        academic_group = GroupStorage.get_student_group(user_id)
        
        # Create subject chat (should succeed)
        result = GroupController.create_subject_chat(user_id, "Mathematics", academic_group.id)
        
        # Verify
        self.assertEqual(result["status"], "success", "Should succeed")
        self.assertIn("chat", result)
        self.assertEqual(result["chat"]["type"], "subject_chat")
        
        # Verify creator was recorded
        creator = GroupStorage.get_group_creator(result["chat"]["id"])
        self.assertEqual(creator, user_id)

    def test_create_subject_chat_denied_not_in_group(self):
        """E5: Test creating subject chat fails if user not in group"""
        user_id = 65552
        academic_group_id = 99999  # Non-existent group
        
        # Try to create chat
        result = GroupController.create_subject_chat(user_id, "Physics", academic_group_id)
        
        # Verify denied
        self.assertEqual(result["status"], "error")
        self.assertIn("не состоит в группе", result["message"].lower())

    def test_create_subject_chat_denied_wrong_group(self):
        """E5: Test creating chat for wrong group fails"""
        user_id1 = 65553
        user_id2 = 65554
        
        GroupController.connect_student_to_group(user_id1, "E5-TEST-GROUP1")
        GroupController.connect_student_to_group(user_id2, "E5-TEST-GROUP2")
        
        group1 = GroupStorage.get_student_group(user_id1)
        group2 = GroupStorage.get_student_group(user_id2)
        
        # User1 tries to create chat for group2 (should fail)
        result = GroupController.create_subject_chat(user_id1, "Chemistry", group2.id)
        
        # Verify denied
        self.assertEqual(result["status"], "error")
        self.assertIn("своей группы", result["message"].lower())

    def test_archive_subject_chat_allowed(self):
        """E5: Test archiving subject chat when user is creator"""
        user_id = 65555
        GroupController.connect_student_to_group(user_id, "E5-TEST-ARCHIVE")
        academic_group = GroupStorage.get_student_group(user_id)
        
        # Create chat
        create_result = GroupController.create_subject_chat(user_id, "History", academic_group.id)
        chat_id = create_result["chat"]["id"]
        
        # Archive it
        result = GroupController.archive_subject_chat(user_id, chat_id)
        
        # Verify
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["chat"]["status"], "archived")
        
        # Verify status in database
        status = GroupStorage.get_group_status(chat_id)
        self.assertEqual(status, "archived")

    def test_archive_subject_chat_denied_not_creator(self):
        """E5: Test archiving fails if user is not creator"""
        creator_id = 65556
        other_user_id = 65557
        
        GroupController.connect_student_to_group(creator_id, "E5-TEST-ARCHIVE2")
        GroupController.connect_student_to_group(other_user_id, "E5-TEST-ARCHIVE2")
        
        academic_group = GroupStorage.get_student_group(creator_id)
        
        # Creator creates chat
        create_result = GroupController.create_subject_chat(creator_id, "Geography", academic_group.id)
        chat_id = create_result["chat"]["id"]
        
        # Other user tries to archive (should fail)
        result = GroupController.archive_subject_chat(other_user_id, chat_id)
        
        # Verify denied
        self.assertEqual(result["status"], "error")
        self.assertIn("создатель", result["message"].lower())

    def test_unarchive_subject_chat_allowed(self):
        """E5: Test restoring archived chat when user is creator"""
        user_id = 65558
        GroupController.connect_student_to_group(user_id, "E5-TEST-UNARCHIVE")
        academic_group = GroupStorage.get_student_group(user_id)
        
        # Create and archive
        create_result = GroupController.create_subject_chat(user_id, "Art", academic_group.id)
        chat_id = create_result["chat"]["id"]
        GroupController.archive_subject_chat(user_id, chat_id)
        
        # Restore it
        result = GroupController.unarchive_subject_chat(user_id, chat_id)
        
        # Verify
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["chat"]["status"], "active")
        
        # Verify status in database
        status = GroupStorage.get_group_status(chat_id)
        self.assertEqual(status, "active")

    def test_verify_subject_chat_access_all_actions(self):
        """E5: Test verificator for all access actions"""
        user_id = 65559
        GroupController.connect_student_to_group(user_id, "E5-TEST-VERIFY")
        academic_group = GroupStorage.get_student_group(user_id)
        
        create_result = GroupController.create_subject_chat(user_id, "Music", academic_group.id)
        chat_id = create_result["chat"]["id"]
        
        # Test view access
        view_result = GroupController.verify_subject_chat_access(user_id, chat_id, "view")
        self.assertEqual(view_result["status"], "allowed")
        
        # Test archive access
        archive_result = GroupController.verify_subject_chat_access(user_id, chat_id, "archive")
        self.assertEqual(archive_result["status"], "allowed")

    def test_create_subject_chat_name_formatting(self):
        """E5: Test that subject chat names are formatted correctly"""
        user_id = 65560
        GroupController.connect_student_to_group(user_id, "E5-TEST-FORMAT")
        academic_group = GroupStorage.get_student_group(user_id)
        
        # Create chat
        result = GroupController.create_subject_chat(user_id, "English Literature", academic_group.id)
        
        # Verify name format
        expected_name = f"[{academic_group.number}] English Literature"
        self.assertEqual(result["chat"]["name"], expected_name)

class TestScheduleController(unittest.TestCase):
    def setUp(self):
        self.user_id = 12346
        # Ensure user is in a group
        GroupController.connect_student_to_group(self.user_id, "CS-102")
        entries = ScheduleController.get_schedule_entries(self.user_id)
        for entry in entries:
            ScheduleController.delete_schedule_entry(self.user_id, entry.id)
    
    def test_create_schedule_entry(self):
        result = ScheduleController.create_schedule_entry(
            self.user_id, 
            "Monday",
            "Math",
            "09:00-11:00"
        )
        self.assertEqual(result['status'], 'success', "Failed to create schedule entry")
    
    def test_get_schedule_entries(self):
        ScheduleController.create_schedule_entry(
            self.user_id,
            "Tuesday",
            "Physics",
            "10:00-12:00"
        )
        entries = ScheduleController.get_schedule_entries(self.user_id)
        self.assertGreater(len(entries), 0, "No schedule entries found")
    
    def test_display_schedule(self):
        ScheduleController.create_schedule_entry(
            self.user_id,
            "Wednesday",
            "Chemistry",
            "14:00-16:00"
        )
        display = ScheduleController.display_schedule(self.user_id)
        self.assertIn("расписание", display.lower(), "Schedule display failed")

    def test_update_schedule_entry(self):
        created = ScheduleController.create_schedule_entry(
            self.user_id,
            "Thursday",
            "Biology",
            "10:00-11:30"
        )
        entry_id = created["entry"].id
        updated = ScheduleController.update_schedule_entry(
            self.user_id,
            entry_id,
            {"subject": "Advanced Biology", "start_time": "10:30", "end_time": "12:00"}
        )
        self.assertTrue(updated, "Failed to update schedule entry")

        entries = ScheduleController.get_schedule_entries(self.user_id, "Thursday")
        self.assertEqual(entries[0].subject, "Advanced Biology")
        self.assertEqual(entries[0].start_time, "10:30")
        self.assertEqual(entries[0].end_time, "12:00")

    def test_delete_schedule_entry(self):
        created = ScheduleController.create_schedule_entry(
            self.user_id,
            "Friday",
            "Programming",
            "12:00-13:30"
        )
        entry_id = created["entry"].id
        deleted = ScheduleController.delete_schedule_entry(self.user_id, entry_id)
        self.assertTrue(deleted, "Failed to delete schedule entry")
        self.assertEqual(ScheduleController.get_schedule_entries(self.user_id, "Friday"), [])
    
    def test_auto_generate_subject_groups_from_schedule(self):
        """E2: Test automatic generation of subject_chat groups from schedule"""
        # Create schedule entries with different subjects
        ScheduleController.create_schedule_entry(self.user_id, "Monday", "Mathematics", "09:00-11:00")
        ScheduleController.create_schedule_entry(self.user_id, "Tuesday", "Physics", "10:00-12:00")
        ScheduleController.create_schedule_entry(self.user_id, "Wednesday", "Mathematics", "14:00-16:00")
        
        # Get the user's group
        user_group = GroupStorage.get_student_group(self.user_id)
        self.assertIsNotNone(user_group, "User should be in a group")
        
        # Call auto-generate method
        result = ScheduleController.auto_generate_subject_groups_from_schedule(
            self.user_id, 
            user_group.id, 
            user_group.number
        )
        
        # Verify result
        self.assertEqual(result["status"], "success", "Auto-generate should succeed")
        self.assertEqual(result["created_count"], 2, "Should create 2 subject groups (Math, Physics)")
        
        # Verify groups were created with correct type
        subject_chat_groups = GroupStorage.get_groups_by_type("subject_chat")
        created_group_numbers = [g.number for g in subject_chat_groups if g.number.startswith(f"[{user_group.number}]")]
        self.assertGreaterEqual(len(created_group_numbers), 2, "Should have created at least 2 subject_chat groups")
        
        # Verify groups have subject_chat type
        for group in subject_chat_groups:
            if group.number.startswith(f"[{user_group.number}]"):
                self.assertEqual(group.group_type, "subject_chat", f"Group {group.number} should be subject_chat type")

class TestHomeworkController(unittest.TestCase):
    def setUp(self):
        self.user_id = 12347
        GroupController.connect_student_to_group(self.user_id, "CS-103")
    
    def test_write_down_homework(self):
        result = HomeworkController.write_down_homework(
            self.user_id,
            "Math",
            "Solve equations from chapter 5",
            "2025-01-20"
        )
        self.assertEqual(result['status'], 'success', "Failed to write homework")
    
    def test_get_active_tasks(self):
        HomeworkController.write_down_homework(
            self.user_id,
            "Physics",
            "Lab report on optics",
            "2025-01-25"
        )
        tasks = HomeworkController.get_active_tasks(self.user_id)
        self.assertGreater(len(tasks), 0, "No active tasks found")
    
    def test_mark_as_completed(self):
        result = HomeworkController.write_down_homework(
            self.user_id,
            "Chemistry",
            "Read chapter 10",
            "2025-01-22"
        )
        if result['status'] == 'success':
            task_id = result['task'].id
            completed = HomeworkController.mark_homework_as_completed(self.user_id, task_id)
            self.assertTrue(completed, "Failed to mark homework as completed")

class TestQueueController(unittest.TestCase):
    def test_get_available_subjects(self):
        subjects = QueueController.get_available_subjects("2025-01-15")
        # Should return empty list or list of subjects
        self.assertIsInstance(subjects, list, "Failed to get available subjects")
    
    def test_take_place_in_queue(self):
        user_id = 12348
        result = QueueController.take_place_in_queue(user_id, "2025-01-15", "Math")
        # Result should have status key
        self.assertIn('status', result, "Queue result missing status")

class TestNotificationController(unittest.TestCase):
    def setUp(self):
        self.user_id = 12349
    
    def test_get_notification_settings(self):
        settings = NotificationController.get_notification_settings(self.user_id)
        self.assertIn('enabled', settings, "Settings missing 'enabled' field")
        self.assertIn('reminder_hours', settings, "Settings missing 'reminder_hours' field")
    
    def test_update_notification_settings(self):
        result = NotificationController.update_notification_settings(
            self.user_id,
            True,
            24
        )
        self.assertTrue(result, "Failed to update notification settings")
    
    def test_queue_notification_settings(self):
        settings = NotificationController.get_queue_notification_settings(self.user_id)
        self.assertIn('enabled', settings, "Queue settings missing 'enabled' field")

class TestStorageLayer(unittest.TestCase):
    def test_group_storage(self):
        group = GroupStorage.create_group_if_not_exists("CS-104")
        self.assertIsNotNone(group, "Failed to create group")
        self.assertEqual(group.number, "CS-104", "Group number mismatch")
    
    def test_schedule_storage(self):
        user_id = 12350
        GroupController.connect_student_to_group(user_id, "CS-105")
        entry = ScheduleStorage.save_schedule_entry(
            user_id, 1, "Thursday", "History", "08:00", "09:30"
        )
        self.assertIsNotNone(entry, "Failed to save schedule entry")
        self.assertEqual(entry.subject, "History", "Subject mismatch")
    
    def test_homework_storage(self):
        user_id = 12351
        GroupController.connect_student_to_group(user_id, "CS-106")
        group = GroupStorage.get_student_group(user_id)
        task = HomeworkStorage.create_homework_task(
            user_id, group.id, "English", "Write essay", "2025-02-01"
        )
        self.assertIsNotNone(task, "Failed to create homework task")
        self.assertEqual(task.subject, "English", "Subject mismatch")

class TestNSUIntegration(unittest.TestCase):
    def test_fit_groups_parser_filters_only_bachelor_groups(self):
        faculty_html = """
        <html>
            <body>
                <a class="group" href="/group/25201">25201</a>
                <a class="group" href="/group/25216">25216</a>
                <a class="group" href="/group/25221">25221</a>
                <a class="group" href="/group/22215">22215</a>
                <a class="group" href="/group/24226">24226</a>
            </body>
        </html>
        """
        service = NSUIntegrationService(fetcher=lambda _: faculty_html)
        groups = service.get_fit_groups()

        self.assertIn("25201", groups)
        self.assertIn("25216", groups)
        self.assertIn("22215", groups)
        self.assertNotIn("25221", groups)
        self.assertNotIn("24226", groups)

    def test_group_schedule_parser_extracts_lessons(self):
        schedule_html = """
        <html>
            <body>
                <table class="time-table">
                    <tr>
                        <th>Время</th>
                        <th>Понедельник</th>
                        <th>Вторник</th>
                        <th>Среда</th>
                        <th>Четверг</th>
                        <th>Пятница</th>
                        <th>Суббота</th>
                    </tr>
                    <tr>
                        <td>9:00</td>
                        <td>
                            <div class="cell">
                                <span class="type">лек</span>
                                <div class="subject" title="Математический анализ">Мат.анализ</div>
                                <div class="room">Ауд. 211 КПА</div>
                                <a class="tutor">Терсенов А.С.</a>
                            </div>
                        </td>
                        <td></td><td></td><td></td><td></td><td></td>
                    </tr>
                    <tr>
                        <td>16:20</td>
                        <td></td><td></td><td></td><td></td><td></td>
                        <td>
                            <div class="cell">
                                <span class="type">ф, лаб</span>
                                <div class="subject" title="Алгоритмы и структура данных">Алг.и структ.дан.</div>
                                <div class="room">Ауд. Google Meet</div>
                                <a class="tutor">Исаченко В..</a>
                                <div class="week">Нечетная</div>
                            </div>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
        """
        service = NSUIntegrationService(fetcher=lambda _: schedule_html)
        lessons = service.get_group_schedule("25201")

        self.assertEqual(len(lessons), 2)
        self.assertEqual(lessons[0].day_of_week, "Понедельник")
        self.assertEqual(lessons[0].start_time, "09:00")
        self.assertEqual(lessons[0].end_time, "10:35")
        self.assertEqual(lessons[0].subject, "Математический анализ")
        self.assertEqual(lessons[0].room, "211 КПА")
        self.assertEqual(lessons[0].group_number, "25201")
        self.assertEqual(lessons[0].discipline_key, "математическийанализ")
        self.assertEqual(lessons[1].teacher, "Исаченко В.")
        self.assertEqual(lessons[1].week, "Нечетная")

    def test_entity_normalization(self):
        service = NSUIntegrationService(fetcher=lambda _: "")
        group = service.normalize_group_entity(" 23-202 ")
        discipline = service.normalize_discipline_entity("Мат.анализ")
        teacher = service.normalize_teacher_entity("Исаченко В..")
        room = service.normalize_room_entity("Ауд. 211 КПА")

        self.assertEqual(group.normalized, "23202")
        self.assertEqual(group.key, "23202")
        self.assertEqual(discipline.normalized, "Математический анализ")
        self.assertEqual(teacher.normalized, "Исаченко В.")
        self.assertEqual(room.normalized, "211 КПА")

class TestGroupControllerNSUSync(unittest.TestCase):
    def test_connect_student_to_group_with_details_syncs_nsu_schedule(self):
        class FakeNSUService:
            def get_fit_groups(self):
                return ["25201"]

            def get_group_schedule(self, group_number):
                return [
                    ParsedScheduleEntry(
                        day_of_week="Понедельник",
                        start_time="09:00",
                        end_time="10:35",
                        subject="Математический анализ",
                        lesson_type="лек",
                        teacher="Терсенов А.С.",
                        room="Ауд. 211 КПА",
                        week="",
                    )
                ]

        user_id = 12352
        result = GroupController.connect_student_to_group_with_details(
            user_id=user_id,
            group_number="25201",
            integration_service=FakeNSUService(),
        )
        self.assertEqual(result["status"], "success")

        entries = ScheduleController.get_schedule_entries(user_id)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].day_of_week, "Понедельник")
        self.assertIn("Математический анализ", entries[0].subject)

    def test_display_nsu_schedule_groups_lessons_by_day(self):
        class FakeNSUService:
            def get_group_schedule(self, group_number):
                return [
                    ParsedScheduleEntry(
                        day_of_week="Вторник",
                        start_time="12:40",
                        end_time="14:15",
                        subject="Физика",
                        lesson_type="лек",
                        teacher="Иванов И.И.",
                        room="101",
                        week="",
                    ),
                    ParsedScheduleEntry(
                        day_of_week="Понедельник",
                        start_time="09:00",
                        end_time="10:35",
                        subject="Математика",
                        lesson_type="прак",
                        teacher="Петров П.П.",
                        room="202",
                        week="",
                    ),
                ]

        user_id = 12354
        group = GroupStorage.create_group_if_not_exists("25201")
        GroupStorage.add_student_to_group(user_id, group.id)

        message = ScheduleController.display_nsu_schedule(user_id, integration_service=FakeNSUService())
        self.assertIn("📚 Расписание группы 25201", message)
        self.assertLess(message.index("📅 Понедельник"), message.index("📅 Вторник"))
        self.assertIn("Математика", message)
        self.assertIn("Физика", message)

    def test_display_nsu_schedule_includes_manual_entries(self):
        class FakeNSUService:
            def get_group_schedule(self, group_number):
                return []

        user_id = 12355
        group = GroupStorage.create_group_if_not_exists("25202")
        GroupStorage.add_student_to_group(user_id, group.id)
        ScheduleController.create_schedule_entry(user_id, "Понедельник", "Химия", "15:00-16:30")

        message = ScheduleController.display_nsu_schedule(user_id, integration_service=FakeNSUService())
        self.assertIn("Химия", message)
        self.assertIn("Понедельник", message)

    def test_display_schedule_changes_formats_diff_card(self):
        changes = [
            {
                "change_type": "added",
                "subject": "Математика",
                "day": "Понедельник",
                "time": "09:00-10:35",
                "details": "Новая пара",
            },
            {
                "change_type": "removed",
                "subject": "Физика",
                "day": "Вторник",
                "time": "12:40-14:15",
                "details": "Пара отменена",
            },
        ]

        with patch.object(ScheduleController, "get_schedule_changes", return_value=changes):
            message = ScheduleController.display_schedule_changes(12356)

        self.assertIn("🗂 Что изменилось в расписании", message)
        self.assertIn("➕ Добавлено", message)
        self.assertIn("➖ Удалено", message)
        self.assertIn("Понедельник", message)
        self.assertIn("Физика", message)

    def test_connect_student_to_group_with_details_rejects_unknown_nsu_group(self):
        class FakeNSUService:
            def get_fit_groups(self):
                return ["25201"]

            def get_group_schedule(self, group_number):
                return []

        user_id = 12353
        result = GroupController.connect_student_to_group_with_details(
            user_id=user_id,
            group_number="25299",
            integration_service=FakeNSUService(),
        )
        self.assertEqual(result["status"], "error")
        self.assertFalse(GroupStorage.is_student_in_any_group(user_id))

class TestSnapshotStorage(unittest.TestCase):
    """Tests for A3: Snapshot storage for schedule tracking"""
    
    def setUp(self):
        self.user_id = 54321
        GroupController.connect_student_to_group(self.user_id, "CS-103")
        self.group = GroupStorage.get_student_group(self.user_id)
        # Clean up any previous test data
        db = get_db()
        db.query(ScheduleEntry).filter(ScheduleEntry.user_id == self.user_id).delete()
        db.commit()
        db.close()
    
    def test_promote_current_to_previous_snapshot(self):
        """Test that current snapshot can be promoted to previous"""
        entries = [
            {
                "day_of_week": "Monday",
                "subject": "Math 101",
                "start_time": "09:00",
                "end_time": "10:35",
            },
            {
                "day_of_week": "Tuesday",
                "subject": "Physics 101",
                "start_time": "10:50",
                "end_time": "12:25",
            },
        ]
        
        # Save initial schedule as current
        ScheduleStorage.replace_schedule_entries_for_user(self.user_id, self.group.id, entries)
        
        # Verify all entries are marked as current
        current_entries = ScheduleStorage.get_schedule_entries_by_snapshot(self.user_id, "current")
        self.assertEqual(len(current_entries), 2)
        
        # Promote current to previous
        promoted_count = ScheduleStorage.promote_current_to_previous_for_user(self.user_id)
        self.assertEqual(promoted_count, 2)
        
        # Verify entries are now marked as previous
        previous_entries = ScheduleStorage.get_schedule_entries_by_snapshot(self.user_id, "previous")
        self.assertEqual(len(previous_entries), 2)
        
        # Verify no entries are marked as current
        current_entries = ScheduleStorage.get_schedule_entries_by_snapshot(self.user_id, "current")
        self.assertEqual(len(current_entries), 0)
    
    def test_snapshot_version_tracking_on_sync(self):
        """Test that snapshot versions are properly maintained during sync"""
        # First sync: load initial schedule
        entries_v1 = [
            {
                "day_of_week": "Monday",
                "subject": "Math 101",
                "start_time": "09:00",
                "end_time": "10:35",
            },
        ]
        ScheduleStorage.replace_schedule_entries_for_user(self.user_id, self.group.id, entries_v1)
        
        current_v1 = ScheduleStorage.get_schedule_entries_by_snapshot(self.user_id, "current")
        self.assertEqual(len(current_v1), 1)
        self.assertEqual(current_v1[0].subject, "Math 101")
        
        # Second sync: promote v1 to previous, add new entries
        promoted = ScheduleStorage.promote_current_to_previous_for_user(self.user_id)
        self.assertEqual(promoted, 1)
        
        entries_v2 = [
            {
                "day_of_week": "Monday",
                "subject": "Math 102 (Updated room)",
                "start_time": "09:00",
                "end_time": "10:35",
            },
            {
                "day_of_week": "Wednesday",
                "subject": "Physics 101",
                "start_time": "14:30",
                "end_time": "16:05",
            },
        ]
        ScheduleStorage.replace_schedule_entries_for_user(self.user_id, self.group.id, entries_v2)
        
        # Verify: v1 is in previous, v2 is in current
        previous = ScheduleStorage.get_schedule_entries_by_snapshot(self.user_id, "previous")
        current = ScheduleStorage.get_schedule_entries_by_snapshot(self.user_id, "current")
        
        self.assertEqual(len(previous), 1)
        self.assertEqual(previous[0].subject, "Math 101")
        
        self.assertEqual(len(current), 2)
        subjects = {e.subject for e in current}
        self.assertIn("Math 102 (Updated room)", subjects)
        self.assertIn("Physics 101", subjects)
    
    def test_get_previous_snapshot_for_diff(self):
        """Test retrieving previous snapshot for diff calculation"""
        entries = [
            {
                "day_of_week": "Monday",
                "subject": "Test Subject",
                "start_time": "09:00",
                "end_time": "10:35",
            },
        ]
        ScheduleStorage.replace_schedule_entries_for_user(self.user_id, self.group.id, entries)
        ScheduleStorage.promote_current_to_previous_for_user(self.user_id)
        
        previous = ScheduleStorage.get_previous_snapshot_for_user(self.user_id)
        self.assertEqual(len(previous), 1)
        self.assertEqual(previous[0].subject, "Test Subject")

class TestSnapshotComparison(unittest.TestCase):
    """Tests for snapshot comparison (A3/A4 integration)"""
    
    def test_compare_snapshots_detects_added_lessons(self):
        """Test detection of added lessons"""
        current = [
            ParsedScheduleEntry(
                day_of_week="Monday",
                start_time="09:00",
                end_time="10:35",
                subject="Math",
                lesson_type="лек",
                teacher="Prof. Smith",
                room="211",
                week="",
                group_number="25201",
                discipline_raw="Мат.",
                discipline_key="mathematika",
                teacher_raw="Prof. Smith",
                teacher_key="prof.smith",
                room_raw="211",
                room_key="211",
                group_key="25201",
            ),
            ParsedScheduleEntry(
                day_of_week="Tuesday",
                start_time="10:50",
                end_time="12:25",
                subject="Physics",
                lesson_type="пр",
                teacher="Prof. Jones",
                room="312",
                week="",
                group_number="25201",
                discipline_raw="Физ.",
                discipline_key="physika",
                teacher_raw="Prof. Jones",
                teacher_key="prof.jones",
                room_raw="312",
                room_key="312",
                group_key="25201",
            ),
        ]
        
        previous = [
            ParsedScheduleEntry(
                day_of_week="Monday",
                start_time="09:00",
                end_time="10:35",
                subject="Math",
                lesson_type="лек",
                teacher="Prof. Smith",
                room="211",
                week="",
                group_number="25201",
                discipline_raw="Мат.",
                discipline_key="mathematika",
                teacher_raw="Prof. Smith",
                teacher_key="prof.smith",
                room_raw="211",
                room_key="211",
                group_key="25201",
            ),
        ]
        
        comparison = NSUIntegrationService.compare_snapshots(current, previous)
        
        self.assertTrue(comparison['has_changes'])
        self.assertEqual(len(comparison['added']), 1)
        self.assertEqual(comparison['added'][0].subject, "Physics")
        self.assertEqual(len(comparison['removed']), 0)

    def test_compare_snapshots_detects_transfer_as_removed_and_added(self):
        previous = [
            ParsedScheduleEntry(
                day_of_week="Monday",
                start_time="09:00",
                end_time="10:35",
                subject="Math",
                lesson_type="лек",
                teacher="Prof. Smith",
                room="211",
                week="",
                group_number="25201",
                discipline_raw="Math",
                discipline_key="math",
                teacher_raw="Prof. Smith",
                teacher_key="prof.smith",
                room_raw="211",
                room_key="211",
                group_key="25201",
            )
        ]
        current = [
            ParsedScheduleEntry(
                day_of_week="Tuesday",
                start_time="10:50",
                end_time="12:25",
                subject="Math",
                lesson_type="лек",
                teacher="Prof. Smith",
                room="211",
                week="",
                group_number="25201",
                discipline_raw="Math",
                discipline_key="math",
                teacher_raw="Prof. Smith",
                teacher_key="prof.smith",
                room_raw="211",
                room_key="211",
                group_key="25201",
            )
        ]

        comparison = NSUIntegrationService.compare_snapshots(current, previous)
        self.assertEqual(len(comparison["added"]), 1)
        self.assertEqual(len(comparison["removed"]), 1)
        self.assertEqual(len(comparison["modified"]), 0)

    def test_compare_snapshots_detects_cancellation(self):
        previous = [
            ParsedScheduleEntry(
                day_of_week="Wednesday",
                start_time="12:40",
                end_time="14:15",
                subject="Physics",
                lesson_type="прак",
                teacher="Prof. Jones",
                room="312",
                week="",
                group_number="25201",
                discipline_raw="Physics",
                discipline_key="physics",
                teacher_raw="Prof. Jones",
                teacher_key="prof.jones",
                room_raw="312",
                room_key="312",
                group_key="25201",
            )
        ]

        comparison = NSUIntegrationService.compare_snapshots([], previous)
        self.assertEqual(len(comparison["added"]), 0)
        self.assertEqual(len(comparison["removed"]), 1)
        self.assertFalse(comparison["modified"])

    def test_compare_snapshots_detects_room_change_as_modified(self):
        previous = [
            ParsedScheduleEntry(
                day_of_week="Friday",
                start_time="14:30",
                end_time="16:05",
                subject="Algorithms (лек; Prof. Smith; 211)",
                lesson_type="лек",
                teacher="Prof. Smith",
                room="211",
                week="",
                group_number="25201",
                discipline_raw="Algorithms",
                discipline_key="algorithms",
                teacher_raw="Prof. Smith",
                teacher_key="prof.smith",
                room_raw="211",
                room_key="211",
                group_key="25201",
            )
        ]
        current = [
            ParsedScheduleEntry(
                day_of_week="Friday",
                start_time="14:30",
                end_time="16:05",
                subject="Algorithms (лек; Prof. Smith; 212)",
                lesson_type="лек",
                teacher="Prof. Smith",
                room="212",
                week="",
                group_number="25201",
                discipline_raw="Algorithms",
                discipline_key="algorithms",
                teacher_raw="Prof. Smith",
                teacher_key="prof.smith",
                room_raw="212",
                room_key="212",
                group_key="25201",
            )
        ]

        comparison = NSUIntegrationService.compare_snapshots(current, previous)
        self.assertEqual(len(comparison["added"]), 0)
        self.assertEqual(len(comparison["removed"]), 0)
        self.assertEqual(len(comparison["modified"]), 1)

class TestDiffCalculation(unittest.TestCase):
    """Tests for A4: Diff calculation between snapshots"""
    
    def setUp(self):
        self.user_id = 65432
        GroupController.connect_student_to_group(self.user_id, "CS-104")
        self.group = GroupStorage.get_student_group(self.user_id)
        # Clean up any previous test data
        db = get_db()
        db.query(ScheduleEntry).filter(ScheduleEntry.user_id == self.user_id).delete()
        db.query(ScheduleDiff).filter(ScheduleDiff.user_id == self.user_id).delete()
        db.commit()
        db.close()
    
    def test_detect_added_lessons(self):
        """Test detection of added lessons"""
        # Create previous snapshot with one lesson
        prev_entries = [
            {
                "day_of_week": "Monday",
                "subject": "Math",
                "start_time": "09:00",
                "end_time": "10:35",
            },
        ]
        ScheduleStorage.replace_schedule_entries_for_user(self.user_id, self.group.id, prev_entries)
        ScheduleStorage.promote_current_to_previous_for_user(self.user_id)
        
        # Create current snapshot with two lessons (one added)
        current_entries = [
            {
                "day_of_week": "Monday",
                "subject": "Math",
                "start_time": "09:00",
                "end_time": "10:35",
            },
            {
                "day_of_week": "Tuesday",
                "subject": "Physics",
                "start_time": "10:50",
                "end_time": "12:25",
            },
        ]
        ScheduleStorage.replace_schedule_entries_for_user(self.user_id, self.group.id, current_entries)
        
        # Calculate diff
        result = ScheduleController.calculate_diff_on_sync(self.user_id, self.group.id)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['changes']['added']), 1)
        self.assertEqual(result['changes']['added'][0]['subject'], 'Physics')
        self.assertEqual(len(result['changes']['removed']), 0)
    
    def test_detect_removed_lessons(self):
        """Test detection of removed lessons"""
        # Create previous snapshot with two lessons
        prev_entries = [
            {
                "day_of_week": "Monday",
                "subject": "Math",
                "start_time": "09:00",
                "end_time": "10:35",
            },
            {
                "day_of_week": "Tuesday",
                "subject": "Physics",
                "start_time": "10:50",
                "end_time": "12:25",
            },
        ]
        ScheduleStorage.replace_schedule_entries_for_user(self.user_id, self.group.id, prev_entries)
        ScheduleStorage.promote_current_to_previous_for_user(self.user_id)
        
        # Create current snapshot with one lesson (one removed)
        current_entries = [
            {
                "day_of_week": "Monday",
                "subject": "Math",
                "start_time": "09:00",
                "end_time": "10:35",
            },
        ]
        ScheduleStorage.replace_schedule_entries_for_user(self.user_id, self.group.id, current_entries)
        
        # Calculate diff
        result = ScheduleController.calculate_diff_on_sync(self.user_id, self.group.id)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['changes']['removed']), 1)
        self.assertEqual(result['changes']['removed'][0]['subject'], 'Physics')
        self.assertEqual(len(result['changes']['added']), 0)
    
    def test_detect_modified_lessons(self):
        """Test detection of modified lessons (subject change)"""
        # Create previous snapshot
        prev_entries = [
            {
                "day_of_week": "Monday",
                "subject": "Math 101",
                "start_time": "09:00",
                "end_time": "10:35",
            },
        ]
        ScheduleStorage.replace_schedule_entries_for_user(self.user_id, self.group.id, prev_entries)
        ScheduleStorage.promote_current_to_previous_for_user(self.user_id)
        
        # Create current snapshot with modified subject
        current_entries = [
            {
                "day_of_week": "Monday",
                "subject": "Math 102",
                "start_time": "09:00",
                "end_time": "10:35",
            },
        ]
        ScheduleStorage.replace_schedule_entries_for_user(self.user_id, self.group.id, current_entries)
        
        # Calculate diff
        result = ScheduleController.calculate_diff_on_sync(self.user_id, self.group.id)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['changes']['modified']), 1)
        self.assertEqual(result['changes']['modified'][0]['old'], 'Math 101')
        self.assertEqual(result['changes']['modified'][0]['new'], 'Math 102')
    
    def test_diff_saved_to_database(self):
        """Test that diff changes are saved to database"""
        # Create snapshots
        prev_entries = [
            {
                "day_of_week": "Monday",
                "subject": "Math",
                "start_time": "09:00",
                "end_time": "10:35",
            },
        ]
        ScheduleStorage.replace_schedule_entries_for_user(self.user_id, self.group.id, prev_entries)
        ScheduleStorage.promote_current_to_previous_for_user(self.user_id)
        
        current_entries = [
            {
                "day_of_week": "Tuesday",
                "subject": "Physics",
                "start_time": "10:50",
                "end_time": "12:25",
            },
        ]
        ScheduleStorage.replace_schedule_entries_for_user(self.user_id, self.group.id, current_entries)
        
        # Calculate diff
        result = ScheduleController.calculate_diff_on_sync(self.user_id, self.group.id)
        
        # Check that diffs are saved in database
        diffs = DiffStorage.get_schedule_diffs_for_user(self.user_id)
        self.assertEqual(len(diffs), 2)  # One added, one removed
        
        types = {diff.change_type for diff in diffs}
        self.assertIn('added', types)
        self.assertIn('removed', types)
    
    def test_get_schedule_changes_formatting(self):
        """Test that schedule changes are properly formatted for display"""
        # Create and calculate diff
        prev_entries = [
            {
                "day_of_week": "Monday",
                "subject": "Math",
                "start_time": "09:00",
                "end_time": "10:35",
            },
        ]
        ScheduleStorage.replace_schedule_entries_for_user(self.user_id, self.group.id, prev_entries)
        ScheduleStorage.promote_current_to_previous_for_user(self.user_id)
        
        current_entries = [
            {
                "day_of_week": "Tuesday",
                "subject": "Physics",
                "start_time": "10:50",
                "end_time": "12:25",
            },
        ]
        ScheduleStorage.replace_schedule_entries_for_user(self.user_id, self.group.id, current_entries)
        ScheduleController.calculate_diff_on_sync(self.user_id, self.group.id)
        
        # Get formatted changes
        changes = ScheduleController.get_schedule_changes(self.user_id)
        
        self.assertEqual(len(changes), 2)
        for change in changes:
            self.assertIn('change_type', change)
            self.assertIn('subject', change)
            self.assertIn('day', change)


class TestEventPublisher(unittest.TestCase):
    def setUp(self):
        self.user_id = 65433
        self.group_id = 1
        GroupController.connect_student_to_group(self.user_id, "CS-102")
        db = get_db()
        db.query(ScheduleUpdatedEvent).filter(ScheduleUpdatedEvent.user_id == self.user_id).delete()
        db.query(EventLog).delete()
        db.commit()
        db.close()
    
    def test_publish_schedule_updated_event(self):
        """Test publishing schedule_updated event"""
        changes = {
            'added': [{'subject': 'Алгоритмы', 'day': 'Понедельник', 'time': '09:00-11:00'}],
            'removed': [],
            'modified': []
        }
        result = EventPublisher.publish_schedule_updated(self.user_id, self.group_id, changes)
        self.assertEqual(result['status'], 'published')
        self.assertIn('event_id', result)
    
    def test_event_saved_to_database(self):
        """Test event is saved to database"""
        changes = {'added': [], 'removed': [], 'modified': []}
        EventPublisher.publish_schedule_updated(self.user_id, self.group_id, changes)
        
        events = EventStorage.get_events_for_user(self.user_id)
        self.assertGreater(len(events), 0)
        self.assertEqual(events[0].user_id, self.user_id)
        self.assertEqual(events[0].event_type, 'schedule_updated')
    
    def test_mark_event_processed(self):
        """Test marking event as processed"""
        result = EventPublisher.publish_schedule_updated(self.user_id, self.group_id, {})
        event_id = result['event_id']
        
        success = EventStorage.mark_event_processed(event_id)
        self.assertTrue(success)
        
        db = get_db()
        event = db.query(ScheduleUpdatedEvent).filter(ScheduleUpdatedEvent.id == event_id).first()
        self.assertTrue(event.is_processed)
        db.close()

class TestGroupBroadcastQA(unittest.TestCase):
    """D8 / NSU-037: QA for group broadcast on a large group"""

    def setUp(self):
        self.creator_id = 37000
        self.group_number = "QA-BROADCAST-037"

        self.group = GroupStorage.create_group_if_not_exists(self.group_number)
        GroupStorage.add_student_to_group(self.creator_id, self.group.id)
        GroupStorage.save_group_creator(self.group.id, self.creator_id)

        self.member_ids = [37001 + i for i in range(50)]

        for user_id in self.member_ids:
            GroupStorage.add_student_to_group(user_id, self.group.id)

    def test_large_group_broadcast_delivery_log(self):
        """
        Проверяем общий сбор на большой группе:
        - рассылка не падает
        - есть delivery_log
        - количество доставленных совпадает с количеством участников
        - у каждой доставки есть user_id, status и delivered_at
        """
        result = GroupController.send_group_broadcast(
            user_id=self.creator_id,
            group_id=self.group.id,
            message="QA load test broadcast NSU-037"
        )

        self.assertEqual(result["status"], "success")
        self.assertIn("delivery_log", result)

        delivery_log = result["delivery_log"]

        self.assertIn("delivered", delivery_log)
        self.assertIn("failed", delivery_log)
        self.assertIn("delivered_count", delivery_log)
        self.assertIn("failed_count", delivery_log)

        expected_members_count = len(GroupStorage.get_group_members(self.group.id))

        self.assertEqual(delivery_log["delivered_count"], expected_members_count)
        self.assertEqual(delivery_log["failed_count"], 0)

        for delivery in delivery_log["delivered"]:
            self.assertIn("user_id", delivery)
            self.assertEqual(delivery["status"], "delivered")
            self.assertIn("delivered_at", delivery)

    def test_broadcast_history_after_large_group_broadcast(self):
        """
        Проверяем, что после рассылки можно получить историю общего сбора.
        """
        GroupController.send_group_broadcast(
            user_id=self.creator_id,
            group_id=self.group.id,
            message="QA history test broadcast NSU-037"
        )

        history_result = GroupController.get_broadcast_history(self.group.id)

        self.assertEqual(history_result["status"], "success")
        self.assertIn("history", history_result)
        self.assertGreater(history_result["history_count"], 0)

class TestSmartNotificationsQA(unittest.TestCase):
    """F9 / NSU-054: QA for notification priorities, digests, feed and analytics"""

    def setUp(self):
        self.user_id = 54054

        db = get_db()
        db.query(EventLog).filter(EventLog.user_id == self.user_id).delete()
        db.commit()
        db.close()

    def test_high_and_critical_notifications_are_sent_instantly(self):
        """
        Проверяем F3:
        critical/high должны отправляться сразу.
        """
        critical_result = Notifier.send_notification(
            user_id=self.user_id,
            event_type="qa_critical_event",
            message="Critical QA notification",
            priority="critical"
        )

        high_result = Notifier.send_notification(
            user_id=self.user_id,
            event_type="qa_high_event",
            message="High QA notification",
            priority="high"
        )

        self.assertEqual(critical_result["status"], "sent")
        self.assertEqual(critical_result["delivery_mode"], "instant")
        self.assertEqual(critical_result["priority"], "critical")

        self.assertEqual(high_result["status"], "sent")
        self.assertEqual(high_result["delivery_mode"], "instant")
        self.assertEqual(high_result["priority"], "high")

    def test_normal_and_low_notifications_go_to_digest(self):
        """
        Проверяем F4:
        normal/low должны попадать в дайджест.
        """
        normal_result = Notifier.send_notification(
            user_id=self.user_id,
            event_type="qa_normal_event",
            message="Normal QA notification",
            priority="normal"
        )

        low_result = Notifier.send_notification(
            user_id=self.user_id,
            event_type="qa_low_event",
            message="Low QA notification",
            priority="low"
        )

        self.assertEqual(normal_result["status"], "queued")
        self.assertEqual(normal_result["delivery_mode"], "digest")
        self.assertEqual(normal_result["priority"], "normal")

        self.assertEqual(low_result["status"], "queued")
        self.assertEqual(low_result["delivery_mode"], "digest")
        self.assertEqual(low_result["priority"], "low")

        digest_result = Notifier.send_batch_digest(user_id=self.user_id)

        self.assertEqual(digest_result["status"], "success")
        self.assertGreaterEqual(digest_result["digests_sent"], 1)
        self.assertGreaterEqual(digest_result["events_processed"], 2)

    def test_aggregated_feed_returns_queued_events(self):
        """
        Проверяем F7:
        агрегированная лента должна возвращать события пользователя.
        """
        Notifier.send_notification(
            user_id=self.user_id,
            event_type="schedule_updated",
            message="QA schedule feed event",
            priority="normal"
        )

        Notifier.send_notification(
            user_id=self.user_id,
            event_type="homework_deadline",
            message="QA homework feed event",
            priority="low"
        )

        feed_result = GroupController.get_aggregated_feed(
            user_id=self.user_id,
            limit=20,
            event_type_filter="all"
        )

        self.assertEqual(feed_result["status"], "success")
        self.assertEqual(feed_result["user_id"], self.user_id)
        self.assertGreaterEqual(feed_result["events_count"], 2)
        self.assertIsInstance(feed_result["feed"], list)

    def test_aggregated_feed_filters_by_event_type(self):
        """
        Проверяем F6/F7:
        фильтр schedule должен отдавать только события расписания.
        """
        Notifier.send_notification(
            user_id=self.user_id,
            event_type="schedule_updated",
            message="QA schedule filter event",
            priority="normal"
        )

        Notifier.send_notification(
            user_id=self.user_id,
            event_type="homework_deadline",
            message="QA homework filter event",
            priority="normal"
        )

        feed_result = GroupController.get_aggregated_feed(
            user_id=self.user_id,
            limit=20,
            event_type_filter="schedule"
        )

        self.assertEqual(feed_result["status"], "success")
        self.assertGreaterEqual(feed_result["events_count"], 1)

        for item in feed_result["feed"]:
            event_type = str(item.get("event_type", "")).lower()
            message = str(item.get("message", "")).lower()
            self.assertTrue(
                "schedule" in event_type or "распис" in message or "lesson" in event_type
            )

    def test_notification_analytics_open_and_click_metrics(self):
        """
        Проверяем F8:
        open/click метрики должны сохраняться и попадать в summary.
        """
        open_result = AnalyticsTracker.track_notification_metric(
            user_id=self.user_id,
            metric_type="open",
            notification_id=1,
            event_type="schedule_updated",
            target="feed"
        )

        click_result = AnalyticsTracker.track_notification_metric(
            user_id=self.user_id,
            metric_type="click",
            notification_id=1,
            event_type="schedule_updated",
            target="open_schedule"
        )

        self.assertEqual(open_result["status"], "success")
        self.assertEqual(click_result["status"], "success")

        summary = AnalyticsTracker.get_notification_metrics_summary(user_id=self.user_id)

        self.assertEqual(summary["status"], "success")
        self.assertGreaterEqual(summary["opens_count"], 1)
        self.assertGreaterEqual(summary["clicks_count"], 1)
        self.assertGreaterEqual(summary["ctr"], 0)
class TestGatewayFilters(unittest.TestCase):
    """Tests for A6: Gateway schedule filtering"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user_id = 99999
        self.group_id = 2
        
        # Clear previous test data
        db = get_db()
        db.query(ScheduleEntry).filter(ScheduleEntry.user_id == self.user_id).delete()
        db.query(Student).filter(Student.user_id == self.user_id).delete()
        db.commit()
        db.close()
        
        # Create test student and group
        group = GroupStorage.create_group_if_not_exists("99999")
        GroupStorage.add_student_to_group(self.user_id, group.id)
        
        # Add test schedule entries
        entries_data = [
            ("Monday", "Математика", "09:00", "10:30"),
            ("Monday", "Физика", "10:45", "12:15"),
            ("Wednesday", "Математика", "14:00", "15:30"),
            ("Friday", "Химия", "09:00", "10:30"),
        ]
        
        for day, subject, start, end in entries_data:
            ScheduleStorage.save_schedule_entry(
                self.user_id, group.id, day, subject, start, end, 'current'
            )
    
    def test_get_all_schedule(self):
        """Test getting all schedule without filters"""
        entries = ScheduleController.get_filtered_schedule(self.user_id)
        self.assertEqual(len(entries), 4)
    
    def test_filter_by_subject(self):
        """Test filtering schedule by subject"""
        filters = {"subject": "Математика"}
        entries = ScheduleController.get_filtered_schedule(self.user_id, filters)
        self.assertEqual(len(entries), 2)
        for entry in entries:
            self.assertIn("Математика", entry.subject)
    
    def test_filter_by_day(self):
        """Test filtering schedule by day of week"""
        filters = {"day_of_week": "Monday"}
        entries = ScheduleController.get_filtered_schedule(self.user_id, filters)
        self.assertEqual(len(entries), 2)
        for entry in entries:
            self.assertEqual(entry.day_of_week, "Monday")
    
    def test_filter_by_group_id(self):
        """Test filtering schedule by group_id"""
        group = GroupStorage.get_student_group(self.user_id)
        filters = {"group_id": group.id}
        entries = ScheduleController.get_filtered_schedule(self.user_id, filters)
        self.assertGreater(len(entries), 0)
        for entry in entries:
            self.assertEqual(entry.group_id, group.id)
    
    def test_combined_filters(self):
        """Test applying multiple filters at once"""
        filters = {
            "day_of_week": "Monday",
            "subject": "Математика"
        }
        entries = ScheduleController.get_filtered_schedule(self.user_id, filters)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].subject, "Математика")
        self.assertEqual(entries[0].day_of_week, "Monday")
    
    def tearDown(self):
        """Clean up test data"""
        db = get_db()
        db.query(ScheduleEntry).filter(ScheduleEntry.user_id == self.user_id).delete()
        db.query(Student).filter(Student.user_id == self.user_id).delete()
        db.query(Group).filter(Group.number == "99999").delete()
        db.commit()
        db.close()


def run_tests():

    """Run all tests and print results"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestGroupController))
    suite.addTests(loader.loadTestsFromTestCase(TestScheduleController))
    suite.addTests(loader.loadTestsFromTestCase(TestHomeworkController))
    suite.addTests(loader.loadTestsFromTestCase(TestQueueController))
    suite.addTests(loader.loadTestsFromTestCase(TestNotificationController))
    suite.addTests(loader.loadTestsFromTestCase(TestStorageLayer))
    suite.addTests(loader.loadTestsFromTestCase(TestNSUIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestGroupControllerNSUSync))
    suite.addTests(loader.loadTestsFromTestCase(TestSnapshotStorage))
    suite.addTests(loader.loadTestsFromTestCase(TestSnapshotComparison))
    suite.addTests(loader.loadTestsFromTestCase(TestDiffCalculation))
    suite.addTests(loader.loadTestsFromTestCase(TestEventPublisher))
    suite.addTests(loader.loadTestsFromTestCase(TestGroupBroadcastQA))
    suite.addTests(loader.loadTestsFromTestCase(TestSmartNotificationsQA))
    suite.addTests(loader.loadTestsFromTestCase(TestGatewayFilters))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    import sys
    sys.exit(run_tests())
