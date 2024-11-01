from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import google.generativeai as genai
import time
import ssl
import smtplib
import random
import re
import requests
import os
from time import sleep


proxy_ip = "161.123.152.115"
proxy_port = "6360"


model = genai.GenerativeModel(model_name='gemini-1.5-flash')
service = Service(ChromeDriverManager().install())
options = webdriver.ChromeOptions()



def scrape_upwork_jobs(keyword: str) -> list: #Done
    jobs = []
    try:
        driver = webdriver.Chrome(service=service, options=options)
        for i in range(1, 3):
            url = f'https://www.upwork.com/nx/search/jobs?per_page=50&q={keyword}%20%28com%20AND%20www%29'
            driver.get(url)
            time.sleep(random.randint(2, 5))
            for i in range(3, 102, 2):
                time.sleep(random.randint(2, 5))
                
                # Find the <p> elements by XPath
                job_listings = driver.find_elements(By.XPATH, f'//*[@id="air3-line-clamp-{i}"]/p')

                
                for job_listing in job_listings:  # Loop through the list of elements
                    job = job_listing.text  # Extract the text from each <p> element
                    jobs.append(job)  # Append the text to the jobs list
                    
    except:
        return jobs
    finally:
        print("Driver unexpectedly closed.")

    driver.quit()
    return jobs


def gemini_check_job(job_text: str) -> bool: #Done
    genai.configure(api_key=os.environ["GOOGLE_API_KEY_AI"])
    response = model.generate_content(f"```Job: {job_text}```" + 
                                      "\n\nAbout Me: We are a Company that provides AI Autoamtions services to Agency Owners and Service based businesses and help them reach their ideal customers using AI. We do this by send 100k+ automated DM and then book meetings using AI. We can also create automatios for scraping Data from websites and tasks that require repetition (AI can be integrated in any workflow we create)" + 
                                      "\n\n\nI've given you a Job post above and told you about myself, we want you to check if we can do that job or not. If we are able to do the job then reply me 'yes' and if not then 'no'. " + 
                                      "\n\n\nDon't send me anything else!")
    if "yes" in response.text:
        return True
    else:
        return False


def validate_response(response_text):
    pattern = r'^(None|[^,]+),\s*(None|[^,]+)$'  # Matches "company_name, website" or "None, None"
    return bool(re.match(pattern, response_text.strip()))


def gemini_info_search(job_text: str) -> list: #Done
    genai.configure(api_key=os.environ["GOOGLE_API_KEY_AI"])
    response = model.generate_content(f"""Job Description: `{job_text}`
                                      
                                      
                                          Only provide a *comma-separated* pair in this format: `company_name,website`. 
                                          If no company or website is found, respond with exactly: `None,None`.
                                          Remember that these are Jobs so please find the Company name and email with care... It can be tricky for you.
                                          If you only find compnay name then respond: `company_name,None` and if you only find a website then respond: `None,website`. 
                                          Provide no other text or information outside of this.
                                          If you find an incomplete URL... ignore it. and return None for the website.
                                          Look for Big Brands and eCommerce URL. Don't send my those!
                                          NOTE: Your final response must be `company_name, website` and if any of those is not found then None in that place.
                                          If you find multiple links, then only give me the one you think that will belong to the company
                                          Don't send me anything else!""")
   
    if validate_response(response.text):  # Call the validation function
        data = [item.strip() for item in response.text.split(",")]
        data.append(0)
        return data
    else:
        print(f"Invalid response: {response.text}")
        return [None, None, 1]  # Return a safe default   


def google_search(data:list) -> str:
    # Extract API key and Custom Search Engine (CSE) ID
    search_api = os.environ.get("GOOGLE_API_KEY_SEARCH")
    cse_id = '826dfb73d8c7347d9'
    
    # Check if API key is available
    if not search_api:
        return "Error: Google API key not found in environment variables."

    # Extract company name and create the search query
    company_name, _ = data
    search_query = company_name + " About page and Contact Info"
    
    # API request setup
    url = 'https://www.googleapis.com/customsearch/v1'
    params = {
        'q': search_query,
        'key': search_api,
        'cx': cse_id,
    }

    # Send the request
    response = requests.get(url, params=params)
    
    # Check the response status
    if response.status_code != 200:
        return f"Error: Request failed with status code {response.status_code}"

    # Attempt to parse the JSON response
    response_json = response.json()
    
    # Handle cases where no items are found in the response
    if 'items' not in response_json:
        return "No results found."

    # Format the search results into a readable text format
    results_text = ""
    for i, item in enumerate(response_json['items'][:10]):
        results_text += f"Result {i+1}:\n"
        results_text += f"Title: {item.get('title', 'N/A')}\n"
        results_text += f"Link: {item.get('link', 'N/A')}\n"
        results_text += f"Snippet: {item.get('snippet', 'N/A')}\n\n"

    return results_text
    
    
def ask_gemini_about_company(job_text: str, google_search_text: str) -> str: #Done
    genai.configure(api_key=os.environ["GOOGLE_API_KEY_AI_21"])
    response = model.generate_content(f"""
                                      Job Text: `{job_text}`
                                      
                                      Google Search: `{google_search_text}`
                                      
                                      If the Google Search is empty then return Send me None as you response
                                      
                                      If you are unsure which one is the real company then return me None too
                                      
                                      I have provided you a job text and a Google search of the list of companies that can be the original company who posted the job
                                      
                                      What I want you to do is to go through all the results of the Google search and tell me which company can it be
                                      
                                      Only send me the company URL, no other thing is needed. Just send me back the URL off the company you think is the company who posted the job
                                      
                                      NOTE: You final Output should only be: url
                                      
                                      Don't send me anything else!""")
    return response.text    


