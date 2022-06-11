import unittest
from datetime import datetime, timedelta, timezone
from pprint import pprint
import os

import numpy as np
import matplotlib.pyplot as plt
import requests_cache
from dateutil import parser
from tqdm import tqdm

API_KEY=os.getenv('SCALE_SERP_API_KEY')
my_date = datetime.utcnow()
now_utc = datetime.now(timezone.utc)
an_hour_ago = my_date - timedelta(hours=1)
s = requests_cache.CachedSession()


def get_reviews(data_id):
    next_page_token = None
    cnt = 0
    page = 0
    result = []
    while next_page_token is not None or page == 0:
        url = 'https://api.scaleserp.com/search?'
        parampairs = []
        params = {
            'search_type': 'place_reviews',
            'data_id': data_id ,
            'next_page_token': next_page_token,
            'api_key': API_KEY,
        }

        for k, v in params.items():
            if v is not None:
                parampairs.append(f"{k}={v}")
        url += '&'.join(parampairs)
        api_result = s.get(url)
        if api_result.status_code != 200:
            print(api_result.text)
            print('*' * 200)
            raise
        jkl = api_result.json()
        if page == 0:
            total = jkl['place_info']['reviews']
            pbar = tqdm(total=total)
        for review in jkl['place_reviews_results']:
            cnt += 1
            try:
                if 'date_utc' not in review:
                    review['date_utc'] = an_hour_ago.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                dt = parser.parse(review['date_utc'])
                delta = now_utc - dt
                review['hours_ago'] = round(delta.seconds / 60 / 60)
                review['days_ago'] = round(delta.days)
                review['weeks_ago'] = round(delta.days / 7.0)
                result.append(review)
            except:
                pprint(review)
                raise
        pbar.update(len(jkl['place_reviews_results']))
        if 'pagination' in jkl:
            prev_page_token = next_page_token
            next_page_token = jkl['pagination']['next_page_token']
        else:
            next_page_token = None
        page += 1
    return result


def stacked_bar_by_month(title, data_id):
    result = get_reviews(data_id)
    data = {}
    for review in result:
        review['date_period'] = review['date_utc'][:7]
        if review['date_period'] not in data:
            data[review['date_period']] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        data[review['date_period']][review['rating']] += 1
    labels = sorted(list(data.keys()))
    y = {1: np.array([]), 2: np.array([]), 3: np.array([]), 4: np.array([]), 5: np.array([])}
    for label, ratings in sorted(data.items()):
        for star, cnt in ratings.items():
            y[star] = np.append(y[star], cnt)
        pass
    legend = ["*", "**", "***", "****", '*****']
    c = ["darkred", "red", "lightblue", "green", "darkgreen"]
    fig = plt.figure(figsize=(11, 9))
    plt.bar(labels, y[1], 1, label=legend[0], color=c[0])
    plt.bar(labels, y[2], 1, bottom=y[1], label=legend[1], color=c[1])
    plt.bar(labels, y[3], 1, bottom=y[2] + y[1], label=legend[2], color=c[2])
    plt.bar(labels, y[4], 1, bottom=y[3] + y[2] + y[1], label=legend[3], color=c[3])
    plt.bar(labels, y[5], 1, bottom=y[4] + y[3] + y[2] + y[1], label=legend[4], color=c[4])

    plt.xlabel('month', fontsize=20)
    plt.ylabel('reviewers', fontsize=20)
    plt.title(data_id, fontsize=26)
    plt.xticks(rotation=45)  # Rotates X-Axis Ticks by 45-degrees
    plt.legend(bbox_to_anchor=(0, -0.15, 1, 0), loc=2, ncol=2, mode="expand", borderaxespad=0)
    plt.legend()
    plt.savefig('chart.png', dpi=200)