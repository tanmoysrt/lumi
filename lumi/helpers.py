from urllib import parse

def parseQueryParameter(query:str) -> dict:
    data = {}
    try:
        for record in parse.parse_qsl(query):
            data[record[0]] = record[1]
    except:
        print("[ERROR] failed to decode query string")
        print("Query -> ", query or "")
    return data