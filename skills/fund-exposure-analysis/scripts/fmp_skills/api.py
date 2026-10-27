import os,re,json,urllib.request,urllib.parse

def fetch(endpoint,params):
    if not re.fullmatch(r"[a-zA-Z0-9/_-]+",endpoint): raise ValueError("Invalid FMP stable endpoint.")
    key=os.environ.get("FMP_API_KEY")
    if not key: raise ValueError("FMP_API_KEY is absent. Use the connected FMP tool and snapshot-input route, or set your own key.")
    query=urllib.parse.urlencode({**params,"apikey":key})
    request=urllib.request.Request("https://financialmodelingprep.com/stable/"+endpoint+"?"+query,
                                  headers={"User-Agent":"WilliamSharesFMPResearch/0.1"})
    try:
        with urllib.request.urlopen(request,timeout=45) as response: data=json.load(response)
        if isinstance(data,dict) and any(k in data for k in ['Error Message','error','errorMessage']):raise ValueError('Provider returned an error envelope.')
        return data
    except Exception as e:
        # Never include credential-bearing request URLs or exception strings.
        raise RuntimeError(f"FMP request failed ({type(e).__name__}); no provider substitution or automatic retry.") from None
