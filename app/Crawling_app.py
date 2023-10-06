import uvicorn, time, openai, sys, os, re
from fastapi import FastAPI ,HTTPException
from selenium import webdriver
from selenium.webdriver.common.by import By
from starlette.middleware.cors import CORSMiddleware
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from sqlalchemy import create_engine,text
from bs4 import BeautifulSoup
from fastapi.responses import JSONResponse

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from private.api_key import api_key
from private.db_connect import db_host, db_user, db_password, db_database, table_name

def main(Main_Page_Url):
    try:
        options = Options()
        options.add_argument('--no-sandbox')        
        options.add_argument('--headless')       
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--disable-setuid-sandbox") 
        options.add_argument('--disable-gpu')
        options.add_argument("--window-size=1920,1080")
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--allow-running-insecure-content')
        
        # server
        service = ChromeService(executable_path = "/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(Main_Page_Url)
        time.sleep(1)

        # # local
        # driver = webdriver.Chrome(options=options)
        # driver.get(Main_Page_Url)
        # time.sleep(1)

        region = driver.find_element(By.ID, "expand")
        region.click()
        time.sleep(1)

        title = driver.find_elements(By.XPATH, '//*[@id="title"]/h1/yt-formatted-string')
        script = driver.find_elements(By.XPATH, '//*[@id="description-inline-expander"]')

        for i in title:
            title_text = i.text

        for i in script:
            scrpit_text = i.text

        scrpit_text = scrpit_text.replace('\n',' ')
        return title_text, scrpit_text
    
    except Exception as e:
        print('error:', e)
        quit()
        
def main_bs4(Main_Page_Url):
    try:
        options = Options()
        options.add_argument('--no-sandbox')        
        options.add_argument('--headless')       
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--disable-setuid-sandbox") 
        options.add_argument('--disable-gpu')
        options.add_argument("--window-size=1920,1080")
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--allow-running-insecure-content')
        
        # server
        service = ChromeService(executable_path = "/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(Main_Page_Url)
        time.sleep(1)

        # # local
        # driver = webdriver.Chrome(options=options)
        # driver.get(Main_Page_Url)
        # time.sleep(1)

        region = driver.find_element(By.ID, "expand")
        region.click()
        
        page_source = driver.page_source 
        soup = BeautifulSoup(page_source, "html.parser")
        
        soup = soup.find(id='above-the-fold')
        title_text = soup.find(id='title')
        title_text = title_text.get_text().replace('\n','')
        
        scrpit_text = soup.find(id='description-inline-expander')
        scrpit_text = scrpit_text.get_text().replace('\n',' ')
        
        return title_text, scrpit_text
    
    except Exception as e:
        print('error:', e)
        quit()

def connect_db(URL_id):
    
    # MySQL 데이터베이스에 연결
    db_engine = create_engine(f'mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_database}')

    query = f"SELECT url FROM {table_name};"

    with db_engine.connect() as connection:
        result = connection.execute(text(query))
        db_title = True
        for row in result.fetchall():  
            url = re.sub("[()',]","",str(row))
            if url == URL_id:
                db_title = False
                id_query = f'SELECT contents_id FROM {table_name} WHERE url = "{URL_id}";'
                result = connection.execute(text(id_query))
                for result in result.fetchall():
                    contentsId = int(*result) # *는 언패킹
                    print(contentsId)
                break
            else:
                db_title = True
                contentsId = 0
            
    return db_title, contentsId

def get_products(scrpit_text):
    openai.api_key = api_key
    query = """아래 주어진 글에서 재료만 뽑아서 아래 형태로 정리해줘. 요청한 정보외 다른글은 제거해줘.

                형태 : {'양파' : '1개', '당근': '1개', ...}
                
                """ + f"""글 : {scrpit_text}"""
                
    messages = [
        {"role": "user",
         "content": query}
    ]

    # ChatGPT API 호출하기
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.4
    )
    answer = response['choices'][0]['message']['content']
    
    answer = eval(answer)
    return answer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/{URL_id}")
def process(URL_id:str):
    Main_Page_Url = 'https://www.youtube.com/watch?v='+ URL_id
    db_title, contentsId = connect_db(URL_id)  
    if db_title:
        title_text, scrpit_text = main_bs4(Main_Page_Url)
        answer = get_products(scrpit_text)
        answer_2 = str(answer).replace("{","").replace("}","").replace("'","").replace(":","").replace(", ","\n")
        final = {}
        final['title'] = title_text
        final['description_1'] = answer
        final['description_2'] = answer_2
        return final
    else:
        return JSONResponse(
        status_code=409,
        content={"detail":"videoId find in DB","contentsId": f"{contentsId}"},
        )
    #   raise HTTPException(status_code=409, detail=f"videoId find in DB", headers={f"contentsId:{URL_id}"},)
    #   print("이미 등록된 자료.")
    #   return "이미 등록된 자료."

# # local test용
# if __name__ == '__main__':
#     uvicorn.run("Crawling_app:app", host='localhost', port=3000, reload=True)