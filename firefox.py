import datetime
import logging
import sys
import time
import signal
import warnings  # install geckodriver via pip
from colorama import Fore, init
from urllib.parse import urlparse

init(autoreset=True)
import geckodriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.common.by import By

import send_twilio as twi

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
geckodriver_autoinstaller.install()


def refresh_ip_table():
	"""
	refresh_ip_table crawls free proxies from sslproxies.org

	:return: proxies: list of dictionaries of ssl proxies
	"""

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
		# Format of the dictionary
		# {'IP Address': '200.85.169.18',
		#  'Port': '47548',
		#  'Code': 'NI',
		#  'Country': 'Nicaragua',
		#  'Anonymity': 'elite proxy',
		#  'Google': 'no',
		#  'Https': 'yes',
		#  'Last Checked': '8 secs ago'}
		return proxies


def crawl(filepath, has_limit=False, visits_limit=2000, notification=True, headless=False, add_to_cart=True,
		  checkout=False, duration=86400, retry_timeout=600, log=False):
	"""
	crawl does periodic crawling of selected sites from input file, has capabilities to perform actions case-by-case

	:param filepath: absolute path of input file that contains urls
    :param has_limit: flag for limiting access frequency
    :param visits_limit: quantity of access limit, default is 2000 times
    :param notification: flag for remote notification of in-stock alert
    :param headless: flag for headless execution of webdriver
    :param add_to_cart: flag for default action performed
    :param checkout: flag for default action performed
	:param duration: timeout for crawl which ever comes first, default is 1 day
	:param retry_timeout: timeout for retry after a DNS Not Found error, default is 10 minutes
	:param log: flag for periodic crawl report

	:return None
	"""

	# proxies = refreshIPTable()
	# index = 0
	# index = random.randint(0, len(proxies) - 1)
	# PROXY = proxies[index]["IP Address"] + ":" + proxies[index]["Port"]
	# "IPv4:PORT"
	# PROXY = "149.19.224.15:3128"
	# webdriver.DesiredCapabilities.FIREFOX['proxy'] = {
	# 	"httpProxy": PROXY,
	# 	"sslProxy": PROXY,
	# 	"proxyType": "MANUAL",
	# }
	textFile = open(filepath, "r")
	lines = textFile.readlines()
	textFile.close()
	logging.info(f"list of url to crawl: {lines}")
	foundButtons = []
	foundDrivers = []
	urls = []
	errors = []
	stat_num_of_visits = 0
	start_time = time.time()
	stat_runtime = 0
	stat_num_of_fails = 0

	def report():
		end_time = time.time()
		stat_runtime = end_time - start_time
		spacer = Fore.LIGHTYELLOW_EX + "=-" * 30 + "="
		spacer2 = Fore.LIGHTYELLOW_EX + "|" + " " * 59 + "|"
		header = "|" + " " * 14 + "Runtime Report " + str(datetime.datetime.now().time()) + " " * 15 + '|'
		content = "|" + " " * 7 + f"{Fore.BLUE}Program Runtime: {'%.2f' % stat_runtime}, {Fore.GREEN}Visits: " \
				  						f"{stat_num_of_visits}, {Fore.RED}Fails:" \
								   							f" {stat_num_of_fails} {Fore.LIGHTYELLOW_EX}" + " " * 9 + "|"
		print(f"{spacer}\n{spacer2}\n{header}\n{content}\n{spacer2}\n{spacer}")

	def teardown():
		if log: report()
		sys.exit()

	def handler_teardown(signum, frame):

		"""
		handler terminates the program when called

		"""
		logging.info(f"Stopping: execution duration of {duration} seconds reached")
		teardown()

	signal.signal(signal.SIGALRM, handler_teardown)
	signal.alarm(duration)  # A whole day would be 60 * 60 * 24 = 86400 secs

	for url in lines:
		if url == '\n':
			continue
		urls.append(url)
		foundButtons.append(False)
		foundDrivers.append(None)
		errors.append((False, False))

	unit_report = 100  # say 1 report per 100 visits
	while True:
		d = None  # reference before exception
		for i, b in enumerate(foundButtons):
			if not b and not errors[i][0]:
				try:
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
						addToCartButton = d.find_element_by_class_name("add-to-cart-button")
						if "c-button-disabled" not in addToCartButton.get_attribute("class"):
							if add_to_cart:
								addToCartButton.click()
								action = "added to cart"
							title = d.find_element_by_tag_name("h1").get_attribute("innerText")
							price = d.find_element_by_class_name("priceView-hero-price").find_element_by_xpath(
								".//span").get_attribute("innerText")
							message = f"{title} {price} {action} for Bestbuy at {datetime.datetime.now().time()}. Quicklink: {url}"
							if notification: twi.send_simple_sms(message)
							logging.info(message)
							foundButtons[i] = True

					elif domain == "www.gamestop.com":
						addToCartButton = d.find_element_by_id("add-to-cart")
						text = addToCartButton.get_attribute("innerText")
						if "Not Available" not in text and "Unavailable" not in text:
							title = d.find_element_by_class_name("product-name").get_attribute("innerText")
							message = f"{title} {action} for Gamestop at {datetime.datetime.now().time()}. Quicklink: {url}"
							if notification: twi.send_simple_sms(message)
							logging.info(message)
							foundButtons[i] = True

					elif domain == "www.walmart.com":  # need to modify webdriver
						try:
							addToCartButton = d.find_element_by_xpath(
								"//*[@id=\"__next\"]/div[1]/div/div/div/div/section/main/div/div[2]/div/div[1]/div/div/div[1]/div/div[2]/div/div/div[3]/button")
							if add_to_cart:
								addToCartButton.click()
								action = "added to cart"
							title = d.find_element_by_tag_name("h1").get_attribute("innerText")
							message = f"{title} {action} for Walmart at {datetime.datetime.now().time()}. Quicklink: {url}"
							if notification: twi.send_simple_sms(message)
							logging.info(message)
							foundButtons[i] = True
						except Exception:
							# not available/out of stock
							pass

					elif domain == "www.target.com":
						try:
							title = d.find_element_by_tag_name("h1").get_attribute("innerText")
							message = f"{title} {action} for Target at {datetime.datetime.now().time()}. Quicklink: {url}"
							logging.info(message)
							if notification: twi.send_simple_sms(message)
							foundButtons[i] = True

						except Exception as e:
							# not available
							pass
					if foundButtons[i]:
						if add_to_cart:
							foundDrivers[i] = d
						else:
							time.sleep(1)
							d.close()
							d.quit()
					else:
						time.sleep(1)
						d.close()
						d.quit()

					stat_num_of_visits += 1
					if stat_num_of_visits != 0 and stat_num_of_visits % unit_report == 0: report()

					if has_limit and stat_num_of_visits == visits_limit:
						d.close()
						d.quit()
						message = f"Configured visits limit of {visits_limit} reached, terminating crawler"
						if notification: twi.send_simple_sms(message)
						logging.info(message)
						teardown()

				except KeyboardInterrupt:
					teardown()

				except Exception as e:
					logging.error(f"{e} occured at {datetime.datetime.now().time()}")
					errors[i] = True
					# close and retry
					stat_num_of_fails += 1
					d.close()
					d.quit()
			elif not b and errors[i][0]:
				# skip the errored url until timeout complete
				def handler_retry(signum, frame):
					# turn error flag off when called
					errors[i] = (False, False)
				# the second subflag of error flag indicates if timeout is triggered
				if not errors[i][1]:
					errors[i] = (True, True)
					signal.signal(signal.SIGALRM, handler_retry)
					signal.alarm(retry_timeout)  # A whole day would be 60 * 60 * 24 = 86400 secs


def main():
	crawl('ps5_source.txt', headless=True, add_to_cart=False, log=True)


if __name__ == '__main__':
	main()
