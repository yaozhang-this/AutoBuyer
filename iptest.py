import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import geckodriver_autoinstaller
import random, datetime, os
import sendtwilio as twi
from urllib.parse import urlparse

# install geckodriver via pip
from selenium.webdriver.support.wait import WebDriverWait
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
geckodriver_autoinstaller.install()


def refreshIPTable():
	with webdriver.Firefox() as driver:
		driver.get("https://sslproxies.org/")
		table = driver.find_element(By.TAG_NAME, 'table')
		thead = table.find_element(By.TAG_NAME, 'thead').find_elements(By.TAG_NAME, 'th')
		tbody = table.find_element(By.TAG_NAME, 'tbody').find_elements(By.TAG_NAME, 'tr')

		headers = []
		for th in thead:
			headers.append(th.text.strip())

		proxies = []
		for tr in tbody:
			proxy_data = {}
			tds = tr.find_elements(By.TAG_NAME, 'td')
			for i in range(len(headers)):
				proxy_data[headers[i]] = tds[i].text.strip()
			# Might extend this part to selectively filter regions
			# Proxy quality is disconcerting, only get proxy verified within 10 minutes
			if proxy_data["Country"] == "United States":
				if "mins ago" in proxy_data["Last Checked"]:
					if int(proxy_data["Last Checked"][0:2]) < 10:
						proxies.append(proxy_data)
					else:
						pass
				else:
					proxies.append(proxy_data)
		return proxies


# Format of the dictionary
# {'IP Address': '200.85.169.18',
#  'Port': '47548',
#  'Code': 'NI',
#  'Country': 'Nicaragua',
#  'Anonymity': 'elite proxy',
#  'Google': 'no',
#  'Https': 'yes',
#  'Last Checked': '8 secs ago'}

def ipCheck(filepath, visit_limits=2000, notification=True, headless=False,):
	# proxies = refreshIPTable()
	index = 0
	# index = random.randint(0, len(proxies) - 1)
	# PROXY = proxies[index]["IP Address"] + ":" + proxies[index]["Port"]
	# PROXY = "149.19.224.15:3128"
	# webdriver.DesiredCapabilities.FIREFOX['proxy'] = {
	# 	"httpProxy": PROXY,
	# 	"sslProxy": PROXY,
	# 	"proxyType": "MANUAL",
	# }
	textFile = open(filepath, "r")
	lines = textFile.readlines()
	print(lines)
	drivers = []
	foundButtons = []
	for url in lines:
		if url == '\n':
			continue
		# profile = webdriver.FirefoxProfile(os.path.expanduser("/Volumes/Rocket-XTRM/Users/seseme/Library/Application\ Support/Firefox/Profiles/u5e1vmwr.default-release"))
		# d = webdriver.Firefox(profile)
		d = webdriver.Firefox()
		d.get(url)
		drivers.append(d)
		domain = urlparse(url).netloc
		if domain == "www.bestbuy.com":
			addToCartButton = addButton = d.find_element_by_class_name("add-to-cart-button")
			if "c-button-disabled" not in addToCartButton.get_attribute("class"):
				addToCartButton.click()
				title = d.find_element_by_tag_name("h1").get_attribute("innerText")
				price = d.find_element_by_class_name("priceView-hero-price").find_element_by_xpath(
					".//span").get_attribute("innerText")
				message = f"{title} {price} added to cart for Bestbuy at {datetime.datetime.now().time()}. Quicklink: {url}"
				if notification: twi.send_simple_sms(message)
				print(message)
				foundButtons.append(True)
			else:
				foundButtons.append(False)
		if domain == "www.gamestop.com":
			addToCartButton = addButton = d.find_element_by_id("add-to-cart")
			text = addToCartButton.get_attribute("innerText")
			if "Not Available" not in text and "Unavailable" not in text:
				title = d.find_element_by_class_name("product-name").get_attribute("innerText")
				message = f"{title} is on stock for Gamestop at {datetime.datetime.now().time()}. Quicklink: {url}"
				if notification: twi.send_simple_sms(message)
				print(addToCartButton.get_attribute("innerText"))
				print(message)

				foundButtons.append(True)
			else:
				foundButtons.append(False)
	while True:
		try:
			for i, b in enumerate(foundButtons):
				if b is False:
					drivers[i].refresh()
					url = drivers[i].current_url
					domain = urlparse(url).netloc
					if domain == "www.bestbuy.com":
						addToCartButton = addButton = drivers[i].find_element_by_class_name("add-to-cart-button")
						if "c-button-disabled" not in addToCartButton.get_attribute("class"):
							addToCartButton.click()
							title = drivers[i].find_element_by_tag_name("h1").get_attribute("innerText")
							price = drivers[i].find_element_by_class_name("priceView-hero-price").find_element_by_xpath(
								".//span").get_attribute("innerText")
							message = f"{title} {price} added to cart for Bestbuy at {datetime.datetime.now().time()}. Quicklink: {url}"
							if notification: twi.send_simple_sms(message)
							print(message)
							foundButtons[i] = True
					if domain == "www.gamestop.com":
						addToCartButton = addButton = drivers[i].find_element_by_id("add-to-cart")
						text = addToCartButton.get_attribute("innerText")
						if "Not Available" not in text and "Unavailable" not in text:
							title = drivers[i].find_element_by_class_name("product-name").get_attribute("innerText")
							message = f"{title} is on stock for Gamestop at {datetime.datetime.now().time()}. Quicklink: {url}"
							if notification: twi.send_simple_sms(message)
							print(text, "Not Available")
							print(message)
							foundButtons[i] = True
					time.sleep(2)
					visit_limits -= 1
					if visit_limits == 0:
						for i, f in enumerate(foundButtons):
							if not f:
								url = lines[i]
								drivers[i].close()
								drivers[i].quit()
								drivers[i] = webdriver.Firefox()
								drivers[i].get(url)
						break


		except Exception as e:
			print(f"{e} occured at {datetime.datetime.now().time()}")
			# delete bad proxy from list
			# could optimize
			# print(f"Removed {proxies.pop(index)} from list")
			for i, f in enumerate(foundButtons):
				if not f:
					url = lines[i]
					drivers[i].close()
					drivers[i].quit()
					drivers[i] = webdriver.Firefox()
					drivers[i].get(url)


def main():
	# every 10 minutes, refresh ip table and ping each of them
	ipCheck('test.txt')


if __name__ == '__main__':
	main()
