import time
import os
import json
import requests
from bs4 import BeautifulSoup
import subprocess

# settings
config_path = '/home/ok/.devault/devault.conf'
URL = 'https://devault.online/'
LOGIN = 'login'
LOGIN_CHECK = 'login_check'

HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36',
           'origin': 'https://devault.online/', 'referer': 'https://devault.online/login',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
           'Accept-Encoding': 'gzip, deflate, br',
          }


# Check if RPC creds exist if not create?
# add get info if exists
def has_config():
    # does the config file exist
    if not os.path.exists(config_path):
        with open(config_path, 'w+') as file:
            # write rpc creds
            file.write('server = 1\nrpcuser = user\nrpcpassword = password\n')

def login(devault_online_username, devault_online_password):
    # start requests session and vote
    print("login 1")
    with requests.session() as s:
        s.headers = HEADERS
        response = s.get(URL+LOGIN)
        print(response)
        time.sleep(1)
        print("login 2")

        #get csrf token using bs to extract from login page where it is a hidden input
        print(URL+LOGIN_CHECK)
        soup_token = BeautifulSoup(s.get(URL+LOGIN).text, 'html.parser')
        time.sleep(1)
        print("login 3")

        for i in soup_token.find_all('input'):
            print(i)
            if i['name'] == '_csrf_token':
                csrf_token = i['value']
                print("found token")
        if csrf_token == "":
            print('login error csrf token')
            return 'login error csrf token'
        print(csrf_token)

        print("login 4")

        login_payload = {
                '_username': devault_online_username,
                '_password': devault_online_password,
                 '_csrf_token': csrf_token,
                '_submit': 'Log in',
                }

        print(login_payload)
        print("login 5")

        login_req = s.post(URL + LOGIN_CHECK, headers=HEADERS, data=login_payload)
        time.sleep(1)
        cookies = login_req.cookies
        print('login response:', login_req.status_code)
        return s

def get_online_proposals():
    base_url = "https://devault.online"
    online_filter = "?filter=online"
    page_url = base_url + "/proposals"
    page_online = requests.get(page_url + online_filter)
    soup = BeautifulSoup(page_online.text, 'html.parser')
    proposal_links = []
    for link in soup.find_all('a'):
        if "/proposal/vote/" in link.get('href'):
            if link.get('href')[-2:] == 'up':
                proposal_links += [(base_url + link.get("href"))[0:-2]]
    return proposal_links


def get_verification_key(s, proposal, vote):
    print('\ngetting verification key for' + vote + ' vote on ',proposal)
    proposal_req = s.get(proposal+vote)
    time.sleep(1)
    proposal_soup = BeautifulSoup(proposal_req.text, 'html.parser')
    vkey = ''

    for i in proposal_soup.find_all('input', id='js-copyInput'):
        print(i)
        vkey = i['value']
        print(vkey)
    return vkey


def get_voting_addresses():
    print("getting voting addresses")
    stream = os.popen('devault-cli listaddressgroupings')
    addresses = json.loads(stream.read())
    addresses_w_amount = []
    for l in addresses:
        for a in l:
            print(a[0])
            if a[1] > 0.0:
                addresses_w_amount += [a]
    return sorted(addresses_w_amount, key=lambda i: i[0])


def unlock_wallet(walletpassphrase, time):
    print('devault-cli walletpassphrase "' + walletpassphrase + '" ' + str(time))
    unlock = os.system('devault-cli walletpassphrase "' + walletpassphrase + '" ' + str(time))
    print("wallet unlock:", unlock)
    return unlock

def lock_wallet():
    stream = os.popen('devault-cli walletlock')
    print("wallet locked")


def sign_vote(vaddress, vkey):
    print('devault-cli signmessage ' + vaddress + ' ' + vkey)
    stream = os.popen('devault-cli signmessage ' + vaddress + ' ' + vkey)
    signature = stream.read()
    return signature


def post_vote(s, proposal, vote, address, signature):
    #get token
    print('\ngetting verification key for' + vote + ' vote on ', proposal)
    vtoken_req = s.get(proposal + vote)
    time.sleep(1)
    vtoken_soup = BeautifulSoup(vtoken_req.text, 'html.parser')
    vtoken = ''
    for i in vtoken_soup.find_all('input', id='proposal_vote__token'):
        vtoken = i['value']
        print('vtoken: ', vtoken)

    print('\nposting vote for ' + proposal + vote + ' with addy ' + address + ' and signature ' + signature)
    vote_payload = {
        'proposal_vote[walletAddress]': address,
        'proposal_vote[verificationSignature]': signature,
        'proposal_vote[_token]': vtoken,
        'proposal_vote[submit]': 'Submit!',
        }

    print(vote_payload)
    time.sleep(1)
    vote_req = s.post(proposal + vote, headers=HEADERS, data=vote_payload)
    time.sleep(1)
    return vote_req.status_code


#
# # testing
#     print('unlock', unlock_wallet(wallet_pass))
#
#     voting_addresses = get_voting_addresses()
#     # generate list of current proposals
#     proposals = get_online_proposals(soup_online)
#
#     for p in proposals:
#         print('proposal:', p)
#
#     print('voting addresses: ', voting_addresses)
#     key1 = get_verification_key(proposals[0], 'up')
#     print('verification key: ', key1)
#
#     #vote up with all addresses for all proposals
#     for p in proposals:
#         vkey = get_verification_key(p,'up')
#         for a in voting_addresses:
#             signature = sign_vote(a[0], vkey)
#             print(signature)
#             print(post_vote(p, 'up', a[0], signature))
