import streamlit as st
import pandas as pd
import requests
# import json
# import datetime as dt
# from datetime import datetime
# import time

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Random User Picker',
    page_icon=':white_check_mark:'
)

# -----------------------------------------------------------------------------
# Declare some useful functions.

@st.cache_data(ttl='1d')
def pull_all_users_from_APIs(token):
    base_url = "https://app.circle.so/api/admin/v2/community_members?per_page=100&page="
    headers = {'Authorization': token}
    df_all = pd.DataFrame(columns=['name', 'email', 'created_at', 'last_seen_at'])
    page = 1  
    while True:
        url = base_url + str(page)
        response = requests.get(url, headers=headers)
        # data = response.json()
        # records = data.get('records', [])

        data = pd.json_normalize(response.json())
        records_list = data['records'][0]
        if not records_list: 
            break
        # df = pd.json_normalize(records)
        df = pd.json_normalize(records_list)
        df = df[['name', 'email', 'created_at', 'last_seen_at']] #comments_count, posts_count, activity_score
        df_all = pd.concat([df_all, df], ignore_index=True)
        if page % 5 == 0:
            st.write("Made the API call for page: " + str(page))
        page += 1
        # time.sleep(0.15)
    df_all['last_seen_at'] = pd.to_datetime(df_all['last_seen_at'])
    df_all['created_at'] = pd.to_datetime(df_all['created_at'])
    st.write("Made " + str(page) + " API calls.")
    return df_all

# members = st.empty() # as a placeholder? not sure how that works with cacheing...


def get_one_page(token):
    url = "https://app.circle.so/api/admin/v2/community_members?per_page=10&page=1"
    headers = {'Authorization': (token)}
    response = requests.get(url, headers=headers)
    # st.write(response.text)
    # st.write(response.status_code)
    data = pd.json_normalize(response.json())
    records_list = data['records'][0]  
    df = pd.json_normalize(records_list)
    return df[['name', 'email', 'created_at', 'last_seen_at']]


def get_five_pages(token):
    base_url = "https://app.circle.so/api/admin/v2/community_members?per_page=10&page="
    headers = {'Authorization': token}
    df_all = pd.DataFrame(columns=['name', 'email', 'created_at', 'last_seen_at'])
    
    # Set the maximum number of pages to fetch
    max_pages = 5
    for page in range(1, max_pages + 1):  # Loop over the first 5 pages
        url = base_url + str(page)
        response = requests.get(url, headers=headers)

        # Flatten JSON response into a DataFrame
        data = response.json()
        records_list = data.get('records', [])
        
        if not records_list:
            break  # Exit the loop if there are no records (early exit)

        # Normalize the records into a DataFrame and select required columns
        df = pd.json_normalize(records_list)
        df = df[['name', 'email', 'created_at', 'last_seen_at']]  # Modify as needed
        df_all = pd.concat([df_all, df], ignore_index=True)

        # Optionally show progress in the Streamlit app
        if page % 1 == 0:
            st.write(f"Made the API call for page: {page}")
    
    # Convert datetime fields to pandas datetime objects
    df_all['last_seen_at'] = pd.to_datetime(df_all['last_seen_at'])
    df_all['created_at'] = pd.to_datetime(df_all['created_at'])
    
    # # Display the number of API calls made
    # st.write(f"Made {page} API calls.")
    
    return df_all








def get_random_members(df, number_picks=1, last_seen_option="None",
                        # posts_count=0, comments_count=0,
                        created_option="None"):#, activity_score=0):
    
    #filter out admins/gigg people -- have a special option for this??????
    # raw_df = pd.DataFrame(member_df)
    # df_no_gigg = raw_df[~raw_df['email'].str.contains('gigg', case=False, na=False)]
    # df = df_no_gigg[~df_no_gigg['name'].str.contains('admin', case=False, na=False)]

    # df = pd.DataFrame(df)

    if last_seen_option != "None":
        df = filter_last_seen(df, last_seen_option)
        #call the date function to filter out by certain dates

    if created_option != "None":
        df = filter_account_creation(df, created_option)

    # if posts_count > 0:
    #     df = filter_posts(df, posts_count)

    # if comments_count > 0:
    #     df = filter_comments(df, comments_count)
        
    # if activity_score > 0:
    #     df = filter_activity_score(df, activity_score)
        
    # st.write("There were " + {len(df)} + " people in the final group, so the odds were " + {number_picks}/{len(df)} + ", or " + {number_picks/len(df)* 100:.3f} + "%") 
    # print(f"There were {len(df)} people in the final group, so the odds were {number_picks}/{len(df)}, or {number_picks/len(df)* 100}%") #maybe calculate the odds of people chosen then?? 1/XXX

    return pd.DataFrame(df).sample(n=number_picks)


