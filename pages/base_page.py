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
from PIL import Image
from pixelmatch.contrib.PIL import pixelmatch
import io


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

    @allure.step('Нажать клавишу "{key}"')
    def press_key(self, key: str) -> None:
        """Нажимает клавишу (например, Keys.ENTER)"""
        ActionChains(self.driver).send_keys(key).perform()

    @allure.step('Ввести текст "{text}" с клавиатуры')
    def type_text(self, text: str) -> None:
        """Вводит текст с клавиатуры (имитация набора)"""
        ActionChains(self.driver).send_keys(text).perform()

    @allure.step('Переключиться на новую вкладку')
    def switch_to_new_tab(self, close_current: bool = False) -> None:
        """Переключается на новую вкладку"""
        if close_current:
            self.driver.close()
        handles = self.driver.window_handles
        self.driver.switch_to.window(handles[-1])

    @allure.step('Закрыть текущую вкладку')
    def close_current_tab(self) -> None:
        """Закрывает текущую вкладку"""
        self.driver.close()
        self.switch_to_new_tab()

    @allure.step('Переключиться на iframe')
    def switch_to_iframe(self, locator: Tuple[str, str]) -> None:
        """Переключается на iframe по локатору"""
        iframe = self.wait_and_find_element(locator)
        self.driver.switch_to.frame(iframe)

    @allure.step('Вернуться из iframe')
    def switch_to_default_content(self) -> None:
        """Возвращается из iframe в основной контент"""
        self.driver.switch_to.default_content()

    @allure.step('Выполнить JavaScript: "{script}"')
    def execute_js(self, script: str, *args) -> any:
        """Выполняет JavaScript-код и возвращает результат"""
        return self.driver.execute_script(script, *args)

    @allure.step('Проскроллить к элементу')
    def scroll_to_element(self, locator: Tuple[str, str]) -> None:
        """Скроллит страницу к указанному элементу"""
        element = self.wait_and_find_element(locator)
        self.execute_js("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)

    @allure.step('Проскроллить страницу вниз')
    def scroll_page_down(self, pixels: int = 500) -> None:
        """Скроллит страницу вниз на указанное количество пикселей"""
        self.execute_js(f"window.scrollBy(0, {pixels});")

    @allure.step('Проскроллить страницу вверх')
    def scroll_page_up(self, pixels: int = 500) -> None:
        """Скроллит страницу вверх на указанное количество пикселей"""
        self.execute_js(f"window.scrollBy(0, -{pixels});")

    @allure.step('Навести курсор на элемент')
    def hover_element(self, locator: Tuple[str, str], timeout: int = None) -> None:
        """
        Наводит курсор мыши на указанный элемент.

        Args:
            locator: Кортеж (By.XXX, 'значение') для поиска элемента
            timeout: Время ожидания элемента (по умолчанию из self.timeout)
        """
        element = self.wait_and_find_element(locator, timeout)
        ActionChains(self.driver).move_to_element(element).perform()

    @allure.step('Навести курсор на элемент с ID "{element_id}"')
    def hover_element_by_id(self, element_id: str, timeout: int = None) -> None:
        locator = (By.ID, element_id)
        self.hover_element(locator, timeout)

    @allure.step('Навести курсор на элемент с классом "{class_name}"')
    def hover_element_by_class(self, class_name: str, timeout: int = None) -> None:
        locator = (By.CLASS_NAME, class_name)
        self.hover_element(locator, timeout)

    @allure.step('Навести курсор на элемент с data-component="{component_name}"')
    def hover_element_by_data_component(self, component_name: str, timeout: int = None) -> None:
        locator = (By.CSS_SELECTOR, f'[data-component="{component_name}"]')
        self.hover_element(locator, timeout)

    @allure.step('Проверить, что элемент активен')
    def is_element_active(self, locator: Tuple[str, str], timeout: int = None) -> bool:
        """
        Проверяет, что элемент:
        1. Видим на странице
        2. Не имеет атрибута 'disabled'
        3. Ширина/высота > 0 (опционально)

        Args:
            locator: Кортеж (By.XXX, 'значение')
            timeout: Время ожидания элемента

        Returns:
            bool: True если элемент активен, False если нет
        """
        try:
            element = self.wait_and_find_element(locator, timeout)
            return (
                    element.is_displayed()
                    and element.is_enabled()
                    and element.size['width'] > 0
                    and element.size['height'] > 0
            )
        except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
            return False

    @allure.step('Проверить, что элемент неактивен')
    def is_element_disabled(self, locator: Tuple[str, str], timeout: int = None) -> bool:
        """
        Проверяет, что элемент:
        1. Имеет атрибут 'disabled' ИЛИ
        2. Неактивен через .is_enabled() ИЛИ
        3. Скрыт (опционально)

        Args:
            locator: Кортеж (By.XXX, 'значение')
            timeout: Время ожидания элемента

        Returns:
            bool: True если элемент неактивен, False если активен
        """
        try:
            element = self.wait_and_find_element(locator, timeout)
            return (
                    not element.is_enabled()
                    or element.get_attribute("disabled") is not None
                    or not element.is_displayed()
            )
        except (NoSuchElementException, TimeoutException):
            return True  # Элемент не найден = считается неактивным

    @allure.step('Проверить, что кнопка активна')
    def is_button_active(self, locator: Tuple[str, str], timeout: int = None) -> bool:
        """Специализированная проверка для button/input[type='button']"""
        return self.is_element_active(locator, timeout)

    @allure.step('Проверить, что кнопка неактивна')
    def is_button_disabled(self, locator: Tuple[str, str], timeout: int = None) -> bool:
        """Специализированная проверка для button/input[type='button']"""
        return self.is_element_disabled(locator, timeout)

    @allure.step("Сделать скриншот страницы")
    def take_screenshot(self, screenshot_name: str = "screenshot") -> Image.Image:
        """
        Делает скриншот текущей страницы и возвращает объект PIL.Image.

        Args:
            screenshot_name: Название для сохранения в отчете Allure

        Returns:
            PIL.Image: Объект изображения
        """
        screenshot_bytes = self.driver.get_screenshot_as_png()
        allure.attach(
            screenshot_bytes,
            name=screenshot_name,
            attachment_type=allure.attachment_type.PNG
        )
        return Image.open(io.BytesIO(screenshot_bytes))

    @allure.step("Сделать скриншот элемента {locator}")
    def take_element_screenshot(
            self,
            locator: Tuple[str, str],
            screenshot_name: str = "element_screenshot"
    ) -> Image.Image:
        """
        Делает скриншот конкретного элемента.

        Args:
            locator: Локатор элемента (By.XPATH, By.CSS_SELECTOR и т.д.)
            screenshot_name: Название для отчета Allure

        Returns:
            PIL.Image: Объект изображения элемента
        """
        element = self.wait_and_find_element(locator)
        screenshot_bytes = element.screenshot_as_png
        allure.attach(
            screenshot_bytes,
            name=screenshot_name,
            attachment_type=allure.attachment_type.PNG
        )
        return Image.open(io.BytesIO(screenshot_bytes))

    @allure.step("Сравнить скриншоты")
    def compare_screenshots(
            self,
            actual_image: Image.Image,
            expected_image_path: str,
            threshold: float = 0.1,
            save_diff: bool = True
    ) -> bool:
        """
        Сравнивает текущий скриншот с эталоном.

        Args:
            actual_image: Скриншот (PIL.Image)
            expected_image_path: Путь к эталонному изображению
            threshold: Допустимый порог различий (0-1)
            save_diff: Сохранять ли изображение с различиями

        Returns:
            bool: True если различия в пределах threshold, иначе False
        """
        expected_image = Image.open(expected_image_path)

        if actual_image.size != expected_image.size:
            raise ValueError("Размеры изображений не совпадают!")

        diff = Image.new("RGBA", actual_image.size)
        mismatch = pixelmatch(
            actual_image.convert("RGB"),
            expected_image.convert("RGB"),
            diff.convert("RGB"),
            threshold=threshold
        )

        if save_diff:
            diff_path = "diff.png"
            diff.save(diff_path)
            allure.attach.file(
                diff_path,
                name="DIFF: " + os.path.basename(expected_image_path),
                attachment_type=allure.attachment_type.PNG
            )

        return mismatch / (actual_image.width * actual_image.height) <= threshold

    @allure.step("Сравнить элемент с эталоном")
    def compare_element_with_expected(
            self,
            locator: Tuple[str, str],
            expected_image_path: str,
            threshold: float = 0.1
    ) -> bool:
        """
        Сравнивает элемент с эталонным изображением.

        Args:
            locator: Локатор элемента
            expected_image_path: Путь к эталону
            threshold: Допустимый порог различий

        Returns:
            bool: True если различия в пределах threshold
        """
        actual_image = self.take_element_screenshot(locator)
        return self.compare_screenshots(actual_image, expected_image_path, threshold)

    @allure.step("Проверить полную загрузку страницы")
    def wait_for_full_page_load(self, timeout: int = 15) -> bool:
        """
        Комплексная проверка полной загрузки страницы
        """
        try:
            # 1. Базовое ожидание готовности документа
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete",
                message="Документ не перешел в состояние 'complete'"
            )

            # 2. Проверка завершения AJAX-запросов
            try:
                WebDriverWait(self.driver, timeout).until(
                    lambda d: d.execute_script("""
                        if (typeof jQuery != 'undefined') return jQuery.active === 0;
                        if (typeof axios != 'undefined') return axios.activeRequests === 0;
                        return true;
                    """),
                    message="AJAX-запросы не завершились"
                )
            except:
                pass

            # 3. Автопоиск основных структурных элементов
            structural_elements = [
                ('body', By.TAG_NAME),
                ('main, .main, [role="main"]', By.CSS_SELECTOR),
                ('header, .header', By.CSS_SELECTOR),
                ('footer, .footer', By.CSS_SELECTOR)
            ]

            for selector, by in structural_elements:
                try:
                    elements = self.driver.find_elements(by, selector)
                    if elements:
                        WebDriverWait(self.driver, 5).until(
                            ec.visibility_of(elements[0]),
                            message=f"Структурный элемент {selector} не виден"
                        )
                except:
                    continue

            # 4. Проверка стабильности DOM
            initial_height = self.driver.execute_script("return document.body.scrollHeight")
            time.sleep(1)
            current_height = self.driver.execute_script("return document.body.scrollHeight")
            assert initial_height == current_height, "DOM не стабилен"

            return True

        except Exception as e:
            self.take_screenshot("page_load_failed")
            raise AssertionError(f"Ошибка загрузки страницы: {str(e)}")