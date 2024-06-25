# email/send_email.py
from fastapi import FastAPI, Form

import smtplib
from email.message import EmailMessage

app = FastAPI()

@app.post("/submit")
def submit(name: str = Form(), emailAddress: str = Form(), message: str = Form()):
    print(name)
    print(emailAddress)
    print(message)

    email_address = "nest70518@gmail.com"  # type Email
    email_password = "pB**+^>+z@N4p6H"  # If you do not have a gmail apps password, create a new app with using generate password. Check your apps and passwords https://myaccount.google.com/apppasswords

    # create email
    msg = EmailMessage()
    msg['Subject'] = "Email subject"
    msg['From'] = email_address
    msg['To'] = "nest70518@gmail.com"  # type Email
    msg.set_content(
        f"""\
    Name : {name}
    Email : {emailAddress}
    Message : {message}    
    """,

    )
    # send email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(email_address, email_password)
        smtp.send_message(msg)

    return "email successfully sent"