def filter_last_seen(df, date):
    today = pd.Timestamp.now(tz='UTC')
    match date:
        case "Today": #TODAY
            # print(f"Filtering to users that were last seen today:")
            start_of_today = today.normalize()  # Resets time to 00:00:00
            today_filter = df['last_seen_at'] >= start_of_today
            return df.loc[today_filter]

        case "This Week": #THIS WEEK
            # print(f"Filtering to users that were last seen sometime this week:")
            this_week_filter = df['last_seen_at'] >= (today - pd.DateOffset(days=7))
            return df.loc[this_week_filter]

        case "This Month": #THIS MONTH
            # print(f"Filtering to users that were last seen sometime this month:")
            this_month_filter = (df['last_seen_at'] >= pd.to_datetime(f"{today.year}-{today.month}-01", utc=True)) 
            return df.loc[this_month_filter]
                
    #specific date -- do something HERE
    return df


def filter_posts(df, count):
    # print(f"Filtering to users that have made at least {count} post(s):")
    return df.loc[(df['posts_count'] >= count)]


def filter_comments(df, count):
    # print(f"Filtering to users that have made at least {count} comment(s):")
    return df.loc[(df['posts_count'] >= count)]


def filter_account_creation(df, date):
    today = pd.Timestamp.now(tz='UTC')
    match date:
        case "This Month":
            # print(f"Filtering to users that became members this month:")
            this_month_filter = (df['created_at'] >= pd.to_datetime(f"{today.year}-{today.month}-01", utc=True)) 
            return df.loc[this_month_filter]
        case "Last Two Months":
            # print(f"Filtering to users that became members this or last month:")
            last_month_start = pd.to_datetime(f"{today.year}-{today.month - 1}-01", utc=True) if today.month > 1 else pd.to_datetime(f"{today.year - 1}-12-01", utc=True)
            last_two_months_filter = df['created_at'] >= last_month_start
            return df.loc[last_two_months_filter]
        case "On Launch":
            # print(f"Filtering to users that became members in the launch month (May 2024):")
            #May 2024
            start_date = pd.to_datetime("2024-05-01", utc=True)
            end_date = pd.to_datetime("2024-05-31 23:59:59", utc=True)
            may_users_filter = (df['created_at'] >= start_date) & (df['created_at'] <= end_date)
            return df.loc[may_users_filter]

    # filter by a specific date??
    return df


def filter_activity_score(df, score):
    # print(f"Filtering to users that have an activity score of at least {score}:")
    return df.loc[(df['activity_score'] >= score)]
    
















# @st.cache_data
# def get_gdp_data():
#     """Grab GDP data from a CSV file.

#     This uses caching to avoid having to read the file every time. If we were
#     reading from an HTTP endpoint instead of a file, it's a good idea to set
#     a maximum age to the cache with the TTL argument: @st.cache_data(ttl='1d')
#     """

#     # Instead of a CSV on disk, you could read from an HTTP endpoint here too.
#     DATA_FILENAME = Path(__file__).parent/'data/gdp_data.csv'
#     raw_gdp_df = pd.read_csv(DATA_FILENAME)

#     MIN_YEAR = 1960
#     MAX_YEAR = 2022

#     # The data above has columns like:
#     # - Country Name
#     # - Country Code
#     # - [Stuff I don't care about]
#     # - GDP for 1960
#     # - GDP for 1961
#     # - GDP for 1962
#     # - ...
#     # - GDP for 2022
#     #
#     # ...but I want this instead:
#     # - Country Name
#     # - Country Code
#     # - Year
#     # - GDP
#     #
#     # So let's pivot all those year-columns into two: Year and GDP
#     gdp_df = raw_gdp_df.melt(
#         ['Country Code'],
#         [str(x) for x in range(MIN_YEAR, MAX_YEAR + 1)],
#         'Year',
#         'GDP',
#     )

#     # Convert years from string to integers
#     gdp_df['Year'] = pd.to_numeric(gdp_df['Year'])

