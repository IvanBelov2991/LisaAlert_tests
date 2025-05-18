import os
import time

import allure
from selenium.common import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from typing import List, Tuple


class BasePage:
    def __init__(self, driver, timeout=10):
        self.driver = driver
        self.timeout = timeout

    # region Основные методы ожидания
    @allure.step('Найти видимый элемент')
    def wait_and_find_element(self, locator: Tuple[str, str], timeout: int = None) -> WebElement:
        """
        Улучшенная версия с кастомным таймаутом
        Args:
            locator: Кортеж (By.XXX, 'значение')
            timeout: Опциональное время ожидания
        """
        timeout = timeout or self.timeout
        return WebDriverWait(self.driver, timeout).until(
            ec.visibility_of_element_located(locator),
            message=f"Элемент {locator} не стал видимым за {timeout} сек"
        )

    @allure.step('Найти все элементы')
    def wait_and_find_elements(self, locator: Tuple[str, str], timeout: int = None) -> List[WebElement]:
        timeout = timeout or self.timeout
        return WebDriverWait(self.driver, timeout).until(
            ec.presence_of_all_elements_located(locator),
            message=f"Элементы {locator} не найдены за {timeout} сек"
        )

    @allure.step('Ожидание кликабельности элемента')
    def wait_for_clickable(self, locator: Tuple[str, str], timeout: int = None) -> WebElement:
        timeout = timeout or self.timeout
        return WebDriverWait(self.driver, timeout).until(
            ec.element_to_be_clickable(locator),
            message=f"Элемент {locator} не стал кликабельным за {timeout} сек"
        )

    # endregion

    # region Методы взаимодействия
    @allure.step('Клик по элементу')
    def click_element(self, locator: Tuple[str, str], timeout: int = None) -> None:
        """Улучшенный метод с обработкой StaleElementReferenceException"""
        try:
            self.wait_for_clickable(locator, timeout).click()
        except StaleElementReferenceException:
            # Повторная попытка если элемент устарел
            self.wait_for_clickable(locator, timeout).click()

    @allure.step('Ввод текста "{text}"')
    def enter_text(self, locator: Tuple[str, str], text: str, clear: bool = True, timeout: int = None) -> None:
        element = self.wait_and_find_element(locator, timeout)
        if clear:
            element.clear()
        element.send_keys(text)

    # endregion

    # region Поиск по атрибутам (универсальные методы)
    @allure.step('Кликнуть по элементу с атрибутом "{attr}"="{value}"')
    def click_by_attribute(self, attr: str, value: str, element_type: str = "*", timeout: int = None) -> None:
        """Универсальный метод для клика по любому атрибуту"""
        locator = (By.CSS_SELECTOR, f'{element_type}[{attr}="{value}"]')
        self.click_element(locator, timeout)

    @allure.step('Ввести "{text}" в поле с атрибутом "{attr}"="{value}"')
    def enter_text_by_attribute(self, attr: str, value: str, text: str, element_type: str = "input",
                                timeout: int = None) -> None:
        locator = (By.CSS_SELECTOR, f'{element_type}[{attr}="{value}"]')
        self.enter_text(locator, text, timeout=timeout)

    @allure.step('Кликнуть на текст "{text}"')
    def click_by_text(self, text: str, element_type: str = "*", timeout: int = None) -> None:
        """
        Универсальный метод для клика по тексту
        Args:
            text: Текст для поиска
            element_type: Тип элемента (button, div, span и т.д.)
            timeout: Кастомное время ожидания
        """
        locator = (By.XPATH, f"//{element_type}[contains(text(), '{text}')]")
        self.click_element(locator, timeout=timeout)

    @allure.step('Кликнуть на точный текст "{exact_text}"')
    def click_by_exact_text(self, exact_text: str, element_type: str = "*", timeout: int = None) -> None:
        """Для точного совпадения текста"""
        locator = (By.XPATH, f"//{element_type}[text()='{exact_text}']")
        self.click_element(locator, timeout=timeout)

    # endregion

    # region Специализированные методы (удобные обертки)
    def click_by_data_component(self, component_name: str, timeout: int = None) -> None:
        """Специализированная версия click_by_attribute"""
        self.click_by_attribute("data-component", component_name, timeout=timeout)

    def enter_text_to_data_component(self, component_name: str, text: str, timeout: int = None) -> None:
        """Специализированная версия enter_text_by_attribute"""
        self.enter_text_by_attribute("data-component", component_name, text, timeout=timeout)

    @allure.step('Ввести "{text}" в поле с placeholder="{placeholder}"')
    def enter_text_to_placeholder(self, text: str, placeholder: str, timeout: int = None):
        """
        Универсальный метод для input и textarea
        Args:
            text: Текст для ввода
            placeholder: Текст плейсхолдера
            timeout: Кастомное время ожидания
        """
        timeout = timeout or self.timeout
        locator = (By.XPATH, f"//*[@placeholder='{placeholder}' and (self::input or self::textarea)]")
        element = self.wait_and_find_element(locator, timeout)
        element.clear()
        element.send_keys(text)

    # endregion

    # region Проверки
    @allure.step('Проверить видимость элемента')
    def is_element_visible(self, locator: Tuple[str, str], timeout: int = None) -> bool:
        """Возвращает True если элемент видим, False если нет (без исключения)"""
        try:
            return self.wait_and_find_element(locator, timeout).is_displayed()
        except (NoSuchElementException, TimeoutException):
            return False

    @allure.step('Проверить отсутствие элемента')
    def is_element_not_visible(self, locator: Tuple[str, str], timeout: int = None) -> bool:
        """Возвращает True если элемент невидим/отсутствует"""
        timeout = timeout or self.timeout
        try:
            WebDriverWait(self.driver, timeout).until(
                ec.invisibility_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False

    @allure.step('Проверить наличие текста "{text}"')
    def is_text_present(self, text: str, exact_match: bool = False, timeout: int = None) -> bool:
        """
        Улучшенная версия с возможностью точного поиска
        Args:
            text: Искомый текст
            exact_match: True для точного совпадения, False для частичного
            timeout: Кастомное время ожидания
        """
        timeout = timeout or self.timeout
        xpath = f"//*[text()='{text}']" if exact_match else f"//*[contains(text(), '{text}')]"

        try:
            WebDriverWait(self.driver, timeout).until(
                ec.visibility_of_element_located((By.XPATH, xpath)),
                message=f"Текст '{text}' не найден за {timeout} сек"
            )
            return True
        except TimeoutException:
            allure.attach(
                self.driver.get_screenshot_as_png(),
                name=f"text_not_found_{text}",
                attachment_type=allure.attachment_type.PNG
            )
            return False

    @allure.step('Проверить отсутствие текста "{text}"')
    def is_text_not_present(self, text: str, exact_match: bool = False, timeout: int = None) -> bool:
        """Проверяет отсутствие текста на странице"""
        return not self.is_text_present(text, exact_match, timeout)

    # endregion

    # region Навигация
    @allure.step('Открыть страницу "{url}"')
    def open_page(self, url: str, verify: bool = True, timeout: int = None) -> None:
        """Улучшенная версия с обработкой редиректов"""
        timeout = timeout or self.timeout
        self.driver.get(url)

        # Ожидание полной загрузки
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete",
            message=f"Страница не загрузилась за {timeout} сек"
        )

        if verify:
            current_url = self.driver.current_url
            assert current_url == url, (
                f"URL страницы не совпадает с ожидаемым!\n"
                f"Ожидалось: {url}\nФактический: {current_url}"
            )

    # endregion

    # region Работа с файлами
    @allure.step('Загрузить файл "{file_path}" в элемент')
    def upload_file(self, locator: Tuple[str, str], file_path: str) -> None:
        """
        Загрузка файла через input[type="file"]

        Args:
            self: Экземпляр класса
            locator: Локатор элемента для загрузки
            file_path: Путь к файлу (абсолютный или относительный)
        """
        absolute_path = os.path.abspath(file_path)
        self.wait_and_find_element(locator).send_keys(absolute_path)

    @allure.step('Скачать файл по ссылке')
    def download_file(self, locator: Tuple[str, str], download_dir: str) -> str:
        """
        Кликает по ссылке для скачивания и возвращает путь к файлу

        Args:
            self: Экземпляр класса
            locator: Локатор ссылки/кнопки скачивания
            download_dir: Директория для скачивания

        Returns:
            str: Путь к скачанному файлу
        """
        self.click_element(locator)
        time.sleep(3)  # Ожидание загрузки файла
        return max(
            [os.path.join(download_dir, f) for f in os.listdir(download_dir)],
            key=os.path.getctime
        )

    # endregion

    # region Drag and Drop
    @allure.step('Переместить элемент {source_locator} на {target_locator}')
    def drag_and_drop(self, source_locator: Tuple[str, str], target_locator: Tuple[str, str]) -> None:
        """
        Перетаскивание элемента из source в target

        Args:
            self: Экземпляр класса
            source_locator: Локатор перетаскиваемого элемента
            target_locator: Локатор целевого элемента
        """
        source_element = self.wait_and_find_element(source_locator)
        target_element = self.wait_and_find_element(target_locator)
        ActionChains(self.driver).drag_and_drop(source_element, target_element).perform()
    # endregion
