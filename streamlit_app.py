import streamlit as st
import pandas as pd
import math
from pathlib import Path
import requests
import json
import datetime as dt
from datetime import datetime
import time

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Random User Picker',
    page_icon=':thumbsup:', # This is an emoji shortcode. Could be a URL too.
)

# -----------------------------------------------------------------------------
# Declare some useful functions.

@st.cache_data(ttl='1d')
def pull_all_users_from_APIs(token):
    base_url = "https://app.circle.so/api/admin/v2/community_members?per_page=100&page="
    headers = {'Authorization': token}
    df_all = pd.DataFrame()
    page = 1  
    while True:
        url = base_url + str(page)
        response = requests.get(url, headers=headers)
        data = response.json()
        records = data.get('records', [])
        if not records: 
            break
        df = pd.json_normalize(records)
        df = df[['name', 'email', 'created_at', 'last_seen_at']] #comments_count, posts_count, activity_score
        df_all = pd.concat([df_all, df], ignore_index=True)
        page += 1
        time.sleep(0.15)
    df_all['last_seen_at'] = pd.to_datetime(df_all['last_seen_at'])
    df_all['created_at'] = pd.to_datetime(df_all['created_at'])
    return df_all




def get_random_members(member_df, number_picks=1, last_seen_option="NONE",
                        # posts_count=0, comments_count=0,
                        created_option="NONE"):#, activity_score=0):
    
    #filter out admins/gigg people -- have a special option for this??????
    raw_df = pd.DataFrame(member_df)
    df_no_gigg = raw_df[~raw_df['email'].str.contains('gigg', case=False, na=False)]
    df = df_no_gigg[~df_no_gigg['name'].str.contains('admin', case=False, na=False)]

    if last_seen_option != "NONE":
        df = filter_last_seen(df, last_seen_option)
        #call the date function to filter out by certain dates

    if created_option != "NONE":
        df = filter_account_creation(df, created_option)

    # if posts_count > 0:
    #     df = filter_posts(df, posts_count)

    # if comments_count > 0:
    #     df = filter_comments(df, comments_count)
        
    # if activity_score > 0:
    #     df = filter_activity_score(df, activity_score)
        
    print(f"There were {len(df)} people in the final group, so the odds were {number_picks}/{len(df)}, or {number_picks/len(df)* 100:.3f}%") 
    # print(f"There were {len(df)} people in the final group, so the odds were {number_picks}/{len(df)}, or {number_picks/len(df)* 100}%") #maybe calculate the odds of people chosen then?? 1/XXX

    return df.sample(n=number_picks)


def filter_last_seen(df, date):
    today = pd.Timestamp.now(tz='UTC')
    match date:
        case "TODAY": #TODAY
            print(f"Filtering to users that were last seen today:")
            start_of_today = today.normalize()  # Resets time to 00:00:00
            today_filter = df['last_seen_at'] >= start_of_today
            return df.loc[today_filter]

        case "THIS WEEK": #THIS WEEK
            print(f"Filtering to users that were last seen sometime this week:")
            this_week_filter = all_users['last_seen_at'] >= (today - pd.DateOffset(days=7))
            return df.loc[this_week_filter]

        case "THIS MONTH": #THIS MONTH
            print(f"Filtering to users that were last seen sometime this month:")
            this_month_filter = (all_users['last_seen_at'] >= pd.to_datetime(f"{today.year}-{today.month}-01", utc=True)) 
            return df.loc[this_month_filter]
                
    #specific date -- do something HERE
    return df


def filter_posts(df, count):
    print(f"Filtering to users that have made at least {count} post(s):")
    return df.loc[(df['posts_count'] >= count)]


def filter_comments(df, count):
    print(f"Filtering to users that have made at least {count} comment(s):")
    return df.loc[(df['posts_count'] >= count)]


def filter_account_creation(df, date):
    today = pd.Timestamp.now(tz='UTC')
    match date:
        case "THIS MONTH": #THIS MONTH
            print(f"Filtering to users that became members this month:")
            this_month_filter = (df['created_at'] >= pd.to_datetime(f"{today.year}-{today.month}-01", utc=True)) 
            return df.loc[this_month_filter]
        case "TWO MONTHS":
            print(f"Filtering to users that became members this or last month:")
            last_month_start = pd.to_datetime(f"{today.year}-{today.month - 1}-01", utc=True) if today.month > 1 else pd.to_datetime(f"{today.year - 1}-12-01", utc=True)
            last_two_months_filter = all_users['created_at'] >= last_month_start
            return df.loc[last_two_months_filter]
        case "ON LAUNCH":
            print(f"Filtering to users that became members in the launch month (May 2024):")
            # Define the start and end of May 2024
            start_date = pd.to_datetime("2024-05-01", utc=True)
            end_date = pd.to_datetime("2024-05-31 23:59:59", utc=True)
            may_users_filter = (df['created_at'] >= start_date) & (df['created_at'] <= end_date)
            return df.loc[may_users_filter]

    # filter by a specific date??
    return df


