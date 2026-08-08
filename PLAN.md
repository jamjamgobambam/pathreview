## Solution plan

**Issue:**
Title: Add inline docstrings to all public methods in core/services/
Link: https://github.com/ascherj/pathreview/issues/119

### Understand

What is the root cause of this issue? What behavior is expected vs. actual?
The cause of this issue is that when the files in core/services were created the developer neglected to add inline doctrings to the methods in them. This does not directly change the behavior of the code, however it reduces the maintainability and explainability of the code other people.

### Map

Which files, functions, or modules are involved?
List the specific files you expect to touch.
core/services/profile_service.py
core/services/review_service.py
Note that the problem statement in GitHub also lists core/services/notification_service.py, but that file doesn't appear to be in the repo.

### Plan

What are the steps to fix this issue?
Break it into 3–5 concrete sub-tasks.

1. For each method in the above mentioned files, read them to understand exactly what their function is, arguments, returns, and error cases.
2. Review inline docstrings in other files in the repo in order to understand the expected style of level of detail for a docstring.
3. Write a docstring that has the correct information and style for each method in core/services that is missing one.

### Inputs & outputs

What does your fix take as input? What should it produce or change?
My fix takes no inputs or outputs because it is just documentation. However what it changes is that it makes the code in core/services easier to understand and maintain for people in the future.

### Risks & unknowns

What could go wrong? What are you still unsure about?
If I misunderstand the purpose or how a method works I could write a misleading docstring. For example review_service.py has async errors that are complex and difficult to explain correctly. I need to make sure that I avoid this by spending time reading the code to understand what each line does. I'm still unsure about what level of detail is expected for a docstring.

### Edge cases

What inputs or states should your fix handle gracefully?
My docstring must do a good job at explaining the various failure modes of functions because in many cases the methods have complex failure modes. One example is an execption that gets thrown in profile_service.get_profile() when the profile doesn't exist. Another example is documenting how in review_service.py the submit_review() function will give an error when the external API times out.
