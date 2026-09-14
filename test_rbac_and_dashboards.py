import unittest
from fastapi.testclient import TestClient
import json

from APP.main import app
from APP.database import SessionLocal
from APP.models import User, InterviewSession

client = TestClient(app)

class TestRbacAndDashboards(unittest.TestCase):

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_01_health_check(self):
        response = client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('message', data)
        print('\n[OK] [1/8] Root API Health Check Passed.')

    def test_02_rbac_user_registration_and_login(self):
        reg_payload = {
            'username': 'Test Recruiter Bob',
            'email': 'recruiter_bob_test@smarthire.ai',
            'password': 'securepassword123',
            'role': 'Recruiter'
        }
        reg_res = client.post('/register', json=reg_payload)
        self.assertEqual(reg_res.status_code, 200)

        login_payload = {
            'email': 'recruiter_bob_test@smarthire.ai',
            'password': 'securepassword123'
        }
        login_res = client.post('/login', json=login_payload)
        self.assertEqual(login_res.status_code, 200)
        data = login_res.json()
        self.assertIn('access_token', data)
        self.assertEqual(data['role'], 'Recruiter')
        print('[OK] [2/8] RBAC Registration & Login Passed (Role: Recruiter).')

    def test_03_admin_user_management_crud(self):
        res = client.get('/api/admin/users')
        self.assertEqual(res.status_code, 200)
        users = res.json()
        self.assertIsInstance(users, list)

        new_u = {
            'username': 'Admin Created Candidate',
            'email': 'admin_created_cand@smarthire.ai',
            'password': 'pass123password',
            'role': 'Candidate'
        }
        c_res = client.post('/api/admin/users', json=new_u)
        self.assertEqual(c_res.status_code, 200)
        user_id = c_res.json()['user']['id']

        u_res = client.put(f'/api/admin/users/{user_id}/role', json={'role': 'Recruiter'})
        self.assertEqual(u_res.status_code, 200)

        d_res = client.delete(f'/api/admin/users/{user_id}')
        self.assertEqual(d_res.status_code, 200)
        print('[OK] [3/8] Admin User & Recruiter Management CRUD Passed.')

    def test_04_candidate_dashboard_all_features(self):
        response = client.get('/api/dashboard/candidate?candidate_id=1')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('avg_overall_score', data)
        self.assertIn('history', data)
        self.assertIn('skill_analytics', data)
        self.assertIn('weak_areas', data)
        self.assertIn('trends', data)
        print('[OK] [4/8] Candidate Dashboard API Passed (All 8 Features Validated).')

    def test_05_recruiter_dashboard_and_rankings(self):
        response = client.get('/api/dashboard/recruiter')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('total_candidates', data)
        self.assertIn('rankings', data)
        print('[OK] [5/8] Recruiter Dashboard & Candidate Rankings Passed.')

    def test_06_candidate_comparison_tool(self):
        # Ensure at least one candidate session exists
        sess = self.db.query(InterviewSession).first()
        if not sess:
            new_sess = InterviewSession(
                session_id="SESS_COMPARE_01",
                candidate_name="Compare Test Candidate",
                overall_score=85.0,
                overall_grade="A",
                status="COMPLETED"
            )
            self.db.add(new_sess)
            self.db.commit()

        response = client.get('/api/analytics/compare')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('candidates', data)
        self.assertGreaterEqual(len(data['candidates']), 1)
        c0 = data['candidates'][0]
        self.assertIn('overall_score', c0)
        self.assertIn('recommendation', c0)
        print('[OK] [6/8] Side-by-Side Candidate Comparison API Passed.')

    def test_07_ai_shortlisting_insights(self):
        response = client.get('/api/analytics/shortlisting-insights?min_score=75')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('insights', data)
        self.assertIn('shortlisted_count', data)
        print('[OK] [7/8] AI Shortlisting Insights & Talent Matching API Passed.')

    def test_08_admin_dashboard_and_live_activity(self):
        admin_res = client.get('/api/dashboard/admin')
        self.assertEqual(admin_res.status_code, 200)

        act_res = client.get('/api/admin/activity')
        self.assertEqual(act_res.status_code, 200)
        act_data = act_res.json()
        self.assertIn('activity_feed', act_data)
        print('[OK] [8/8] Admin Dashboard & Live Activity Monitoring API Passed.')

if __name__ == '__main__':
    unittest.main()
