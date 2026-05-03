"""
Test suite for Mergington High School Activities API.
Tests follow the AAA pattern: Arrange, Act, Assert.
"""
import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client):
        """
        Test that GET /activities returns all activities with correct structure.
        
        AAA Pattern:
        - Arrange: Set up test client (fixture)
        - Act: Send GET request to /activities
        - Assert: Verify response contains all activities with structured data
        """
        # Arrange: client is provided by fixture
        
        # Act: Make request
        response = client.get("/activities")
        data = response.json()
        
        # Assert: Check response status and structure
        assert response.status_code == 200
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        
        # Assert: Verify activity structure
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)

    def test_get_activities_contains_participant_list(self, client):
        """
        Test that participants list is included in activity data.
        
        AAA Pattern:
        - Arrange: Set up test client
        - Act: Fetch activities
        - Assert: Verify participant data
        """
        # Arrange: client is provided by fixture
        
        # Act: Make request
        response = client.get("/activities")
        data = response.json()
        
        # Assert: Verify initial participants
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]
        assert len(data["Chess Club"]["participants"]) == 2


class TestRootRedirect:
    """Tests for GET / endpoint."""

    def test_root_redirects_to_static_index(self, client):
        """
        Test that GET / redirects to /static/index.html.
        
        AAA Pattern:
        - Arrange: Set up test client
        - Act: Send GET request to root
        - Assert: Verify redirect response
        """
        # Arrange: client is provided by fixture
        
        # Act: Make request (follow_redirects=False to check redirect)
        response = client.get("/", follow_redirects=False)
        
        # Assert: Check redirect status
        assert response.status_code == 307  # Temporary redirect
        assert response.headers["location"] == "/static/index.html"


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_successful_signup(self, client):
        """
        Test that a student can successfully sign up for an activity.
        
        AAA Pattern:
        - Arrange: Set up test data (new email for signup)
        - Act: Send POST signup request
        - Assert: Verify response and participant list updated
        """
        # Arrange: Prepare test data
        activity_name = "Chess Club"
        new_email = "alice@mergington.edu"
        
        # Act: Send signup request
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert: Check response
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert new_email in data["message"]
        assert activity_name in data["message"]

    def test_signup_adds_participant_to_list(self, client):
        """
        Test that signup correctly adds a participant to the activity's participants list.
        
        AAA Pattern:
        - Arrange: Fetch current activity state before signup
        - Act: Sign up a student
        - Assert: Verify participant count increased and email in list
        """
        # Arrange: Get initial state
        activity_name = "Chess Club"
        new_email = "bob@mergington.edu"
        
        response_before = client.get("/activities")
        participants_before = response_before.json()[activity_name]["participants"]
        count_before = len(participants_before)
        
        # Act: Sign up
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert: Verify participant was added
        response_after = client.get("/activities")
        participants_after = response_after.json()[activity_name]["participants"]
        
        assert len(participants_after) == count_before + 1
        assert new_email in participants_after

    def test_duplicate_signup_returns_error(self, client):
        """
        Test that signing up twice with the same email prevents the duplicate.
        
        AAA Pattern:
        - Arrange: Sign up a student once
        - Act: Attempt to sign up again with same email
        - Assert: Verify 400 error and no duplicate in list
        """
        # Arrange: First signup
        activity_name = "Chess Club"
        email = "charlie@mergington.edu"
        
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Act: Attempt duplicate signup
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert: Verify error response
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"].lower()
        
        # Assert: Verify no duplicate in list
        response_activities = client.get("/activities")
        participants = response_activities.json()[activity_name]["participants"]
        assert participants.count(email) == 1  # Only one instance

    def test_signup_for_nonexistent_activity_returns_404(self, client):
        """
        Test that signing up for a non-existent activity returns 404.
        
        AAA Pattern:
        - Arrange: Set up test data with invalid activity
        - Act: Attempt signup for non-existent activity
        - Assert: Verify 404 error response
        """
        # Arrange: Prepare invalid activity name
        invalid_activity = "Nonexistent Club"
        email = "dave@mergington.edu"
        
        # Act: Attempt signup
        response = client.post(
            f"/activities/{invalid_activity}/signup",
            params={"email": email}
        )
        
        # Assert: Verify error response
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_multiple_students_can_signup_for_same_activity(self, client):
        """
        Test that multiple different students can sign up for the same activity.
        
        AAA Pattern:
        - Arrange: Prepare multiple new emails
        - Act: Sign up multiple students
        - Assert: Verify all are in the participants list
        """
        # Arrange: Prepare test data
        activity_name = "Programming Class"
        new_emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        # Act: Sign up multiple students
        for email in new_emails:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Assert: Verify all students are registered
        response_activities = client.get("/activities")
        participants = response_activities.json()[activity_name]["participants"]
        
        for email in new_emails:
            assert email in participants


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint."""

    def test_successful_unregister(self, client):
        """
        Test that a student can successfully unregister from an activity.
        
        AAA Pattern:
        - Arrange: Use existing participant (from fixture)
        - Act: Send DELETE unregister request
        - Assert: Verify response and participant removed
        """
        # Arrange: Use existing participant
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        
        # Act: Send unregister request
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email_to_remove}
        )
        
        # Assert: Check response
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert email_to_remove in data["message"]
        assert activity_name in data["message"]

    def test_unregister_removes_participant_from_list(self, client):
        """
        Test that unregister correctly removes a participant from the activity's participants list.
        
        AAA Pattern:
        - Arrange: Fetch activity state before unregister
        - Act: Unregister a participant
        - Assert: Verify participant removed and count decreased
        """
        # Arrange: Get initial state
        activity_name = "Chess Club"
        email_to_remove = "daniel@mergington.edu"
        
        response_before = client.get("/activities")
        count_before = len(response_before.json()[activity_name]["participants"])
        
        # Act: Unregister
        client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email_to_remove}
        )
        
        # Assert: Verify participant was removed
        response_after = client.get("/activities")
        participants_after = response_after.json()[activity_name]["participants"]
        
        assert email_to_remove not in participants_after
        assert len(participants_after) == count_before - 1

    def test_unregister_nonexistent_participant_returns_error(self, client):
        """
        Test that unregistering a participant not in the activity returns 400.
        
        AAA Pattern:
        - Arrange: Set up test data with non-participant email
        - Act: Attempt to unregister non-existent participant
        - Assert: Verify 400 error response
        """
        # Arrange: Email not registered for this activity
        activity_name = "Chess Club"
        non_participant_email = "notregistered@mergington.edu"
        
        # Act: Attempt unregister
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": non_participant_email}
        )
        
        # Assert: Verify error response
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"].lower()

    def test_unregister_from_nonexistent_activity_returns_404(self, client):
        """
        Test that unregistering from a non-existent activity returns 404.
        
        AAA Pattern:
        - Arrange: Set up test data with invalid activity
        - Act: Attempt unregister from non-existent activity
        - Assert: Verify 404 error response
        """
        # Arrange: Invalid activity name
        invalid_activity = "Nonexistent Club"
        email = "eve@mergington.edu"
        
        # Act: Attempt unregister
        response = client.delete(
            f"/activities/{invalid_activity}/unregister",
            params={"email": email}
        )
        
        # Assert: Verify error response
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestSignupAndUnregisterWorkflow:
    """Integration tests for signup and unregister workflows."""

    def test_student_can_reregister_after_unregister(self, client):
        """
        Test that a student can sign up again after unregistering from an activity.
        
        AAA Pattern:
        - Arrange: Sign up a student
        - Act: Unregister, then sign up again
        - Assert: Verify student is registered and no duplicates
        """
        # Arrange: Initial signup
        activity_name = "Gym Class"
        email = "frank@mergington.edu"
        
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Act: Unregister
        response_unreg = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        assert response_unreg.status_code == 200
        
        # Act: Sign up again
        response_signup = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response_signup.status_code == 200
        
        # Assert: Verify in participants list (only once)
        response_activities = client.get("/activities")
        participants = response_activities.json()[activity_name]["participants"]
        
        assert email in participants
        assert participants.count(email) == 1  # Only one instance

    def test_unregister_one_participant_does_not_affect_others(self, client):
        """
        Test that unregistering one participant doesn't affect others in the activity.
        
        AAA Pattern:
        - Arrange: Get initial participants and add a new one
        - Act: Unregister one participant
        - Assert: Verify other participants unchanged
        """
        # Arrange: Add new participant and get initial list
        activity_name = "Programming Class"
        new_email = "grace@mergington.edu"
        
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        response_before = client.get("/activities")
        all_participants_before = response_before.json()[activity_name]["participants"].copy()
        
        # Act: Unregister a different participant
        email_to_remove = "emma@mergington.edu"
        client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email_to_remove}
        )
        
        # Assert: Verify only the intended participant was removed
        response_after = client.get("/activities")
        participants_after = response_after.json()[activity_name]["participants"]
        
        for email in all_participants_before:
            if email == email_to_remove:
                assert email not in participants_after
            else:
                assert email in participants_after
