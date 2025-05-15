from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import asyncio
from google import genai
from dotenv import load_dotenv
import random
import os
load_dotenv()
LLM = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
model = "gemini-2.0-flash"
mcp = FastMCP("ZaubaInvestorTool")

@mcp.tool()
async def get_correct_company_name(company_name: str) -> str:
    prompt = f"""
    You are given the name of a company: {company_name}. Your task is to return the full registered name of the company from your own knowledge. For example
    retistered name of Paytm is One 97 Communications. However, if you dont know the registered name, dont change the {company_name}. If you are unsure about which company the user is talking about, IIMEDIATELY STOP and give them option of around 5 companies from zaubacorp website.
    Also note that you should ONLY RETURN CONTAIN COMPANY NAME in 1-5 words (max 10). No suffix, no prefix.
    """

    response = LLM.models.generate_content(
        model=model,
        contents=prompt
    )
    raw_response = response.text.strip()
    return raw_response
    #return '''You are given the name of a company: {prompt}. Your task is to return the full registered name of the company from your own knowledge. For example
    #retistered name of Paytm is One 97 Communications. However, if you dont know the registered name, dont change the {prompt}. If you are unsure about which company the user is talking about, give them option of around 5 companies.'''

@mcp.tool()
async def extract_investor_section(company_name: str) -> str:
    """
    Extracts text between 'investors' and 'Annual Compliance Status' from zaubacorp.com
    for the given company name.
    """
    #return (raw_response)
    HEADFUL = False
    VIEWPORT = {"width": 1366, "height": 768}
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.5790.170 Safari/537.36"
    )

    async with async_playwright() as p:
        launch_args = {"headless": not HEADFUL}
        browser = await p.chromium.launch(**launch_args)
        context = await browser.new_context(
            viewport=VIEWPORT,
            user_agent=USER_AGENT,
            locale="en-US",
            timezone_id="Asia/Kolkata",
            java_script_enabled=True,
        )
        page = await context.new_page()
        await stealth_async(page)

        await page.goto(f"https://www.zaubacorp.com/companysearchresults/{company_name}", timeout=60000)
        await asyncio.sleep(random.uniform(1, 2))

        link_elements = await page.query_selector_all("a")
        links = []
        count = 0
        for el in link_elements:
            href = await el.get_attribute("href")
            if href and href.startswith("https://www.zaubacorp.com"):
                links.append(href)
                count += 1
                break
                if count == 10:
                    break

        await browser.close()

        if not links:
            return "No company links found."
        companies = []
        for link in links:
            # Re-launch for second page visit
            browser = await p.chromium.launch(**launch_args)
            context = await browser.new_context(
                viewport=VIEWPORT,
                user_agent=USER_AGENT,
                locale="en-US",
                timezone_id="Asia/Kolkata",
                java_script_enabled=True,
            )
            page = await context.new_page()
            await stealth_async(page)

            await page.goto(link, timeout=60000)
            await asyncio.sleep(random.uniform(1, 2))

            await page.get_by_role("link", name="Contact Information").click()
            await asyncio.sleep(1)

            viewport_text = await page.locator("body").inner_text()

            start_marker = "investors"
            end_marker = "Annual Compliance Status"

            lower_text = viewport_text.lower()
            start_index = lower_text.find(start_marker)
            end_index = lower_text.find(end_marker.lower())

            await browser.close()

            if start_index != -1 and end_index != -1 and end_index > start_index:
                extracted_text = viewport_text[start_index + len(start_marker):end_index].strip()
                companies.append(extracted_text)
            #else:
                #print("Markers not found or out of order.")
        
        return (
                    f'From the following texts, extract the relevant company as asked and give the information about the company including CIN number, '
                    f'registration number, email address, physical address, phone number, current status, directors, '
                    f'date of incorporation and company type. This is the text for all the companies: {companies}'
                )

if __name__ == "__main__":
    #print(asyncio.run(get_correct_company_name('CashRich is a Mutual fund company')))
    #mcp.run(transport = "streamable-http", host="0.0.0.0", port=8000)
    port = int(os.environ.get("PORT", 8000)) 
    mcp.run(transport="sse", port=port)
