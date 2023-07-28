import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib import colors
from reportlab.platypus.flowables import Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import gspread
from gspread_dataframe import set_with_dataframe

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

st.title("Enter Details for Invoice")

# Get user input for customer details
name = st.text_input('Your Name')
phno = st.text_input('Enter your Phone Number')
email = st.text_input('Enter Your Email-ID')
invoice_date = st.date_input('Date')
ad = st.text_area("Billing Address")


# Predefined list of items
predefined_items = ['Eggs','Milk','Bread','Chocolates','Coffee','Fruits','Protien Bar','Butter','Cake','Cheese']

# Get the number of items and their details for the invoice
num_items = st.number_input('Number of items', min_value=0, step=1)
data = []
for i in range(num_items):
    item_key = f"item_{i}"
    price_key = f"price_{i}"
    quant_key = f"quant_{i}"
    item = st.selectbox('Item', predefined_items, key=item_key)
    price = st.number_input('Price of item', key=price_key, min_value=0)
    quantity = st.number_input('Quantity of item', key=quant_key, min_value=0)
    total = price * quantity
    data.append([item, price, quantity, total])

# Create a DataFrame from the invoice item data
df = pd.DataFrame(data,columns = ['Item','Price','Quantity','Total'])

# Display the invoice item table
st.table(df)
stotal = df['Total'].sum()

# Get the mode of payment from the user
mop = st.selectbox('Mode of Payement',['Cash','Credit Card','Debit Card','UPI'])


# Create a Flowable to render the DataFrame as a table
class DataFrameTable(Flowable):
    def __init__(self, data):
        self.data = data
        self.widths = [100, 100, 100, 100]  # Adjust column widths as needed

    def wrap(self, avail_width, avail_height):
        return sum(self.widths), len(self.data) * 30

    def draw(self):
        table = Table(self.data, self.widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        table.wrapOn(self.canv, 0, 0)
        table.drawOn(self.canv, 0, 0)

# If the "Print Invoice" button is clicked
if st.button('Next'):
    # Check if all required fields are filled
    if not name or not phno or not email or not ad or not num_items:
        st.error("Please fill in all the required fields.")
    else:
        # Generate a unique invoice number based on the phone number
        last_four_digits = phno[-4:]
        cust_id = f"INV_{last_four_digits}"

        # Generate the PDF invoice
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        
        # Get the sample stylesheet
        styles = getSampleStyleSheet()

        # Custom styles for the invoice
        invoice_title_style = ParagraphStyle(
            'InvoiceTitleStyle',
            parent=styles['Title'],
            fontSize=24,
            textColor='blue',
            spaceAfter=10,
        )

        separator_style = ParagraphStyle(
            'SeparatorStyle',
            parent=styles['Normal'],
            fontSize=12,
            textColor='gray',
            spaceAfter=5,
        )

        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor='black',
            spaceAfter=5,
        )

        subtotal_style = ParagraphStyle(
            'SubtotalStyle',
            parent=styles['Heading3'],
            fontSize=14,
            textColor='darkblue',
            spaceAfter=10,
        )

        # Sample data for the invoice
        elements = []
        elements.append(Paragraph('Invoice', invoice_title_style))
        elements.append(Paragraph(f'Customer ID: {cust_id}', styles['Normal']))
        elements.append(Paragraph(f'Invoice Date: {invoice_date}', styles['Normal']))
        elements.append(Paragraph("Transtag Lifecycle pvt. ltd.", header_style))
        elements.append(Paragraph("A-105, RIDGEWOOD ESTATE", styles['Normal']))
        elements.append(Paragraph("DLF PHASE IV", styles['Normal']))
        elements.append(Paragraph("GURGAON - 122001", styles['Normal']))
        elements.append(Paragraph("Haryana", styles['Normal']))
        elements.append(Paragraph('<p class="line-spacing">------------------------------------------------------------</p>', separator_style))
        elements.append(Paragraph("Bill To", header_style))
        elements.append(Paragraph(f"Name: {name}", styles['Normal']))
        elements.append(Paragraph(f"Phone Number: {phno}", styles['Normal']))
        elements.append(Paragraph(f"Billing Address: {ad}", styles['Normal']))
        elements.append(Paragraph(f"Mode of Payment: {mop}", styles['Normal']))


        # Convert the DataFrame to a list of lists for the Flowable
        df_data = [df.columns.to_list()] + df.values.tolist()
        
        # Render the DataFrame as a table using the custom Flowable
        elements.append(DataFrameTable(df_data))
        elements.append(Paragraph(f"Subtotal = {stotal}",header_style))
        elements.append(Paragraph(f"Thank You", subtotal_style))

        col3, col4, col5 = st.columns(3)
        with col5:
            st.markdown(f'####  Subtotal = {stotal}')
        with col3:
            st.markdown('## Thank You')

        doc.build(elements)

        # Save the PDF to a temporary buffer
        pdf_data = buffer.getvalue()
        buffer.close()

        # Offer the file to download
        st.markdown("##### Click below to download the invoice as a PDF file.")
        st.download_button(
            label="Download Invoice",
            data=pdf_data,
            file_name=f"invoice_{cust_id}.pdf",
            mime="application/pdf"
        )
       
        # Update Google Sheet with invoice data
        try:
            # Load data from the public Google Sheet
            gc = gspread.service_account(filename='invoice-system-app.json')
            sheet_url = 'https://docs.google.com/spreadsheets/d/1whMQ8VX585ea-1_gdVi3I41bP1tHFtwYcJ0hTaDfvyM/edit?usp=sharing'
            sh = gc.open_by_url(sheet_url)
            worksheet = sh.get_worksheet(0)  # Replace 0 with the index of your desired worksheet

            # Read the existing data from the Google Sheet
            existing_data = worksheet.get_all_records()
            existing_df = pd.DataFrame(existing_data)

            # Append the new invoice data to the existing DataFrame
            invoice_data = df[['Item','Quantity']]
            invoice_data.insert(0, 'Invoice Date', invoice_date)
            invoice_data.insert(0, 'Email ID', email)
            invoice_data.insert(0, 'Name', name)
            invoice_data.insert(0, 'Customer Id', cust_id)
                
            updated_df = pd.concat([existing_df,invoice_data], ignore_index=True)

            # Clear the worksheet contents to avoid duplicate data
            worksheet.clear()

            # Write the updated DataFrame back to the Google Sheet
            set_with_dataframe(worksheet, updated_df, resize=False, include_index=False, include_column_header=True)

            st.success("Invoice data updated in Google Sheet successfully!")
            st.markdown(f"View the Google Sheet: [Invoice Google Sheet]({sheet_url})")
        except Exception as e:
            st.error(f"Error updating Google Sheet: {e}")


   




   



