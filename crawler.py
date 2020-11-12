import requests
import re
from db.mongo import getDb, connect2db
import json
from config.envparams import Params
from config.statuslogger import LOGGER
from datetime import datetime
import time
path = './'
PARAM_FILE_PATH = "./params.json"
prms = Params(param_file_path=PARAM_FILE_PATH)
logger = LOGGER(status=prms.DEBUG, param_handler=prms)

headers = {
    'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64)'
                   'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36')}

main_url = "https://www.hepsiburada.com/sitemaps/sitemap.xml"
initial_link = "https://www.hepsiburada.com/"
mongoclient = connect2db(prms.DB_HOST_IP, prms.DB_HOST_PORT, prms.MAXSEVSELDELAY, logging=logger.log)


def get_sitemap_links(page):
    links = []
    req = requests.get(page, headers=headers)
    splitted = req.text.split("<sitemap>")[1:]
    for text in splitted:
        pattern = "<loc>(.*?)</loc>"
        substring = re.search(pattern, text).group(1)
        links.append(substring)
    return links


def get_products(link):
    prod_links = []
    try:
        req = requests.get(link, headers=headers)
        splitted = req.text.split("<url>")[1:]
        for text in splitted:
            pattern = "<loc>(.*?)</loc>"
            substring = re.search(pattern, text).group(1)
            prod_links.append(substring)
    except requests.exceptions.ChunkedEncodingError:
        time.sleep(5)
        get_products(link)
    return prod_links


def get_prod_details(page, non_id):
    prod_detail_dict = dict()
    non_detail_id = "non"+str(non_id)
    non_detail_dict = dict()
    req = requests.get(page, headers=headers)
    utag_data = req.text.split(";")
    for data in utag_data:
        if "utag_data" in data:
            prod_detail = data
            pattern = "{(.*?)}"
            try:
                prod_detail_text = "{"+re.search(pattern, prod_detail).group(1)+"}"
                prod_detail_dict = json.loads(prod_detail_text)
            except (AttributeError, json.decoder.JSONDecodeError):
                non_detail_dict["id"] = non_detail_id
                non_detail_dict["non_taken_page"] = page
                _db = getDb(mongoclient, prms.DB, logging=logger.log)
                collection = _db[prms.DB_HEPSIBURADA_COLLECTION]
                try:
                    collection.insert_one(non_detail_dict)
                except Exception as e:
                    logger.log.info(str(e))

    return prod_detail_dict


def run():
    start = datetime.now()
    sitemap_links = get_sitemap_links(main_url)
    default_blank_value = ""
    id_counter = 0
    for link in sitemap_links:
        prods = get_products(link)
        for prod_link in prods:
            id_counter += 1
            raw_prod_dict = get_prod_details(prod_link, id_counter)
            if not raw_prod_dict:
                continue
            prod_dict = dict()
            try:
                prod_dict['site_name'] = raw_prod_dict['page_site_name']
            except KeyError:
                prod_dict['site_name'] = default_blank_value
                prod_dict['raw_data'] = raw_prod_dict
            try:
                prod_dict['category_path'] = raw_prod_dict['category_path']
            except KeyError:
                prod_dict['category_path'] = default_blank_value
                prod_dict['raw_data'] = raw_prod_dict
            try:
                prod_dict['seller_name'] = raw_prod_dict['order_store']
            except KeyError:
                prod_dict['seller_name'] = default_blank_value
                prod_dict['raw_data'] = raw_prod_dict
            try:
                prod_dict['page_url'] = raw_prod_dict['page_url']
            except KeyError:
                prod_dict['page_url'] = default_blank_value
                prod_dict['raw_data'] = raw_prod_dict
            try:
                prod_dict['price'] = raw_prod_dict['product_prices'][0]
            except KeyError:
                prod_dict['price'] = default_blank_value
                prod_dict['raw_data'] = raw_prod_dict
            try:
                prod_dict['unit_price'] = raw_prod_dict['product_unit_prices'][0]
            except KeyError:
                prod_dict['unit_price'] = default_blank_value
                prod_dict['raw_data'] = raw_prod_dict
            try:
                prod_dict['brand'] = raw_prod_dict['product_brand']
            except KeyError:
                prod_dict['brand'] = default_blank_value
                prod_dict['raw_data'] = raw_prod_dict
            try:
                prod_dict['id'] = raw_prod_dict['product_ids'][0]
            except KeyError:
                prod_dict['id'] = id_counter
                prod_dict['raw_data'] = raw_prod_dict
                logger.log.info("id not found. Assigned id is: " + str(id_counter))
            try:
                prod_dict['category'] = raw_prod_dict['product_categories'][0]
            except KeyError:
                prod_dict['category'] = default_blank_value
                prod_dict['raw_data'] = raw_prod_dict
            try:
                prod_dict['barcode'] = raw_prod_dict['product_barcode']
            except KeyError:
                prod_dict['barcode'] = default_blank_value
                prod_dict['raw_data'] = raw_prod_dict
            try:
                prod_dict['name'] = raw_prod_dict['product_name_array']
            except KeyError:
                prod_dict['name'] = default_blank_value
                prod_dict['raw_data'] = raw_prod_dict
            try:
                ids_split = raw_prod_dict['category_id_hierarchy'].split('>')
                names_split = raw_prod_dict['category_name_hierarchy'].split('>')
                category_dict = dict()
                for index, key in enumerate(names_split):
                    key = key.lstrip().rstrip()
                    ids_split[index] = ids_split[index].lstrip().strip()
                    category_dict[key] = ids_split[index]
                prod_dict['category_dict'] = category_dict
            except KeyError:
                prod_dict['category_dict'] = dict()
                prod_dict['raw_data'] = raw_prod_dict
            try:
                prod_dict['product_status'] = raw_prod_dict['product_status']
            except KeyError:
                prod_dict['product_status'] = ""
                prod_dict['raw_data'] = raw_prod_dict

            _db = getDb(mongoclient, prms.DB, logging=logger.log)
            collection = _db[prms.DB_HEPSIBURADA_COLLECTION]
            try:
                collection.insert_one(prod_dict)
            except Exception as e:
                logger.log.info(str(e))
    end = datetime.now()
    logger.log.info("Process finished in " + str(end - start))


run()
