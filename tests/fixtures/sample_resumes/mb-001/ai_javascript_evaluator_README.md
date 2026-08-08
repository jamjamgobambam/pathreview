# 🤖 AI JavaScript Code Evaluator

**Built for the JavaScript Coding Specialist - AI Trainer role**

This tool evaluates AI-generated JavaScript code for three critical failure modes that large language models commonly produce.

## The Three Checks

| Check              |              What It Detects                                 | Severity      |
|--------------------|--------------------------------------------------------------|---------------|
| **Async/Await**    | Mixed `.then()` patterns, missing await                      | HIGH          |
| **Error Handling** | Async operations without try/catch, empty catch blocks       | HIGH → CRITICAL 
| **Memory Leaks**   | setInterval without cleanup, event listeners without removal | MEDIUM → HIGH |

## Scoring Philosophy

This evaluator uses **strict** scoring because AI models need to learn production-ready code:

- **HIGH issue** = -20 points
- **MEDIUM issue** = -10 points  
- **CRITICAL issue** = auto-fail
- **Passing score** = 95+ (tougher than typical linters)

## Demo: 3 AI-Generated Failures

### 1. Bad Async/Await (Score: 55/100 - FAIL)
```javascript
async function fetchUserData(userId) {
  const response = fetch(`/api/users/${userId}`); // ❌ missing await
  return response.then(res => res.json()); // ❌ mixing patterns
}

```

What the evaluator catches:

Missing await before fetch() call
Mixing async/await with .then() chains
Async function invoked without proper handling

Why it matters: AI models often confuse promise syntax, leading to race conditions and undefined behavior.


### 2. No Error Handling (Score 35/100 - FAIL)
```javascript
async function deleteDatabaseRecord(id) {
  // ❌ No try/catch around database operation
  const result = await database.query(`DELETE FROM users WHERE id = ${id}`);
  
  // ❌ Promise created without .catch() - unhandled rejection
  new Promise((resolve, reject) => {
    if (!id) reject(new Error('No ID provided'));
    resolve(id);
  });
  
  return result;
}

function updateUser(data) {
  try {
    JSON.parse(data);
  } catch(e) {
    // ❌ Empty catch block - silent failure
    // This hides errors instead of handling them
  }
}

// ❌ Async function called without error handling
deleteDatabaseRecord(123);
```

What the evaluator catches:

Async function with await lacks try/catch
Promise created without .catch() handler
Empty catch block that silently ignores errors

Why it matters: AI frequently ignores error handling, which causes production crashes and silent failures.


### 3. Memory Leak (Score: 45/100 - FAIL)
```javascript
function setupAutoSave() {
  // ❌ setInterval without cleanup - runs forever
  setInterval(() => {
    console.log('Auto-saving...');
  }, 5000);
  
  // ❌ Large array trapped in closure - never garbage collected
  const massiveCache = new Array(1000000);
  return function() {
    console.log('Cache size:', massiveCache.length);
  };
}

function attachHandlers() {
  // ❌ Event listener without removal - accumulates over time
  window.addEventListener('resize', () => {
    console.log('Window resized');
  });
  
  // ❌ Another listener, still no cleanup
  document.addEventListener('click', () => {
    fetch('/api/track');
  });
}

setupAutoSave();
attachHandlers();
const leak = setupAutoSave(); // Second leak!
```

What the evaluator catches:

setInterval without clearInterval reference
Large array held in closure (prevents garbage collection)
addEventListener without removeEventListener
Multiple listeners accumulating indefinitely

Why it matters: AI models don't "remember" cleanup requirements, leading to memory exhaustion in long-running apps.
