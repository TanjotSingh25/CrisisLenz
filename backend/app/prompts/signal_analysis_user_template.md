Analyze the following public signal for operational risk relevance.

## Signal Details

- **Source:** {{source_name}} ({{source_type}})
- **Title:** {{title}}
- **Published:** {{published_at}}
- **Category hint:** {{category_hint}}
- **Matched keywords:** {{matched_keywords}}
- **URL:** {{url}}

## Signal Content

**Summary:**
{{summary}}

**Body:**
{{body}}

## Location Data (if already available from source)

- Latitude: {{latitude}}
- Longitude: {{longitude}}
- Event category: {{event_category}}
- Event status: {{event_status}}

---

## Required JSON Output

Return ONLY a JSON object with exactly these fields:

```
{
  "is_event_worthy": true or false,
  "rejection_reason": "short reason if rejected, null if accepted",
  "event_type": "one of: wildfire, flood, earthquake, severe_storm, volcano, explosion, bombing, civil_unrest, transport_disruption, power_outage, industrial_incident, political_security, other",
  "severity": "one of: low, medium, high, critical, unknown",
  "confidence": 0.0 to 1.0,
  "title": "clean event title or null if rejected",
  "summary": "1-2 sentence operational summary or null if rejected",
  "location_name": "city, region, country or null",
  "latitude": float or null,
  "longitude": float or null,
  "business_impact": "description of potential business/operational impact or null if rejected",
  "recommended_action": "suggested operational response or null if rejected",
  "reasoning_brief": "1-2 sentences explaining your decision"
}
```

Return only the JSON object. No markdown, no code block markers, no extra text.
