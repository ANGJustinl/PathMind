"""
学习路径页面组件
提供可展开的学习线路图及视频学习资源
"""
import gradio as gr
import logging
import asyncio
import json
import traceback
from urllib.parse import quote

# 设置日志
logger = logging.getLogger(__name__)

def create_learning_path_tab(api_service, user_id):
    """创建学习路径标签页"""
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 学习路径规划")
            gr.Markdown("探索个性化学习路径，按您的节奏学习新知识。")
            
            # 学习路径选择
            with gr.Group():
                gr.Markdown("#### 选择学习路径")
                subject_area = gr.Dropdown(
                    label="主题领域",
                    choices=["编程与开发", "数据科学", "人工智能", "Web开发", "移动应用开发", "网络安全"],
                    value="编程与开发"
                )
                specific_path = gr.Dropdown(
                    label="具体路径",
                    choices=[]  # 将根据主题领域动态加载
                )
                goal_level = gr.Radio(
                    label="目标水平",
                    choices=["初学者", "中级", "高级", "专家"],
                    value="中级"
                )
                generate_path_btn = gr.Button("生成学习路径", variant="primary")
            
            # 当前节点信息
            with gr.Group(visible=False) as current_node_group:
                gr.Markdown("#### 当前学习节点")
                node_title = gr.Markdown("### 未选择节点")
                node_description = gr.Markdown("请从右侧学习路径图中选择一个节点开始学习。")
                node_resources = gr.Markdown("**推荐资源：**\n暂无资源")
                search_videos_btn = gr.Button("搜索相关视频", variant="secondary")

        # 学习路径展示和视频区域
        with gr.Column(scale=2):
            # 学习路径图区域
            path_container = gr.HTML("""
            <div style="padding: 20px; border: 1px solid #ddd; border-radius: 5px; background-color: #f9f9f9; height: 400px; overflow: auto;">
                <p style="text-align: center; margin-top: 150px; color: #666;">
                    点击"生成学习路径"按钮查看您的个性化学习计划
                </p>
            </div>
            """)
            
            # 视频区域
            video_title = gr.Markdown("### 学习视频资源", visible=False)
            with gr.Row(visible=False) as video_container:
                with gr.Column(scale=1):
                    video_list = gr.HTML("加载视频列表中...")
                    # 学习状态和时间显示
                    with gr.Group():
                        study_status = gr.HTML("""
                        <div class="study-status" style="margin-top: 15px; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                            <p style="margin: 0; font-size: 14px;">学习状态: <span id="study-state">未开始</span></p>
                            <p style="margin: 5px 0 0; font-size: 14px;">本次学习时长: <span id="current-duration">0</span>分钟</p>
                            <p style="margin: 5px 0 0; font-size: 14px;">累计学习时长: <span id="total-duration">0</span>小时</p>
                        </div>
                        """)
                        study_control = gr.Button("开始学习", variant="primary")

                with gr.Column(scale=2):
                    video_embed = gr.HTML("""
                    <div style="padding: 20px; border: 1px solid #ddd; border-radius: 5px; background-color: #f9f9f9; height: 315px; display: flex; align-items: center; justify-content: center;">
                        <p style="text-align: center; color: #666;">
                            从左侧选择视频进行观看
                        </p>
                    </div>
                    <script>
                    let studyStartTime = null;
                    let currentContentId = null;
                    let studyTimer = null;
                    
                    function updateStudyDuration() {
                        if (studyStartTime) {
                            const duration = Math.floor((Date.now() - studyStartTime) / 60000); // 转换为分钟
                            document.getElementById('current-duration').textContent = duration;
                        }
                    }
                    
                    function startStudy() {
                        studyStartTime = Date.now();
                        document.getElementById('study-state').textContent = '学习中';
                        document.getElementById('study-control').textContent = '结束学习';
                        studyTimer = setInterval(updateStudyDuration, 60000); // 每分钟更新一次
                    }
                    
                    function endStudy() {
                        if (studyStartTime) {
                            const endTime = Date.now();
                            const duration = Math.floor((endTime - studyStartTime) / 60000);
                            
                            // 将学习记录发送到后端
                            if (currentContentId) {
                                fetch('/api/v1/learning-paths/' + pathId + '/progress', {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json' },
                                    body: JSON.stringify({
                                        user_id: userId,
                                        content_id: currentContentId,
                                        study_time: duration,
                                        session_start: new Date(studyStartTime).toISOString(),
                                        session_end: new Date(endTime).toISOString()
                                    })
                                });
                            }
                            
                            clearInterval(studyTimer);
                            studyStartTime = null;
                            document.getElementById('study-state').textContent = '已暂停';
                            document.getElementById('study-control').textContent = '开始学习';
                        }
                    }
                    
                    window.addEventListener('beforeunload', endStudy);
                    </script>
                    """)

    # 根据所选主题领域更新具体路径选项
    def update_specific_paths(subject):
        """更新具体路径下拉菜单选项，并确保有默认选项"""
        paths_mapping = {
            "编程与开发": ["Python从入门到精通", "Java核心技术学习路径", "C/C++系统编程", "Go语言开发路径"],
            "数据科学": ["数据分析师成长路径", "数据可视化专家", "大数据工程师", "商业智能分析"],
            "人工智能": ["机器学习基础到实战", "深度学习算法工程师", "NLP研发工程师", "计算机视觉专家"],
            "Web开发": ["全栈Web开发", "前端开发进阶", "后端架构师", "响应式网站设计"],
            "移动应用开发": ["Android应用开发", "iOS开发者路径", "Flutter跨平台开发", "React Native学习路径"],
            "网络安全": ["网络安全基础", "渗透测试工程师", "安全架构师", "密码学与加密技术"]
        }
        # 确保始终有默认选项
        choices = paths_mapping.get(subject, [])
        default = choices[0] if choices else subject  # 如果没有选项，就使用主题本身作为默认值
        # 修复这里：使用 gr.update() 而不是 gr.Dropdown.update()
        return gr.update(choices=choices, value=default)

    # 生成学习路径
    def generate_learning_path(subject, path, level):
        try:
            logger.info(f"生成学习路径: 主题={subject}, 路径={path}, 级别={level}")
            
            # 确保path_name不为空，避免API请求错误
            if not path or path is None:
                path = subject   # 如果路径为空，使用主题作为路径
                logger.warning(f"路径名为空，使用主题作为替代: {path}")
            
            # 构建API请求参数
            path_request = {
                "user_id": user_id,
                "subject_area": subject,
                "path_name": path,
                "target_level": level
            }
            
            # 尝试调用后端API获取学习路径数据
            try:
                loop = asyncio.new_event_loop()
                path_data = loop.run_until_complete(
                    api_service.request("GET", "learning/path", params=path_request)
                )
                loop.close()
                logger.info(f"API返回学习路径数据: {json.dumps(path_data, ensure_ascii=False)[:200]}...")
            except Exception as e:
                logger.warning(f"调用学习路径API失败: {str(e)}，使用模拟数据")
                # 如果API调用失败，使用模拟数据
                path_data = generate_mock_learning_path(subject, path, level)
            
            # 验证路径数据
            if not path_data or "nodes" not in path_data or not path_data["nodes"]:
                raise ValueError("无法获取有效的学习路径数据")
            
            # 生成路径可视化HTML
            path_html = generate_path_visualization(path_data)
            
            # 获取第一个节点信息用于显示
            first_node = path_data["nodes"][0]
            node_info = {
                "title": first_node["title"],
                "description": first_node["description"],
                "resources": first_node.get("resources", [])
            }
            
            # 准备资源显示文本
            resources_md = "**推荐资源：**\n"
            if node_info["resources"]:
                for i, res in enumerate(node_info["resources"], 1):
                    resources_md += f"{i}. [{res['title']}]({res['url']}) - {res['type']}\n"
            else:
                resources_md += '暂无推荐资源，请点击"搜索相关视频"按钮查找学习视频。'
            
            # 修复这里：使用value而不是innerHTML
            return (
                gr.update(value=path_html),
                gr.update(visible=True),
                f"### {node_info['title']}",
                node_info["description"],
                resources_md
            )
            
        except Exception as e:
            logger.error(f"生成学习路径失败: {str(e)}")
            logger.error(traceback.format_exc())
            error_html = f"""
            <div style="padding: 20px; border: 1px solid #dc3545; border-radius: 5px; background-color: #f8d7da;">
                <h4 style="color: #721c24;">生成学习路径时发生错误</h4>
                <p>错误信息: {str(e)}</p>
                <p>请尝试选择不同的主题或刷新页面后重试。</p>
            </div>
            """
            # 修复这里：使用value而不是innerHTML
            return (
                gr.update(value=error_html),
                gr.update(visible=False),
                "### 发生错误",
                "生成学习路径时发生错误，请重试。",
                "**推荐资源：**\n暂无资源"
            )

    # 搜索相关视频
    def search_videos(node_title):
        try:
            logger.info(f"搜索相关视频: 节点标题={node_title}")
            
            # 移除标题中的 "### " 前缀
            if node_title.startswith("### "):
                node_title = node_title[4:]
            
            # 构建搜索请求
            search_request = {
                "query": node_title,
                "max_results": 5,
                "type": "video"
            }
            
            # 尝试调用后端API搜索视频
            try:
                loop = asyncio.new_event_loop()
                video_results = loop.run_until_complete(
                    api_service.request("GET", "learning/search-videos", params=search_request)
                )
                loop.close()
                logger.info(f"API返回视频搜索结果: {json.dumps(video_results, ensure_ascii=False)[:200]}...")
            except Exception as e:
                logger.warning(f"调用视频搜索API失败: {str(e)}，使用模拟数据")
                # 如果API调用失败，使用模拟数据
                video_results = generate_mock_video_results(node_title)
            
            # 验证视频数据
            if not video_results or "videos" not in video_results or not video_results["videos"]:
                raise ValueError("未找到相关视频")
            
            # 生成视频列表HTML
            videos = video_results["videos"]
            video_list_html = """<div style="height: 315px; overflow-y: auto; padding-right: 10px;">"""
            
            for i, video in enumerate(videos):
                video_id = video.get("video_id", "")
                thumbnail = video.get("thumbnail", "https://via.placeholder.com/120x67")
                title = video.get("title", "无标题视频")
                channel = video.get("channel", "未知频道")
                
                video_list_html += f"""
                <div class="video-item" style="margin-bottom: 15px; cursor: pointer; padding: 8px; border: 1px solid #ddd; border-radius: 4px; display: flex;" 
                    onclick="selectVideo('{video_id}', this)" id="video-{video_id}">
                    <img src="{thumbnail}" style="width: 120px; height: 67px; object-fit: cover; margin-right: 10px;">
                    <div>
                        <p style="margin: 0; font-weight: bold; font-size: 14px;">{title}</p>
                        <p style="margin: 5px 0 0; font-size: 12px; color: #666;">{channel}</p>
                    </div>
                </div>
                """
            
            video_list_html += """</div>
            <script>
            function selectVideo(videoId, element) {
                // 移除所有选中状态
                document.querySelectorAll('.video-item').forEach(item => {
                    item.style.backgroundColor = '';
                    item.style.borderColor = '#ddd';
                });
                
                // 设置当前选中项样式
                element.style.backgroundColor = '#f0f7ff';
                element.style.borderColor = '#007bff';
                
                // 更新嵌入视频
                const embedContainer = document.getElementById('video-embed-container');
                if (embedContainer) {
                    embedContainer.innerHTML = `<iframe width="100%" height="315" src="https://www.youtube.com/embed/${videoId}" 
                        title="YouTube video player" frameborder="0" 
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                        allowfullscreen></iframe>`;
                }
            }
            
            // 自动选择第一个视频
            window.addEventListener('DOMContentLoaded', (event) => {
                setTimeout(() => {
                    const firstVideo = document.querySelector('.video-item');
                    if (firstVideo) {
                        firstVideo.click();
                    }
                }, 100);
            });
            </script>
            """
            
            # 生成视频嵌入容器HTML
            embed_html = """
            <div id="video-embed-container" style="width: 100%; height: 315px; display: flex; align-items: center; justify-content: center;">
                <p style="text-align: center; color: #666;">从左侧选择视频进行观看</p>
            </div>
            """
            
            # 修复这里：使用value代替innerHTML
            return (
                gr.update(visible=True),
                gr.update(visible=True),
                gr.update(value=video_list_html),
                gr.update(value=embed_html)
            )
            
        except Exception as e:
            logger.error(f"搜索视频失败: {str(e)}")
            logger.error(traceback.format_exc())
            error_html = f"""
            <div style="padding: 15px; border: 1px solid #dc3545; border-radius: 5px; background-color: #f8d7da;">
                <p style="color: #721c24; margin: 0;">搜索视频时发生错误: {str(e)}</p>
                <p style="margin: 5px 0 0;">请尝试使用不同的关键词或稍后重试。</p>
            </div>
            """
            # 修复这里：使用value代替innerHTML
            return (
                gr.update(visible=True),
                gr.update(visible=True),
                gr.update(value=error_html),
                gr.update(value="<p style='text-align: center; color: #666;'>无法加载视频</p>")
            )

    # 生成学习路径可视化HTML
    def generate_path_visualization(path_data):
        """生成可视化的学习路径HTML"""
        nodes = path_data.get("nodes", [])
        connections = path_data.get("connections", [])
        
        html = """
        <div class="learning-path-container" style="padding: 20px; border: 1px solid #ddd; border-radius: 5px; background-color: #f9f9f9; height: 400px; overflow: auto;">
            <h4 style="text-align: center; margin-top: 0; margin-bottom: 20px;">学习路径图</h4>
            <div class="path-visualization">
        """
        
        # 添加节点
        for node in nodes:
            node_id = node.get("id", "")
            node_title = node.get("title", "无标题节点")
            node_type = node.get("type", "topic")
            node_status = node.get("status", "未开始")
            
            # 根据节点类型和状态设置不同的样式
            bg_color = "#ffffff"
            border_color = "#ddd"
            icon = "📚"
            
            if node_type == "milestone":
                icon = "🏆"
                border_color = "#ffc107"
            elif node_type == "project":
                icon = "🛠️"
                border_color = "#17a2b8"
            
            if node_status == "已完成":
                bg_color = "#d4edda"
                border_color = "#28a745"
            elif node_status == "进行中":
                bg_color = "#fff3cd"
                border_color = "#ffc107"
            
            # 创建节点HTML
            html += f"""
            <div class="path-node" id="node-{node_id}" 
                style="margin-bottom: 15px; padding: 12px; border: 2px solid {border_color}; border-radius: 5px; background-color: {bg_color}; cursor: pointer;"
                onclick="selectPathNode('{node_id}', '{node_title}', '{node.get('description', '')}', {json.dumps(node.get('resources', []))})">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 24px; margin-right: 10px;">{icon}</span>
                    <div>
                        <h5 style="margin: 0; font-size: 16px;">{node_title}</h5>
                        <p style="margin: 5px 0 0; color: #666; font-size: 12px;">
                            {node.get('level', '基础')} · {node_status}
                        </p>
                    </div>
                </div>
                <div class="node-content" style="margin-top: 10px; display: none;">
                    <p>{node.get('description', '无描述')}</p>
                    <button class="expand-btn" onclick="event.stopPropagation(); toggleNodeContent(this, '{node_id}')" 
                        style="background: none; border: none; color: #007bff; cursor: pointer; font-size: 12px; padding: 0;">
                        显示更多
                    </button>
                </div>
            </div>
            """
            
            # 如果有连接，添加连接线
            if connections:
                for conn in connections:
                    if conn.get("source") == node_id:
                        html += f"""
                        <div style="text-align: center; margin: 10px 0;">
                            <span style="display: inline-block; width: 20px; height: 20px;">↓</span>
                        </div>
                        """
                        break
        
        # 添加JavaScript逻辑
        html += """
        </div>
        <script>
            function toggleNodeContent(btn, nodeId) {
                const content = btn.closest('.node-content');
                const isHidden = content.style.display === 'none';
                
                content.style.display = isHidden ? 'block' : 'none';
                btn.innerText = isHidden ? '收起' : '显示更多';
            }
            
            function selectPathNode(nodeId, title, description, resources) {
                // 更新当前节点信息
                const titleElement = document.querySelector('[data-testid="markdown"][data-node-title="true"]');
                const descriptionElement = document.querySelector('[data-testid="markdown"][data-node-description="true"]');
                const resourcesElement = document.querySelector('[data-testid="markdown"][data-node-resources="true"]');
                
                if (titleElement) titleElement.innerHTML = `<h3>${title}</h3>`;
                if (descriptionElement) descriptionElement.innerHTML = `<p>${description}</p>`;
                
                // 生成资源列表
                let resourcesHTML = '<p><strong>推荐资源：</strong></p>';
                if (resources && resources.length > 0) {
                    resourcesHTML += '<ul>';
                    resources.forEach((res, index) => {
                        resourcesHTML += `<li><a href="${res.url}" target="_blank">${res.title}</a> - ${res.type}</li>`;
                    });
                    resourcesHTML += '</ul>';
                } else {
                    resourcesHTML += '<p>暂无推荐资源，请点击"搜索相关视频"按钮查找学习视频。</p>';
                }
                
                if (resourcesElement) resourcesElement.innerHTML = resourcesHTML;
                
                // 高亮选中节点，取消其他节点高亮
                document.querySelectorAll('.path-node').forEach(node => {
                    node.style.boxShadow = '';
                });
                document.getElementById(`node-${nodeId}`).style.boxShadow = '0 0 0 3px rgba(0, 123, 255, 0.5)';
            }
            
            // 添加数据属性以便JavaScript能找到元素
            document.addEventListener('DOMContentLoaded', () => {
                setTimeout(() => {
                    const markdownElements = document.querySelectorAll('[data-testid="markdown"]');
                    const titleElement = markdownElements[4]; // 根据位置找到标题元素
                    const descriptionElement = markdownElements[5]; // 根据位置找到描述元素
                    const resourcesElement = markdownElements[6]; // 根据位置找到资源元素
                    
                    if (titleElement) titleElement.setAttribute('data-node-title', 'true');
                    if (descriptionElement) descriptionElement.setAttribute('data-node-description', 'true');
                    if (resourcesElement) resourcesElement.setAttribute('data-node-resources', 'true');
                    
                    // 默认选中第一个节点
                    const firstNode = document.querySelector('.path-node');
                    if (firstNode) firstNode.click();
                }, 500);
            });
        </script>
        </div>
        """
        
        return html

    # 生成模拟学习路径数据
    def generate_mock_learning_path(subject, path, level):
        """生成模拟学习路径数据"""
        logger.info(f"生成模拟学习路径数据: {subject} - {path} - {level}")
        
        # 根据主题和路径名称生成不同的模拟数据
        if "Python" in path:
            return {
                "path_id": "python-beginner-to-advanced",
                "title": "Python从入门到精通",
                "description": "全面学习Python编程，从基础语法到高级应用",
                "estimated_duration": "3-6个月",
                "nodes": [
                    {
                        "id": "python-basics",
                        "title": "Python基础语法",
                        "description": "学习Python的基本语法、数据类型、变量、条件语句和循环。掌握Python编程的基础知识，为后续更深入的学习打下基础。",
                        "type": "topic",
                        "level": "初级",
                        "status": "未开始",
                        "resources": [
                            {
                                "title": "Python官方教程",
                                "url": "https://docs.python.org/zh-cn/3/tutorial/",
                                "type": "文档"
                            },
                            {
                                "title": "Python编程：从入门到实践",
                                "url": "https://book-link-placeholder.com/python-crash-course",
                                "type": "书籍"
                            }
                        ]
                    },
                    {
                        "id": "python-data-structures",
                        "title": "Python数据结构",
                        "description": "学习Python的列表、元组、字典和集合等数据结构，以及它们的使用方法和适用场景。",
                        "type": "topic",
                        "level": "初级",
                        "status": "未开始",
                        "resources": [
                            {
                                "title": "Python数据结构与算法",
                                "url": "https://realpython.com/python-data-structures/",
                                "type": "教程"
                            }
                        ]
                    },
                    {
                        "id": "python-functions",
                        "title": "Python函数与模块",
                        "description": "学习如何定义和使用函数，创建和导入模块，理解函数参数和返回值。",
                        "type": "topic",
                        "level": "初级",
                        "status": "未开始"
                    },
                    {
                        "id": "python-first-project",
                        "title": "第一个Python项目",
                        "description": "创建一个简单的命令行工具，应用所学的Python基础知识，如数据类型、控制流和函数。",
                        "type": "project",
                        "level": "初级",
                        "status": "未开始"
                    },
                    {
                        "id": "python-oop",
                        "title": "Python面向对象编程",
                        "description": "学习类、对象、继承、多态和封装等面向对象编程概念，理解如何在Python中应用这些概念。",
                        "type": "topic",
                        "level": "中级",
                        "status": "未开始"
                    },
                    {
                        "id": "python-exceptions",
                        "title": "Python异常处理",
                        "description": "学习如何捕获和处理Python中的异常，编写健壮的错误处理代码。",
                        "type": "topic",
                        "level": "中级",
                        "status": "未开始"
                    },
                    {
                        "id": "python-file-io",
                        "title": "Python文件操作与I/O",
                        "description": "学习如何在Python中读写文件，处理不同类型的文件格式，如文本文件、CSV、JSON等。",
                        "type": "topic",
                        "level": "中级",
                        "status": "未开始"
                    },
                    {
                        "id": "python-intermediate-milestone",
                        "title": "Python中级里程碑",
                        "description": "完成一个综合性项目，应用所学的面向对象编程、异常处理和文件操作知识。",
                        "type": "milestone",
                        "level": "中级",
                        "status": "未开始"
                    },
                    {
                        "id": "python-advanced-topics",
                        "title": "Python高级特性",
                        "description": "学习装饰器、生成器、迭代器、上下文管理器等Python高级特性。",
                        "type": "topic",
                        "level": "高级",
                        "status": "未开始"
                    }
                ],
                "connections": [
                    {"source": "python-basics", "target": "python-data-structures"},
                    {"source": "python-data-structures", "target": "python-functions"},
                    {"source": "python-functions", "target": "python-first-project"},
                    {"source": "python-first-project", "target": "python-oop"},
                    {"source": "python-oop", "target": "python-exceptions"},
                    {"source": "python-exceptions", "target": "python-file-io"},
                    {"source": "python-file-io", "target": "python-intermediate-milestone"},
                    {"source": "python-intermediate-milestone", "target": "python-advanced-topics"}
                ]
            }
        elif "数据科学" in path or "data" in path.lower():
            return {
                "path_id": "data-analysis-path",
                "title": "数据分析师成长路径",
                "description": "从零开始成为一名专业数据分析师",
                "estimated_duration": "4-8个月",
                "nodes": [
                    {
                        "id": "data-basics",
                        "title": "数据分析基础",
                        "description": "了解数据分析的基本概念、数据类型和分析流程。学习如何提出正确的问题，并通过数据寻找答案。",
                        "type": "topic",
                        "level": "初级",
                        "status": "未开始"
                    },
                    {
                        "id": "excel-analytics",
                        "title": "Excel数据分析",
                        "description": "学习使用Excel进行数据整理、分析和可视化，掌握常用函数、数据透视表和图表制作。",
                        "type": "topic",
                        "level": "初级",
                        "status": "未开始"
                    },
                    {
                        "id": "sql-fundamentals",
                        "title": "SQL基础",
                        "description": "学习SQL语言基础，包括查询、过滤、排序和聚合数据，以及多表连接和子查询。",
                        "type": "topic",
                        "level": "初级",
                        "status": "未开始"
                    },
                    {
                        "id": "python-for-data",
                        "title": "Python数据分析",
                        "description": "学习使用Python进行数据分析，包括NumPy、Pandas库的基本用法。",
                        "type": "topic",
                        "level": "中级",
                        "status": "未开始"
                    },
                    {
                        "id": "data-visualization",
                        "title": "数据可视化",
                        "description": "学习使用Matplotlib、Seaborn等工具创建有效的数据可视化，理解各种图表类型的适用场景。",
                        "type": "topic",
                        "level": "中级",
                        "status": "未开始"
                    }
                ],
                "connections": [
                    {"source": "data-basics", "target": "excel-analytics"},
                    {"source": "excel-analytics", "target": "sql-fundamentals"},
                    {"source": "sql-fundamentals", "target": "python-for-data"},
                    {"source": "python-for-data", "target": "data-visualization"}
                ]
            }
        else:
            # 默认学习路径
            return {
                "path_id": "default-learning-path",
                "title": path,
                "description": f"{subject}领域的学习路径",
                "estimated_duration": "3-6个月",
                "nodes": [
                    {
                        "id": "basics",
                        "title": "基础知识",
                        "description": f"{path}的基础知识与核心概念。",
                        "type": "topic",
                        "level": "初级",
                        "status": "未开始"
                    },
                    {
                        "id": "intermediate",
                        "title": "进阶内容",
                        "description": f"{path}的进阶知识与技能。",
                        "type": "topic",
                        "level": "中级",
                        "status": "未开始"
                    },
                    {
                        "id": "project",
                        "title": "实践项目",
                        "description": "通过动手项目巩固所学知识。",
                        "type": "project",
                        "level": "中级",
                        "status": "未开始"
                    },
                    {
                        "id": "advanced",
                        "title": "高级内容",
                        "description": "深入学习高级技术与概念。",
                        "type": "topic",
                        "level": "高级",
                        "status": "未开始"
                    }
                ],
                "connections": [
                    {"source": "basics", "target": "intermediate"},
                    {"source": "intermediate", "target": "project"},
                    {"source": "project", "target": "advanced"}
                ]
            }

    # 生成模拟视频搜索结果
    def generate_mock_video_results(query):
        """生成模拟视频搜索结果"""
        logger.info(f"生成模拟视频搜索结果: 查询={query}")
        
        # 将查询词编码为URL安全格式
        query_encoded = quote(query)
        
        # 根据不同查询返回相关的模拟视频数据
        if "python" in query.lower() or "编程" in query:
            return {
                "videos": [
                    {
                        "video_id": "rfscVS0vtbw",
                        "title": "Python教程 - 初学者全套课程",
                        "channel": "freeCodeCamp.org",
                        "thumbnail": "https://i.ytimg.com/vi/rfscVS0vtbw/mqdefault.jpg"
                    },
                    {
                        "video_id": "_uQrJ0TkZlc",
                        "title": "Python Tutorial - Python for Beginners [2023]",
                        "channel": "Programming with Mosh",
                        "thumbnail": "https://i.ytimg.com/vi/_uQrJ0TkZlc/mqdefault.jpg"
                    },
                    {
                        "video_id": "kqtD5dpn9C8",
                        "title": "Python速成课程 - 30分钟学会Python基础",
                        "channel": "Python入门",
                        "thumbnail": "https://i.ytimg.com/vi/kqtD5dpn9C8/mqdefault.jpg"
                    }
                ]
            }
        elif "数据" in query or "data" in query.lower():
            return {
                "videos": [
                    {
                        "video_id": "r-uOLxNrNk8",
                        "title": "数据分析全套教程 - 从零开始学数据分析",
                        "channel": "数据分析师训练营",
                        "thumbnail": "https://i.ytimg.com/vi/r-uOLxNrNk8/mqdefault.jpg"
                    },
                    {
                        "video_id": "GPVsHOlRBBI",
                        "title": "Python数据分析库Pandas入门教程",
                        "channel": "Python数据科学",
                        "thumbnail": "https://i.ytimg.com/vi/GPVsHOlRBBI/mqdefault.jpg"
                    }
                ]
            }
        else:
            # 通用视频结果
            return {
                "videos": [
                    {
                        "video_id": "dQw4w9WgXcQ",  # 这是一个著名的视频ID :)
                        "title": f"{query} - 视频教程",
                        "channel": "学习频道",
                        "thumbnail": "https://via.placeholder.com/120x67"
                    },
                    {
                        "video_id": "C0DPdy98e4c",
                        "title": f"{query} 从入门到精通",
                        "channel": "教育课堂",
                        "thumbnail": "https://via.placeholder.com/120x67"
                    }
                ]
            }

    # 处理学习控制按钮事件
    def toggle_study_session():
        """切换学习会话状态"""
        js = """
        async () => {
            let button = document.getElementById('study-control');
            let state = document.getElementById('study-state');
            if (button.textContent === '开始学习') {
                startStudy();
                return '结束学习';
            } else {
                endStudy();
                return '开始学习';
            }
        }
        """
        return js

    # 更新学习时间显示
    def update_study_duration(last_total_time):
        """更新累计学习时长"""
        js = f"""
        () => {{
            document.getElementById('total-duration').textContent = '{last_total_time}';
        }}
        """
        return js

    # 绑定事件处理函数
    subject_area.change(
        fn=update_specific_paths,
        inputs=subject_area,
        outputs=specific_path
    )
    
    generate_path_btn.click(
        fn=generate_learning_path,
        inputs=[subject_area, specific_path, goal_level],
        outputs=[
            path_container,
            current_node_group,
            node_title,
            node_description,
            node_resources
        ]
    )
    
    search_videos_btn.click(
        fn=search_videos,
        inputs=node_title,
        outputs=[
            video_title,
            video_container,
            video_list,
            video_embed
        ]
    )
    
    # 绑定学习控制按钮事件
    study_control.click(
        fn=lambda: "结束学习" if study_control.value == "开始学习" else "开始学习",
        outputs=study_control,
        _js=toggle_study_session()
    )
    
    # 初始化全局变量
    gr.HTML(f"""
    <script>
    // 全局变量
    window.userId = {user_id};
    window.pathId = null;
    window.currentContentId = null;
    window.totalStudyTime = 0;
    
    // 监听路径和内容选择事件
    document.addEventListener('DOMContentLoaded', () => {{
        const pathSelect = document.querySelector('[data-testid="specific_path"]');
        if (pathSelect) {{
            pathSelect.addEventListener('change', (e) => {{
                window.pathId = e.target.value;
            }});
        }}
    }});
    </script>
    """)
    
    return path_container
