import json
import requests
import jinja2
import os
import stat
import sys
from requests.auth import HTTPDigestAuth

PATH = os.path.realpath('./..')
if len(sys.argv) < 3:
    print("usage: python restgerrit.py user pass")
    sys.exit(1)
MY_DIGEST_AUTH = HTTPDigestAuth(sys.argv[1], sys.argv[2])

#TODO make these into cmd parameters
review_number = 83503
blueprint_name = "configuration-parameters-in-db"

def get_blueprint_reviews(blueprint_name):
    REVIEW_URL = "https://review.openstack.org/a/changes/?q=topic:bp/%s"
    r = requests.get(REVIEW_URL % blueprint_name, auth=MY_DIGEST_AUTH)
    resp = json.loads(r.text[5:])
    output = []
    for review in resp:
        project = review['project']
        number = review['_number']
        output.append(get_review(number))
    return output

def get_review(review_number):
    REVIEW_URL = "https://review.openstack.org/a/changes/?q=%s&o=CURRENT_REVISION&o=DOWNLOAD_COMMANDS"
    r = requests.get(REVIEW_URL % review_number, auth=MY_DIGEST_AUTH)
    resp = json.loads(r.text[5:])
    project = resp[0]['project'].split('/')[-1]
    revisions = resp[0]['revisions']
    checkout_command = revisions[revisions.keys()[0]]['fetch']['anonymous http']['commands']['Checkout']

    return {
        'project': project,
        'checkout_command': checkout_command
    }

review_list = get_blueprint_reviews(blueprint_name)
print(review_list)

env = jinja2.Environment(loader=jinja2.FileSystemLoader(PATH + "/trovetester/templates"))
# env = jinja2.Environment(loader=jinja2.PackageLoader("trovetester", "templates"))
template = env.get_template('checkout-reviews.template')
rendered = template.render(review_list=review_list)

with open(PATH + "/checkout-reviews.sh", 'w') as f:
    f.write(rendered)
st = os.stat(PATH + "/checkout-reviews.sh")
os.chmod(PATH + "/checkout-reviews.sh", st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