def find_email_using_snov_io(url: str) -> list: #Done
    options.add_argument(f'--proxy-server=socks5://{proxy_ip}:{proxy_port}')
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://snov.io/email-finder/")
    domain_input = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/section[2]/div[1]/div/form/div[1]/input"))
    )
    domain_input.clear()
    domain_input.send_keys(url)
    button = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/section[2]/div[1]/div/form/div[1]/button"))
    )
    button.click()
    button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "/html/body/section[2]/div[1]/div/form/div[1]/div/a[1]"))
    )
    button.click()
    print(1)
    sleep(10)
    main_element = driver.find_element(By.XPATH, '/html/body/section[2]/div[1]/div/form/div[2]/ul')
    print(2)
    span_elements = main_element.find_elements(By.TAG_NAME, 'span')
    print(span_elements)
    emails = [span.text for span in span_elements]
    print(emails)
    cleaned_emails = list(filter(None, emails))
    print(cleaned_emails)
    if cleaned_emails != []:
        for i in range(3):
            cleaned_emails.pop()
            print(f"{i} - 6")
    driver.quit()
    return cleaned_emails


def scrape_info(url: str) -> list: #Done
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://" + url)
    main_element = driver.find_element(By.XPATH, '/html')
    all_elements = main_element.find_elements(By.XPATH, './/*')
    text_list = []
    for element in all_elements:
        text = element.text.strip()
        if text:
            text_list.append(text)
    driver.quit()
    return text_list


def find_info(scraped_info: list, job_text: str) -> str: #Done
    genai.configure(api_key=os.environ["GOOGLE_API_KEY_AI_21"])
    text = " | ".join(scraped_info)
    response = model.generate_content(f"""I'm going to be providing you with a website front page And what I want you to do is find any info about the owner of the website I am also be giving you the job tax that the owner posted on upwork.com. 
                                      
                                      ```{text}```
                                      
                                      ```{job_text}```
                                      
                                      
                                      Now that you have the website front page and the job text, I want you to find the owner's data for example you can find his name what his company does and what kind of services does he provide.
                                      
                                      When you find all of this data, Give me back all of what you find""")
    return response.text


def write_an_email(client_info: str, job_text: str): #Done
    genai.configure(api_key=os.environ["GOOGLE_API_KEY_AI_22"])
    response = model.generate_content(f"""I am going to give you clients data about what he does, what his name is, and what services does he provide
                                      
                                      Info: ```{client_info}```
                                      
                                      This is the job that was posted by the this client: ```{job_text}```
                                      
                                      Now What I want you to do is to carefully understand all the client info and job text and write an Email. (If name not available, write hey there or don't write anything there.)
                                      
                                      The e-mail should be focusing on what he asked in the job text and how we can provide it.
                                      
                                      I am an AI Autiomation expert that who specialize in helping my clients solve repetitive tasks and increase efficiency by building complex systems and implementing AI.
                                      
                                      You have to tell the client how I can solve his problem using my skills. In the CTA ask him to book an appointment with me and I am looking forward to it.""")
    return response.text


def send_email(recipient_email: str, subject: str, message_text: str) -> bool: #Done
    # Sender email and SMTP server details
    sender_email = "email"
    sender_password = "apppass"  # Replace with your email password
    smtp_server = "smtp.gmail.com"
    smtp_port = 465  # Port number for SSL

    try:
        # Create the MIME message
        msg = MIMEMultipart()
        msg['From'] = f"You know... <{sender_email}>"
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message_text, "plain"))

        # Create a secure SSL context
        context = ssl.create_default_context()

        # Connect to the SMTP server using SSL
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(sender_email, sender_password)  # Login with email and password
            server.sendmail(sender_email, recipient_email, msg.as_string())  # Send email

        return True  # Return True if email is successfully sent

    except Exception as e:
        print(f"Failed to send email: {e}")
        return False  # Return False if there's any issue


def fix_urls_jobs(text):
    # Pattern to find URLs that start with "https://" and are missing "www" and a valid domain extension
    pattern = r"https://(\.?)(\w+)\.(\w+)?(/[\w\-./]*)?"
    
    # Substitute pattern to add "www" if missing and a default ".com" if the domain extension is missing
    def replacer(match):
        prefix, domain, extension, path = match.groups()
        # Add 'www' if missing
        prefix = "www." if not prefix else ""
        # Add '.com' if no valid domain extension is present
        extension = extension if extension else "com"
        return f"https://{prefix}{domain}.{extension}{path if path else ''}"

    fixed_text = re.sub(pattern, replacer, text)
    
    return fixed_text    


with open("upwork_jobs_eligible.txt", "r", encoding="utf-8") as file:
    jobs = file.readlines()


def fix_url_answer(url: str):
    if url.startswith("www") and url.endswith("com"):
        return url
    
    url = re.sub(r"https://|/$", "", url)
    
    # Remove any leading dot
    if url.startswith("."):
        url = url[1:]

    # Extract the root part of the URL (e.g., "original_url")
    root_url = url.split("/")[0].split(".")[0]

    # Construct the fixed URL with "www" and ".com"
    fixed_url = f"www.{root_url}.com"
    
    return fixed_url