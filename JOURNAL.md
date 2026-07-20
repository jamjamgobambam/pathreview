## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/154

**Issue title:** Health check DB probe passes a raw SQL string, which fails under SQLAlchemy 2.x

**Tier:** [ x] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
In summary, the code check if the database is working using 'SELECT 1'. However, once it is upgraded to SQLAlchemy version 2.x, the testing query is now outdated. Consequently, the SQLAlchemy does not read the database, which causes the health check to fail, since it assumes that the database is faulty or is non-functional. In other to correct this issue, the SQL string has to be wrapped in a text format, text(), which then allows the health check to function properly.

**Branch name:** fix/154-healthcheck-SQL-string

**Setup confirmation:** [ x] App runs locally at localhost:5173
