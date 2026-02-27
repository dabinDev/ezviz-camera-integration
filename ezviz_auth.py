import requests

def get_access_token(app_key: str, app_secret: str) -> str:
    """
    获取萤石开放平台 AccessToken
    """
    url = "https://open.ys7.com/api/lapp/token/get"
    data = {
        "appKey": app_key,
        "appSecret": app_secret
    }
    resp = requests.post(url, data=data)
    result = resp.json()
    if result.get("code") == "200":
        return result["data"]["accessToken"]
    else:
        raise Exception(f"获取AccessToken失败: {result.get('msg')}")
