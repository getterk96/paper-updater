import queue
import threading
import requests
import os, re
from bs4 import BeautifulSoup

storage_dir = '/Users/gaojinghan/Desktop/few-shot papers/'
threads = 8
cur_papers = []

for dir in os.listdir(storage_dir):
    if dir != 'finished':
        cur_papers.append(dir)
    else:
        for dir in os.listdir(os.path.join(storage_dir, dir)):
            cur_papers.append(dir)

class PDFDownloader(threading.Thread):
    def __init__(self, queue, num):
        threading.Thread.__init__(self)
        self.queue = queue
        self.num = num

    def run(self):
        while self.queue.qsize() > 0:
            index = self.queue.get()
            print("Thread-{} working on {}".format(self.num, index['title']))
            path = os.path.join(storage_dir, index['title'])
            r = requests.get(index['url'])
            with open(path, "wb") as f:
                f.write(r.content)
            with open(os.path.join(storage_dir, 'bibtexs', index['title'].replace('.pdf', '.bib')), 'w') as f:
                f.write(index['bibtex'])


def CVPR(year=2019, search=''):
    url = f'http://openaccess.thecvf.com/CVPR{year}.py'
    r = requests.get(url)
    soup = BeautifulSoup(r.text, features="html.parser")
    papers = soup.dl.find_all('dd')[1::2]
    results = []
    for paper in papers:
        result = {}
        result['bibtex'] = paper.find(class_='bibref').text[1:]
        result['title'] = re.search(r'title = {(.*?)}', result['bibtex'], re.I).group()[9:-1].replace(' ', '_') + '.pdf'
        result['url'] = 'http://openaccess.thecvf.com/' + paper.a.get('href')
        if search in result['title'].lower() and result['title'] not in cur_papers:
            results.append(result)

    return results


def download_paper(indexs):
    if not os.path.exists(os.path.join(storage_dir, 'bibtexs')):
        os.mkdir(os.path.join(storage_dir, 'bibtexs'))

    paper_queue = queue.Queue()
    for item in indexs:
        paper_queue.put(item)

    my_downloaders = []
    for i in range(threads):
        my_downloaders.append(PDFDownloader(paper_queue, i + 1))

    for downloader in my_downloaders:
        downloader.start()

    for downloader in my_downloaders:
        downloader.join()



if __name__ == "__main__":
    download_paper(CVPR(search='shot')) # use lower case to search
    print("Finish update!")
