# QUICK START GUIDE: Intelligence Dashboard

## For Government Officials

### First Time Using the System?

1. **Go to Dashboard**
   - Click "Intelligence Dashboard" in navigation menu
   - Or visit: `http://localhost:3000/intelligence`

2. **What You'll See**
   - **Top Performing States** (green) — These states are executing well
   - **Risk Alerts** (red) — These states need attention
   - **Emerging Trends** (blue) — Patterns that are catching on nationally
   - **Stats** (gray) — System-wide overview

3. **Key Metrics Explained**
   - **Score (0-10)**: Higher = better governance execution
     - 8-10: Excellent | 6-7: Good | 4-5: Needs work | 0-3: Critical
   - **Risk Severity**: Critical > High > Medium > Low

### Common Questions

**Q: Why does my state have a low score?**  
A: Look at the risk factors. Usually: low activity, limited scheme coverage, or reporting delays.

**Q: What should I do about a risk alert?**  
A: Read the "Recommended Action" for that specific risk.

**Q: How often is the data updated?**  
A: New reports → analyzed within 2 minutes.

**Q: Can I export this data?**  
A: Yes, click "Export" button on any card.

---

## Technical Users

### Architecture Overview

```
Raw Reports (PDF/Word)
    ↓
[Parsing Service] → Extract text, metadata
    ↓
[Database] → Store embeddings + full text
    ↓
[Intelligence Engine] → Score states, detect risks
    ↓
[Analysis Layer] → Synthesize insights
    ↓
[Dashboard / API] → Display to officials
```

### Key APIs

```bash
# Get national intelligence
curl http://localhost:8000/api/intelligence/national

# Get state-specific intelligence  
curl http://localhost:8000/api/intelligence/state/Maharashtra

# Get trending patterns
curl http://localhost:8000/api/intelligence/trends

# Check system health
curl http://localhost:8000/api/system/status
```

### Customization

**Change scoring weights** → Edit `intelligence_service.py:StateHealthScore.compute()`  
**Add new risk rules** → Edit intelligence_service.py `_detect_risks()`  
**Change alert thresholds** → Edit intelligence.py response filtering

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Dashboard shows "No data" | Upload reports first via Upload page |
| Intelligence scores missing | Check System Status — verify database connection |
| Risk alerts not appearing | Verify report parsing succeeded (check logs) |
| Dashboard slow to load | Check network — API calls take <1s usually |

---

## Success Indicators

✓ Dashboard loads within 3 seconds  
✓ State scores range from 0-10 across all states  
✓ Top states have green badges  
✓ Risk alerts have recommended actions  
✓ Trends show multiple states adopting schemes  
✓ System Status shows "All systems operational"

---

## Next Steps

1. **Week 1**: Explore dashboard, review state scores
2. **Week 2**: Run sample queries to verify intelligence quality
3. **Week 3**: Brief your team on findings
4. **Week 4+**: Use for strategic planning and governance decisions

---

**Need help?** → See docs/SYSTEM_DOCUMENTATION.md for full technical reference
