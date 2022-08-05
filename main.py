from bs4 import BeautifulSoup
import requests
import csv
import pandas as pd
import base64
import streamlit as st


def make_initial_request(keywords, location=None):
    result = requests.get('https://panoramafirm.pl/szukaj?k={}&l={}'.format(keywords, location))
    if result.status_code == 200:
        return result.content
    else:
        return False


def make_request(url):
    result = requests.get(url)
    if result.status_code == 200:
        return result.content
    else:
        return False


def get_request_url(keywords, location):
    return 'https://panoramafirm.pl/szukaj?k={}&l={}'.format(keywords, location)


def create_google_contacts_entry(company_name, phone, website, email, label):
    company = {'Name': company_name, 'Given Name': company_name, 'Additional Name': '', 'Family Name': '',
               'Yomi Name': '', 'Given Name Yomi': '', 'Additional Name Yomi': '', 'Family Name Yomi': '',
               'Name Prefix': '', 'Name Suffix': '', 'Initials': '', 'Nickname': '', 'Short Name': '',
               'Maiden Name': '', 'Birthday': '', 'Gender': '', 'Location': '', 'Billing Information': '',
               'Directory Server': '', 'Mileage': '', 'Occupation': '', 'Hobby': '', 'Sensitivity': '', 'Priority': '',
               'Subject': '', 'Notes': '', 'Language': '', 'Photo': '',
               'Group Membership': '{}:::* myContacts'.format(label), 'E-mail 1 - Type': '', 'E-mail 1 - Value': email,
               'Phone 1 - Type': 'Mobile', 'Phone 1 - Value': phone, 'Organization 1 - Type': 'Work',
               'Organization 1 - Name': company_name, 'Organization 1 - Yomi Name': '', 'Organization 1 - Title': '',
               'Organization 1 - Department': '', 'Organization 1 - Symbol': '', 'Organization 1 - Location': '',
               'Organization 1 - Job Description': '', 'Website 1 - Type': '', 'Website 1 - Value': website}
    return company


def get_email(content):
    email = content.find('a',
                         class_='ajax-modal-link icon-envelope cursor-pointer addax addax-cs_hl_email_submit_click')
    if email:
        email = email.get('data-company-email')
    else:
        email = ''
    return email


def get_website(content):
    website = content.find('a', 'icon-website addax addax-cs_hl_hit_homepagelink_click')
    if website:
        website = website.get('href')
    else:
        website = ''
    return website


def get_phone(content):
    phone = content.find('a', 'icon-telephone addax addax-cs_hl_phonenumber_click')
    if phone:
        phone = phone.get('title')
    else:
        phone = ''
    return phone


def get_data(content, company_name):
    data = {'company_name': company_name, 'phone': get_phone(content), 'website': get_website(content),
            'email': get_email(content)}
    return data


def parse_page(soup):
    company_names = soup.find_all('a', 'company-name addax addax-cs_hl_hit_company_name_click')
    contents = soup.find_all('div', 'row company-bottom-content border-top')
    for content, company_name in zip(contents, company_names):
        company_name = company_name.next.strip()
        content = content.div.div
        data = get_data(content, company_name)
        output.append(data)


def get_next_page_url(soup):
    paginator = soup.find('a', 'text-dark py-1 addax addax-cs_hl_nextpage')
    if paginator:
        next_page_url = paginator.get('href')
        return next_page_url


def scrape(url):
    while url:
        content = make_request(url)
        if content:
            soup = BeautifulSoup(content, 'lxml')
            parse_page(soup)
            url = get_next_page_url(soup)


def save_to_csv(toCSV):
    keys = toCSV[0].keys()
    with open('people.csv', 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(toCSV)


def download_link(object_to_download, download_filename, download_link_text):
    """
    Generates a link to download the given object_to_download.

    object_to_download (str, pd.DataFrame):  The object to be downloaded.
    download_filename (str): filename and extension of file. e.g. mydata.csv, some_txt_output.txt
    download_link_text (str): Text to display for download link.
    """
    if isinstance(object_to_download, pd.DataFrame):
        object_to_download = object_to_download.to_csv(index=False)

    # some strings <-> bytes conversions necessary here
    b64 = base64.b64encode(object_to_download.encode()).decode()

    return f'<a href="data:file/txt;base64,{b64}" download="{download_filename}">{download_link_text}</a>'


def create_google_contacts_data_frame(output, label):
    contacts = []
    for company in output:
        contact = create_google_contacts_entry(company['company_name'], company['phone'],
                                               company['website'], company['email'], label)
        contacts.append(contact)
    return pd.DataFrame(contacts)


if __name__ == "__main__":
    output = []
    keyword = st.text_input('Search phrase: ')
    location = st.text_input('Location: ')

    if st.button('Search'):
        label = keyword + '-' + location
        url = get_request_url(keyword, location)
        scrape(url)
        output_df = pd.DataFrame(output)
        google_contacts_df = create_google_contacts_data_frame(output, label)
        st.dataframe(output_df)
        output_download_link = download_link(output_df, '{}.csv'.format(label), 'Download output as csv file')
        google_contacts_download_link = download_link(google_contacts_df, '{}.csv'.format(label),
                                                      'Download output as Google Contacts csv file')
        st.markdown(output_download_link, unsafe_allow_html=True)
        st.markdown(google_contacts_download_link, unsafe_allow_html=True)
