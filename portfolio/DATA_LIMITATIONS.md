# Data Limitations

MovieLens 25M contains ratings and tags. It does not contain registration events, impressions, clicks, watch time, demographic data, campaign logs, recommendation exposures, or randomized experiment assignment.

Consequences:

- Rating activity is a proxy for platform activity.
- New users are first observed rating users, not confirmed registrations.
- Retention is a later rating event, not confirmed product return.
- Churn and future activity targets are proxy labels.
- A/B results cannot be estimated from this historical observational dataset.
- Anomaly flags need business and pipeline logs for root-cause confirmation.
