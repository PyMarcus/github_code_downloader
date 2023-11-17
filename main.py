import time
import typing
import httpx
import base64
import os
import json
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from configparser import RawConfigParser


load_dotenv()


class Downloader:
    def __init__(self, token: str) -> None:
        self.__token = token
        if not os.path.exists("result"):
            os.mkdir("result")
        self.__path: str = "result"

    def __read_ini_file(self, content: str):
        parser = RawConfigParser()
        parser.read("links.ini")
        return parser[content]

    def get_with_auth(self) -> None:
        header = {"Authorization": f"token {self.__token}"}
        content =  self.__read_ini_file("repository")
        pares = list(zip(content.get("username").strip().split(","), content.get("repository").strip().split(","), content.get("path").strip().split(",")))
        for items in pares:
            url: str = f'https://api.github.com/repos/{items[0].strip()}/{items[1].strip()}/contents/{items[2].strip()}'
            print(url)
            asyncio.run(self.__fetch(items[1], url, header))

    async def get_without_auth(self) -> None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/91.0.4472.124 Safari/537.36'
        }
        data = self.__read_ini_file("links").values()
        for links in data:
            for url in links.split(","):
                url = url.strip()
                print(url)
                async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
                    try:
                        code = await client.get(url, follow_redirects=True)
                        if code.status_code == 200:
                            self.__parser(url.split("/")[4] + "_" + url.split("/")[-1], code)
                        else:
                            print(code.status_code)
                    except httpx.ConnectError as e:
                        time.sleep(20)
                        print(f"ERROR {e} {url}")

    def __parser(self, name: str, code) -> None:
        try:
            parse = BeautifulSoup(code.text, "html.parser")
            code_content = json.loads(parse.text)["payload"]["blob"]["rawLines"]
            try:
                self.__save_code(name, ''.join(code_content))
            except TypeError as e:
                print(e)
                return code_content
        except Exception as e:
            print(e)

    async def __fetch(self, name: str, url: str, header: typing.Dict[str, str]) -> None:
        async with httpx.AsyncClient(headers=header) as cliente:
            try:
                response = await cliente.get(url)
                if response.status_code == 200:
                    data = response.json()["content"]
                    self.__save_code(name, base64.b64decode(data).decode())
                else:
                    print(f"{name} - {response.status_code}")
            except httpx.HTTPError as e:
                print(e)

    def __save_code(self, name: str, response: str) -> None:
        with open(f"result/{name}.txt", 'w') as f:
            f.write(response)


if __name__ == '__main__':
    import asyncio

    # PARA BAIXAR COM TOKEN DE AUTENTICAÇÂO:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise "Missing GITHUB_TOKEN"
    downloader: Downloader = Downloader(token)
    downloader.get_with_auth()

    # PARA BAIXAR SEM TOKEN DE AUTENTICACAO
    #downloader: Downloader = Downloader("")
    #asyncio.run(downloader.get_without_auth())
