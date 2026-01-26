#!/usr/bin/env python3
"""
Backend API Testing for Daily Training Decision Engine
Tests the new features: Prescription Types, Cooldown Override, and Reroll Constraints
"""

import requests
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any, List

# Backend URL from frontend .env
BACKEND_URL = "https://fitness-planner-138.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.test_results = []
        self.session_id = None
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = f"{status}: {test_name}"
        if details:
            result += f" - {details}"
        print(result)
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
        
    def reset_state(self):
        """Reset backend state for clean testing"""
        try:
            response = self.session.post(f"{BACKEND_URL}/reset")
            if response.status_code == 200:
                self.log_test("Reset State", True, "Backend state reset successfully")
                return True
            else:
                self.log_test("Reset State", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Reset State", False, f"Error: {str(e)}")
            return False
    
    def test_prescription_types_and_protocols(self):
        """Test Prescription Types & Protocol System"""
        print("\n=== Testing Prescription Types & Protocol System ===")
        
        # Test 1: GET /api/protocols returns protocol library
        try:
            response = self.session.get(f"{BACKEND_URL}/protocols")
            if response.status_code == 200:
                protocols = response.json()
                if isinstance(protocols, list) and len(protocols) > 0:
                    # Check if protocols have required fields
                    sample_protocol = protocols[0]
                    required_fields = ["id", "name", "prescription_type", "description_short"]
                    has_all_fields = all(field in sample_protocol for field in required_fields)
                    self.log_test("GET /api/protocols", has_all_fields, 
                                f"Found {len(protocols)} protocols with required fields")
                else:
                    self.log_test("GET /api/protocols", False, "Empty or invalid protocol list")
            else:
                self.log_test("GET /api/protocols", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("GET /api/protocols", False, f"Error: {str(e)}")
        
        # Test 2: POST /api/generate returns exercises with prescription_type and correct fields
        questionnaire = {
            "feeling": "great",
            "sleep": "good", 
            "pain": "none",
            "time_available": "30-45",
            "equipment": "minimal"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/generate", json=questionnaire)
            if response.status_code == 200:
                session = response.json()
                exercises = session.get("exercises", [])
                
                if exercises:
                    all_have_prescription_type = True
                    correct_fields = True
                    field_details = []
                    
                    for ex in exercises:
                        # Check prescription_type exists
                        if "prescription_type" not in ex:
                            all_have_prescription_type = False
                            
                        # Check protocol fields
                        protocol_fields = ["protocol_id", "protocol_name", "protocol_description"]
                        if not all(field in ex for field in protocol_fields):
                            correct_fields = False
                            
                        # Check correct output fields based on prescription type
                        prescription_type = ex.get("prescription_type", "")
                        
                        if prescription_type in ["KB_STRENGTH", "BW_DYNAMIC", "POWER_SWING"]:
                            if "reps" not in ex or ex.get("reps") is None:
                                correct_fields = False
                                field_details.append(f"{ex['name']} ({prescription_type}) missing reps")
                            if "hold_time" in ex and ex.get("hold_time") is not None:
                                correct_fields = False
                                field_details.append(f"{ex['name']} ({prescription_type}) has hold_time but shouldn't")
                            if "time" in ex and ex.get("time") is not None:
                                correct_fields = False
                                field_details.append(f"{ex['name']} ({prescription_type}) has time but shouldn't")
                                
                        elif prescription_type == "ISOMETRIC_HOLD":
                            if "hold_time" not in ex or ex.get("hold_time") is None:
                                correct_fields = False
                                field_details.append(f"{ex['name']} (ISOMETRIC_HOLD) missing hold_time")
                            if "reps" in ex and ex.get("reps") is not None:
                                correct_fields = False
                                field_details.append(f"{ex['name']} (ISOMETRIC_HOLD) has reps but shouldn't")
                                
                        elif prescription_type in ["CARRY_TIME", "CRAWL_TIME"]:
                            if "time" not in ex or ex.get("time") is None:
                                correct_fields = False
                                field_details.append(f"{ex['name']} ({prescription_type}) missing time")
                            if "reps" in ex and ex.get("reps") is not None:
                                correct_fields = False
                                field_details.append(f"{ex['name']} ({prescription_type}) has reps but shouldn't")
                    
                    self.log_test("Exercises have prescription_type", all_have_prescription_type)
                    self.log_test("Exercises have protocol fields", correct_fields, 
                                "; ".join(field_details) if field_details else "All exercises have correct fields")
                    
                    # Store session for later tests
                    self.session_id = session.get("id")
                else:
                    self.log_test("POST /api/generate exercises", False, "No exercises returned")
            else:
                self.log_test("POST /api/generate", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("POST /api/generate", False, f"Error: {str(e)}")
    
    def test_cooldown_override_toggle(self):
        """Test Cooldown Override Toggle functionality"""
        print("\n=== Testing Cooldown Override Toggle ===")
        
        # Reset state first
        self.reset_state()
        
        # Test 1: PUT /api/settings with cooldown_override
        try:
            response = self.session.put(f"{BACKEND_URL}/settings", json={"cooldown_override": True})
            if response.status_code == 200:
                state = response.json()
                override_set = state.get("cooldown_override") == True
                self.log_test("PUT /api/settings cooldown_override=True", override_set)
            else:
                self.log_test("PUT /api/settings cooldown_override", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("PUT /api/settings cooldown_override", False, f"Error: {str(e)}")
        
        # Test 2: GET /api/state returns cooldown_override field
        try:
            response = self.session.get(f"{BACKEND_URL}/state")
            if response.status_code == 200:
                state = response.json()
                has_override_field = "cooldown_override" in state
                self.log_test("GET /api/state has cooldown_override", has_override_field, 
                            f"cooldown_override: {state.get('cooldown_override')}")
            else:
                self.log_test("GET /api/state", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("GET /api/state", False, f"Error: {str(e)}")
        
        # Test 3: Set cooldown counter and test override behavior
        # First, trigger cooldown with bad feedback
        bad_questionnaire = {
            "feeling": "bad",
            "sleep": "bad",
            "pain": "none",
            "time_available": "30-45",
            "equipment": "minimal"
        }
        
        try:
            # Generate session with bad conditions (should set cooldown)
            response = self.session.post(f"{BACKEND_URL}/generate", json=bad_questionnaire)
            if response.status_code == 200:
                session = response.json()
                
                # Check if day_type is "easy" due to bad conditions
                day_type_easy = session.get("day_type") == "easy"
                self.log_test("Bad conditions → day_type=easy", day_type_easy, 
                            f"day_type: {session.get('day_type')}")
                
                # Check state has cooldown and override is reset
                state_response = self.session.get(f"{BACKEND_URL}/state")
                if state_response.status_code == 200:
                    state = state_response.json()
                    cooldown_set = state.get("cooldown_counter", 0) > 0
                    override_reset = state.get("cooldown_override") == False
                    self.log_test("Bad conditions set cooldown", cooldown_set, 
                                f"cooldown_counter: {state.get('cooldown_counter')}")
                    self.log_test("Bad conditions reset override", override_reset, 
                                f"cooldown_override: {state.get('cooldown_override')}")
        except Exception as e:
            self.log_test("Bad conditions test", False, f"Error: {str(e)}")
        
        # Test 4: Test override behavior with cooldown active
        try:
            # Set override to True while cooldown is active
            self.session.put(f"{BACKEND_URL}/settings", json={"cooldown_override": True})
            
            # Generate session with great conditions but cooldown active + override ON
            great_questionnaire = {
                "feeling": "great",
                "sleep": "good",
                "pain": "none",
                "time_available": "30-45",
                "equipment": "minimal"
            }
            
            response = self.session.post(f"{BACKEND_URL}/generate", json=great_questionnaire)
            if response.status_code == 200:
                session = response.json()
                day_type = session.get("day_type")
                
                # With override ON and great conditions, should be medium or hard despite cooldown
                override_working = day_type in ["medium", "hard"]
                self.log_test("Cooldown override allows medium/hard", override_working, 
                            f"day_type: {day_type} (with cooldown + override)")
        except Exception as e:
            self.log_test("Cooldown override test", False, f"Error: {str(e)}")
        
        # Test 5: Test auto-reset on not_good feedback
        try:
            # Set override to True first
            self.session.put(f"{BACKEND_URL}/settings", json={"cooldown_override": True})
            
            # Complete session with not_good feedback
            feedback_data = {
                "session_id": "test_session",
                "feedback": "not_good"
            }
            
            response = self.session.post(f"{BACKEND_URL}/complete", json=feedback_data)
            if response.status_code == 200:
                # Check if override was reset
                state_response = self.session.get(f"{BACKEND_URL}/state")
                if state_response.status_code == 200:
                    state = state_response.json()
                    override_reset = state.get("cooldown_override") == False
                    cooldown_set = state.get("cooldown_counter", 0) > 0
                    self.log_test("not_good feedback resets override", override_reset, 
                                f"cooldown_override: {state.get('cooldown_override')}")
                    self.log_test("not_good feedback sets cooldown", cooldown_set, 
                                f"cooldown_counter: {state.get('cooldown_counter')}")
        except Exception as e:
            self.log_test("not_good feedback test", False, f"Error: {str(e)}")
    
    def test_reroll_preserves_constraints(self):
        """Test Reroll Preserves Constraints functionality"""
        print("\n=== Testing Reroll Preserves Constraints ===")
        
        # Reset state first
        self.reset_state()
        
        # Test 1: Generate initial session
        questionnaire = {
            "feeling": "great",
            "sleep": "good",
            "pain": "none",
            "time_available": "30-45",
            "equipment": "minimal"
        }
        
        try:
            response = self.session.post(f"{BACKEND_URL}/generate", json=questionnaire)
            if response.status_code == 200:
                original_session = response.json()
                original_day_type = original_session.get("day_type")
                original_priority_bucket = original_session.get("priority_bucket")
                original_exercises = [ex["id"] for ex in original_session.get("exercises", [])]
                
                self.log_test("Generate original session", True, 
                            f"day_type: {original_day_type}, priority_bucket: {original_priority_bucket}")
                
                # Test 2: Reroll with preserved constraints
                reroll_data = {
                    "questionnaire": questionnaire,
                    "preserve_day_type": original_day_type,
                    "preserve_priority_bucket": original_priority_bucket
                }
                
                reroll_response = self.session.post(f"{BACKEND_URL}/reroll", json=reroll_data)
                if reroll_response.status_code == 200:
                    rerolled_session = reroll_response.json()
                    rerolled_day_type = rerolled_session.get("day_type")
                    rerolled_priority_bucket = rerolled_session.get("priority_bucket")
                    rerolled_exercises = [ex["id"] for ex in rerolled_session.get("exercises", [])]
                    
                    # Check constraints preserved
                    day_type_preserved = rerolled_day_type == original_day_type
                    priority_bucket_preserved = rerolled_priority_bucket == original_priority_bucket
                    
                    # Check exercises changed (at least some should be different)
                    exercises_changed = rerolled_exercises != original_exercises
                    
                    self.log_test("Reroll preserves day_type", day_type_preserved, 
                                f"Original: {original_day_type}, Rerolled: {rerolled_day_type}")
                    self.log_test("Reroll preserves priority_bucket", priority_bucket_preserved, 
                                f"Original: {original_priority_bucket}, Rerolled: {rerolled_priority_bucket}")
                    self.log_test("Reroll changes exercises", exercises_changed, 
                                f"Original: {len(original_exercises)} exercises, Rerolled: {len(rerolled_exercises)} exercises")
                    
                    # Test 3: Multiple rerolls should produce different results
                    if exercises_changed:
                        second_reroll_response = self.session.post(f"{BACKEND_URL}/reroll", json=reroll_data)
                        if second_reroll_response.status_code == 200:
                            second_rerolled_session = second_reroll_response.json()
                            second_rerolled_exercises = [ex["id"] for ex in second_rerolled_session.get("exercises", [])]
                            
                            # At least one exercise should be different between rerolls
                            multiple_rerolls_work = second_rerolled_exercises != rerolled_exercises
                            self.log_test("Multiple rerolls produce variations", multiple_rerolls_work, 
                                        "Exercise variations between rerolls")
                else:
                    self.log_test("POST /api/reroll", False, f"Status: {reroll_response.status_code}")
            else:
                self.log_test("Generate original session", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Reroll constraints test", False, f"Error: {str(e)}")
    
    def test_basic_connectivity(self):
        """Test basic API connectivity"""
        print("\n=== Testing Basic Connectivity ===")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/")
            if response.status_code == 200:
                self.log_test("Backend Connectivity", True, "API is accessible")
                return True
            else:
                self.log_test("Backend Connectivity", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Backend Connectivity", False, f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🧪 Starting Backend API Tests for Daily Training Decision Engine")
        print(f"Backend URL: {BACKEND_URL}")
        print("="*80)
        
        # Test backend connectivity first
        if not self.test_basic_connectivity():
            print("❌ Cannot connect to backend. Stopping tests.")
            return
        
        # Run feature tests
        self.test_prescription_types_and_protocols()
        self.test_cooldown_override_toggle()
        self.test_reroll_preserves_constraints()
        
        # Summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        passed_tests = [r for r in self.test_results if r["passed"]]
        failed_tests = [r for r in self.test_results if not r["passed"]]
        
        print(f"✅ PASSED: {len(passed_tests)}")
        print(f"❌ FAILED: {len(failed_tests)}")
        
        if failed_tests:
            print("\n🚨 FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        
        print(f"\n📈 SUCCESS RATE: {len(passed_tests)}/{len(self.test_results)} ({len(passed_tests)/len(self.test_results)*100:.1f}%)")
        
        return len(failed_tests) == 0

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    
    if not success:
        sys.exit(1)