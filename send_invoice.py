import os
import smtplib
import mimetypes
from email.message import EmailMessage

from config import load_config

# SMTP settings, addresses, subject and body are read from config.toml.

SEND_DIR = "./send"  # Directory containing the files to send


def send_invoices():
    email = load_config()["email"]

    # Check that the directory exists
    if not os.path.exists(SEND_DIR):
        print(f"Error: directory '{SEND_DIR}' does not exist.")
        return

    # Collect all files in the directory
    files_to_send = [
        f for f in os.listdir(SEND_DIR) if os.path.isfile(os.path.join(SEND_DIR, f))
    ]

    if not files_to_send:
        print(f"Directory '{SEND_DIR}' is empty, nothing to send.")
        return

    # Build the message
    msg = EmailMessage()
    msg["Subject"] = email["subject"]
    msg["From"] = email["sender"]
    msg["To"] = email["receiver"]
    msg.set_content(email["body"])

    # Attach each file
    print(f"Found {len(files_to_send)} file(s), attaching...")
    for filename in files_to_send:
        filepath = os.path.join(SEND_DIR, filename)

        # Guess the MIME type (application/pdf for PDFs)
        ctype, encoding = mimetypes.guess_type(filepath)
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)

        with open(filepath, "rb") as f:
            msg.add_attachment(
                f.read(), maintype=maintype, subtype=subtype, filename=filename
            )
        print(f" - Attached: {filename}")

    # Send the email
    print("\nConnecting to SMTP server...")
    try:
        # Connect over SSL
        with smtplib.SMTP_SSL(email["smtp_server"], email["smtp_port"]) as server:
            server.login(email["sender"], email["password"])
            server.send_message(msg)
        print("✅ Email and all attachments sent successfully!")

        print("Cleaning up sent files...")
        for filename in files_to_send:
            filepath = os.path.join(SEND_DIR, filename)
            try:
                os.remove(filepath)
                print(f" - Deleted: {filename}")
            except Exception as e:
                print(f" ❌ Could not delete {filename}: {e}")
        # ---------------------

    except Exception as e:
        print(f"❌ Failed to send email: {e}")


if __name__ == "__main__":
    send_invoices()