def filter_activity_score(df, score):
    print(f"Filtering to users that have an activity score of at least {score}:")
    return df.loc[(df['activity_score'] >= score)]
    
















@st.cache_data
def get_gdp_data():
    """Grab GDP data from a CSV file.

    This uses caching to avoid having to read the file every time. If we were
    reading from an HTTP endpoint instead of a file, it's a good idea to set
    a maximum age to the cache with the TTL argument: @st.cache_data(ttl='1d')
    """

    # Instead of a CSV on disk, you could read from an HTTP endpoint here too.
    DATA_FILENAME = Path(__file__).parent/'data/gdp_data.csv'
    raw_gdp_df = pd.read_csv(DATA_FILENAME)

    MIN_YEAR = 1960
    MAX_YEAR = 2022

    # The data above has columns like:
    # - Country Name
    # - Country Code
    # - [Stuff I don't care about]
    # - GDP for 1960
    # - GDP for 1961
    # - GDP for 1962
    # - ...
    # - GDP for 2022
    #
    # ...but I want this instead:
    # - Country Name
    # - Country Code
    # - Year
    # - GDP
    #
    # So let's pivot all those year-columns into two: Year and GDP
    gdp_df = raw_gdp_df.melt(
        ['Country Code'],
        [str(x) for x in range(MIN_YEAR, MAX_YEAR + 1)],
        'Year',
        'GDP',
    )

    # Convert years from string to integers
    gdp_df['Year'] = pd.to_numeric(gdp_df['Year'])

    return gdp_df

gdp_df = get_gdp_data()

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
'''
# :thumbsup: title here.....

This is an app made by *me* that picks a random user for a circle community, probably to give a prize to
I want to see if this change will actually show up ... ... 
'''

title = st.text_input("Community Token", "...")
if title != "...":
    members = pull_all_users_from_APIs("Token " + title)

# Add some spacing
''
''
'''
Filter By:
'''

last_seen = st.selectbox(
    "Last Seen Date",
    ("None", "Today", "This Week", "This Month"),
)

account_created = st.selectbox(
    "Account Creation Date",
    ("None", "This Month", "Last 2 Months", "On Launch")
)

result = st.button("Submit Filters")
if result: 
    random_user = get_random_members(members, number_picks=1, last_seen_option="NONE", created_option="NONE")
    st.write(random_user)








min_value = gdp_df['Year'].min()
max_value = gdp_df['Year'].max()

from_year, to_year = st.slider(
    'Which years are you interested in?',
    min_value=min_value,
    max_value=max_value,
    value=[min_value, max_value])

countries = gdp_df['Country Code'].unique()

if not len(countries):
    st.warning("Select at least one country")

selected_countries = st.multiselect(
    'Which countries would you like to view?',
    countries,
    ['DEU', 'FRA', 'GBR', 'BRA', 'MEX', 'JPN'])

''
''
''

# Filter the data
filtered_gdp_df = gdp_df[
    (gdp_df['Country Code'].isin(selected_countries))
    & (gdp_df['Year'] <= to_year)
    & (from_year <= gdp_df['Year'])
]

st.header('GDP over time', divider='gray')

''

st.line_chart(
    filtered_gdp_df,
    x='Year',
    y='GDP',
    color='Country Code',
)

''
''


first_year = gdp_df[gdp_df['Year'] == from_year]
last_year = gdp_df[gdp_df['Year'] == to_year]

st.header(f'GDP in {to_year}', divider='gray')

''

cols = st.columns(4)

for i, country in enumerate(selected_countries):
    col = cols[i % len(cols)]

    with col:
        first_gdp = first_year[first_year['Country Code'] == country]['GDP'].iat[0] / 1000000000
        last_gdp = last_year[last_year['Country Code'] == country]['GDP'].iat[0] / 1000000000

        if math.isnan(first_gdp):
            growth = 'n/a'
            delta_color = 'off'
        else:
            growth = f'{last_gdp / first_gdp:,.2f}x'
            delta_color = 'normal'

        st.metric(
            label=f'{country} GDP',
            value=f'{last_gdp:,.0f}B',
            delta=growth,
            delta_color=delta_color
        )
