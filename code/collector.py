import requests

test_URL = """https://www.google.com/search?q=Free Streaming&sca_esv=6a464870af6be845&sxsrf=APpeQntsmLYZR-H8-LTAO5HVJjzhOz7sTg:1789164589470&ei=LXykauiwHKvKp84PzZS3oQ8&biw=2493&bih=623&ved=2ahUKEwio-7K-xeeWAxUr5ckDHU3KLfQQ4dUDegQIBhAM&oq=Free Streaming&gs_lp=Egxnd3Mtd2l6LXNlcnAiDkZyZWUgU3RyZWFtaW5nMgoQABhHGNYEGLADMgoQABhHGNYEGLADMgoQABhHGNYEGLADMgoQABhHGNYEGLADMgoQABhHGNYEGLADMgoQABhHGNYEGLADMgoQABhHGNYEGLADMgoQABhHGNYEGLADMg0QABiABBiKBRhDGLADMg0QABiABBiKBRhDGLADMg0QABiABBiKBRhDGLADMg0QABiABBiKBRhDGLADMhcQLhjcBhi4BhjaBhjYAhjIAxiwA9gBATIXEC4Y3AYYuAYY2gYY2AIYyAMYsAPYAQEyFxAuGNwGGLgGGNoGGNgCGMgDGLAD2AEBMhcQLhjcBhi4BhjaBhjYAhjIAxiwA9gBATIXEC4Y3AYYuAYY2gYY2AIYyAMYsAPYAQEyFxAuGNwGGLgGGNoGGNgCGMgDGLAD2AEBMhcQLhjcBhi4BhjaBhjYAhjIAxiwA9gBAUjnFFAAWABwAXgBkAEAmAEAoAEAqgEAuAEMyAEAmAIBoAIKmAMAiAYBkAYTugYGCAEQARgZkgcBMaAHALIHALgHAMIHAzItMcgHB4AIAQ&sclient=gws-wiz-serp"""

def get_raw_url_content(URL):
    """This is a first function to just pull in a single URL"""

    content = requests.get(URL)

    return content

def output_requests_response(URL):
    """Prings out the Headers, response code, and text of a website"""

    content = get_raw_url_content(URL)

    print(f"Headers: {content.headers}")
    print(f"Response Code: {content.status_code}")
    print(f"Website Text: {content.text}")

# for i in range(10):
#     output_requests_response(test_URL)
