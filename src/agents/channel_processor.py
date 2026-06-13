from .base_agent import BaseAgent
# Assume tools are passed in __init__ or accessed globally/via context
from ..tools.formatter import Formatter
from datetime import datetime
from langchain_core.messages import HumanMessage, ChatMessage, AIMessage

class ChannelContentProcessor(BaseAgent):
    def __init__(self, llm=None, tools=None):
        super().__init__(llm, tools)
        self.formatter = Formatter() # Assuming Formatter is available

    def process(self, state: dict) -> dict:
        """Formats content for different distribution channels."""
        print("Channel Content Processor is formatting content.")
        # reviewed_article = state.get("reviewed_article")
        # if not reviewed_article:
        #     print("No reviewed article found to format.")
        #     return state
        type = state["publish_type"]
        formatted_content = ""
        match type:
            case "daily":
                formatted_content = self.daily_markdown(state["summary"])

        # # Placeholder for formatting for different channels
        # formatted_content = {
        #     "wechat": self.formatter.format_content(reviewed_article, "WeChat"),
        #     "weibo": self.formatter.format_content(reviewed_article, "Weibo"),
        #     # Add other channels as needed
        # }

        state["formatted_content"] = formatted_content
        return state 
    
    def daily_markdown(self, content):
        prompt = f"""
        你是一个 markdown 日报校准器，将原始 markdown 文章按要求格式修改。

        要求:
        1. 生产的 markdown 格式内容必须合法
        2. 按如下格式添加文章标题，标题为今日 AI 资讯，publishedAt 为当前日期，一句话总结今日资讯要闻作为 summary， tag 为 Journal
        ---
        title: "Can I Do It?"
        publishedAt: "2024-03-05"
        summary: "As design engineers, we're often defined by the 1% of our work that makes it into the final product."
        tag: "Journal"
        ---
        ### 具体的markdown 内容 
        xxxxx
        3. 直接返回 markdown 格式，不要用 ```markdown 包裹

        """
        input = f"""
            原始资讯为:
            {content}
            当前日期是: { datetime.now().strftime('%Y-%m-%d') }
        """
        messages = [AIMessage(content=prompt), HumanMessage(content=input)]

        # Use the LLM to extract content
        response = self.llm.invoke(messages)
        return response.content.strip()        

    def write_html(self, content): 
        prompt = f"""
        你是一名资深设计师与前端开发工程师，擅长将原始文章内容转化为结构清晰、视觉友好的 HTML 海报页面。

        要求:
        1. 保证返回的 html 正确有效
        2. 使用TailwindCSS 3.3+（CDN引入）  
        3. 使用 echarts（CDN引入）表格与图表来生成文章中可能涉及到的图标
        4. 移动端优先响应式设计（断点：768px/1024px）       
        5. 请直接返回 html 内容，不要包裹 markdown ```html``` 语法块              
        6. 满足以下视觉要求
        - 主色调：使用黑灰白来构建深黑背景增强科技感
        - 结构: 结构清晰，增强用户可读性
        
        ### 整体风格
            - **主题色调**：以深色系为主，海报主题为每日 AI 发现
            - **视觉风格**：体现未来科技感，整体美观大方
            - **排版规范**：
            - 无衬线字体（推荐Inter或Roboto）
            - 标题与正文采用明确的层级对比
            - 关键数据使用荧光色高亮

            ### 内容结构
            **头部区域**：
            - 短报标题（加粗发光效果）
            - 日期与来源信息（半透明悬浮样式）
            - 主题标签（霓虹色圆角标签）

            **正文区域**：
            - 新闻导语（首行缩进+发光下划线）
            - 内容分块（使用卡片式布局，带渐变边框）
            - 数据可视化模块（包含：
                - 动态数字滚动效果
                - echarts 图标
                - 科技图标装饰）

            **辅助元素**：
            - 角落装饰（如二进制代码、电路符号）
            - 悬浮动态光点（随鼠标移动）
            - 底部版权信息（荧光字体+渐变背景）

            ### 交互效果
            - 鼠标悬停时卡片产生上浮与阴影加深效果
            - 标题文字带有呼吸灯闪烁动画
            - 数据模块数字支持自动刷新动态
            - 背景粒子随滚动条位置变化分布

            ### 技术要求
            - 使用HTML5与CSS3标准语法
            - 引入Tailwind CSS
            - 集成Font Awesome图标库
            - 包含必要的JavaScript实现动画效果
            - 确保代码结构清晰，添加关键注释 
    
 
        """
        input = f"""
            原始资讯为:
            {content}
        """

        messages = [AIMessage(content=prompt), HumanMessage(content=input)]

        # Use the LLM to extract content
        response = self.llm.invoke(messages)
        return response.content.strip()