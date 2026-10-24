# Task 2: Job Listings from myjob.mu

## Columns

| Column | Description |
|---|---|
| job_title | Job title |
| company_name | Employer |
| employment_type | Full-time, Part-time, Fixed-term contract (CDD), Temporary or Internship |
| location | District of Mauritius, or Overseas |
| category | Job category as listed on myjob.mu |
| posted_date | Date posted (YYYY-MM-DD) |
| closing_date | Closing date (YYYY-MM-DD) |


## Method

- Job pages were found through the public sitemap of myjob.mu, since the listing pages load further results through an API host that robots.txt does not allow crawling.
- Each job page was fetched and parsed with Python (requests and BeautifulSoup)
