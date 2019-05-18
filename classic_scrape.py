from bs4 import BeautifulSoup
import requests

def soup(s):
    return BeautifulSoup(s, 'html.parser')

