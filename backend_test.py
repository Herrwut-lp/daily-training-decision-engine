#!/usr/bin/env python3
"""
Backend API Testing for Daily Training Decision Engine
Tests all backend APIs with comprehensive scenarios
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List

# Backend URL from frontend .env
BACKEND_URL = "https://decide-fit.preview.emergentagent.com/api"

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.test_results = []
        self.session_id = None
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details
        })
        
    def test_get_exercises(self):
        """Test GET /api/exercises - Returns full exercise library"""
        try:
            response = self.session.get(f"{BACKEND_URL}/exercises")
            
            if response.status_code != 200:
                self.log_test("GET /api/exercises", False, f"Status: {response.status_code}")
                return False
                
            exercises = response.json()
            
            # Validate response structure
            if not isinstance(exercises, list):
                self.log_test("GET /api/exercises", False, "Response is not a list")
                return False
                
            if len(exercises) == 0:
                self.log_test("GET /api/exercises", False, "No exercises returned")
                return False
                
            # Check first exercise has required fields
            first_ex = exercises[0]
            required_fields = ['id', 'name', 'category', 'equipment']
            for field in required_fields:
                if field not in first_ex:
                    self.log_test("GET /api/exercises", False, f"Missing field: {field}")
                    return False
                    
            # Check categories exist
            categories = set(ex['category'] for ex in exercises)
            expected_categories = {'squat', 'hinge', 'push', 'pull', 'carry', 'crawl'}
            if not expected_categories.issubset(categories):
                missing = expected_categories - categories
                self.log_test("GET /api/exercises", False, f"Missing categories: {missing}")
                return False
                
            self.log_test("GET /api/exercises", True, f"Found {len(exercises)} exercises with {len(categories)} categories")
            return True
            
        except Exception as e:
            self.log_test("GET /api/exercises", False, f"Exception: {str(e)}")
            return False
            
    def test_get_state(self):
        """Test GET /api/state - Returns current user state"""
        try:
            response = self.session.get(f"{BACKEND_URL}/state")
            
            if response.status_code != 200:
                self.log_test("GET /api/state", False, f"Status: {response.status_code}")
                return False
                
            state = response.json()
            
            # Validate required fields
            required_fields = ['next_priority_bucket', 'week_mode', 'cooldown_counter', 'power_frequency']
            for field in required_fields:
                if field not in state:
                    self.log_test("GET /api/state", False, f"Missing field: {field}")
                    return False
                    
            # Validate values
            if state['next_priority_bucket'] not in ['squat', 'pull', 'hinge', 'push']:
                self.log_test("GET /api/state", False, f"Invalid priority bucket: {state['next_priority_bucket']}")
                return False
                
            if state['week_mode'] not in ['A', 'B']:
                self.log_test("GET /api/state", False, f"Invalid week mode: {state['week_mode']}")
                return False
                
            self.log_test("GET /api/state", True, f"Priority: {state['next_priority_bucket']}, Week: {state['week_mode']}, Cooldown: {state['cooldown_counter']}")
            return True
            
        except Exception as e:
            self.log_test("GET /api/state", False, f"Exception: {str(e)}")
            return False
            
    def test_generate_session_great_feeling(self):
        """Test POST /api/generate with great feeling - should be medium or hard"""
        try:
            payload = {
                "feeling": "great",
                "sleep": "good", 
                "pain": "none",
                "time_available": "30-45",
                "equipment": "minimal"
            }
            
            response = self.session.post(f"{BACKEND_URL}/generate", json=payload)
            
            if response.status_code != 200:
                self.log_test("Generate Session (Great Feeling)", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
            session = response.json()
            
            # Validate response structure
            required_fields = ['id', 'day_type', 'priority_bucket', 'exercises', 'equipment']
            for field in required_fields:
                if field not in session:
                    self.log_test("Generate Session (Great Feeling)", False, f"Missing field: {field}")
                    return False
                    
            # Should be medium or hard for great feeling
            if session['day_type'] not in ['medium', 'hard']:
                self.log_test("Generate Session (Great Feeling)", False, f"Expected medium/hard, got: {session['day_type']}")
                return False
                
            # Should have exercises
            if not session['exercises'] or len(session['exercises']) == 0:
                self.log_test("Generate Session (Great Feeling)", False, "No exercises in session")
                return False
                
            # Equipment should match
            if session['equipment'] != 'minimal':
                self.log_test("Generate Session (Great Feeling)", False, f"Equipment mismatch: {session['equipment']}")
                return False
                
            self.session_id = session['id']  # Store for later tests
            self.log_test("Generate Session (Great Feeling)", True, f"Day type: {session['day_type']}, {len(session['exercises'])} exercises")
            return True
            
        except Exception as e:
            self.log_test("Generate Session (Great Feeling)", False, f"Exception: {str(e)}")
            return False
            
    def test_generate_session_bad_feeling(self):
        """Test POST /api/generate with bad feeling - should be easy and set cooldown"""
        try:
            payload = {
                "feeling": "bad",
                "sleep": "good",
                "pain": "none", 
                "time_available": "20-30",
                "equipment": "bodyweight"
            }
            
            response = self.session.post(f"{BACKEND_URL}/generate", json=payload)
            
            if response.status_code != 200:
                self.log_test("Generate Session (Bad Feeling)", False, f"Status: {response.status_code}")
                return False
                
            session = response.json()
            
            # Should be easy for bad feeling
            if session['day_type'] != 'easy':
                self.log_test("Generate Session (Bad Feeling)", False, f"Expected easy, got: {session['day_type']}")
                return False
                
            # Check state was updated with cooldown
            state_response = self.session.get(f"{BACKEND_URL}/state")
            if state_response.status_code == 200:
                state = state_response.json()
                if state['cooldown_counter'] != 2:
                    self.log_test("Generate Session (Bad Feeling)", False, f"Cooldown not set, got: {state['cooldown_counter']}")
                    return False
                    
            self.log_test("Generate Session (Bad Feeling)", True, f"Day type: {session['day_type']}, cooldown set")
            return True
            
        except Exception as e:
            self.log_test("Generate Session (Bad Feeling)", False, f"Exception: {str(e)}")
            return False
            
    def test_bodyweight_equipment_filter(self):
        """Test that bodyweight equipment shows only bodyweight exercises"""
        try:
            payload = {
                "feeling": "ok",
                "sleep": "good",
                "pain": "none",
                "time_available": "30-45", 
                "equipment": "bodyweight"
            }
            
            response = self.session.post(f"{BACKEND_URL}/generate", json=payload)
            
            if response.status_code != 200:
                self.log_test("Bodyweight Equipment Filter", False, f"Status: {response.status_code}")
                return False
                
            session = response.json()
            
            # Check that all exercises are bodyweight compatible
            bodyweight_exercises = {
                'atg_split_squat', 'rear_leg_assisted_shrimp', 'bw_lunge',
                'single_leg_hip_thrust', 'pushup', 'diamond_pushup', 'deficit_pushup',
                'sfg_plank', 'pushup_plank', 'bw_batwing_hold', 'bear_crawl', 'tiger_crawl'
            }
            
            for exercise in session['exercises']:
                if exercise['id'] not in bodyweight_exercises:
                    # Check if it's a valid bodyweight exercise from the library
                    exercises_response = self.session.get(f"{BACKEND_URL}/exercises")
                    if exercises_response.status_code == 200:
                        all_exercises = exercises_response.json()
                        ex_data = next((ex for ex in all_exercises if ex['id'] == exercise['id']), None)
                        if ex_data and 'bodyweight' not in ex_data.get('equipment', []):
                            self.log_test("Bodyweight Equipment Filter", False, f"Non-bodyweight exercise: {exercise['id']}")
                            return False
                            
            self.log_test("Bodyweight Equipment Filter", True, f"All {len(session['exercises'])} exercises are bodyweight compatible")
            return True
            
        except Exception as e:
            self.log_test("Bodyweight Equipment Filter", False, f"Exception: {str(e)}")
            return False
            
    def test_reroll_session(self):
        """Test POST /api/reroll - Same input as generate, keeps same day type but swaps exercises"""
        try:
            payload = {
                "feeling": "great",
                "sleep": "good",
                "pain": "none",
                "time_available": "30-45",
                "equipment": "minimal"
            }
            
            response = self.session.post(f"{BACKEND_URL}/reroll", json=payload)
            
            if response.status_code != 200:
                self.log_test("Reroll Session", False, f"Status: {response.status_code}")
                return False
                
            session = response.json()
            
            # Should have same structure as generate
            required_fields = ['id', 'day_type', 'priority_bucket', 'exercises']
            for field in required_fields:
                if field not in session:
                    self.log_test("Reroll Session", False, f"Missing field: {field}")
                    return False
                    
            # Should have exercises
            if not session['exercises'] or len(session['exercises']) == 0:
                self.log_test("Reroll Session", False, "No exercises in rerolled session")
                return False
                
            self.log_test("Reroll Session", True, f"Rerolled session with {len(session['exercises'])} exercises")
            return True
            
        except Exception as e:
            self.log_test("Reroll Session", False, f"Exception: {str(e)}")
            return False
            
    def test_swap_exercise(self):
        """Test POST /api/swap - Swaps a single exercise"""
        try:
            if not self.session_id:
                self.log_test("Swap Exercise", False, "No session ID available from previous test")
                return False
                
            # First get an exercise to swap
            payload = {
                "session_id": self.session_id,
                "exercise_id": "kb_goblet_squat",  # Common exercise
                "equipment": "minimal"
            }
            
            response = self.session.post(f"{BACKEND_URL}/swap", json=payload)
            
            if response.status_code != 200:
                self.log_test("Swap Exercise", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
            new_exercise = response.json()
            
            # Validate response structure
            required_fields = ['id', 'name', 'category', 'load_level', 'protocol']
            for field in required_fields:
                if field not in new_exercise:
                    self.log_test("Swap Exercise", False, f"Missing field: {field}")
                    return False
                    
            # Should be different exercise
            if new_exercise['id'] == 'kb_goblet_squat':
                self.log_test("Swap Exercise", False, "Returned same exercise")
                return False
                
            self.log_test("Swap Exercise", True, f"Swapped to: {new_exercise['name']} ({new_exercise['category']})")
            return True
            
        except Exception as e:
            self.log_test("Swap Exercise", False, f"Exception: {str(e)}")
            return False
            
    def test_complete_session(self):
        """Test POST /api/complete - Marks session done and advances priority bucket"""
        try:
            if not self.session_id:
                self.log_test("Complete Session", False, "No session ID available")
                return False
                
            # Get current state
            state_response = self.session.get(f"{BACKEND_URL}/state")
            if state_response.status_code != 200:
                self.log_test("Complete Session", False, "Could not get current state")
                return False
                
            old_state = state_response.json()
            old_bucket = old_state['next_priority_bucket']
            
            # Complete session with good feedback
            payload = {
                "session_id": self.session_id,
                "feedback": "good"
            }
            
            response = self.session.post(f"{BACKEND_URL}/complete", json=payload)
            
            if response.status_code != 200:
                self.log_test("Complete Session", False, f"Status: {response.status_code}")
                return False
                
            result = response.json()
            
            # Should return success and next bucket
            if not result.get('success'):
                self.log_test("Complete Session", False, "Success not returned")
                return False
                
            # Check priority bucket advanced
            new_state_response = self.session.get(f"{BACKEND_URL}/state")
            if new_state_response.status_code == 200:
                new_state = new_state_response.json()
                new_bucket = new_state['next_priority_bucket']
                
                # Should have rotated (squat -> pull -> hinge -> push -> squat)
                rotation = ["squat", "pull", "hinge", "push"]
                old_idx = rotation.index(old_bucket)
                expected_new_idx = (old_idx + 1) % len(rotation)
                expected_new_bucket = rotation[expected_new_idx]
                
                if new_bucket != expected_new_bucket:
                    self.log_test("Complete Session", False, f"Priority bucket not rotated correctly: {old_bucket} -> {new_bucket}, expected {expected_new_bucket}")
                    return False
                    
            self.log_test("Complete Session", True, f"Priority rotated: {old_bucket} -> {new_bucket}")
            return True
            
        except Exception as e:
            self.log_test("Complete Session", False, f"Exception: {str(e)}")
            return False
            
    def test_complete_session_bad_feedback(self):
        """Test POST /api/complete with bad feedback - should set cooldown"""
        try:
            # Generate a new session first
            payload = {
                "feeling": "ok",
                "sleep": "good",
                "pain": "none",
                "time_available": "20-30",
                "equipment": "minimal"
            }
            
            gen_response = self.session.post(f"{BACKEND_URL}/generate", json=payload)
            if gen_response.status_code != 200:
                self.log_test("Complete Session (Bad Feedback)", False, "Could not generate test session")
                return False
                
            session = gen_response.json()
            
            # Complete with bad feedback
            complete_payload = {
                "session_id": session['id'],
                "feedback": "not_good"
            }
            
            response = self.session.post(f"{BACKEND_URL}/complete", json=complete_payload)
            
            if response.status_code != 200:
                self.log_test("Complete Session (Bad Feedback)", False, f"Status: {response.status_code}")
                return False
                
            # Check cooldown was set
            state_response = self.session.get(f"{BACKEND_URL}/state")
            if state_response.status_code == 200:
                state = state_response.json()
                if state['cooldown_counter'] != 2:
                    self.log_test("Complete Session (Bad Feedback)", False, f"Cooldown not set to 2, got: {state['cooldown_counter']}")
                    return False
                    
            self.log_test("Complete Session (Bad Feedback)", True, "Cooldown set to 2")
            return True
            
        except Exception as e:
            self.log_test("Complete Session (Bad Feedback)", False, f"Exception: {str(e)}")
            return False
            
    def test_get_benchmarks(self):
        """Test GET /api/benchmarks - User benchmarks"""
        try:
            response = self.session.get(f"{BACKEND_URL}/benchmarks")
            
            if response.status_code != 200:
                self.log_test("GET /api/benchmarks", False, f"Status: {response.status_code}")
                return False
                
            benchmarks = response.json()
            
            # Should have benchmark fields
            expected_fields = ['press_bell_kg', 'pushup_max', 'pullup_max', 'available_bells_minimal']
            for field in expected_fields:
                if field not in benchmarks:
                    self.log_test("GET /api/benchmarks", False, f"Missing field: {field}")
                    return False
                    
            self.log_test("GET /api/benchmarks", True, "Benchmarks structure valid")
            return True
            
        except Exception as e:
            self.log_test("GET /api/benchmarks", False, f"Exception: {str(e)}")
            return False
            
    def test_put_benchmarks(self):
        """Test PUT /api/benchmarks - Update user benchmarks"""
        try:
            payload = {
                "press_bell_kg": 24,
                "pushup_max": 30,
                "pullup_max": 8,
                "available_bells_minimal": [16, 24, 32]
            }
            
            response = self.session.put(f"{BACKEND_URL}/benchmarks", json=payload)
            
            if response.status_code != 200:
                self.log_test("PUT /api/benchmarks", False, f"Status: {response.status_code}")
                return False
                
            updated_benchmarks = response.json()
            
            # Verify updates were applied
            if updated_benchmarks['press_bell_kg'] != 24:
                self.log_test("PUT /api/benchmarks", False, f"Press bell not updated: {updated_benchmarks['press_bell_kg']}")
                return False
                
            if updated_benchmarks['pushup_max'] != 30:
                self.log_test("PUT /api/benchmarks", False, f"Pushup max not updated: {updated_benchmarks['pushup_max']}")
                return False
                
            self.log_test("PUT /api/benchmarks", True, "Benchmarks updated successfully")
            return True
            
        except Exception as e:
            self.log_test("PUT /api/benchmarks", False, f"Exception: {str(e)}")
            return False
            
    def test_put_settings(self):
        """Test PUT /api/settings - Update week_mode and power_frequency"""
        try:
            payload = {
                "week_mode": "B",
                "power_frequency": "weekly"
            }
            
            response = self.session.put(f"{BACKEND_URL}/settings", json=payload)
            
            if response.status_code != 200:
                self.log_test("PUT /api/settings", False, f"Status: {response.status_code}")
                return False
                
            updated_state = response.json()
            
            # Verify updates
            if updated_state['week_mode'] != 'B':
                self.log_test("PUT /api/settings", False, f"Week mode not updated: {updated_state['week_mode']}")
                return False
                
            if updated_state['power_frequency'] != 'weekly':
                self.log_test("PUT /api/settings", False, f"Power frequency not updated: {updated_state['power_frequency']}")
                return False
                
            self.log_test("PUT /api/settings", True, "Settings updated successfully")
            return True
            
        except Exception as e:
            self.log_test("PUT /api/settings", False, f"Exception: {str(e)}")
            return False
            
    def test_minimal_equipment_kb_filter(self):
        """Test minimal equipment filters KB exercises correctly"""
        try:
            payload = {
                "feeling": "ok",
                "sleep": "good", 
                "pain": "none",
                "time_available": "30-45",
                "equipment": "minimal"
            }
            
            response = self.session.post(f"{BACKEND_URL}/generate", json=payload)
            
            if response.status_code != 200:
                self.log_test("Minimal Equipment KB Filter", False, f"Status: {response.status_code}")
                return False
                
            session = response.json()
            
            # Get all exercises to check equipment compatibility
            exercises_response = self.session.get(f"{BACKEND_URL}/exercises")
            if exercises_response.status_code != 200:
                self.log_test("Minimal Equipment KB Filter", False, "Could not get exercise library")
                return False
                
            all_exercises = exercises_response.json()
            exercise_dict = {ex['id']: ex for ex in all_exercises}
            
            # Check each exercise in session is minimal equipment compatible
            for exercise in session['exercises']:
                ex_data = exercise_dict.get(exercise['id'])
                if ex_data and 'minimal' not in ex_data.get('equipment', []):
                    self.log_test("Minimal Equipment KB Filter", False, f"Non-minimal exercise: {exercise['id']}")
                    return False
                    
            self.log_test("Minimal Equipment KB Filter", True, f"All {len(session['exercises'])} exercises are minimal equipment compatible")
            return True
            
        except Exception as e:
            self.log_test("Minimal Equipment KB Filter", False, f"Exception: {str(e)}")
            return False
            
    def reset_state(self):
        """Reset state for clean testing"""
        try:
            response = self.session.post(f"{BACKEND_URL}/reset")
            if response.status_code == 200:
                print("🔄 State reset for clean testing")
                return True
            else:
                print(f"⚠️  Could not reset state: {response.status_code}")
                return False
        except Exception as e:
            print(f"⚠️  Could not reset state: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all API tests"""
        print(f"🧪 Starting Backend API Tests for Daily Training Decision Engine")
        print(f"🔗 Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # Reset state for clean testing
        self.reset_state()
        
        # Test order matters for some tests (generate before swap/complete)
        tests = [
            self.test_get_exercises,
            self.test_get_state,
            self.test_generate_session_great_feeling,
            self.test_generate_session_bad_feeling,
            self.test_bodyweight_equipment_filter,
            self.test_minimal_equipment_kb_filter,
            self.test_reroll_session,
            self.test_swap_exercise,
            self.test_complete_session,
            self.test_complete_session_bad_feedback,
            self.test_get_benchmarks,
            self.test_put_benchmarks,
            self.test_put_settings,
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"❌ FAIL {test.__name__}: Unexpected error: {str(e)}")
                
        print("=" * 80)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"⚠️  {total - passed} tests failed")
            return False

def main():
    """Main test runner"""
    tester = APITester()
    success = tester.run_all_tests()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()