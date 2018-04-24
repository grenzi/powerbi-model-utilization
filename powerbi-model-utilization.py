import os
import json
import binascii
import collections
from six import iteritems
import click
import zipfile

def nested_lookup(key, document, wild=False):
    """Lookup a key in a nested document, yield a value"""
    if isinstance(document, list):
        for d in document:
            for result in nested_lookup(key, d, wild=wild):
                yield result

    if isinstance(document, dict):
        for k, v in iteritems(document):
            if key == k or (wild and key.lower() in k.lower()):
                yield v
            elif isinstance(v, dict):
                for result in nested_lookup(key, v, wild=wild):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in nested_lookup(key, d, wild=wild):
                        yield result

def parse_pbix_embedded_json(dct):
    """
    parse_pbix_embedded_json is an object_hook that expands the "it's json but stored as a string" into 
    proper json objects 
    :param dct: dictionary of whatever json.loads is working on 
    :return: returns dictionary containg parsed json objects for candidate keys
    """
    if 'config' in dct:
        dct['config'] = json.loads(dct['config'])
    if 'filters' in dct:
        dct['filters'] = json.loads(dct['filters'])
    if 'Value' in dct:
        try: 
            newval = json.loads(dct['Value'])
            dct['Value'] = newval
        except: 
            pass                
    if 'query' in dct:
        try: 
            newval = json.loads(dct['query'])
            dct['query'] = newval
        except: 
            pass           
    return dct

def get_layout_from_pbix(pbixpath):
    """
    get_layout_from_pbix loads a pbix file, grabs the layout from it, and returns json
    :parameter pbixpath: file to read
    :return: json goodness
    """
    archive = zipfile.ZipFile(pbixpath, 'r')
    bytes_read = archive.read('Report/Layout')
    s = bytes_read.decode('utf-16-le')
    json_obj = json.loads(s, object_hook=parse_pbix_embedded_json)
    return json_obj

################################################################################
## main
@click.command()
@click.argument('pbixfile', type=click.Path(exists=True))
@click.argument('reflistingout',type=click.File('w'))
@click.option('-jsonout', default=None, type=click.File('w'))
def main(pbixfile, reflistingout, jsonout=None): #, jsonout):
    my_layout = get_layout_from_pbix(pbixfile)

    if jsonout: jsonout.write(json.dumps(my_layout, indent=4, sort_keys=True))
        
    references = set(nested_lookup('queryRef', my_layout))
    reflist = list(references)
    reflist.sort()

    for x in reflist:
        reflistingout.write(x + '\n')

if __name__ == '__main__':
    main()

#python .\powerbi-model-utilization.py '.\samples\Customer Profitability Sample PBIX.pbix' '.\samples\Customer Profitability Sample.reflisting.txt' -jsonout '.\samples\Customer Profitability Sample.Enriched Layout.json'