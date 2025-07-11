import asyncio
import random
from typing import List, Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError, Page, Browser

class PlaywrightTwitterClient:
    """
    Handles browser automation for Twitter using Playwright (async, headless, with IP rotation and stealth).
    """
    def __init__(self, username: str, password: str, proxies: Optional[List[str]] = None):
        """Initialize with Twitter credentials and optional list of proxy URLs."""
        self.username = username
        self.password = password
        self.proxies = proxies or []
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.proxy = None
        self.context = None

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.proxy = random.choice(self.proxies) if self.proxies else None
        self.browser = await self.playwright.chromium.launch(headless=True, ignore_default_args=[
            '--disable-extensions', 
            '--disable-default-apps', 
            '--disable-component-extensions-with-background-pages'
        ])
        context_args = {}
        if self.proxy:
            context_args["proxy"] = {"server": self.proxy}
        self.context = await self.browser.new_context(**context_args)
        self.page = await self.context.new_page()
        webdriver_script = "Object.defineProperty(navigator, 'webdriver', {get: () => false})"
        await self.page.add_init_script(webdriver_script)
        permission_script = "Object.defineProperty(Notification, 'permission', {get: () => 'default'})"
        await self.page.add_init_script(permission_script)
        USER_AGENT = {
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
            "platform": "Win32",
            "acceptLanguage": "en-US, en",
            "userAgentMetadata": {
            "brands": [
                {"brand": " Not A;Brand", "version": "99"},
                {"brand": "Chromium", "version": "74"},
                {"brand": "Google Chrome", "version": "74"},
            ],
            "fullVersion": "74.0.3729.169",
            "platform": "Windows",
            "platformVersion": "10.0",
            "architecture": "x86",
            "model": "",
            "mobile": False,
            },
        }
        cdp = await self.page.context.new_cdp_session(self.page)
        await cdp.send('Network.setUserAgentOverride', USER_AGENT)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
        if self.playwright:
            await self.playwright.stop()

    async def _human_delay(self, min_sec=0.7, max_sec=1.8):
        await asyncio.sleep(random.uniform(min_sec, max_sec))

    async def login(self):
        """Simulate human login to Twitter."""
        try:
            await self.page.goto("https://twitter.com/login", timeout=30000)
            await self._human_delay(2, 3)
            # Wait for username input to appear (debugging aid)
            try:
                await self.page.wait_for_selector('input[name="text"]', timeout=60000)
            except Exception as e:
                print("Selector for username input not found within 60s.")
                await self.page.screenshot(path="login_page.png")
                print(await self.page.content())
                raise
            # Fill username
            await self.page.fill('input[name="text"]', self.username)
            await self._human_delay()
            await self.page.keyboard.press('Enter')
            await self._human_delay(2, 3)
            # Fill password
            await self.page.fill('input[name="password"]', self.password)
            await self._human_delay()
            await self.page.keyboard.press('Enter')
            await self._human_delay(3, 5)
            # Wait for home feed
            await self.page.wait_for_selector('div[data-testid="primaryColumn"]', timeout=20000)
        except PlaywrightTimeoutError:
            print("Login failed: Timeout.")
            await self.close()
            raise
        except Exception as e:
            print(f"Login failed: {e}")
            await self.close()
            raise

    async def scrape_feed(self, count: int = 20):
        """Scrape the latest `count` tweets from the home feed."""
        tweets = []
        if not self.page:
            raise RuntimeError("Not logged in. Call login() first.")
        await self.page.goto("https://twitter.com/home", timeout=30000)
        await self._human_delay(2, 3)
        last_height = 0
        tries = 0
        while len(tweets) < count and tries < 10:
            await self._human_delay(1, 2)
            tweet_elements = await self.page.query_selector_all('article[data-testid="tweet"]')
            for el in tweet_elements:
                try:
                    content = await el.query_selector('div[lang]')
                    content_text = await content.inner_text() if content else ""
                    author_el = await el.query_selector('div[dir="ltr"] span')
                    author = await author_el.inner_text() if author_el else ""
                    url_el = await el.query_selector('a[role="link"][href*="/status/"]')
                    url = await url_el.get_attribute('href') if url_el else None
                    tweet_id = url.split('/')[-1] if url else None
                    # Engagement metrics
                    likes_content = await el.query_selector('button[data-testid="like"]')
                    likes_label = await likes_content.get_attribute('aria-label')
                    likes = int(''.join(filter(str.isdigit, likes_label)) or 0)
                    retweets_content = await el.query_selector('button[data-testid="retweet"]')
                    retweets_label = await retweets_content.get_attribute('aria-label')
                    retweets = int(''.join(filter(str.isdigit, retweets_label)) or 0)
                    replies_content = await el.query_selector('button[data-testid="reply"]')
                    replies_label = await replies_content.get_attribute('aria-label')
                    replies = int(''.join(filter(str.isdigit, replies_label)) or 0)
            
                    tweet = {
                        'content': content_text,
                        'author': author,
                        'url': f'https://twitter.com{url}' if url else None,
                        'tweet_id': tweet_id,
                        'likes': likes,
                        'retweets': retweets,
                        'replies': replies
                    }
                    if tweet not in tweets and tweet['url']:
                        tweets.append(tweet)
                        if len(tweets) >= count:
                            break
                except Exception:
                    continue
            # Scroll to load more
            await self.page.mouse.wheel(0, 2000)
            await self._human_delay(1, 2)
            new_height = await self.page.evaluate('document.body.scrollHeight')
            if new_height == last_height:
                tries += 1
            else:
                tries = 0
            last_height = new_height
        return tweets[:count]

    async def repost_tweet(self, tweet_url: str):
        """Simulate reposting (retweeting) a tweet given its URL."""
        if not self.page:
            raise RuntimeError("Not logged in. Call login() first.")
        try:
            await self.page.goto(tweet_url, timeout=20000)
            await self._human_delay(2, 3)
            
            # Try multiple possible retweet selectors
            retweet_selectors = [
                'div[data-testid="retweet"]',
                '[data-testid="retweet"]',
                'div[aria-label*="Retweet"]',
                'div[aria-label*="Repost"]',
                'div[role="button"][aria-label*="Retweet"]',
                'div[role="button"][aria-label*="Repost"]'
            ]
            
            retweet_btn = None
            for selector in retweet_selectors:
                retweet_btn = await self.page.query_selector(selector)
                if retweet_btn:
                    print(f"Found retweet button with selector: {selector}")
                    break
            
            if not retweet_btn:
                print("Retweet button not found with any selector.")
                await self.page.screenshot(path="retweet_page.png")
                # print("Page content:", await self.page.content())
                return
                
            await retweet_btn.click()
            await self._human_delay(1, 2)
            
            # Try multiple confirm button selectors
            confirm_selectors = [
                'div[data-testid="retweetConfirm"]',
                '[data-testid="retweetConfirm"]',
                'div[data-testid="retweet"]',
                'div[role="button"][aria-label*="Retweet"]',
                'div[role="button"][aria-label*="Repost"]'
            ]
            
            confirm_btn = None
            for selector in confirm_selectors:
                confirm_btn = await self.page.query_selector(selector)
                if confirm_btn:
                    print(f"Found confirm button with selector: {selector}")
                    break
                    
            if not confirm_btn:
                print("Retweet confirm button not found.")
                await self.page.screenshot(path="retweet_confirm_page.png")
                return
                
            await confirm_btn.click()
            await self._human_delay(1, 2)
            print(f"Reposted tweet: {tweet_url}")
        except Exception as e:
            print(f"Failed to repost tweet: {e}")
            await self.page.screenshot(path="repost_error.png")

    async def reply_to_tweet(self, tweet_url: str, reply_text: str):
        """Simulate replying to a tweet with the given text."""
        if not self.page:
            raise RuntimeError("Not logged in. Call login() first.")
        try:
            await self.page.goto(tweet_url, timeout=20000)
            await self._human_delay(2, 3)
            
            # Try multiple possible reply selectors
            reply_selectors = [
                'div[data-testid="reply"]',
                'button[data-testid="reply"]',
                '[data-testid="reply"]',
                'div[aria-label*="Reply"]',
                'div[role="button"][aria-label*="Reply"]'
            ]
            
            reply_btn = None
            for selector in reply_selectors:
                reply_btn = await self.page.query_selector(selector)
                if reply_btn:
                    print(f"Found reply button with selector: {selector}")
                    break
                    
            if not reply_btn:
                print("Reply button not found with any selector.")
                await self.page.screenshot(path="reply_page.png")
                print("Page content:", await self.page.content())
                return
                
            await reply_btn.click()
            await self._human_delay(1, 2)
            
            # Try multiple textarea selectors
            textarea_selectors = [
                'div[role="textbox"]',
                '[data-testid="tweetTextarea_0_label"]',
                'div[contenteditable="true"]',
                'div[data-testid="tweetTextarea"]'
            ]
            
            textarea = None
            for selector in textarea_selectors:
                textarea = await self.page.query_selector(selector)
                if textarea:
                    print(f"Found textarea with selector: {selector}")
                    break
                    
            if not textarea:
                print("Reply textarea not found.")
                await self.page.screenshot(path="reply_textarea_page.png")
                return
                
            await textarea.click()
            await self._human_delay(0.5, 1.2)
            for char in reply_text:
                await textarea.type(char, delay=random.randint(30, 80))
            await self._human_delay(1, 7)
            
            # Try multiple send button selectors
            send_selectors = [
                'button[data-testid="tweetButton"]',
                'div[data-testid="tweetButton"]',
                '[data-testid="tweetButton"]',
                'div[data-testid="tweetButtonInline"]',
                'div[role="button"][aria-label*="Tweet"]'
            ]
            
            send_btn = None
            for selector in send_selectors:
                send_btn = await self.page.query_selector(selector)
                if send_btn:
                    print(f"Found send button with selector: {selector}")
                    break
                    
            if not send_btn:
                print("Send reply button not found.")
                await self.page.screenshot(path="reply_send_page.png")
                return
                
            await send_btn.scroll_into_view_if_needed()
            await self._human_delay(0.5, 1.2)
            try:
                await send_btn.click(timeout=10000)
            except Exception:
                print("Normal click on reply failed, trying force click.")
                await send_btn.click(timeout=10000, force=True)
            print(f"Replied to tweet: {tweet_url}")
        except Exception as e:
            print(f"Failed to reply to tweet: {e}")
            await self.page.screenshot(path="reply_error.png")

    async def close(self):
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.page = None 