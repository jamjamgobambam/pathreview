## Solution plan

**Issue:** Issue 154: https://github.com/ascherj/pathreview/issues/154

### Understand
What is the root cause of this issue? What behavior is expected vs. actual?
The root cause of this issue is located with in the health.py file within the routes folder on line 31 where (await db.execute("SELECT 1")) is used for a POSTGRES call which lacks the text wrapper introduce by sqlalchemy to safely help run SQL commands. Since this implementation lacks it, it currently fails and logs redis, vectordb, and postgres as unhealthy with an error code. If this command succeeded, these libraries would instead be labeled as healthy and no exception would be raised by this error.

### Map
Which files, functions, or modules are involved?
List the specific files you expect to touch.
The only file that needs to be addressed is health.py within the routes folder, specifically, only line 31 by introducing a test wrapper that lets the db execution command succeed and run safely.

### Plan
What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.
1. First I import the text wrapper introduced by the sqlalchemy library
2. Second, I will wrap the SELECT 1 command within the text wrapper and store it as a variable so I can log it and best keep track of it's declaration
3. Third, I will put the variable holding the sqlalchemy command within the await db.execute statement

### Inputs & outputs
What does your fix take as input? What should it produce or change?
The fix, or the text wrapper introduced by the sqlalchemy library takes in a sqlcommand and produces a sqlalchemy command that it can understand or safely interpret. This changed was introduced in sqlalchemy 2.X for safety purposes as to avoid running or executing raw sql commands.

### Risks & unknowns
What could go wrong? What are you still unsure about?

Since the only expected change is a single line of code without impacting any lasting memory within the database, the only possible error is the fix not working or executing correctly. I'm unsure whether I am able to save the sqlalchemy command as a variable for later usage or logging for any possible bug fixing.

### Edge cases
A possible edge case is that the database connections itself is unavailable or unreachable through other means or reasons. In this situation the database would report other possible errors and also report the database as unhealthy.