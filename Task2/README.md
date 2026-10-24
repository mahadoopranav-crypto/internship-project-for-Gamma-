# Task 2: Job Listings from myjob.mu

`Task2.csv` contains 300 job listings scraped from myjob.mu on 24 October 2026. It is the input for Task 3.

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
| url | Link to the listing on myjob.mu |

## Method

- Job pages were found through the public sitemap of myjob.mu, since the listing pages load further results through an API host that robots.txt does not allow crawling.
- Each job page was fetched and parsed with Python (requests and BeautifulSoup), with a 1.5 second pause between requests.
- 1,000 live listings were collected in total.

## Cleaning

- Listings with no named employer ("Not Disclosed") were removed.
- Listings with "Mauritius" as the location were removed, because that value does not say where the job is.
- One exact duplicate was removed.
- Job titles written entirely in capitals were changed to title case, keeping acronyms such as IT, HR and ERP.
- Extra spaces were removed from all fields.

The 300 listings kept are the first 300 clean ones in the order myjob.mu lists them, newest first. They were posted between 14 and 24 October 2026. Every field is filled in.

Only public job information was collected. No personal data is included.
