from django.test import TestCase, Client
from .models import UserData, Feedback, ToolResult
from django.contrib.auth.models import User
from django.urls import reverse
import json

class UserDataModelTest(TestCase):
     def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
    
     def test_user_data_creation(self):
        user_data = UserData.objects.create(
            user=self.user,
            goal=0,
            attackT=1,
            skill=2,
            automation=1,
            platform=0,
            suggest=0
        )
        self.assertEqual(user_data.goal, 0)
        self.assertEqual(user_data.get_goal_display(), 'Web-application')
        self.assertEqual(user_data.attackT, 1)
        self.assertEqual(user_data.get_attackT_display(), 'Stored')
        self.assertEqual(user_data.skill, 2)
        self.assertEqual(user_data.get_skill_display(), 'Advanced')
        self.assertEqual(user_data.automation, 1)
        self.assertEqual(user_data.get_automation_display(), 'Yes')
        self.assertEqual(user_data.platform, 0)
        self.assertEqual(user_data.get_platform_display(), 'Windows')
        print(f"Test Name: test_user_data_creation - OK")

class FeedbackModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.user_data = UserData.objects.create(
            user=self.user, goal=0, attackT=0, skill=1, automation=1, platform=1, suggest=1
        )

    def test_feedback_creation(self):
        feedback = Feedback.objects.create(user_data=self.user_data, agree=True, preferred_suggestion='Suggestion')
        self.assertTrue(feedback.agree)
        print(f"Test Name: test_feedback_creation - OK")

class ToolResultModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_tool_result_creation(self):
        tool_result = ToolResult.objects.create(user=self.user, tool_name='Nmap', target='localhost', result='Output')
        self.assertEqual(tool_result.tool_name, 'Nmap')
        self.assertEqual(tool_result.result, 'Output')
        print(f"Test Name: test_tool_result_creation - OK")
        
class NewDataIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')

    def test_new_data_submission(self):
        response = self.client.post(reverse('new_data'), {
            'goal': 0,
            'attackT': 1,
            'skill': 2,
            'automation': 1,
            'platform': 0
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(UserData.objects.filter(user=self.user).exists())
        print(f"Test Name: test_new_data_submission - OK")
        
    def test_new_data_integration(self):
        response = self.client.post('/new_data/', {
            'goal': '1',
            'attackT': '1',
            'skill': '0',
            'automation': '1',
            'platform': '0'
        })
        self.assertEqual(response.status_code, 302)
        user_data = UserData.objects.last()
        self.assertEqual(user_data.goal, 1)
        self.assertEqual(user_data.attackT, 1)
        self.assertEqual(user_data.skill, 0)
        self.assertEqual(user_data.automation, 1)
        self.assertEqual(user_data.platform, 0)
        print(f"Test Name: test_new_data_integration - OK")

    def test_nmap_tool_integration(self):
        response = self.client.post('/nmap_tool/', {'target': 'localhost'})
        self.assertEqual(response.status_code, 200)
        tool_result = ToolResult.objects.last()
        self.assertEqual(tool_result.tool_name, 'Nmap')
        print(f"Test Name: test_nmap_tool_integration - OK")
        
    def test_pwnxss_tool_integration(self):
        response = self.client.post('/run_pwnxss/', {'url': 'http://example.com'})
        self.assertEqual(response.status_code, 200)
        tool_result = ToolResult.objects.last()
        self.assertEqual(tool_result.tool_name, 'PwnXSS')
        self.assertIn('Checking connection to:', tool_result.result)
        print(f"Test Name: test_pwnxss_tool_integration - OK")

    def test_xsstrike_tool_integration(self):
        response = self.client.post('/run_xsstrike/', {'url': 'http://testphp.vulnweb.com'})
        self.assertEqual(response.status_code, 200)
        tool_result = ToolResult.objects.last()
        self.assertEqual(tool_result.tool_name, 'XSStrike')
        self.assertIn('Crawling the target', tool_result.result)
        print(f"Test Name: test_xsstrike_tool_integration - OK")

    def test_tool_results_integration(self):
        ToolResult.objects.create(user=self.user, tool_name='Nmap', target='localhost', result='Output')
        ToolResult.objects.create(user=self.user, tool_name='PwnXSS', target='http://example.com', result='Output')
        ToolResult.objects.create(user=self.user, tool_name='XSStrike', target='http://testphp.vulnweb.com', result='Output')
        response = self.client.get('/tool_results/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nmap')
        self.assertContains(response, 'PwnXSS')
        self.assertContains(response, 'XSStrike')
        print(f"Test Name: test_results_integration - OK")
        
class UserRegistrationTest(TestCase):
    def test_user_registration(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        print(f"Test Name: test_user_registration - OK")
        
class ViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.user_data = UserData.objects.create(
            user=self.user, goal=0, attackT=0, skill=1, automation=1, platform=1, suggest=1
        )

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'suggestxss/home.html')
        print(f"Test Name: test_home_view - OK")

    def test_login_view(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'suggestxss/login.html')
        print(f"Test Name: test_login_view - OK")

        # Test login functionality
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': '12345'
        })
        self.assertEqual(response.status_code, 302)  # Redirects after successful login
        print(f"Test Name: test_login_functionality - OK")

    def test_logout_view(self):
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)  # Redirects after logout
        print(f"Test Name: test_logout_view - OK")

    def test_dashboard_view(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'suggestxss/dashboard.html')
        print(f"Test Name: test_dashboard_view - OK")

    def test_new_data_view(self):
        response = self.client.get(reverse('new_data'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'suggestxss/new_data.html')
        print(f"Test Name: test_new_data_view - OK")

        # Test data submission
        response = self.client.post(reverse('new_data'), {
            'goal': 1,
            'attackT': 1,
            'skill': 1,
            'automation': 1,
            'platform': 1
        })
        self.assertEqual(response.status_code, 302)  # Redirects after successful submission
        self.assertTrue(UserData.objects.filter(user=self.user).exists())
        print(f"Test Name: test_new_data_submission - OK")

    def test_success_view(self):
        response = self.client.get(reverse('success'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'suggestxss/success.html')
        print(f"Test Name: test_success_view - OK")

    def test_tool_results_view(self):
        # Create some tool results for the user
        ToolResult.objects.create(user=self.user, tool_name='Nmap', target='localhost', result='Nmap output')
        ToolResult.objects.create(user=self.user, tool_name='PwnXSS', target='http://example.com', result='PwnXSS output')

        response = self.client.get(reverse('tool_results'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'suggestxss/tool_results.html')
        self.assertContains(response, 'Nmap')
        self.assertContains(response, 'PwnXSS')
        print(f"Test Name: test_tool_results_view - OK")

    def test_feedback_view(self):
        feedback_data = {
            'agree': True,
            'preferred_suggestion': 'Suggestion'
        }
        response = self.client.post(reverse('submit_feedback'), data=json.dumps(feedback_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Feedback.objects.filter(user_data=self.user_data, agree=True).exists())
        print(f"Test Name: test_feedback_view - OK")
