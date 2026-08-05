## Solution plan

**Issue:** 
<!-- [issue title and link] -->
API docs don't include example curl commands #117

https://github.com/ascherj/pathreview/issues/117

### Understand
What is the root cause of this issue? What behavior is expected vs. actual? \
The root cause of this issue is simply part of the api documentation are missing. The behavior expected is that when an developer opens API.md in pathreview/docs/API.md, they can see curl commands for all the API endpoints present in the file (9 total). The actual behavior is that no curl commands are present in the file, this is an tier 1 documentation issue.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.

Files, Functions, or Modules Involved:

api/routes/auth.py => register(), login()

api/routes/health.py => health_check()

api/routes/profiles.py => create_profile_endpoint(), get_profile_endpoint(), delete_profile_endpoint()

api/routes/reviews.py => create_review_endpoint(), get_review_endpoint(), list_reviews_endpoints()

core/services/profile_service.py => create_profile(), get_profile(), delete_profile() 

core/services/review_service.py => create_review(), get_review(), list_reviews()

Files Expected to Touch:

docs/API.md

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. I need to understand the database better, learning the schema's and the relationships (primary and foreign keys) between each entity in the db. I also need to know the seed data: usernames & passwords combos that work, valid review id's and valid profile id's. These will be my parameter arguments in the URL's. 

2. Visit the service and route files and functions listed in the map section. For each API endpoint I need to know what data needs to passed in the url. For example, for a user login, I need to know a valid username and password such that the user will login sucessfully when I run the curl command.

3. Create the curl commands. Start the docker containers and run the app on one CLI, run the curl commands on another CLI to test them. If the curl command doesn't work, for example, a review contents isn't retrieved with a valid review id in the CLI, I will know a error occurs by the output. This means my curl command doesn't work and I will have to change it. 

4. Add the successfully tested curl commands on the CLI to the API.md file in the path pathreview/docs/API.md and return the HTTP response codes or anything the developer needs to know.

### Inputs & outputs
What does your fix take as input? What should it produce or change?
My fix will take user data as input, such as a valid username and password for authentication, valid profile id for profiles, valid user id for users. It registers a new user or the user logins, retrieves a review, retrieves or deletes a profile.

### Risks & unknowns
What could go wrong? What are you still unsure about?
The sample curl commands that I create may not run sucessfully, so I have to check them before I add them in the api document. I am unsure about "Obtain a JWT access token," I know it relates with authentication, so I will look over the route and service files for authentication as it relates to registering a user and a user login.

### Edge cases
What inputs or states should your fix handle gracefully?
One scenario is when deleting a profile using a valid profile_id, I have to make sure only a profile is deleted from a user ONLY, no other data is lost. Another scenario is when entering the curl CLI command register a user using a new username/email & password combo, the user must be added to the db and the new user must be able to login. 