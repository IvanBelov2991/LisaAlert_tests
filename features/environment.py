from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def before_scenario(context, scenario):
    # Настройка Chrome
    chrome_options = Options()
    # chrome_options.add_argument("--headless=new")  # добавить, чтобы прогонять тесты без включения браузера
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--lang=ru")

    # Инициализация драйвера
    context.driver = webdriver.Chrome(options=chrome_options)
    context.driver.implicitly_wait(10)


def after_scenario(context, scenario):
    # Закрытие браузера после сценария
    context.driver.quit()
