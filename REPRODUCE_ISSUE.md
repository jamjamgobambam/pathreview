# Reproduce: POST /reviews With No Ingested Documents

These commands assume the backend is running at `http://localhost:8000` and using Bash to run commands.

## 0. Create A Test Account (Optional)
- Create an account to use for the reproduction. Adjust the email if this account already exists.
- **NOTE**: A test account isn't needed, can use one of the example or existing accounts as reviews create separate profiles.

```bash
curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "empty-profile@example.com", "password": "password1"}'
```

## 1. Log In And Capture Token
- Using the test account `empty-profile@example.com` with password `password1`. Adjust if using another account for testing.
- Login to an account to get the access token to use for creating a profile and a review.

```bash
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=empty-profile@example.com" \
  -d "password=password1")

TOKEN=$(python -c "import json,sys; print(json.load(sys.stdin)['access_token'])" <<< "$LOGIN_RESPONSE")
echo "$TOKEN"
```

**Result**:
- Echoed the login/account token.
- `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmMGZhM2Q1OS1lOGE2LTQ3NjUtYmUzMS03N2Q0NWRmY2JiMzEiLCJleHAiOjE3ODUwNDQzMTV9.ck5bZ_YHIRjYEOpr8eM8z4zMo-qVelFyXL75I5JI3TY`

## 2. Create A Profile With No Ingested Data
- `POST /profiles` accepts `github_username`, `portfolio_url`, and `resume_file`, but they default to `None`, so send no form fields. (view [`api/routes/profiles.py`](api\routes\profiles.py) )
- Expected profile fields should include null/empty source fields, such as no GitHub username, no portfolio URL, and no resume filename.
- Save the profile id of that profile to use for creating a review.

```bash
PROFILE_RESPONSE=$(curl -s -X POST http://localhost:8000/profiles \
  -H "Authorization: Bearer $TOKEN")

PROFILE_ID=$(python -c "import json,sys; print(json.load(sys.stdin)['id'])" <<< "$PROFILE_RESPONSE")
echo "$PROFILE_RESPONSE"
echo "$PROFILE_ID"
```
**Result**:
- Echoed the response JSON from the profile request and the profile id:
  - `{"id":"b3f81e27-21ac-4787-996b-bbe15997d630","user_id":"f0fa3d59-e8a6-4765-be31-77d45dfcbb31","github_username":null,"portfolio_url":null,"created_at":"2026-07-26T11:39:32.325062Z","resume_filename":null}`
  - `b3f81e27-21ac-4787-996b-bbe15997d630`


## 3. Create A Review For The Empty Profile
- Using the saved login token and profile id, create a review using the `POST /reviews` endpoint for the profile with no ingested content.

```bash
REVIEW_RESPONSE=$(curl -s -X POST http://localhost:8000/reviews \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"profile_id\": \"$PROFILE_ID\"}")

REVIEW_ID=$(python -c "import json,sys; print(json.load(sys.stdin)['id'])" <<< "$REVIEW_RESPONSE")
echo "$REVIEW_RESPONSE"
echo "$REVIEW_ID"
```

**Result**:
- Echoed the response JSON from the review request and the profile id:
  - `{"id":"4d62f114-1246-4bf1-af19-6c509e59d242","profile_id":"b3f81e27-21ac-4787-996b-bbe15997d630","status":"pending","sections":null,"overall_score":null,"error_message":null,"created_at":"2026-07-26T11:39:58.507387Z","updated_at":"2026-07-26T11:39:58.507387Z"}`
  - `4d62f114-1246-4bf1-af19-6c509e59d242`
- Response JSON from the review request suggests that it successfully processed the review rather than rejecting or raising an error to handle.

## 4. Check Review Status

```bash
curl -s -X GET "http://localhost:8000/reviews/$REVIEW_ID" \
  -H "Authorization: Bearer $TOKEN"
```

**Result**:
- Response JSON: 
  - `{"id":"d4c254ff-bf5b-4ac6-9200-a3427e1a44d8","profile_id":"29e71ffd-62aa-4f19-a303-09d580dda50f","status":"complete","sections":[{"section_name":"Technical Skills","content":"Detailed feedback on technical skills based on portfolio analysis","confidence":0.85,"suggestions":["Add more detail on AI/ML experience","Include specific technologies and frameworks"]},{"section_name":"Project Experience","content":"Detailed feedback on project experience and impact","confidence":0.8,"suggestions":["Include measurable impact metrics","Add links to project repositories"]},{"section_name":"Career Growth","content":"Feedback on career progression and development","confidence":0.78,"suggestions":["Document learning from each role","Highlight growth in responsibilities"]}],"overall_score":0.81,"error_message":null,"created_at":"2026-07-26T11:21:16.384891Z","updated_at":"2026-07-26T11:21:16.414575Z"}`
- Review's status becomes "complete" for this profile.
