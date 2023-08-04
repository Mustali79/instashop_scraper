
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert
from time import sleep
import pandas as pd
import os
from glob import glob
import logging
logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S', level=logging.INFO)


class InstaScraper:

    def __init__(self, location):
        self.init_driver()
        self.location = location

    def wait(self, by, selector):
        return WebDriverWait(self.chr_driver, 20).until(
            EC.presence_of_element_located((by, selector)))

    def scroll_down(self):
        self.chr_driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")

    def is_element_present(self, by, value):
        try:
            self.chr_driver.find_element(by, value)
            return True
        except:
            return False

    def get_number_of_products(self, product_class):
        return len(self.chr_driver.find_elements(By.CLASS_NAME, product_class))

    def move_last_column_to_first(self, df):
        # if not isinstance(df, pd.DataFrame):
        #     raise ValueError("Input must be a pandas DataFrame")

        # Get the last column name
        last_column = df.columns[-1]

        # Reorder the DataFrame columns with the last column moved to the first position
        df = df[[last_column] + df.columns[:-1].to_list()]

        return df

    def click_element(self, element):
        for i in range(10):
            try:
                element.click()
                return
            except Exception as e:
                self.chr_driver.find_element(
                    By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
                if i == 9:
                    raise e

    def init_driver(self):
        """
        Initiates chromedriver
        """
        s = Service("Users/Mustali/Desktop/Selenium/chromedriver")
        capabilities = DesiredCapabilities().CHROME
        chrome_options = Options()
        prefs = {
            'profile.default_content_setting_values':
            {
                'notifications': 1,
                'geolocation': 1
            },

            'profile.managed_default_content_settings':
            {
                'geolocation': 1
            },
        }

        chrome_options.add_experimental_option('prefs', prefs)
        capabilities.update(chrome_options.to_capabilities())

        self.chr_driver = webdriver.Chrome(service=s, options=chrome_options)

    def set_location(self):
        location_div = self.wait(
            By.CSS_SELECTOR, "#mainContainer > app-superstore > div > div.col-12.pb-delivery-box > app-delivery-box > div > div > div:nth-child(3) > nb-icon > svg > g")
        location_div.click()
        cookies_button = self.wait(
            By.ID, "CybotCookiebotDialogBodyButtonAccept")
        self.click_element(cookies_button)

        set_location_button = self.wait(
            By.XPATH, '//*[@id="cdk-overlay-0"]/nb-dialog-container/app-map/div/div/nb-card/nb-card-footer/div/app-button/button')
        self.click_element(set_location_button)
        set_location_input = self.wait(
            By.CSS_SELECTOR, '#cdk-overlay-0 > nb-dialog-container > app-map > div > nb-card > nb-card-body > div > div.searchBox.d-flex.justify-content-center > div > input')
        sleep(5)
        set_location_input.clear()
        set_location_input.send_keys(self.location)
        sleep(2)
        set_location_input.send_keys(Keys.ARROW_DOWN)
        set_location_input.send_keys(Keys.RETURN)
        sleep(1)
        confirm_location_button = self.wait(
            By.XPATH, '//*[@id="cdk-overlay-0"]/nb-dialog-container/app-map/div/nb-card/nb-card-footer/div/app-button/button')
        self.click_element(confirm_location_button)

    def parse_product(self, product):
        product_details = {}

        try:
            product_details['product_name'] = product.find_element(
                By.CLASS_NAME, "product-title").text.strip()
        except:
            product_details['product_name'] = "None"

        try:
            product_details['product_description'] = product.find_element(
                By.CLASS_NAME, "product-packaging-string").text.strip()
        except:
            product_details['product_description'] = "None"

        try:
            try:
                product_details['product_price'] = product.find_element(
                    By.CLASS_NAME, "price-txt").text.strip()
            except:
                product_details['product_price'] = product.find_element(
                    By.CLASS_NAME, "discount-price").text.strip()
        except:
            product_details['product price'] = "None"

        try:
            product_details['product_image_url'] = product.find_element(
                By.TAG_NAME, "img").get_attribute("src")
        except:
            product_details['product_image_url'] = "None"

        return product_details

    def parse_category(self, category):
        sleep(2)
        try:
            category_name = category.find_element(
                By.CLASS_NAME, "category-text.mt-1").text.strip()
            self.click_element(category)
        except:
            pass
        sleep(2)
        try:
            age_res_button = self.chr_driver.find_element(
                By.CSS_SELECTOR, f"app-age-restricted > div > nb-card > nb-card-footer > div > div:nth-child(2) > app-button > button")
            self.chr_driver.execute_script(
                "arguments[0].click();", age_res_button)
        except:
            pass
        product_class = "product.ng-star-inserted"
        try:
            self.wait(By.CLASS_NAME, product_class)
            num_products = self.get_number_of_products(product_class)
        except:
            num_products = 0
        while True:
            self.scroll_down()
            sleep(5)
            new_num_products = self.get_number_of_products(product_class)
            if new_num_products == num_products:
                break
            num_products = new_num_products
        products = self.chr_driver.find_elements(
            By.CLASS_NAME, product_class)
        category_products = []
        unique_products = []
        x = 1
        for product in products:
            product_details = self.parse_product(product)
            product_checker = {
                product_details['product_name']: product_details['product_description'], product_details['product_price']: product_details['product_image_url']}
            product_details['category'] = category_name
            if product_checker not in unique_products:
                category_products.append(product_details)
                unique_products.append(product_checker)
                logging.info(
                    f"Successfully Scraped product#{x}, {product_details['product_name']}")
                x += 1
        logging.info(
            f"Total {len(unique_products)} products found in category : {category_name}")
        self.chr_driver.back()
        return category_products

    def get_shop_name(self, shop):
        return shop.find_element(By.CLASS_NAME, "title").text.strip()

    def parse_shop(self, shop, folder_name):
        sleep(2)
        try:
            shop_name = self.get_shop_name(shop)
        except:
            pass
        logging.info(f"Scraping shop {shop_name}")
        self.click_element(shop)
        category_class = "category-item.ng-star-inserted"
        unique_categories = []
        try:
            self.wait(By.CLASS_NAME, category_class)
            categories = self.chr_driver.find_elements(
                By.CLASS_NAME, category_class)

        except:
            pass
        shop_products = []
        for i in range(len(categories)):
            try:
                if categories[i] not in unique_categories:
                    new_products = self.parse_category(categories[i])
                    shop_products = shop_products + new_products
                    shop_products_dataframe = pd.DataFrame(shop_products)
                    shop_products_dataframe = self.move_last_column_to_first(
                        shop_products_dataframe)
                    shop_products_dataframe.to_csv(
                        f"{folder_name}/{shop_name}.csv", index=False)
                    self.wait(By.CLASS_NAME, category_class)
                    categories = self.chr_driver.find_elements(
                        By.CLASS_NAME, category_class)
                    unique_categories.append(categories[i])
            except:
                pass

        self.chr_driver.back()

    def parse_market(self, selector, folder_name):

        sleep(2)
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)
        super_market_button = self.wait(
            By.CSS_SELECTOR, selector)
        self.click_element(super_market_button)
        sleep(2)

        shop_class = "col-12.col-sm-12.col-md-6.col-lg-4.col-xl-4.col-xxl-3.pb-3.app-large-client-class.ng-star-inserted"
        self.wait(By.CLASS_NAME, shop_class)
        shops = self.chr_driver.find_elements(By.CLASS_NAME, shop_class)

        shops_done = glob(folder_name + "/*.csv")
        shops_done = [shop_done.split("\\")[-1].replace(".csv", "")
                      for shop_done in shops_done]

        logging.info(f"Total {len(shops)} shops found")

        for i in range(len(shops)):
            try:
                shop_name = self.get_shop_name(shops[i])
                if shop_name not in shops_done:
                    self.parse_shop(shops[i], folder_name)
                    self.wait(By.CLASS_NAME, shop_class)
                    shops = self.chr_driver.find_elements(
                        By.CLASS_NAME, shop_class)
                    shops_done.append(shop_name)
            except:
                pass
        self.chr_driver.back()

    def start(self):

        logging.info("The scraper is started")

        self.chr_driver.get("https://instashop.com")

        self.set_location()

        market_selectors = [
            '#mainContainer > app-superstore > div > div.ng-star-inserted > div.superstore-pb.ng-star-inserted > div.ng-star-inserted > app-circle-slider > div > swiper > div > div:nth-child(4) > div > img']

        folder_names = ["Pharmacies"]

        for market_selector, folder_name in zip(market_selectors, folder_names):
            logging.info(f"Scraping products for {folder_name}")
            self.parse_market(market_selector, folder_name)


if __name__ == "__main__":
    scraper = InstaScraper(
        "2XJW+44P Sheikh Zayed City, Giza Governorate, Egypt")
    scraper.start()
