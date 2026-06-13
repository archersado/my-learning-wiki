from .base_agent import BaseAgent
from langchain_core.messages import HumanMessage, ChatMessage, AIMessage
# Assume LLM is passed in __init__ or accessed globally/via context
import json

class ProfessionalEditor(BaseAgent):
    def __init__(self, llm=None, tools=None):
        super().__init__(llm, tools)
        # self.llm = llm # LLM would be used here

    def process(self, state: dict) -> dict:
        """Drafts a professional article based on organized knowledge."""
        print("Professional Editor is drafting the article.")
        articles = state.get("pick_article")
        type = state.get("publish_type")
        match type:
            case "daily":
                list = []
                for article in articles:
                    list.append({
                        "title": article["title"],
                        "content": article.get("abstract") or article.get("content"),
                        "link": article["link"],
                    })

                summary = self.daily_writer(list)    
                    # article["report"] = content
                    # self.db_client.get_raw_data_collection().update_one(
                    #     {"_id": article["_id"]},  # Query to find matching title
                    #     {"$set": article},  # Update with new article data
                    #     upsert=True  # Insert if no match found
                    # )

        # Placeholder for article drafting logic using LLM
        state["summary"] = summary[0]
        state["summary_structed"] = summary[1]
        return state 
    


    def daily_writer(self, summary):
        def _chunk(arr, size):
            for i in range(0, len(arr), size):
                yield arr[i:i + size]

        def _merge_items(items):
            # 以 (section,title,content,link,linkTitle) 去重
            seen = set()
            merged = []
            for it in items:
                key = (
                    it.get("section", "").strip(),
                    it.get("title", "").strip(),
                    it.get("content", "").strip(),
                    it.get("link", ""),
                    it.get("linkTitle", ""),
                )
                if key not in seen:
                    seen.add(key)
                    merged.append(it)
            return merged

        def _json_to_markdown(items):
            from collections import defaultdict
            groups = defaultdict(list)
            for it in items:
                groups[it.get("section", "其它")].append(it)
            lines = []
            for section, arr in groups.items():
                lines.append(f"## {section}")
                for i in arr:
                    title = (i.get("title") or "").strip()
                    content = (i.get("content") or "").strip()
                    link = i.get("link")
                    link_title = (i.get("linkTitle") or "来源").strip()
                    bullet = f"- 【{title}】" if title else "-"
                    if content:
                        bullet += f" {content}"
                    if link:
                        bullet += f" [{link_title}]({link})"
                    lines.append(bullet)
                lines.append("")
            return "\n".join(lines).strip()

        prompt = """
        你是一名资深行业每日资讯编辑，擅长将聚合的原始资讯信息转化为逻辑清晰、观点专业的每日聚合咨询。

        要求
        1. 内容翻译
        若原始内容为英文，需要翻译成中文，并且用词要专业、精确
        2. ​​内容重组与优化​​
        需按 「行业头条」「政策速览」「企业动态」「技术前沿」板块重组，将合适的内容重组排列到对应的板块下
        每个板块的内容要求：
        行业头条：聚焦当日最重磅新闻，需包含事件核心、影响范围；
        政策速览：提炼政策要点、落地时间及对行业的直接影响；
        企业动态：企业合作、融资、新产品发布等，需注明企业名称及具体动作；
        技术前沿：包含最新的开源或行业技术资讯、技术产品发布新闻、技术产品头条新闻等
        3. 语言调性轻快简洁但需包含专业深度
        4. 需要从原始咨询内容中获取信息来源，用链接标注
        5. 资讯标题要用 markdown 标题标识，每条资讯控制在 50-80 字， 用「・」符号罗列， 可添加【关键词】标注核心信息（如「政策落地」「跨界合作」）；     
        6. 以如下 json 格式返回 , 直接返回 json 不要用 ```json 包裹
        [{
            "section": "行业头条",
            "title": "标题",
            "content": "内容",
            "link": "链接",
            "linkTitle": "链接标题",
        }]
        """

        # 如果 summary 是列表且长度超过 20，拆分批次调用并合并
        if isinstance(summary, list) and len(summary) > 20:
            all_items = []
            for batch in _chunk(summary, 20):
                input = f"""
                    原始资讯内容为:
                    {json.dumps(batch, ensure_ascii=False)}
                """
                messages = [AIMessage(content=prompt), HumanMessage(content=input)]
                response = self.llm.invoke(messages)
                try:
                    items = json.loads(response.content.strip())
                    if isinstance(items, list):
                        all_items.extend(items)
                except Exception:
                    # 如果模型偶发返回 markdown 文本，跳过该批
                    continue
            merged = _merge_items(all_items)
            return [_json_to_markdown(merged), merged]

        # 否则走单次调用
        input = f"""
            原始资讯内容为:
            {json.dumps(summary, ensure_ascii=False) if not isinstance(summary, str) else summary}
        """
        messages = [AIMessage(content=prompt), HumanMessage(content=input)]
        response = self.llm.invoke(messages)
        try:
            result = json.loads(response.content.strip())
            return [ _json_to_markdown(result if isinstance(result, list) else []), result ]
        except Exception:
            return response.content.strip()
    
    # def rewrite(self, article):

    #     input = f"""
    #         原始资讯为:
    #         {article}
    #     """

    #     messages = [AIMessage(content=prompt), HumanMessage(content=input)]

    #     # Use the LLM to extract content
    #     response = self.llm.invoke(messages)
    #     return response.content.strip()