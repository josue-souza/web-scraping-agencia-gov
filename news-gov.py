import requests
from lxml import html
from datetime import datetime
import time

class NewsGov():
    def __init__(self):
        self.url = 'https://agenciagov.ebc.com.br/noticias'
        self.dept = None
        self.page = 0
        self.journal_dict = {}
        self.list_news = []
        self.url_bd = 'https://scrap-81dd0-default-rtdb.firebaseio.com/.json'


    def get_requests(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            tree = html.fromstring(response.content)
            return tree
        else:
            print(f"Erro na requisição. Status code: {response.status_code}")


    def get_requests_journal_dict(self, dept):
        value = self.journal_dict[self.dept]
        url = value
        response = requests.get(url)
        if response.status_code == 200:
            tree = html.fromstring(response.content)
            return tree
        else:
            print(f"Erro na requisição. Status code: {response.status_code}")


    def replace_all(self, str_replace):
        replacements = {
            'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
            'é': 'e', 'ê': 'e', 'í': 'i', 'ó': 'o',
            'ô': 'o', 'õ': 'o', 'ú': 'u', 'ç': 'c',
            'Á': 'A', 'À': 'A', 'Ã': 'A', 'Â': 'A',
            'É': 'E', 'Ê': 'E', 'Í': 'I', 'Ó': 'O',
            'Ô': 'O', 'Õ': 'O', 'Ú': 'U', 'Ç': 'C', 
            '\n': ' ', '\xa0': ' ', '\x91': "'", '\x92': "'", 
            '\x93': '"', '\x94': '"', '\x96': '-', '\x97': ' ', 
            '\x85': '...', '\x96': '-', '\t': ' ' 
        }
        for key, value in replacements.items():
            str_replace = str_replace.replace(key, value)
        return str_replace


    def get_dept(self):
        tree = self.get_requests(self.url)
        box = tree.xpath('//ul[@class="navTree navTreeLevel0"]')
        dept_path = 'li[*]/a'
        for item in box:
            str_dept = item.xpath(dept_path)
            str_href = item.xpath(f"{dept_path}/@href")
            for dept, href in zip(str_dept, str_href):
                dept = dept.text_content().lower().strip()
                if dept == '':
                    dept = None
                dept = self.replace_all(dept)
                self.journal_dict[dept] = href
        return self.journal_dict


    def get_section(self):
        if self.dept is None:
            self.select_dept()

        if self.dept in self.journal_dict:
            while True:
                page_url = f"{self.url}/{self.dept}?b_start:int={self.page}"
                print(page_url)
                response = requests.get(page_url)
                time.sleep(1.5)
                tree = html.fromstring(response.content)
                box_news = tree.xpath('//ul[@class="demais-noticias"]')
                article_path = 'li[*]/a'
                for item in box_news:
                    str_date = item.xpath(f"{article_path}/div[2]/div")
                    str_hat = item.xpath(f"{article_path}/div[2]/p[1]")
                    str_name = item.xpath(f"{article_path}/div[2]/p[2]/text()")
                    str_href = item.xpath(f"{article_path}/@href")
                    for date, hat, name, href in zip(str_date, str_hat, str_name, str_href):
                        date = date.text_content()[0:10].strip()
                        hat = hat.text_content().strip()
                        name = name.strip()
                        href = href.strip()
                        dict_news = {'data': date, 'chapeu': hat, 'artigo': name, 'link': href, 'materia': None}
                        self.list_news.append(dict_news)
                next_page = tree.xpath('//li[@class="next"]')
                if next_page:
                    self.page += 20
                else:
                    break
        return self.list_news


    def select_dept(self):
        while True:
            select = input('Escolha um departamento ou digite list para listar todos: ')
            if select in self.journal_dict.keys():
                print('Iniciando coleta.')
                self.dept = select
                break

            elif select == 'list':
                for key in self.journal_dict:
                    print(key)
            else:
                print('Digite um nome valido.')
        return select

    def convert_to_date(self, data_str):
        return datetime.strptime(data_str, '%d/%m/%Y')


    def find_to_date(self):
        while True:
            date_start = input('Digite a data inicial para pesquisar (dd/mm/aaaa), ou deixe em branco para todas: ')
            date_end = input('Digite a data final para pesquisar (dd/mm/aaaa), ou deixe em branco para todas: ')
            href_list = []
            if date_start == '' and date_end == '':
                for news in self.list_news:
                    href = news['link']
                    print(href)
                    href_list.append(href)
                break
            elif date_start != '' and date_end != '':
                date_start = self.convert_to_date(date_start)
                date_end = self.convert_to_date(date_end)

                for news in self.list_news:
                    news_date = self.convert_to_date(news['data'])
                    if date_start <= news_date <= date_end:
                        href = news['link']
                        print(href)
                        href_list.append(href)
                break
            else:
                print("Datas inválidas. Por favor, forneça ambas as datas ou deixe ambas em branco.")
        return href_list


    def get_news(self):
      for url in self.find_to_date():
        tree = self.get_requests(url)
        time.sleep(1.5)
        news_box = tree.xpath('//div[@class="texto-conteudo"]')
        
        for news in news_box:
          news.text_content().lower().strip()
          news = news.text_content()
          news_dict = {'link': url, 'materia': self.replace_all(news)}
          found = False
          for idx, news_journal in enumerate(self.list_news):
              if news_journal['link'] == url:
                  if news_journal['materia'] != news_dict['materia']:
                      news_journal.update(news_dict)
                      self.list_news[idx] = news_journal
                      print('Extraindo matérias.')
                  found = True
                  break
          
          if not found:
              self.list_news.append(news_dict)
      return self.list_news


    def extract_news(self):
        for news in self.list_news:
            yield news


    def get_bd(self):
      url = self.url_bd
      response = requests.get(url)
      data = response.json()
      return data

    def post_bd(self, extracted_dict):
      url = self.url_bd
      json_data = extracted_dict
      response = requests.post(url, json=json_data)
      data = response.json()
      return data


    def save_bd(self):
        get_data = self.get_bd()
        if get_data == None:
            for item_extract in self.extract_news():
                print('Matéria adicionada ao banco de dados com sucesso.')
                self.post_bd(item_extract)
            print('Processo de salvamento concluído.')
        else:
            existing_materias = {value_bd.get('materia') for value_bd in get_data.values() if value_bd.get('materia')}
            
            for item_extract in self.extract_news():
                materia_extract = item_extract.get('materia')
                
                if materia_extract in existing_materias:
                    print('Matéria já existe no banco de dados.')
                else:
                    print('Matéria adicionada ao banco de dados com sucesso.')
                    self.post_bd(item_extract)
                    existing_materias.add(materia_extract)

            print('Processo de salvamento concluído.')




journal = NewsGov()
dept = journal.get_dept()
section = journal.get_section()
news = journal.get_news()
save_db = journal.save_bd()