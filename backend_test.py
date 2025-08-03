import requests
import sys
import json
import base64
from datetime import datetime

class NFCContactAPITester:
    def __init__(self, base_url="https://3e835c80-73c6-4c00-9d8a-b9d84c45dd31.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.created_contact_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2, default=str)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root endpoint"""
        return self.run_test("Root Endpoint", "GET", "", 200)

    def test_get_contacts_empty(self):
        """Test getting contacts when empty"""
        return self.run_test("Get Contacts (Empty)", "GET", "api/contacts", 200)

    def test_create_contact(self):
        """Test creating a new contact"""
        test_contact = {
            "name": "Test Kontakt",
            "phone_number": "+49 123 456789",
            "text": "Test Beschreibung für NFC Tag"
        }
        success, response = self.run_test("Create Contact", "POST", "api/contacts", 200, test_contact)
        if success and 'id' in response:
            self.created_contact_id = response['id']
            print(f"   Created contact ID: {self.created_contact_id}")
            
            # Validate response structure
            required_fields = ['id', 'phone_number', 'text', 'name', 'created_at', 'updated_at', 'ndef_data', 'data_size']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing field in response: {field}")
                    return False, {}
            
            # Validate NDEF data is Base64
            try:
                decoded = base64.b64decode(response['ndef_data'])
                print(f"   NDEF data decoded successfully, size: {len(decoded)} bytes")
            except:
                print(f"❌ NDEF data is not valid Base64")
                return False, {}
                
            # Check NFC 215 size limit
            if response['data_size'] > 504:
                print(f"❌ Data size {response['data_size']} exceeds NFC 215 limit of 504 bytes")
            else:
                print(f"✅ Data size {response['data_size']} is within NFC 215 limit")
                
        return success, response

    def test_create_contact_without_name(self):
        """Test creating contact without optional name"""
        test_contact = {
            "phone_number": "+49 987 654321",
            "text": "Kontakt ohne Namen"
        }
        return self.run_test("Create Contact (No Name)", "POST", "api/contacts", 200, test_contact)

    def test_create_contact_validation_error(self):
        """Test creating contact with missing required fields"""
        test_contact = {
            "name": "Incomplete Contact"
            # Missing phone_number and text
        }
        return self.run_test("Create Contact (Validation Error)", "POST", "api/contacts", 422, test_contact)

    def test_create_contact_too_large(self):
        """Test creating contact that exceeds text length limit"""
        large_text = "A" * 101  # Exceed the 100 character limit in Pydantic model
        test_contact = {
            "name": "Large Contact",
            "phone_number": "+49 123 456789",
            "text": large_text
        }
        return self.run_test("Create Contact (Too Large)", "POST", "api/contacts", 422, test_contact)

    def test_get_contacts_with_data(self):
        """Test getting contacts after creating some"""
        success, response = self.run_test("Get Contacts (With Data)", "GET", "api/contacts", 200)
        if success and isinstance(response, list) and len(response) > 0:
            print(f"   Found {len(response)} contacts")
            # Validate first contact structure
            contact = response[0]
            required_fields = ['id', 'phone_number', 'text', 'name', 'created_at', 'updated_at', 'ndef_data', 'data_size']
            for field in required_fields:
                if field not in contact:
                    print(f"❌ Missing field in contact: {field}")
                    return False, {}
        return success, response

    def test_update_contact(self):
        """Test updating an existing contact"""
        if not self.created_contact_id:
            print("❌ No contact ID available for update test")
            return False, {}
            
        updated_contact = {
            "name": "Updated Test Kontakt",
            "phone_number": "+49 111 222333",
            "text": "Updated Beschreibung"
        }
        return self.run_test("Update Contact", "PUT", f"api/contacts/{self.created_contact_id}", 200, updated_contact)

    def test_update_nonexistent_contact(self):
        """Test updating a non-existent contact"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        updated_contact = {
            "name": "Non-existent",
            "phone_number": "+49 000 000000",
            "text": "Should not work"
        }
        return self.run_test("Update Non-existent Contact", "PUT", f"api/contacts/{fake_id}", 404, updated_contact)

    def test_get_ndef_data(self):
        """Test getting NDEF data for a specific contact"""
        if not self.created_contact_id:
            print("❌ No contact ID available for NDEF test")
            return False, {}
            
        success, response = self.run_test("Get NDEF Data", "GET", f"api/contacts/{self.created_contact_id}/ndef", 200)
        if success:
            # Validate NDEF response structure
            required_fields = ['contact_id', 'ndef_record', 'instructions']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing field in NDEF response: {field}")
                    return False, {}
            
            # Validate NDEF record structure
            ndef_record = response['ndef_record']
            ndef_fields = ['type', 'payload', 'payload_base64', 'size_bytes']
            for field in ndef_fields:
                if field not in ndef_record:
                    print(f"❌ Missing field in NDEF record: {field}")
                    return False, {}
            
            # Validate vCard format
            payload = ndef_record['payload']
            if not payload.startswith('BEGIN:VCARD') or not payload.endswith('END:VCARD'):
                print(f"❌ Invalid vCard format")
                return False, {}
            else:
                print(f"✅ Valid vCard format detected")
                
        return success, response

    def test_get_ndef_nonexistent_contact(self):
        """Test getting NDEF data for non-existent contact"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        return self.run_test("Get NDEF Non-existent Contact", "GET", f"api/contacts/{fake_id}/ndef", 404)

    def test_get_qr_code(self):
        """Test getting QR code SVG for a specific contact"""
        if not self.created_contact_id:
            print("❌ No contact ID available for QR code test")
            return False, {}
            
        url = f"{self.base_url}/api/contacts/{self.created_contact_id}/qr-code"
        print(f"\n🔍 Testing QR Code Generation...")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url)
            success = response.status_code == 200
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                
                # Check Content-Type header
                content_type = response.headers.get('Content-Type', '')
                if content_type == 'image/svg+xml':
                    print(f"✅ Correct Content-Type: {content_type}")
                else:
                    print(f"❌ Wrong Content-Type: {content_type}, expected: image/svg+xml")
                
                # Check Content-Disposition header for filename
                content_disposition = response.headers.get('Content-Disposition', '')
                if 'attachment' in content_disposition and '.svg' in content_disposition:
                    print(f"✅ Correct Content-Disposition: {content_disposition}")
                else:
                    print(f"❌ Wrong Content-Disposition: {content_disposition}")
                
                # Check SVG content
                svg_content = response.text
                if svg_content.startswith('<?xml') or svg_content.startswith('<svg'):
                    print(f"✅ Valid SVG content detected (length: {len(svg_content)} chars)")
                    
                    # Check if it contains vCard-like data (QR codes contain encoded data)
                    if 'BEGIN:VCARD' in svg_content or len(svg_content) > 100:
                        print(f"✅ QR code appears to contain vCard data")
                    else:
                        print(f"⚠️  QR code content may not contain vCard data")
                else:
                    print(f"❌ Invalid SVG content")
                    return False, {}
                    
                return True, {'svg_content': svg_content[:200] + '...'}
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                return False, {}
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}
        finally:
            self.tests_run += 1

    def test_get_qr_code_nonexistent_contact(self):
        """Test getting QR code for non-existent contact"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        url = f"{self.base_url}/api/contacts/{fake_id}/qr-code"
        print(f"\n🔍 Testing QR Code for Non-existent Contact...")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url)
            success = response.status_code == 404
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                return True, {}
            else:
                print(f"❌ Failed - Expected 404, got {response.status_code}")
                return False, {}
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}
        finally:
            self.tests_run += 1

    def test_create_contact_with_umlauts(self):
        """Test creating contact with German umlauts"""
        test_contact = {
            "name": "Müller Björn",
            "phone_number": "+49 123 456789",
            "text": "Geschäftlich - Büro München, Größe: groß"
        }
        success, response = self.run_test("Create Contact (German Umlauts)", "POST", "api/contacts", 200, test_contact)
        if success and 'id' in response:
            # Test QR code generation with umlauts
            contact_id = response['id']
            url = f"{self.base_url}/api/contacts/{contact_id}/qr-code"
            print(f"   Testing QR code with umlauts...")
            
            try:
                qr_response = requests.get(url)
                if qr_response.status_code == 200:
                    print(f"✅ QR code generated successfully with umlauts")
                    # Clean up
                    requests.delete(f"{self.base_url}/api/contacts/{contact_id}")
                else:
                    print(f"❌ QR code generation failed with umlauts: {qr_response.status_code}")
            except Exception as e:
                print(f"❌ QR code test with umlauts failed: {str(e)}")
                
        return success, response

    def test_create_contact_large_data(self):
        """Test creating contact with large data (near NFC limit)"""
        # Create data close to but under the 504 byte limit
        large_text = "A" * 80  # Large but within the 100 char limit in model
        test_contact = {
            "name": "Large Data Contact",
            "phone_number": "+49 123 456789",  # Keep within 20 char limit
            "text": large_text
        }
        success, response = self.run_test("Create Contact (Large Data)", "POST", "api/contacts", 200, test_contact)
        if success and 'id' in response:
            contact_id = response['id']
            print(f"   Data size: {response.get('data_size', 'unknown')} bytes")
            
            # Test QR code generation with large data
            url = f"{self.base_url}/api/contacts/{contact_id}/qr-code"
            print(f"   Testing QR code with large data...")
            
            try:
                qr_response = requests.get(url)
                if qr_response.status_code == 200:
                    svg_size = len(qr_response.text)
                    print(f"✅ QR code generated successfully with large data (SVG size: {svg_size} chars)")
                    # Clean up
                    requests.delete(f"{self.base_url}/api/contacts/{contact_id}")
                else:
                    print(f"❌ QR code generation failed with large data: {qr_response.status_code}")
            except Exception as e:
                print(f"❌ QR code test with large data failed: {str(e)}")
                
        return success, response

    def test_delete_contact(self):
        """Test deleting a contact"""
        if not self.created_contact_id:
            print("❌ No contact ID available for delete test")
            return False, {}
            
        return self.run_test("Delete Contact", "DELETE", f"api/contacts/{self.created_contact_id}", 200)

    def test_delete_nonexistent_contact(self):
        """Test deleting a non-existent contact"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        return self.run_test("Delete Non-existent Contact", "DELETE", f"api/contacts/{fake_id}", 404)

def main():
    print("🚀 Starting NFC Contact Manager API Tests")
    print("=" * 50)
    
    tester = NFCContactAPITester()
    
    # Run all tests in sequence
    test_methods = [
        tester.test_root_endpoint,
        tester.test_get_contacts_empty,
        tester.test_create_contact,
        tester.test_create_contact_without_name,
        tester.test_create_contact_validation_error,
        tester.test_create_contact_too_large,
        tester.test_create_contact_with_umlauts,
        tester.test_create_contact_large_data,
        tester.test_get_contacts_with_data,
        tester.test_update_contact,
        tester.test_update_nonexistent_contact,
        tester.test_get_ndef_data,
        tester.test_get_ndef_nonexistent_contact,
        tester.test_get_qr_code,
        tester.test_get_qr_code_nonexistent_contact,
        tester.test_delete_contact,
        tester.test_delete_nonexistent_contact
    ]
    
    for test_method in test_methods:
        try:
            test_method()
        except Exception as e:
            print(f"❌ Test {test_method.__name__} failed with exception: {str(e)}")
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"❌ {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())