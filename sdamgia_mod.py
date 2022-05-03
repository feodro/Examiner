# Данный код является отрывком от исходного кода sdamgia-api (убраны ненужные нам функции)
# с добавлением возможности брать задания не только для ЕГЭ, но и ОГЭ
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import requests
from os import path, remove


class SdamGIA:
    def __init__(self, ex):
        self._BASE_DOMAIN = 'sdamgia.ru'
        self._SUBJECT_BASE_URL = {
            'math': f'https://math-{ex}ge.{self._BASE_DOMAIN}',
            'mathb': f'https://mathb-{ex}ge.{self._BASE_DOMAIN}',
            'phys': f'https://phys-{ex}ge.{self._BASE_DOMAIN}',
            'inf': f'https://inf-{ex}ge.{self._BASE_DOMAIN}',
            'rus': f'https://rus-{ex}ge.{self._BASE_DOMAIN}',
            'bio': f'https://bio-{ex}ge.{self._BASE_DOMAIN}',
            'en': f'https://en-{ex}ge.{self._BASE_DOMAIN}',
            'chem': f'https://chem-{ex}ge.{self._BASE_DOMAIN}',
            'geo': f'https://geo-{ex}ge.{self._BASE_DOMAIN}',
            'soc': f'https://soc-{ex}ge.{self._BASE_DOMAIN}',
            'de': f'https://de-{ex}ge.{self._BASE_DOMAIN}',
            'fr': f'https://fr-{ex}ge.{self._BASE_DOMAIN}',
            'lit': f'https://lit-{ex}ge.{self._BASE_DOMAIN}',
            'sp': f'https://sp-{ex}ge.{self._BASE_DOMAIN}',
            'hist': f'https://hist-{ex}ge.{self._BASE_DOMAIN}',
        }
        self.tesseract_src = 'tesseract'
        self.html2img_chrome_path = 'chrome'
        self.grabzit_auth = {'AppKey': 'grabzit', 'AppSecret': 'grabzit'}

    def get_problem_by_id(self,
                          subject, id,
                          img=None, path_to_img=None, path_to_tmp_html=''):
        """
        Получение информации о задаче по ее идентификатору
        :param subject: Наименование предмета
        :type subject: str
        :param id: Идентификатор задачи
        :type subject: str
        :param img: Принимает одно из двух значений: pyppeteer или grabzit;
                    В результате будет использована одна из библиотек для генерации изображения с задачей.
                    Если не передавать этот аргумент, изображение генерироваться не будет
        :type img: str
        :param path_to_img: Путь до изображения, куда сохранить сохранить задание.
        :type path_to_img: str
        :param path_to_html: Можно указать директорию, куда будут сохраняться временные html-файлы заданий при использовании pyppeteer
        :type path_to_html: str
        :param grabzit_auth: При использовании GrabzIT укажите данные для аутентификации: {"AppKey":"...", "AppSecret":"..."}
        :type grabzit_auth: dict
        """

        doujin_page = requests.get(
            f'{self._SUBJECT_BASE_URL[subject]}/problem?id={id}')
        soup = BeautifulSoup(doujin_page.content, 'html.parser')

        probBlock = soup.find('div', {'class': 'prob_maindiv'})
        if probBlock is None:
            return None

        for i in probBlock.find_all('img'):
            if not 'sdamgia.ru' in i['src']:
                i['src'] = self._SUBJECT_BASE_URL[subject] + i['src']

        URL = f'{self._SUBJECT_BASE_URL[subject]}/problem?id={id}'

        TOPIC_ID = ' '.join(probBlock.find(
            'span', {'class': 'prob_nums'}).text.split()[1:][:-2])
        ID = id

        CONDITION, SOLUTION, ANSWER, ANALOGS = {}, {}, '', []

        try:
            CONDITION = {'text': probBlock.find_all('div', {'class': 'pbody'})[0].text,
                         'images': [i['src'] for i in probBlock.find_all('div', {'class': 'pbody'})[0].find_all('img')]
                         }
        except IndexError:
            pass

        try:
            SOLUTION = {'text': probBlock.find_all('div', {'class': 'pbody'})[1].text,
                        'images': [i['src'] for i in probBlock.find_all('div', {'class': 'pbody'})[1].find_all('img')]
                        }
        except IndexError:
            pass
        except AttributeError:
            pass

        try:
            ANSWER = probBlock.find(
                'div', {'class': 'answer'}).text.replace('Ответ: ', '')
        except IndexError:
            pass
        except AttributeError:
            pass

        try:
            ANALOGS = [i.text for i in probBlock.find(
                'div', {'class': 'minor'}).find_all('a')]
            if 'Все' in ANALOGS:
                ANALOGS.remove('Все')
        except IndexError:
            pass
        except AttributeError:
            pass

        if not img is None:

            for i in probBlock.find_all('div', {'class': 'minor'}):  # delete the information parts of problem
                i.decompose()
            probBlock.find_all('div')[-1].decompose()

            # Pyppeteer
            if img == 'pyppeteer':
                import asyncio
                from pyppeteer import launch
                open(f'{path_to_tmp_html}{id}.html', 'w', encoding='utf-8').write(str(probBlock))
                async def main():
                    browser = await launch()
                    page = await browser.newPage()
                    await page.goto('file:' + path.abspath(f'{path_to_tmp_html}{id}.html'))
                    await page.screenshot({'path': path_to_img, 'fullPage': 'true'})
                    await browser.close()
                asyncio.get_event_loop().run_until_complete(main())
                remove(path.abspath(f'{path_to_tmp_html}{id}.html'))

            # Grabz.it
            elif img == 'grabzit':
                from GrabzIt import GrabzItClient, GrabzItImageOptions
                grabzIt = GrabzItClient.GrabzItClient(self.grabzit_auth['AppKey'], self.grabzit_auth['AppSecret'])
                options = GrabzItImageOptions.GrabzItImageOptions()
                options.browserWidth = 800
                options.browserHeight = -1
                grabzIt.HTMLToImage(str(probBlock), options=options)
                grabzIt.SaveTo(path_to_img)

            # HTML2Image
            elif img == 'html2img':
                from html2image import Html2Image
                if self.html2img_chrome_path == 'chrome': hti = Html2Image()
                else: hti = Html2Image(chrome_path=self.html2img_chrome_path, custom_flags=['--no-sandbox'])
                hti.screenshot(html_str=str(probBlock), save_as=path_to_img)

        return {'id': ID, 'topic': TOPIC_ID, 'condition': CONDITION, 'solution': SOLUTION, 'answer': ANSWER,
                'analogs': ANALOGS, 'url': URL}