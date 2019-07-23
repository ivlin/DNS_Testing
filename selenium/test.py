from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
driver = webdriver.Firefox()

extension_dir = "~/.mozilla/firefox/au1p11i6.default-default/extensions/"
extensions = [
    'uBlock0@raymondhill.net.xpi',
    ]

for extension in extensions:
    driver.install_addon(extension_dir + extension, temporary=True)

time.sleep(10)

driver.get("http://www.python.org")

assert "Python" in driver.title
elem = driver.find_element_by_name("q")
elem.clear()
elem.send_keys("pycon")
elem.send_keys(Keys.RETURN)
assert "No results found." not in driver.page_source
driver.close()
