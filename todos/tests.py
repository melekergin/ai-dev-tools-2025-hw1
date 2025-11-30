from django.test import TestCase
from django.urls import reverse
from datetime import date

from .models import Todo


class TodoModelTests(TestCase):
    def test_create_todo_with_all_fields(self):
        due = date(2025, 1, 1)
        todo = Todo.objects.create(
            title="Test todo",
            description="Some description",
            due_date=due,
            is_completed=True,
        )
        self.assertEqual(todo.title, "Test todo")
        self.assertEqual(todo.description, "Some description")
        self.assertEqual(todo.due_date, due)
        self.assertTrue(todo.is_completed)

    def test_default_is_completed_is_false(self):
        todo = Todo.objects.create(title="Incomplete todo")
        self.assertFalse(todo.is_completed)

    def test_str_returns_title(self):
        todo = Todo.objects.create(title="Readable title")
        self.assertEqual(str(todo), "Readable title")


class TodoViewTests(TestCase):
    def setUp(self):
        # Create a sample todo we can use in several tests
        self.todo = Todo.objects.create(
            title="Existing todo",
            description="Existing description",
            due_date=date(2025, 1, 2),
            is_completed=False,
        )

    def test_todo_list_view_shows_todos(self):
        url = reverse("todo_list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "todos/todo_list.html")
        # The created todo should be in the context
        self.assertIn(self.todo, response.context["todos"])

    def test_todo_create_view_get(self):
        url = reverse("todo_create")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "todos/todo_form.html")
        self.assertIn("form", response.context)

    def test_todo_create_view_post_creates_todo(self):
        url = reverse("todo_create")
        data = {
            "title": "New todo",
            "description": "Created via POST",
            "due_date": "2025-01-03",
            "is_completed": False,
        }

        response = self.client.post(url, data)

        self.assertRedirects(response, reverse("todo_list"))
        self.assertTrue(Todo.objects.filter(title="New todo").exists())

    def test_todo_create_view_invalid_data_shows_errors(self):
        url = reverse("todo_create")
        response = self.client.post(url, {"description": "Missing title"})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "todos/todo_form.html")
        self.assertContains(response, "This field is required")
        self.assertEqual(Todo.objects.count(), 1)  # only the one from setUp

    def test_todo_update_view_updates_todo(self):
        url = reverse("todo_edit", args=[self.todo.pk])
        data = {
            "title": "Updated title",
            "description": "Updated description",
            "due_date": "2025-01-04",
            "is_completed": True,
        }

        response = self.client.post(url, data)

        self.assertRedirects(response, reverse("todo_list"))
        self.todo.refresh_from_db()
        self.assertEqual(self.todo.title, "Updated title")
        self.assertTrue(self.todo.is_completed)

    def test_todo_update_view_get_prefills_form(self):
        url = reverse("todo_edit", args=[self.todo.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "todos/todo_form.html")
        self.assertIn("form", response.context)
        self.assertEqual(response.context["form"].instance.pk, self.todo.pk)
        self.assertEqual(response.context["form"].initial["title"], self.todo.title)

    def test_todo_delete_view_deletes_todo(self):
        url = reverse("todo_delete", args=[self.todo.pk])

        response = self.client.post(url)

        self.assertRedirects(response, reverse("todo_list"))
        self.assertFalse(Todo.objects.filter(pk=self.todo.pk).exists())

    def test_todo_delete_view_get_shows_confirmation(self):
        url = reverse("todo_delete", args=[self.todo.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "todos/todo_confirm_delete.html")
        self.assertEqual(response.context["todo"], self.todo)

    def test_todo_list_orders_by_completion_and_due_date(self):
        later_incomplete = Todo.objects.create(
            title="Later incomplete",
            due_date=date(2025, 2, 1),
            is_completed=False,
        )
        completed = Todo.objects.create(
            title="Completed first?",
            due_date=date(2024, 12, 31),
            is_completed=True,
        )

        url = reverse("todo_list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        todos = list(response.context["todos"])
        self.assertEqual(todos, [self.todo, later_incomplete, completed])
