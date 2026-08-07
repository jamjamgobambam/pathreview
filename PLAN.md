## Solution plan

**Issue:** https://github.com/ascherj/pathreview/issues/155

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
Root cause is the Setting defines redis_url but does not define redis_host/redis_port.
This is a problem because it should report the status of Redis's real connectivity status, instead it always says "unhealthy" which is not always the case and this raises an AttributeError on a nonexistant field. 


### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.
Specific files would be listed down below:

core/config.py, this is where Settings is defined and we will either add fields or keep as is
api/routes/health.py, this is where /health is pulling the healht check and we can change how Redis host/port are obtained in the program. 

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.
Option A would be to Parse host/port out of the existing redis_url using urllib.parse.urlparse at the poitn of use in health.py

Option B We can add proper redis_host: str and redis_port: int fields that /health can obtain that replaces redis_url or computed from it in a way 

the specific task would be to decide which way we want to go Option A or B, 2 would be to ipmllent the config/parsing change, 3 update health.py to use this correclty , 4 manually verify curl /health that Redis now reports the real status, 5 update and add a test that covers this process 

### Inputs & outputs
What does your fix take as input? What should it produce or change?
Input: app's Redis conneciton info which is currenlty redis_url 
Output: /health should return "redis: "healthy" when Redis is reachable and "unhealthy" when its down, but it should not crash due to missing config 


### Risks & unknowns
What could go wrong? What are you still unsure about?
We would have to figure out if anything else already parse redis_url from somewhere else that we could reuse instead of writing parsing logic 

Another on would be if changing Settings fields would break other config consumers 

Finding a way to simulate Redis down locally to verify the unhealthy path sitll works after fix like docker compose stop redis 



### Edge cases
What inputs or states should your fix handle gracefully?
Redis genuinly can be unreachable this should still rpeort unhealthy and not crash 
Malformed redis_url (bad scheme/ missing port) we need to find how parsing will handle that 

Redis reachable but auth-protected, we will have to figure out how parsing will preserve that 
