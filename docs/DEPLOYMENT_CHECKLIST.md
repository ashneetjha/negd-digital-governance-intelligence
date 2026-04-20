# DEPLOYMENT CHECKLIST: NeGD Intelligence System

## Pre-Deployment Verification

### Backend Setup
- [ ] Python 3.10+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Environment variables configured (.env file):
  - SUPABASE_URL
  - SUPABASE_KEY
  - GROQ_API_KEY
  - HF_API_TOKEN

### Frontend Setup
- [ ] Node.js 18+ installed
- [ ] Dependencies installed: `npm install` in frontend directory
- [ ] Environment variables configured (.env.local):
  - NEXT_PUBLIC_API_URL (backend API endpoint)

---

## Runtime Verification Tests

### Test 1: Backend Starts
```bash
cd backend
uvicorn app.main:app --reload
# Expected: Server running on http://localhost:8000
```
✓ Passed / ✗ Failed

### Test 2: API Health Check
```bash
curl http://localhost:8000/api/system/status
# Expected: 200 OK with system details
```
✓ Passed / ✗ Failed

### Test 3: Intelligence Endpoints Exist
```bash
curl http://localhost:8000/api/intelligence/national
curl http://localhost:8000/api/intelligence/trends
# Expected: 200 OK with structured data
```
✓ Passed / ✗ Failed

### Test 4: Frontend Builds
```bash
cd frontend
npm run build
# Expected: Build completes without errors
```
✓ Passed / ✗ Failed

### Test 5: Frontend Serves
```bash
npm start
# Expected: Dashboard available at http://localhost:3000
```
✓ Passed / ✗ Failed

### Test 6: Dashboard Loads
- Open browser to `http://localhost:3000/intelligence`
- You should see:
  - [ ] Top Performing States card
  - [ ] Risk Alerts card
  - [ ] Emerging Developments card
  - [ ] System Overview stats
  - [ ] Refresh button (working)
- [ ] Dashboard loads within 3 seconds
- [ ] No console errors

✓ Passed / ✗ Failed

---

## Golden Query Tests

### Query 1: National Intelligence
**Input:** Hit `/api/intelligence/national`  
**Expected Output:**
- [ ] total_states >= 25
- [ ] top_performers array has states
- [ ] risk_alerts array populated
- [ ] emerging_trends array populated
- [ ] all_states_scores has entries

**Result:** ✓ Pass / ✗ Fail

### Query 2: State Scoring
**Input:** Hit `/api/intelligence/state/Maharashtra`  
**Expected Output:**
- [ ] state field = "Maharashtra"
- [ ] score is 0-10 (e.g. 7.3)
- [ ] schemes_covered > 0
- [ ] sections_covered > 0

**Result:** ✓ Pass / ✗ Fail

### Query 3: Trends Detection
**Input:** Hit `/api/intelligence/trends`  
**Expected Output:**
- [ ] scheme_adoption array populated
- [ ] active_months array populated
- [ ] innovation_signals array populated

**Result:** ✓ Pass / ✗ Fail

---

## Data Quality Verification

### Database Health
```bash
# Connect to Supabase and verify:
```
- [ ] Documents table has records
- [ ] Embeddings table has vectors
- [ ] Chunks table is populated

**Result:** ✓ Pass / ✗ Fail

### Sample Report Processing
- [ ] Upload sample PDF/Word document
- [ ] Wait 2 minutes for processing
- [ ] Verify in database: chunks created, embeddings generated
- [ ] Query intelligence endpoints: data reflects new report

**Result:** ✓ Pass / ✗ Fail

---

## Failure Mode Tests

### Scenario 1: Empty Database
- Clear database (delete all documents)
- Hit `/api/intelligence/national`
- **Expected:** Graceful response with placeholder data, no crash

✓ Passed / ✗ Failed

### Scenario 2: API Timeout
- Introduce 5 second delay in query
- **Expected:** Response returns after timeout with fallback answer, no 500 error

✓ Passed / ✗ Failed

### Scenario 3: Invalid State Name
- Hit `/api/intelligence/state/InvalidState`
- **Expected:** 404 or graceful error message, not crash

✓ Passed / ✗ Failed

### Scenario 4: Missing Environment Variables
- Remove GROQ_API_KEY
- Try to run backend
- **Expected:** Clear error message about missing config, clean shutdown

✓ Passed / ✗ Failed

---

## Performance Baseline

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| API Response Time | <1s | ___ms | ✓/✗ |
| Dashboard Load Time | <3s | ___s | ✓/✗ |
| State Scoring (all 28) | <500ms | ___ms | ✓/✗ |
| Risk Detection | <200ms | ___ms | ✓/✗ |
| Trend Analysis | <300ms | ___ms | ✓/✗ |

---

## Integration Tests

### Full User Journey
1. [ ] User logs in to dashboard
2. [ ] Clicks "Intelligence Dashboard"
3. [ ] Dashboard loads with national data
4. [ ] User scrolls through cards (Top States, Risks, Trends)
5. [ ] User clicks "Refresh" — data updates
6. [ ] User tries different languages (if applicable)
7. [ ] User navigates back to other sections
8. [ ] No errors in browser console

**Result:** ✓ Pass / ✗ Fail

---

## Documentation Sign-Off

- [ ] QUICKSTART.md tested by government officials
- [ ] SYSTEM_DOCUMENTATION.md complete and referenced
- [ ] API documentation accurate (OpenAPI/Swagger)
- [ ] Troubleshooting section covers known issues

---

## Security & Compliance

- [ ] Environment variables not committed to git
- [ ] Database credentials protected
- [ ] CORS only allows authorized domains
- [ ] API rate limiting configured
- [ ] Logs don't expose sensitive data
- [ ] User roles/permissions enforced (if applicable)

---

## Final Sign-Off

**Backend Status:** ✓ Ready / ✗ Issues  
**Frontend Status:** ✓ Ready / ✗ Issues  
**Data Quality:** ✓ Ready / ✗ Issues  
**Documentation:** ✓ Ready / ✗ Issues  

**Overall System Status:** 
- ✓ PRODUCTION READY
- ◐ NEEDS MINOR FIXES (list below)
- ✗ NOT READY (detailed issues below)



## Post-Deployment Monitoring

### Week 1
- [ ] Monitor API error rates
- [ ] Collect user feedback on dashboard
- [ ] Verify database query performance
- [ ] Check system logs for warnings

### Ongoing
- [ ] Weekly system health report
- [ ] Monthly intelligence accuracy review
- [ ] Alert threshold tuning based on usage patterns
- [ ] Performance optimization if needed

---

**Questions during testing?** Contact the development team with:
1. Error message (full stack trace if available)
2. Steps to reproduce
3. Expected vs actual behavior
4. Environment details (OS, browser version, etc.)
