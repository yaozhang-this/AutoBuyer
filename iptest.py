import sys
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
warnings.filterwarnings("ignore", category=UserWarning)
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

def ipCheck(filepath, haslimit=False, visits_limit=2000, notification=True, headless=False, addtocart=True, checkout=False):
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
	textFile.close()
	print(lines)
	foundButtons = []
	foundDrivers = []
	urls = []
	for url in lines:
		if url == '\n':
			continue
		urls.append(url)
		# profile = webdriver.FirefoxProfile(os.path.expanduser("/Volumes/Rocket-XTRM/Users/seseme/Library/Application\ Support/Firefox/Profiles/u5e1vmwr.default-release"))
		# d = webdriver.Firefox(profile)
		foundButtons.append(False)
		foundDrivers.append(None)
	while True:
		#reference before exception
		d = None
		try:
			for i, b in enumerate(foundButtons):
				if b is False:
					url = urls[i]
					domain = urlparse(url).netloc
					fireFoxOptions = webdriver.FirefoxOptions()
					if headless: fireFoxOptions.headless = True
					fireFoxOptions.set_preference("geo.enabled", True)
					fireFoxOptions.set_preference("geo.prompt.testing", True)
					fireFoxOptions.set_preference("geo.prompt.testing.allow", True)
					fireFoxOptions.set_preference('geo.provider.network.url',
											  'data:application/json,{"location": {"lat": 38.918910, "lng": -77.220010}, "accuracy": 100.0}')
					d = webdriver.Firefox(options=fireFoxOptions)
					d.get(url)
					action = "is on stock"
					if domain == "www.bestbuy.com":
						addToCartButton = addButton = d.find_element_by_class_name("add-to-cart-button")
						if "c-button-disabled" not in addToCartButton.get_attribute("class"):
							if addtocart:
								addToCartButton.click()
								action = "added to cart"
							title = d.find_element_by_tag_name("h1").get_attribute("innerText")
							price = d.find_element_by_class_name("priceView-hero-price").find_element_by_xpath(
								".//span").get_attribute("innerText")
							message = f"{title} {price} {action} for Bestbuy at {datetime.datetime.now().time()}. Quicklink: {url}"
							if notification: twi.send_simple_sms(message)
							print(message)
							foundButtons[i] = True
					elif domain == "www.gamestop.com":
						addToCartButton = addButton = d.find_element_by_id("add-to-cart")
						text = addToCartButton.get_attribute("innerText")
						if "Not Available" not in text and "Unavailable" not in text:
							title = d.find_element_by_class_name("product-name").get_attribute("innerText")
							message = f"{title} {action} for Gamestop at {datetime.datetime.now().time()}. Quicklink: {url}"
							if notification: twi.send_simple_sms(message)
							foundButtons[i] = True
					elif domain == "www.walmart.com":
						#need to modify webdriver
						try:
							addToCartButton = d.find_element_by_xpath("//*[@id=\"__next\"]/div[1]/div/div/div/div/section/main/div/div[2]/div/div[1]/div/div/div[1]/div/div[2]/div/div/div[3]/button")
							if addtocart:
								addToCartButton.click()
								action = "added to cart"
							title = d.find_element_by_tag_name("h1").get_attribute("innerText")
							message = f"{title} {action} for Walmart at {datetime.datetime.now().time()}. Quicklink: {url}"
							if notification: twi.send_simple_sms(message)
							foundButtons[i] = True
						except Exception as e:
							# not available/out of stock
							pass

					elif domain == "www.target.com":
						try:
							title = d.find_element_by_tag_name("h1").get_attribute("innerText")
							message = f"{title} {action} for Target at {datetime.datetime.now().time()}. Quicklink: {url}"
							print(message)
							if notification: twi.send_simple_sms(message)
							foundButtons[i] = True

						except Exception as e:
							#not available
							pass
					if foundButtons[i]:
						if addtocart: foundDrivers[i] = d
						else:
							time.sleep(1)
							d.close()
							d.quit()
					else:
						time.sleep(1)
						d.close()
						d.quit()

					if haslimit:
						visits_limit -= 1
						if visits_limit == 0:
							d.close()
							d.quit()
							message = f"Configured visits limit of {visits_limit} reached, terminating crawler"
							if notification: twi.send_simple_sms(message)
							print(message)
							sys.exit()



		except Exception as e:
			print(f"{e} occured at {datetime.datetime.now().time()}")
			# delete bad proxy from list
			# could optimize
			# print(f"Removed {proxies.pop(index)} from list")
			# close and retry
			d.close()
			d.quit()


def main():
	# every 10 minutes, refresh ip table and ping each of them
	ipCheck('test.txt', headless=True, addtocart=False)


if __name__ == '__main__':
	main()
