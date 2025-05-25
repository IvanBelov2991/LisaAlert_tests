from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from pages.base_page import BasePage


def before_scenario(context, scenario):
    # Настройка Chrome
    chrome_options = Options()
    # chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--lang=ru")

    # Инициализация драйвера
    context.driver = webdriver.Chrome(options=chrome_options)
    context.driver.implicitly_wait(10)

    context.page = BasePage(context.driver)  # Теперь context.page доступен


def after_scenario(context, scenario):
    if hasattr(context, 'driver'):
        context.driver.quit()