#     return gdp_df

# gdp_df = get_gdp_data()

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
'''
# :white_check_mark: Random User Picker
This is an app for picking a random user from a circle community based on a few filters.
'''

#if it reloads the script everytime a button is pressed, does that mean that MEMBERS is constantly emptied out 
# like when the submit filters button is pressed, it deletes the dataframe???
# is there like a global variable? can it be declared, then filled, and kept at that value???


token1 = "Token " + st.text_input("Input Your V2 Community Token Here", "")

pick_number = st.number_input(
    label = "How many random users do you want to pick?", 
    min_value=1, max_value=20, value="min"#, format="%1f"
)

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
    members = get_five_pages(token1)
    random_user = get_random_members(members, number_picks=pick_number, last_seen_option=last_seen, created_option=account_created)
    st.dataframe(random_user)
    # st.write(random_user)


























# token = "Token " + st.text_input("Input Your V2 Community Token Here", "")
# get_users_button = st.button("Grab ALL of the users")


# if token == "Token ":
#     # nothing was added yet
#     st.write("NOTHING in the token space, so it is just a place holder for now")
#     members = st.empty()
# else:
#     # st.write("Typed in something for the token, NOW RUNNING THE PULL ALL METHOD")
#     # members = pull_all_users_from_APIs("Token " + token)
#     if get_users_button: 
#         st.write("about to run the full script")
#         members = pull_all_users_from_APIs(token)
#     else:
#         st.write("NOT about to run the whole script, but token WAS filled in")
#         members = st.empty() # once a different button is pressed, this goes back to EMPTY


# need to check if members goes back to empty, or if it is recalled but cached so it doesn't need to run again


get_one_random = st.button("Get One Random User")
if get_one_random:
    # df = get_five_pages(token)
    # st.dataframe(df)
    random_user = get_random_members(members, number_picks=1, last_seen_option="None", created_option="None")
    # random_user = get_random_members(df, number_picks=pick_number, last_seen_option=last_seen, created_option=account_created)
    st.dataframe(random_user)


# if token but not get users button
# THEN can't RUN THIS BUTTON YET????
# try this next


 

# #see if this caches it???
# if token != "":
#     members =  pull_all_users_from_APIs("Token " + token) 
# else:
#     members = st.empty()






# could create a test token button where you can first test if it is a good token, THEN run the big function on it???
#so that bad tokens don't crash it??



'''
Notice that pulling all users can take a few minutes
'''


# Add some spacing
''
''
'''
Filter By:
'''




'''Still need to make that button for filtering out the admins....'''




'''Test getting One page and displaying it'''
test_page_button = st.button("Get One Page")
if test_page_button:
    test_df = get_one_page(token)
    st.dataframe(test_df)
    # st.write(test_df)




# # Correct usage
# members5 = pd.DataFrame({'Name': ['Alice', 'Bob'], 'Age': [25, 30]})
# st.dataframe(members5)  # Passes a valid DataFrame



# '''Display the head of the Dataframe so I can see what it looks like:'''
# st.dataframe(members.head(2))



# st.write(members)

result5 = st.button("Show members")
if result5: 
    # random_user = get_random_members(members, number_picks=pick_number, last_seen_option=last_seen, created_option=account_created)
    st.dataframe(members)



test_sample_button = st.button("Test the PD samples function")
if test_sample_button:
    df = pd.DataFrame({'A': range(1, 11), 'B': range(11, 21)})
    sampled_df = df.sample(n=3)
    sampled_df

test_5_pages = st.button("Test 5 pages + filter")
if test_5_pages:
    df = get_five_pages(token)
    st.dataframe(df)
    random_user = get_random_members(df, number_picks=1, last_seen_option="None", created_option="None")
    # random_user = get_random_members(df, number_picks=pick_number, last_seen_option=last_seen, created_option=account_created)
    st.dataframe(random_user)



grab_all = st.button("Test grabbing ALL of the pages")
if grab_all:
    df = pull_all_users_from_APIs(token)
    st.dataframe(df)


# PROGRESS BAR
# Add a placeholder
# latest_iteration = st.empty()
# bar = st.progress(0)

# for i in range(100):
#   # Update the progress bar with each iteration.
#   latest_iteration.text(f'Iteration {i+1}')
#   bar.progress(i + 1)
#   time.sleep(0.1)

# '...and now we\'re done!'






