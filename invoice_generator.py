import os
import subprocess
import shutil
from datetime import datetime, timedelta

from config import load_config

# All personal details, rates and hours are read from config.toml.


def calculate_dynamic_dates():
    """Calculate the invoice dates."""
    today = datetime.today()
    # In Python, weekday() is 0 for Monday and 6 for Sunday
    days_to_sunday = 6 - today.weekday()
    current_sunday = today + timedelta(days=days_to_sunday)

    current_monday = current_sunday - timedelta(days=6)
    prev_monday = current_monday - timedelta(days=7)

    return {
        "invoice_date": today.strftime("%d/%m/%Y"),
        "due_date": current_sunday.strftime("%d/%m/%Y"),
        "service_period": f"{prev_monday.strftime('%d/%m/%Y')} - {current_sunday.strftime('%d/%m/%Y')}",
    }


def generate_invoice():
    cfg = load_config()
    carer, client, bill_to, bank = cfg["carer"], cfg["client"], cfg["bill_to"], cfg["bank"]
    rates, work = cfg["rates"], cfg["work"]

    send_dir = "./send"
    invoice_dir = "./invoice"
    os.makedirs(invoice_dir, exist_ok=True)
    os.makedirs(send_dir, exist_ok=True)
    # 1. Calculate dates
    dates = calculate_dynamic_dates()

    # 2. Calculate costs
    mileage_km = sum(work["mileage_trips_km"])
    daytime_cost = float(rates["hourly"]) * float(work["daytime_hr"])
    mileage_cost = float(mileage_km) * float(rates["mileage_per_km"])

    # 3. Assemble template data
    invoice_data = {
        "carer_name": carer["name"],
        "carer_address": carer["address"],
        "carer_email": carer["email"],
        "carer_phone": carer["phone"],
        "carer_abn": carer["abn"],
        "client": client["name"],
        "customer_name": client["customer_name"],
        "ndis_no": client["ndis_no"],
        "bill_to_name": bill_to["name"],
        "bill_to_email": bill_to["email"],
        "bank_name": bank["name"],
        "bank_bsb": bank["bsb"],
        "bank_acc": bank["account"],
        "invoice_date": dates["invoice_date"],
        "due_date": dates["due_date"],
        "service_period": dates["service_period"],
        "salary_ph": f"{rates['hourly']:.2f}",
        "daytime_hr": f"{work['daytime_hr']:g}",
        "daytime_cost": f"{daytime_cost:.2f}",
        "evening_hr": f"{work['evening_hr']:g}",
        "saturday_hr": f"{work['saturday_hr']:g}",
        "sunday_hr": f"{work['sunday_hr']:g}",
        "holiday_hr": f"{work['holiday_hr']:g}",
        "sleepover_hr": f"{work['sleepover_hr']:g}",
        "mileage_km": f"{mileage_km:g}",
        "mileage_cost_per_km": f"{rates['mileage_per_km']:.2f}",
        "mileage_cost": f"{mileage_cost:.2f}",
    }

    # 4. LaTeX template (no "km" unit in the Hours column of the Mileage row)
    latex_template = r"""\documentclass[11pt, a4paper]{article}
\usepackage[margin=1in]{geometry}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{xeCJK}

\setlength{\parindent}{0pt}

\begin{document}

\begin{center}
    \Huge \textbf{TAX INVOICE}
\end{center}
\vspace{1cm}

\begin{minipage}[t]{0.48\textwidth}
    \textbf{Carer Details:} \\
    Name: {{carer_name}} \\
    Address: {{carer_address}} \\
    Email: {{carer_email}} \\
    Phone: {{carer_phone}} \\
    ABN: {{carer_abn}}
\end{minipage}
\hfill
\begin{minipage}[t]{0.48\textwidth}
    \textbf{Invoice Details:} \\
    Client: {{client}} \\
    Date: {{invoice_date}} \\
    Due Date: {{due_date}} \\
    Service Period: {{service_period}}
\end{minipage}

\vspace{1cm}
\textbf{Bill To:} \\
{{bill_to_name}} \\
{{bill_to_email}}

\vspace{1cm}
\textbf{Description:} \\
\vspace{0.3cm}

\renewcommand{\arraystretch}{1.5}
\begin{tabularx}{\textwidth}{X c c c}
    \toprule
    \textbf{Item} & \textbf{Hours/Qty} & \textbf{Rate} & \textbf{Total} \\
    \midrule
    Weekday Daytime \newline \small{(Customer: {{customer_name}}, NDIS: {{ndis_no}})} & {{daytime_hr}} hr & \${{salary_ph}} / hr & \${{daytime_cost}} \\
    Weekday Evening & {{evening_hr}} & - & \$0.00 \\
    Saturday & {{saturday_hr}} & - & \$0.00 \\
    Sunday & {{sunday_hr}} & - & \$0.00 \\
    Public Holiday & {{holiday_hr}} & - & \$0.00 \\
    Night Time Sleepover & {{sleepover_hr}} & - & \$0.00 \\
    Mileage (km) & {{mileage_km}} & \${{mileage_cost_per_km}} / km & \${{mileage_cost}} \\
    \bottomrule
\end{tabularx}

\vspace{1.5cm}
\textbf{Bank Details} \\
Name: {{bank_name}} \\
BSB: {{bank_bsb}} \\
Account Number: {{bank_acc}}

\end{document}
"""

    # 5. Fill in the data
    for key, value in invoice_data.items():
        latex_template = latex_template.replace("{{" + key + "}}", str(value))

    # 6. Write the .tex file and compile
    tex_filename = os.path.join(invoice_dir, "invoice.tex")
    with open(tex_filename, "w", encoding="utf-8") as f:
        f.write(latex_template)

    print("Compiling LaTeX to PDF...")
    try:
        subprocess.run(
            [
                "xelatex",
                f"-output-directory={invoice_dir}",
                "-interaction=nonstopmode",
                tex_filename,
            ],
            check=True,
        )
        print(f"Successfully generated {invoice_dir}/invoice.pdf")

        pdf_path_invoice = os.path.join(invoice_dir, "invoice.pdf")
        pdf_path_send = os.path.join(send_dir, "invoice.pdf")
        if os.path.exists(pdf_path_invoice):
            shutil.copy2(pdf_path_invoice, pdf_path_send)
            print(f"Successfully generated PDF in {invoice_dir}")
            print(f"Successfully copied PDF to {send_dir}")

        # Clean up auxiliary files
        for ext in [".aux", ".log"]:
            aux_file = tex_filename.replace(".tex", ext)
            if os.path.exists(aux_file):
                os.remove(aux_file)

    except subprocess.CalledProcessError as e:
        print(f"Error during compilation: {e}")
    except FileNotFoundError:
        print("Error: 'xelatex' command not found.")


if __name__ == "__main__":
    generate_invoice()
