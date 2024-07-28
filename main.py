import requests
from bs4 import BeautifulSoup
from newspaper import Article
import schedule
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import nltk
from tenacity import retry, stop_after_attempt, wait_fixed
from twilio.rest import Client
import os
from dotenv import find_dotenv, load_dotenv

dotenv_path = find_dotenv()

load_dotenv(dotenv_path)

SMTP_MAIL = os.getenv('SMTP_MAIL')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')

# Download the NLTK 'punkt' tokenizer data
nltk.download('punkt')

# Function to fetch and summarize news articles
@retry(stop=stop_after_attempt(3), wait=wait_fixed(10))
# Function to fetch and summarize news articles
def fetch_and_summarize_news():
    print("Summarizing news...")
    news_sources = {
        'BBC': 'http://feeds.bbci.co.uk/news/rss.xml',
        # Add more news sources here
    }
    
    summaries = []

    for source, url in news_sources.items():
        response = requests.get(url)
        soup = BeautifulSoup(response.content, features='xml')
        articles = soup.findAll('item')
        
        for a in articles[:5]:  # Limiting to 5 articles per source
            news_url = a.find('link').text
            article = Article(news_url)
            article.download()
            article.parse()
            article.nlp()
            summaries.append({
                'source': source,
                'title': article.title,
                'summary': article.summary,
                'url': news_url
            })
    
    return summaries

# Function to send WhatsApp message


def send_whatsapp_message(summaries):
    account_sid = TWILIO_ACCOUNT_SID
    auth_token = TWILIO_AUTH_TOKEN
    from_whatsapp_number = 'whatsapp:+14155238886'  # Twilio sandbox number
    to_whatsapp_number = 'whatsapp:+971582745157'

    client = Client(account_sid, auth_token)

    message_body = "Daily News Summary:\n\n"
    for summary in summaries:
        message_body += f"Title: {summary['title']}\n"
        message_body += f"Source: {summary['source']}\n"
        message_body += f"Read more: {summary['url']}\n\n"

    client.messages.create(
        body=message_body, from_=from_whatsapp_number, to=to_whatsapp_number)


# Function to send email
def send_email(summaries):
    # Email configuration
    email_user = SMTP_MAIL
    email_password = SMTP_PASSWORD
    email_send = 'nihargandhi0000@gmail.com'
    subject = 'Daily News Summary'
    
    msg = MIMEMultipart("alternative")
    msg['From'] = email_user
    msg['To'] = email_send
    msg['Subject'] = subject

    # Create the plain-text and HTML version of your message
    text = ""
    html = """\
    <html>
      <body>
        <h2>Daily News Summary</h2>
    """

    for summary in summaries:
        text += f"Source: {summary['source']}\n"
        text += f"Title: {summary['title']}\n"
        text += f"Summary: {summary['summary']}\n"
        text += f"Read more: {summary['url']}\n\n"

        html += f"""\
        <div style="border: 1px solid #cccccc; margin-bottom: 10px; padding: 10px;">
          <h3>{summary['title']}</h3>
          <p><strong>Source:</strong> {summary['source']}</p>
          <p>{summary['summary']}</p>
          <p><a href="{summary['url']}">Read more</a></p>
        </div>
        """

    html += """\
      </body>
    </html>
    """

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    msg.attach(part1)
    msg.attach(part2)

    # body = ''
    # for summary in summaries:
    #     body += f"Source: {summary['source']}\n"
    #     body += f"Title: {summary['title']}\n"
    #     body += f"Summary: {summary['summary']}\n"
    #     body += f"Read more: {summary['url']}\n\n"
    
    # msg.attach(MIMEText(body, 'plain'))
    
    # Send the message via Gmail SMTP server
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(email_user, email_password)
    text = msg.as_string()
    server.sendmail(email_user, email_send, text)
    server.quit()

# Function to perform the daily task
def daily_news_summary():
    try:
        summaries = fetch_and_summarize_news()
        if summaries:
            send_whatsapp_message(summaries)
            send_email(summaries)
        else:
            print("No summaries to send.")
    except Exception as e:
        print(f"Error in daily_news_summary: {e}")

# Schedule the task
schedule.every().day.at("10:00").do(daily_news_summary)
schedule.every().day.at("22:00").do(daily_news_summary)

# Keep the script running
while True:
    schedule.run_pending()
    time.sleep(1)
