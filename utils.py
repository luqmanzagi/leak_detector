import glob
from typing import DefaultDict
# import orjson as json
from os.path import basename
from pandas.io import excel
from tld import get_fld
import pandas as pd
import json
from urllib.parse import urlparse
import ipaddress
import pickle
pd.set_option('display.max_rows', 100)

def get_referrer(request):
    try:
        return request['requestHeaders'].get('referer', '')
    except KeyError:
        return ""
    
def get_response_referrer_policy(request):
    try:
        return request['responseHeaders'].get('referrer-policy', '')
    except KeyError:
        return ""
    
def get_req_referrer_policy(request):
    try:
        return request['reqReferrerPolicy']
    except KeyError:
        return ""

def get_ps1_or_host(url):
    if not url.startswith("http"):
        url = 'http://' + url

    try:
        return get_fld(url, fail_silently=False)
    except Exception:
        hostname = urlparse(url).hostname
        try:
            ipaddress.ip_address(hostname)
            return hostname
        except Exception:
            return ""
        
def get_initiators(initiators):
    initiator_domains = set()
    req_initiators = initiators
    for initiator in req_initiators:
        initiator_domain = get_domain(initiator)
        initiator_domains.add(initiator_domain)
    return initiator_domains


def get_domain_fld(domain):
    if domain.startswith('.'):
        url = 'https://www' + domain
    else:
        url = 'https://' + domain 
    try:
        domain = get_fld(url)
    except:
        print('ERR', domain)
    return domain

def get_domain(url):
    try:
        domain_name = get_fld(url)
    except:
        domain_name = url
    return domain_name

# with open('tracker_domain_list.pkl', 'rb') as f:
#     tracker_domains = pickle.load(f)
    
def check_tracker_domains(domain):
    try:
        res_domain = get_fld(domain, fix_protocol=True)
        if res_domain in tracker_domains:
            return True
        return False
    except:
        return False  
    
def check_third_party(req_domain, site_domain):
    # try:
        # site_fld = get_fld(site_domain, fix_protocol=True)
    if req_domain == site_domain:
        return False
    # except:
    #     print('FLD error', site_domain)
    return True


# with open('entity_map.pkl', 'rb') as handle:
#     entity_map = pickle.load(handle)

    
UNKNOWN_TRACKER_PREFIX = 'unknown_tracker_'
def match_entity(domain):
    """Return the entity name for a given eTLD+1 using DuckDuckGo's entity map.

    When the first lookup fails, check for the domain's parent since DuckDuckGo's
    entity map may contain public suffixes."""

    domain = str(domain)  # in case the function is called with None
    if domain in entity_map:
        return entity_map[domain]
    if domain.count(".") >= 2:
        # strip the subdomain and try again
        # e.g. for "imasdk.googleapis.com", we try with "googleapis.com"
        # which is present in DuckDuckGo's entity map despite being a public suffix
        parent_domain = domain.split(".", 1)[-1]
        if parent_domain in entity_map:
            return entity_map[parent_domain]
    # if the domain or its parent are not present, return unknown entity
    # suffixed with the original domain so different unknown entities
    # can be distinguished
    return UNKNOWN_TRACKER_PREFIX + domain


def get_visit_metadata(results, json_name):
    final_domain = ""
    initial_url = ""
    final_url = ""
    should_process = True
    
    if json_name == "metadata.json":
        print("ERROR: error page", initial_url, final_url, json_name)
        should_process = False
        
    if 'finalUrl' in results and 'initialUrl' in results:
        initial_url = results['initialUrl']
        final_url = results['finalUrl']
        if final_url == 'chrome-error://chromewebdata/':
            print("ERROR: Chrome error page", initial_url, final_url, json_name)
            should_process = False
        elif not final_url.startswith('http'):
            print("ERROR: Non-HTTP final URL", initial_url, final_url, json_name)
            should_process = False
        elif final_url.endswith(".xml"):
            print("ERROR: .xml final URL", json_name)
        else:
            final_domain = get_fld(initial_url, fail_silently=True)
            if not final_domain:
                print("ERROR: Cannot get the final URL domain", initial_url, final_url, json_name)
                should_process = False
    else:
        print("ERROR: NO FINAL or INIT URL: ",  json_name)
        should_process = False

    if "data" not in results:
        print("ERROR: No data", initial_url, json_name)
        should_process = False

    elif "requests" not in results['data']:
        print("ERROR: No request", initial_url, json_name)
        should_process = False

    return initial_url, final_url, final_domain, should_process


def get_first_non_redir_req(requests):
    first_non_redir_req ={}
    for request in requests:
        if not str(request["status"]).startswith("3"):
            first_non_redir_req = request
            break
    return first_non_redir_req


def is_failed_visit(results):
    """ Exclude failed visits based on 3 conditions in 
    "https://github.com/asumansenol/kids-tracking-inspector/issues/39#issuecomment-1415837703"
    """
    requests = results["data"]["requests"]
    first_non_redir_req = get_first_non_redir_req(requests)
    first_status = ""
    
    if "status" in first_non_redir_req:
        first_status = first_non_redir_req["status"]


    if str(first_status).startswith("4") or str(first_status).startswith("5"):
        return True

    if "size" in first_non_redir_req and first_non_redir_req["size"]<=512:
        return True

    if not any(request["status"] == 200 for request in requests):
        return True
    
    return False
