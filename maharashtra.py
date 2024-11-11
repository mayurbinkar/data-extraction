import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import pandas as pd
import nest_asyncio
import re

# Apply nest_asyncio if running in an environment with an existing event loop
nest_asyncio.apply()

# Function to clean special characters from text using regex
def clean_text(text):
    return re.sub(r'[^A-Za-z0-9\s]', '', text)  # Removes non-alphanumeric characters, except spaces

async def scrape_indeed_jobs():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Set user agent to avoid bot detection
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })

        # URL for Indeed job search in Pune, Maharashtra
        await page.goto("https://in.indeed.com/jobs?q=&l=Maharashtra&from=searchOnDesktopSerp&vjk=1fee8c4e8b54bf2d")

        jobData = []

        for i in range(50):  # Adjust the range for more pages
            # Wait for the job listings to load using a more stable selector
            await page.wait_for_selector('div.job_seen_beacon')
            dContent = await page.content()
            soup = BeautifulSoup(dContent, 'html.parser')

            # Scrape job data
            for job_card in soup.find_all('div', class_='job_seen_beacon'):
                # Extract job title
                title_tag = job_card.find('h2', class_='jobTitle css-1psdjh5 eu4oa1w0')
                title = title_tag.get_text(strip=True) if title_tag else 'N/A'

                # Extract company name
                company_tag = job_card.find('span', class_='css-1h7lukg eu4oa1w0')
                company = company_tag.get_text(strip=True) if company_tag else 'N/A'

                # Extract location
                location_tag = job_card.find('div', class_='css-1restlb eu4oa1w0')
                location = location_tag.get_text(strip=True) if location_tag else 'N/A'

                # Extract salary (if available)
                salary_tag = job_card.find('div', class_='css-18z4q2i eu4oa1w0')
                salary = salary_tag.get_text(strip=True) if salary_tag else 'N/A'
                salary = clean_text(salary)

                # Extract summary
                summary_tag = job_card.find('div', class_='css-156d248 eu4oa1w0')
                summary = summary_tag.get_text(strip=True) if summary_tag else 'N/A'

                # Extract job link
                job_link_tag = job_card.find('a', href=True)
                job_link = "https://in.indeed.com" + job_link_tag['href'] if job_link_tag else 'N/A'

                # Append the job data
                jobData.append({
                    'Job Title': title,
                    'Company': company,
                    'Location': location,
                    'Salary': salary,
                    'Summary': summary,
                    'Apply Link': job_link
                })

            # # Click on the "Next" button to navigate to the next page
            # next_button = await page.query_selector('nav.css-98e656 eu4oa1w0')
            next_button = await page.query_selector('a[aria-label="Next Page"]')
            if next_button:
                await next_button.click()
            else:
                break

            # Wait a few seconds before scraping the next page to avoid being blocked
            await page.wait_for_timeout(1000)

        # Close the browser
        await browser.close()

        # Return the job data as a DataFrame
        return pd.DataFrame(jobData)

async def main():
    # Run the scraping function
    indeed_jobs_df = await scrape_indeed_jobs()

    # Save the scraped data to a CSV file
    indeed_jobs_df.to_csv('Maharashtra.csv', index=False)

    # Save the scraped data to an Excel file
    indeed_jobs_df.to_excel('Maharashtra.xlsx', index=False)

    # Print the DataFrame
    print(indeed_jobs_df)

# Run the main function
asyncio.run(main())