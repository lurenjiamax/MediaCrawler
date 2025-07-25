# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。


# -*- coding: utf-8 -*-
import asyncio
import json
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlencode

import httpx
from playwright.async_api import BrowserContext, Page

import config
from base.base_crawler import AbstractApiClient
from tools import utils

from .exception import DataFetchError
from .graphql import KuaiShouGraphQL

import hashlib

SIG_SALT = b'772867c19925'

# QParams: GET参数, PParams (POST用Form形式传的参)
def Sig(QParams: dict, PParams: dict) -> str:
    return hashlib.md5(''.join(sorted(f'{i[0]}={i[1]}' for i in sorted(QParams.items()) + sorted(PParams.items()))).encode() + SIG_SALT).hexdigest()
def __NSTokensig(sig: str, ClientSalt: str) -> str:
    return hashlib.sha256((sig + ClientSalt).encode()).hexdigest()

# url3 = "https://api3.XXapisrv.com/rest/lightks/n/photo/playAuth/v1"
# payload3 = {
#     "photoId": f"{photo_id}",
#     "cs": "false",
#     "client_key": "3c2cd3f3",
#     "os": "android",
# }
# params_str3 = sig_1.sort_params(params2, payload3)
# sig_str3 = sig_1.make_sig(params_str3)
# NS_sig3_str3 = sig_3.make_sig3(f"/rest/lightks/n/photo/playAuth/v1{sig_str3}")
# params2["sig"] = sig_str3
# params2["__NS_sig3"] = NS_sig3_str3

