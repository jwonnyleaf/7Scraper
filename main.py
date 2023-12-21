import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os


class EventScraper:
    """A class for scraping event data from a specific website.

    Attributes:
        username: A string representing the username for login.
        password: A string representing the password for login.
        login_url: A string representing the URL of the login page.
        scrape_url: A string representing the URL of the page to scrape.
        driver: A webdriver instance for browser automation.
        wait: A WebDriverWait instance for handling waits in Selenium.
    """

    def __init__(self, login_url, scrape_url):
        """Inits EventScraper with URLs and sets up the driver.

        Args:
            login_url: The URL of the login page.
            scrape_url: The URL of the page to scrape.
        """
        load_dotenv()
        self.username = os.getenv("KEY_USERNAME")
        self.password = os.getenv("KEY_PASSWORD")
        self.login_url = os.getenv("LOGIN_PAGE")
        self.scrape_url = os.getenv("SCRAPE_PAGE")
        self.driver = None
        self.wait = None
        self.setup_driver()

    def setup_driver(self):
        """Sets up the Selenium WebDriver."""
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option("detach", False)
        service = Service("./chromedriver-win64/chromedriver.exe")
        self.driver = webdriver.Chrome(options=chrome_options, service=service)
        self.wait = WebDriverWait(self.driver, 10)

    def login(self):
        """Logs in to the website using provided credentials."""
        self.driver.get(self.login_url)
        self.wait.until(EC.presence_of_element_located((By.NAME, "userName")))
        self.driver.find_element(By.NAME, "userName").send_keys(self.username)
        self.driver.find_element(By.NAME, "password").send_keys(self.password)
        login_button = self.wait.until(
            EC.element_to_be_clickable((By.ID, "loginButton"))
        )
        login_button.click()
        self.wait.until(EC.url_changes(self.login_url))

    def navigate_to_scrape_url(self):
        """Navigates to the URL where the scraping will take place."""
        self.driver.get(self.scrape_url)
        self.wait.until(EC.presence_of_element_located((By.ID, "dailySetupBookings")))

    def click_expand_services(self):
        """Clicks the 'Expand Services' button on the page."""
        self.wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#ngplus-overlay-container.ng-hide")
            )
        )
        expand_services_button = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@title='Show all Services']")
            )
        )
        expand_services_button.click()

    def scrape_events(self):
        """Scrapes the event data from the page.

        Returns:
            A list of dictionaries containing event data.
        """
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        table = soup.find("table", id="dailySetupBookings")
        tbody_elements = table.find_all("tbody")

        events = []
        for tbody in tbody_elements:
            rows = tbody.find_all("tr", recursive=False)
            if len(rows) < 1:
                continue

            main_row = rows[0].find_all("td", recursive=False)
            if len(main_row) >= 7:
                event = {
                    "Event Start": main_row[3].get_text(strip=True),
                    "Event End": main_row[4].get_text(strip=True),
                    "Location": main_row[5].get_text(strip=True),
                    "Event Name": main_row[5].get_text(strip=True),
                    "Group Contact": main_row[6].get_text(strip=True),
                }

            if len(rows) > 1:
                service_details = []
                service_div = rows[1].find("div", attrs={"class": None})
                service_items = service_div.find_all("li")
                print(service_div)
                for item in service_items:
                    text = item.get_text(separator=" ", strip=True)
                    service_details.append(text)
                event["Services"] = "; ".join(service_details)

            events.append(event)

        return events

    def export_to_csv(self, events, filename="events.csv"):
        """Exports the scraped event data to a CSV file.

        Args:
            events: A list of dictionaries containing event data.
            filename: The name of the file to which the data will be exported.
        """
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            if len(events) < 1:
                print("No events to export.")
                return

            csvwriter = csv.DictWriter(csvfile, fieldnames=list(events[0].keys()))
            csvwriter.writeheader()
            for event in events:
                csvwriter.writerow(event)
        print(f"Data exported to {filename} successfully.")

    def close(self):
        """Closes the Selenium WebDriver session."""
        self.driver.quit()


if __name__ == "__main__":
    scraper = EventScraper(
        "", ""
    )
    scraper.login()
    scraper.navigate_to_scrape_url()
    scraper.click_expand_services()
    events = scraper.scrape_events()
    scraper.export_to_csv(events)
    scraper.close()
