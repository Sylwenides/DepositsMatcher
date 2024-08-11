import streamlit as st
import pandas as pd
import io

# Set the title of the app
st.title("Contact and Deposit Matcher with Currency Summary")

# Descriptions for each upload
st.subheader("File 1: Successful Deposits")
st.write("Please upload the file containing data on successful deposits. This could be an `.xls`, `.xlsx`, or `.csv` file.")
uploaded_file1 = st.file_uploader("Choose the first file (Successful Deposits)", type=["xls", "xlsx", "csv"])

st.subheader("File 2: Notes")
st.write("Please upload the file containing your notes. This could be an `.xls`, `.xlsx`, or `.csv` file.")
uploaded_file2 = st.file_uploader("Choose the second file (Notes)", type=["xls", "xlsx", "csv"])

# Field to enter a filter for the Note column
note_filter = st.text_input("Enter a keyword to filter the Note field (optional)")

def load_data(file):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    elif file.name.endswith((".xls", ".xlsx")):
        return pd.read_excel(file)

if uploaded_file1:
    deposits_df = load_data(uploaded_file1)
    st.subheader("Preview of Successful Deposits File")
    st.write(deposits_df.head())  # Display the first 5 rows of the deposits file

if uploaded_file2:
    notes_df = load_data(uploaded_file2)
    
    # Apply the note filter if provided
    if note_filter:
        notes_df = notes_df[notes_df['Note'].str.contains(note_filter, case=False, na=False)]
        st.write(f"Filtering notes with keyword: {note_filter}")
    
    st.subheader("Preview of Filtered Notes File")
    st.write(notes_df.head())  # Display the first 5 rows of the filtered notes file

if uploaded_file1 and uploaded_file2:
    # Convert dates to datetime
    deposits_df['Transaction Date'] = pd.to_datetime(deposits_df['Transaction Date'])
    notes_df['Date'] = pd.to_datetime(notes_df['Date'])

    # Extract the User Name from the first file and Username from the second file
    deposits_usernames = deposits_df['User Name'].unique()
    notes_usernames = notes_df['Username'].unique()

    # Find the matching usernames
    matching_usernames = set(deposits_usernames).intersection(notes_usernames)

    st.subheader("Matching User Names")
    if matching_usernames:
        st.write(list(matching_usernames))  # Display the matching usernames

        # Create a list to hold the matched results
        matched_records = []

        for username in matching_usernames:
            user_notes = notes_df[notes_df['Username'] == username]
            user_deposits = deposits_df[deposits_df['User Name'] == username]

            # Sort deposits by Transaction Date for this user
            user_deposits = user_deposits.sort_values(by='Transaction Date')
            
            for _, note_row in user_notes.iterrows():
                contact_date = note_row['Date']
                
                # Find the first deposit after the contact date
                deposit_after_contact = user_deposits[user_deposits['Transaction Date'] > contact_date]
                
                if not deposit_after_contact.empty:
                    first_deposit = deposit_after_contact.iloc[0]
                    combined_row = {
                        'Username': username,
                        'Date of the note': contact_date,
                        'Date of the deposit': first_deposit['Transaction Date'],
                        'Agent': note_row.get('Agent', ''),  # Assuming there's an 'Agent' column in notes
                        'Amount of the deposit': first_deposit['Amount'],  # Assuming 'Amount' in deposits
                        'Currency of the deposit': first_deposit['Currency'],  # Assuming 'Currency' in deposits
                        'Note': note_row['Note']  # Including the note itself
                    }
                    matched_records.append(combined_row)
        
        # Convert matched records to a DataFrame
        matched_df = pd.DataFrame(matched_records)

        st.subheader("Matched Results")
        if not matched_df.empty:
            st.write(matched_df.head())  # Show a preview of the matched results

            # Group by Currency of the deposit and sum the Amount of the deposit
            currency_summary = matched_df.groupby('Currency of the deposit')['Amount of the deposit'].sum().reset_index()

            st.subheader("Currency Summary")
            st.write(currency_summary)

            # Option to download the matched file in different formats
            st.subheader("Download Matched File")

            # Export as CSV
            csv_data = matched_df.to_csv(index=False).encode('utf-8')
            st.download_button(label="Download as CSV", data=csv_data, file_name="matched_contacts_and_deposits.csv", mime="text/csv")

            # Export as XLS
            xls_buffer = io.BytesIO()
            with pd.ExcelWriter(xls_buffer, engine='xlsxwriter') as writer:
                matched_df.to_excel(writer, index=False, sheet_name='Matched Data')
                writer.close()
            st.download_button(label="Download as XLS", data=xls_buffer.getvalue(), file_name="matched_contacts_and_deposits.xls", mime="application/vnd.ms-excel")

            # Export as XLSX
            xlsx_buffer = io.BytesIO()
            with pd.ExcelWriter(xlsx_buffer, engine='xlsxwriter') as writer:
                matched_df.to_excel(writer, index=False, sheet_name='Matched Data')
                writer.close()
            st.download_button(label="Download as XLSX", data=xlsx_buffer.getvalue(), file_name="matched_contacts_and_deposits.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        else:
            st.write("No matches found.")

    else:
        st.write("No matching user names found.")