class KuaiShouClient(AbstractApiClient):
    def __init__(
        self,
        timeout=60,
        proxies=None,
        *,
        headers: Dict[str, str],
        playwright_page: Page,
        cookie_dict: Dict[str, str],
    ):
        self.proxies = proxies
        self.timeout = timeout
        self.headers = headers
        self._host = "https://www.kuaishou.com/graphql"
        self.playwright_page = playwright_page
        self.cookie_dict = cookie_dict
        self.graphql = KuaiShouGraphQL()
        
        self.android = {}
        self.android.host = "https://az2-api.ksapisrv.com"
        self.android.headers = {
            'Host': 'az2-api.ksapisrv.com',
            'Connection': 'keep-alive',
            'Content-Length': '911',
            'X-REQUESTID': '175271697644040486',
            'User-Agent': 'kwai-android aegon/4.19.1',
            'Accept-Language': 'zh-cn',
            'Cookie': 'kuaishou.api_st=Cg9rdWFpc2hvdS5hcGkuc3QSoAFBwMbvA6KPjUjUQ0N64CBgDacOY20hJNxu7-OqDE7zsMNMSCOPW3frAqIMQADl32tE_BW1Xx8LEP3YllKj-0dkkZFScgpMfG2bgZWlvKj8VesXe23udFXk9HffrHtHnydTYLG1TIpkbRsZrnsnUlXJh6hMPrsjYK38YKont72PV28t0GVavv7vbNl4ONWoR_ewmqsiCr4iTvsKiUDbvB9tGhLbpnOX2M1IRKpGGeQvLfAmAo8iIJjWJ9zecSeAKAqckbVpyT1iY2Yc0d_R4UAiu50R6nO3KAUwAQ;__NSWJ=;token=eaa6eeb817b84871bab76c251d9478b9-2975878723;region_ticket=RT_FDE0444808ADD191DA8176BFCC443494BA1D71F05A6D25DE7D73CEBC918FB6E82C4629EDA',
            'ct-context': '{biz_name:ATTRIBUTION,error_occurred:false,sampled:true,sampled_on_error:true,segment_id:1524217112,service_name:CLIENT_TRACE,span_id:1,trace_id:My4xMzQzODc4Mzk5NDY5OTMyMzYwNy4yNjIzOS4xNzUyNzE2OTc2NDQxLjI=,upstream_error_occurred:false}',
            'page-code': 'FEATURED_DETAIL',
            'kaw': 'MDHkM+9FrbznSEAqyw6JYmWAbX7zYmh5BdXbI/C82jqqLDb50rL6A5Xty9qd+hVru646FNFGiGShrzCtbesIqNKinqX4K+Xjl4+tB30tCt4Ooik1wJGFgNYAJlsksJfB75Aw00OeB2HMusjZ2OLhjiaEYYRZ81gOUYchZVV+YVhYk0ma+hvQ184ehO+su1ku+8WOyqH5B8Jmt/cTEdlmdS3lTo6O/6Y/AA==',
            'kas': '00478e77e181b38fba5fe51acc1ed68722',
            'X-Ref-Page': 'PROFILE&FEATURED_DETAIL',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept-Encoding': 'gzip, deflate, br',
            'X-Client-Info': 'model=CPH2581;os=Android;nqe-score=54;network=WIFI;signal-strength=4;'
        }
        

    async def request(self, method, url, **kwargs) -> Any:
        async with httpx.AsyncClient(proxies=self.proxies) as client:
            response = await client.request(method, url, timeout=self.timeout, **kwargs)
        data: Dict = response.json()
        if data.get("errors"):
            raise DataFetchError(data.get("errors", "unkonw error"))
        else:
            return data.get("data", {})

    async def get(self, uri: str, params=None) -> Dict:
        final_uri = uri
        if isinstance(params, dict):
            final_uri = f"{uri}?" f"{urlencode(params)}"
        return await self.request(
            method="GET", url=f"{self._host}{final_uri}", headers=self.headers
        )

    async def post(self, uri: str, data: dict) -> Dict:
        json_str = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
        return await self.request(
            method="POST", url=f"{self._host}{uri}", data=json_str, headers=self.headers
        )

    async def pong(self) -> bool:
        """get a note to check if login state is ok"""
        utils.logger.info("[KuaiShouClient.pong] Begin pong kuaishou...")
        ping_flag = False
        try:
            post_data = {
                "operationName": "visionProfileUserList",
                "variables": {
                    "ftype": 1,
                },
                "query": self.graphql.get("vision_profile_user_list"),
            }
            res = await self.post("", post_data)
            if res.get("visionProfileUserList", {}).get("result") == 1:
                ping_flag = True
        except Exception as e:
            utils.logger.error(
                f"[KuaiShouClient.pong] Pong kuaishou failed: {e}, and try to login again..."
            )
            ping_flag = False
        return ping_flag

    async def update_cookies(self, browser_context: BrowserContext):
        cookie_str, cookie_dict = utils.convert_cookies(await browser_context.cookies())
        self.headers["Cookie"] = cookie_str
        self.cookie_dict = cookie_dict

    async def search_info_by_keyword(
        self, keyword: str, pcursor: str, search_session_id: str = ""
    ):
        """
        KuaiShou web search api
        :param keyword: search keyword
        :param pcursor: limite page curson
        :param search_session_id: search session id
        :return:
        """
        post_data = {
            "operationName": "visionSearchPhoto",
            "variables": {
                "keyword": keyword,
                "pcursor": pcursor,
                "page": "search",
                "searchSessionId": search_session_id,
            },
            "query": self.graphql.get("search_query"),
        }
        return await self.post("", post_data)

    async def get_video_info(self, photo_id: str) -> Dict:
        """
        Kuaishou web video detail api
        :param photo_id:
        :return:
        """
        post_data = {
            "operationName": "visionVideoDetail",
            "variables": {"photoId": photo_id, "page": "search"},
            "query": self.graphql.get("video_detail"),
        }
        return await self.post("", post_data)

    async def get_video_comments(self, photo_id: str, pcursor: str = "") -> Dict:
        """get video comments
        :param photo_id: photo id you want to fetch
        :param pcursor: last you get pcursor, defaults to ""
        :return:
        """
        post_data = {
            "operationName": "commentListQuery",
            "variables": {"photoId": photo_id, "pcursor": pcursor},
            "query": self.graphql.get("comment_list"),
        }
        return await self.post("", post_data)

    async def get_video_sub_comments(
        self, photo_id: str, rootCommentId: str, pcursor: str = ""
    ) -> Dict:
        """get video sub comments
        :param photo_id: photo id you want to fetch
        :param pcursor: last you get pcursor, defaults to ""
        :return:
        """
        post_data = {
            "operationName": "visionSubCommentList",
            "variables": {
                "photoId": photo_id,
                "pcursor": pcursor,
                "rootCommentId": rootCommentId,
            },
            "query": self.graphql.get("vision_sub_comment_list"),
        }
        return await self.post("", post_data)

    async def get_creator_profile(self, userId: str) -> Dict:
        post_data = {
            "operationName": "visionProfile",
            "variables": {"userId": userId},
            "query": self.graphql.get("vision_profile"),
        }
        return await self.post("", post_data)

    async def get_video_by_creater(self, userId: str, pcursor: str = "") -> Dict:
        post_data = {
            "operationName": "visionProfilePhotoList",
            "variables": {"page": "profile", "pcursor": pcursor, "userId": userId},
            "query": self.graphql.get("vision_profile_photo_list"),
        }
        return await self.post("", post_data)

    async def get_video_all_comments(
        self,
        photo_id: str,
        crawl_interval: float = 1.0,
        callback: Optional[Callable] = None,
        max_count: int = 10,
    ):
        """
        get video all comments include sub comments
        :param photo_id:
        :param crawl_interval:
        :param callback:
        :param max_count:
        :return:
        """

        result = []
        pcursor = ""

        while pcursor != "no_more" and len(result) < max_count:
            comments_res = await self.get_video_comments(photo_id, pcursor)
            vision_commen_list = comments_res.get("visionCommentList", {})
            pcursor = vision_commen_list.get("pcursor", "")
            comments = vision_commen_list.get("rootComments", [])
            if len(result) + len(comments) > max_count:
                comments = comments[: max_count - len(result)]
            if callback:  # 如果有回调函数，就执行回调函数
                await callback(photo_id, comments)
            result.extend(comments)
            await asyncio.sleep(crawl_interval)
            sub_comments = await self.get_comments_all_sub_comments(
                comments, photo_id, crawl_interval, callback
            )
            result.extend(sub_comments)
        return result

    async def get_comments_all_sub_comments(
        self,
        comments: List[Dict],
        photo_id,
        crawl_interval: float = 1.0,
        callback: Optional[Callable] = None,
    ) -> List[Dict]:
        """
        获取指定一级评论下的所有二级评论, 该方法会一直查找一级评论下的所有二级评论信息
        Args:
            comments: 评论列表
            photo_id: 视频id
            crawl_interval: 爬取一次评论的延迟单位（秒）
            callback: 一次评论爬取结束后
        Returns:

        """
        if not config.ENABLE_GET_SUB_COMMENTS:
            utils.logger.info(
                f"[KuaiShouClient.get_comments_all_sub_comments] Crawling sub_comment mode is not enabled"
            )
            return 

        result = []
        for comment in comments:
            sub_comments = comment.get("subComments")
            if sub_comments and callback:
                await callback(photo_id, sub_comments)

            sub_comment_pcursor = comment.get("subCommentsPcursor")
            if sub_comment_pcursor == "no_more":
                continue

            root_comment_id = comment.get("commentId")
            sub_comment_pcursor = ""

            while sub_comment_pcursor != "no_more":
                comments_res = await self.get_video_sub_comments(
                    photo_id, root_comment_id, sub_comment_pcursor
                )
                vision_sub_comment_list = comments_res.get("visionSubCommentList", {})
                sub_comment_pcursor = vision_sub_comment_list.get("pcursor", "no_more")

                comments = vision_sub_comment_list.get("subComments", {})
                if callback:
                    await callback(photo_id, comments)
                await asyncio.sleep(crawl_interval)
                result.extend(comments)
        return result

    async def get_creator_info(self, user_id: str) -> Dict:
        """
        eg: https://www.kuaishou.com/profile/3xfr2ac7e47dp26
        快手用户主页
        """

        visionProfile = await self.get_creator_profile(user_id)
        visionProfile = visionProfile.get("visionProfile", {})
        return visionProfile.get("userProfile")

    async def get_all_videos_by_creator(
        self,
        user_id: str,
        crawl_interval: float = 1.0,
        callback: Optional[Callable] = None,
    ) -> List[Dict]:
        """
        获取指定用户下的所有发过的帖子，该方法会一直查找一个用户下的所有帖子信息
        Args:
            user_id: 用户ID
            crawl_interval: 爬取一次的延迟单位（秒）
            callback: 一次分页爬取结束后的更新回调函数
        Returns:

        """
        result = []
        pcursor = ""

        while pcursor != "no_more":
            videos_res = await self.get_video_by_creater(user_id, pcursor)
            if not videos_res:
                utils.logger.error(
                    f"[KuaiShouClient.get_all_videos_by_creator] The current creator may have been banned by ks, so they cannot access the data."
                )
                break

            vision_profile_photo_list = videos_res.get("visionProfilePhotoList", {})
            pcursor = vision_profile_photo_list.get("pcursor", "")

            videos = vision_profile_photo_list.get("feeds", [])
            utils.logger.info(
                f"[KuaiShouClient.get_all_videos_by_creator] got user_id:{user_id} videos len : {len(videos)}"
            )

            if callback:
                await callback(videos)
            await asyncio.sleep(crawl_interval)
            result.extend(videos)
        return result
