❌ 오류 발생: Message: session not created: This version of ChromeDriver only supports Chrome version 114
Current browser version is 138.0.7204.101 with binary path C:\Program Files (x86)\Google\Chrome\Application\chrome.exe; For documentation on this error, please visit: https://www.selenium.dev/documentation/webdriver/troubleshooting/errors#sessionnotcreatedexception
Stacktrace:
Backtrace:
	GetHandleVerifier [0x00CEA813+48355]
	(No symbol) [0x00C7C4B1]
	(No symbol) [0x00B85358]
	(No symbol) [0x00BA61AC]
	(No symbol) [0x00BA1EF3]
	(No symbol) [0x00BA0579]
	(No symbol) [0x00BD0C55]
	(No symbol) [0x00BD093C]
	(No symbol) [0x00BCA536]
	(No symbol) [0x00BA82DC]
	(No symbol) [0x00BA93DD]
	GetHandleVerifier [0x00F4AABD+2539405]
	GetHandleVerifier [0x00F8A78F+2800735]
	GetHandleVerifier [0x00F8456C+2775612]
	GetHandleVerifier [0x00D751E0+616112]
	(No symbol) [0x00C85F8C]
	(No symbol) [0x00C82328]
	(No symbol) [0x00C8240B]
	(No symbol) [0x00C74FF7]
	BaseThreadInitThunk [0x76915D49+25]
	RtlInitializeExceptionChain [0x77DFD09B+107]
	RtlGetAppContainerNamedObjectPath [0x77DFD021+561]

Traceback (most recent call last):
  File "review_photo.py", line 100, in download_review_images
  File "selenium\webdriver\chrome\webdriver.py", line 47, in __init__
  File "selenium\webdriver\chromium\webdriver.py", line 69, in __init__
  File "selenium\webdriver\remote\webdriver.py", line 261, in __init__
  File "selenium\webdriver\remote\webdriver.py", line 362, in start_session
  File "selenium\webdriver\remote\webdriver.py", line 454, in execute
  File "selenium\webdriver\remote\errorhandler.py", line 232, in check_response
selenium.common.exceptions.SessionNotCreatedException: Message: session not created: This version of ChromeDriver only supports Chrome version 114
Current browser version is 138.0.7204.101 with binary path C:\Program Files (x86)\Google\Chrome\Application\chrome.exe; For documentation on this error, please visit: https://www.selenium.dev/documentation/webdriver/troubleshooting/errors#sessionnotcreatedexception
Stacktrace:
Backtrace:
	GetHandleVerifier [0x00CEA813+48355]
	(No symbol) [0x00C7C4B1]
	(No symbol) [0x00B85358]
	(No symbol) [0x00BA61AC]
	(No symbol) [0x00BA1EF3]
	(No symbol) [0x00BA0579]
	(No symbol) [0x00BD0C55]
	(No symbol) [0x00BD093C]
	(No symbol) [0x00BCA536]
	(No symbol) [0x00BA82DC]
	(No symbol) [0x00BA93DD]
	GetHandleVerifier [0x00F4AABD+2539405]
	GetHandleVerifier [0x00F8A78F+2800735]
	GetHandleVerifier [0x00F8456C+2775612]
	GetHandleVerifier [0x00D751E0+616112]
	(No symbol) [0x00C85F8C]
	(No symbol) [0x00C82328]
	(No symbol) [0x00C8240B]
	(No symbol) [0x00C74FF7]
	BaseThreadInitThunk [0x76915D49+25]
	RtlInitializeExceptionChain [0x77DFD09B+107]
	RtlGetAppContainerNamedObjectPath [0x77DFD021+561]
