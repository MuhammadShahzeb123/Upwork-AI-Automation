from functions import *
import streamlit as st
import functions


st.header("Hello")


st.write("This is a very fucking complex software made by me That will scrape all the jobs from upwork.com and find all the info about the client and then send him the e-mail directly without needing any help at all. It interacts with AI to find all the information or extract the information in the text without needing anything or any kind of assistance of human mind. Make sure to use it everyday so to send at least 50 emails that are highly targeted.")

keyword = st.text_input("Keyword")



if st.button("Search"):
    # Function to scrape the Upwork job listings
    jobs = scrape_upwork_jobs(keyword)
    print(1)

    functions.ask_gemini_about_company()

    eligible_jobs = []
    for job in jobs:
        try: 
            if gemini_check_job(job):
                eligible_jobs.append(job)
                st.success(f"{job}\n\n")
                print(job)
                
        except:
            st.error(job)
        time.sleep(30)
    print(2)

    jobs = eligible_jobs  # Update the original 'jobs' list
    
    with open('upwork_jobs_eligible.txt', 'w', encoding='utf-8') as file:
        for job in jobs:
            file.write(f"{job}\n")
        file.close()

    for job in jobs:
        data = gemini_info_search(job)
        print(3)
        if data[0] and data[1] is not None:
            if None in data[1]:
                websites = google_search(data)
                original_company_website = ask_gemini_about_company(job, websites)
                print(4)
            else:
                original_company_website = data[1]
                print(4)
            
        emails = find_email_using_snov_io(original_company_website)
        print(5)
        website_data = scrape_info(original_company_website)
        print(6)
        cleint_data = find_info(website_data, job)
        print(7)
        email_text = write_an_email(cleint_data, job)
        print(8)
        for email in emails:
            send_email(email, "Upwork Job Proposal", email_text)
        
        
if st.button("Find Info and Send Email"):
    
    with open("upwork_jobs_eligible.txt", "r", encoding="utf-8") as file:
        jobs = file.readlines()
    
    for job in jobs:
        job = fix_urls_jobs(job)
        data = gemini_info_search(job)
        print("3" + f' {data}')
        original_company_website = None
        if "None" in data[0] and data[1]:
            continue
        
        
        if data[2] is 0:
            if "None" in data[1]:
                data.pop()
                sleep(1)
                websites = google_search(data)
                print(websites)
                original_company_website = ask_gemini_about_company(job, websites)
                print("4" + f' {original_company_website}')
            else:
                company_website_url_fixed = fix_url_answer(data[1])
                original_company_website = company_website_url_fixed
                print("4" + f' {original_company_website}')
        

            if original_company_website is not None:
                emails = find_email_using_snov_io(original_company_website)
                print(5)
                if emails == []:
                    continue
                website_data = scrape_info(original_company_website)
                print(6)
                cleint_data = find_info(website_data, job)
                print(7)
                email_text = write_an_email(cleint_data, job)
                print(8)
                for email in emails:
                    send_email(email, "Upwork Job Proposal", email_text)
                    st.success(f"Email Sent to {email}")
    
        elif data[2] is 1:
            continue