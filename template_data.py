TEMPLATE_LIST = [
            ("软件工程", "software_engineering"),
            ("项目管理", "project_management"),
            ("读书笔记", "book_notes"),
            ("头脑风暴", "brainstorming"),
            ("旅游计划", "travel_plan"),
            ("周报总结", "weekly_report"),
            ("课程笔记", "course_notes"),
            ("活动策划", "event_planning"),
            ("组织架构图", "org_chart"),
            ("家族树", "family_tree"),
            ("赛事分析", "match_analysis")
        ]

def get_templates():
    return {
            "software_engineering": {
                "text": "软件工程",
                "style": {
                    "node_bg": "#f0fdf4",
                    "node_border": "#bbf7d0",
                    "root_bg": "#22c55e",
                    "root_border": "#16a34a",
                    "root_text_color": "#ffffff",
                    "text_color": "#14532d",
                    "edge_color": "#86efac",
                    "edge_width": 2,
                    "radius": 4
                },
                "children": [
                    {
                        "text": "需求分析",
                        "children": [{"text": "功能需求"}, {"text": "非功能需求"}, {"text": "用户调研"}]
                    },
                    {
                        "text": "系统设计",
                        "children": [{"text": "架构设计"}, {"text": "数据库设计"}, {"text": "接口文档"}]
                    },
                    {
                        "text": "开发阶段",
                        "children": [{"text": "前端开发"}, {"text": "后端开发"}, {"text": "API联调"}]
                    },
                    {
                        "text": "测试验收",
                        "children": [{"text": "单元测试"}, {"text": "集成测试"}, {"text": "用户验收"}]
                    }
                ]
            },
            "project_management": {
                "text": "项目管理",
                "style": {
                    "node_bg": "#fff7ed",
                    "node_border": "#ffedd5",
                    "root_bg": "#f97316",
                    "root_border": "#ea580c",
                    "root_text_color": "#ffffff",
                    "text_color": "#7c2d12",
                    "edge_color": "#fdba74",
                    "edge_width": 2,
                    "radius": 12
                },
                "children": [
                    {
                        "text": "项目启动",
                        "children": [{"text": "项目目标"}, {"text": "干系人分析"}]
                    },
                    {
                        "text": "项目规划",
                        "children": [{"text": "范围定义"}, {"text": "WBS拆解"}, {"text": "进度计划"}, {"text": "成本预算"}]
                    },
                    {
                        "text": "项目执行",
                        "children": [{"text": "资源分配"}, {"text": "团队沟通"}]
                    },
                    {
                        "text": "项目监控",
                        "children": [{"text": "进度跟踪"}, {"text": "风险控制"}]
                    },
                    {
                        "text": "项目收尾",
                        "children": [{"text": "交付物验收"}, {"text": "复盘总结"}]
                    }
                ]
            },
            "book_notes": {
                "text": "读书笔记",
                "style": {
                    "node_bg": "#fefce8",
                    "node_border": "#fef08a",
                    "root_bg": "#eab308",
                    "root_border": "#ca8a04",
                    "root_text_color": "#ffffff",
                    "text_color": "#713f12",
                    "edge_color": "#fde047",
                    "edge_width": 1,
                    "radius": 0
                },
                "children": [
                    {
                        "text": "书籍信息",
                        "children": [{"text": "书名与作者"}, {"text": "阅读时间"}]
                    },
                    {
                        "text": "核心观点",
                        "children": [{"text": "主旨大意"}, {"text": "重要概念"}]
                    },
                    {
                        "text": "分章摘要",
                        "children": [{"text": "第一部分"}, {"text": "第二部分"}, {"text": "第三部分"}]
                    },
                    {
                        "text": "思考与启发",
                        "children": [{"text": "现实联系"}, {"text": "行动计划"}]
                    }
                ]
            },
            "brainstorming": {
                "text": "头脑风暴",
                "style": {
                    "node_bg": "#faf5ff",
                    "node_border": "#e9d5ff",
                    "root_bg": "#a855f7",
                    "root_border": "#9333ea",
                    "root_text_color": "#ffffff",
                    "text_color": "#581c87",
                    "edge_color": "#d8b4fe",
                    "edge_width": 3,
                    "radius": 20
                },
                "children": [
                    {
                        "text": "核心主题",
                        "children": [{"text": "概念A"}, {"text": "概念B"}, {"text": "概念C"}]
                    },
                    {
                        "text": "目标受众",
                        "children": [{"text": "痛点分析"}, {"text": "期望收益"}]
                    },
                    {
                        "text": "竞争分析",
                        "children": [{"text": "竞品A"}, {"text": "竞品B"}]
                    },
                    {
                        "text": "可行性评估",
                        "children": [{"text": "技术可行性"}, {"text": "成本预估"}, {"text": "风险点"}]
                    }
                ]
            },
            "travel_plan": {
                "text": "旅游计划",
                "style": {
                    "node_bg": "#eff6ff",
                    "node_border": "#bfdbfe",
                    "root_bg": "#3b82f6",
                    "root_border": "#2563eb",
                    "root_text_color": "#ffffff",
                    "text_color": "#1e3a8a",
                    "edge_color": "#93c5fd",
                    "edge_width": 2,
                    "radius": 16
                },
                "children": [
                    {
                        "text": "行前准备",
                        "children": [{"text": "订机票/车票"}, {"text": "预订酒店"}, {"text": "签证办理"}, {"text": "行李打包"}]
                    },
                    {
                        "text": "行程安排",
                        "children": [{"text": "第一天: 到达与周边游"}, {"text": "第二天: 核心景点打卡"}, {"text": "第三天: 购物与返程"}]
                    },
                    {
                        "text": "预算清单",
                        "children": [{"text": "交通费用"}, {"text": "住宿费用"}, {"text": "餐饮与门票"}]
                    },
                    {
                        "text": "注意事项",
                        "children": [{"text": "当地天气"}, {"text": "紧急联系人"}]
                    }
                ]
            },
            "weekly_report": {
                "text": "周报总结",
                "style": {
                    "node_bg": "#f3f4f6",
                    "node_border": "#e5e7eb",
                    "root_bg": "#4b5563",
                    "root_border": "#374151",
                    "root_text_color": "#ffffff",
                    "text_color": "#1f2937",
                    "edge_color": "#9ca3af",
                    "edge_width": 2,
                    "radius": 4
                },
                "children": [
                    {
                        "text": "本周工作完成情况",
                        "children": [{"text": "重点项目A推进"}, {"text": "日常任务清理"}, {"text": "临时需求处理"}]
                    },
                    {
                        "text": "数据与成果",
                        "children": [{"text": "核心指标增长"}, {"text": "交付物清单"}]
                    },
                    {
                        "text": "问题与反思",
                        "children": [{"text": "遇到的阻力"}, {"text": "改进方案"}]
                    },
                    {
                        "text": "下周计划",
                        "children": [{"text": "优先级TOP3事项"}, {"text": "需要协助的支持"}]
                    }
                ]
            },
            "course_notes": {
                "text": "课程笔记",
                "style": {
                    "node_bg": "#fff1f2",
                    "node_border": "#fecdd3",
                    "root_bg": "#e11d48",
                    "root_border": "#be123c",
                    "root_text_color": "#ffffff",
                    "text_color": "#881337",
                    "edge_color": "#fda4af",
                    "edge_width": 1,
                    "radius": 8
                },
                "children": [
                    {
                        "text": "课程背景信息",
                        "children": [{"text": "课程名称/讲师"}, {"text": "学习日期"}]
                    },
                    {
                        "text": "核心知识点",
                        "children": [{"text": "理论一"}, {"text": "理论二"}, {"text": "公式推导"}]
                    },
                    {
                        "text": "案例分析",
                        "children": [{"text": "经典案例拆解"}, {"text": "课后习题记录"}]
                    },
                    {
                        "text": "疑问与解答",
                        "children": [{"text": "不懂的知识盲点"}, {"text": "老师答疑记录"}]
                    }
                ]
            },
            "event_planning": {
                "text": "活动策划",
                "style": {
                    "node_bg": "#f0fdfa",
                    "node_border": "#ccfbf1",
                    "root_bg": "#0d9488",
                    "root_border": "#0f766e",
                    "root_text_color": "#ffffff",
                    "text_color": "#134e4a",
                    "edge_color": "#5eead4",
                    "edge_width": 2,
                    "radius": 12
                },
                "children": [
                    {
                        "text": "活动目标",
                        "children": [{"text": "提升品牌曝光"}, {"text": "拉新转化用户"}]
                    },
                    {
                        "text": "受众分析",
                        "children": [{"text": "核心人群画像"}, {"text": "痛点与吸引力"}]
                    },
                    {
                        "text": "活动方案",
                        "children": [{"text": "线上预热玩法"}, {"text": "线下落地执行"}, {"text": "奖品与激励机制"}]
                    },
                    {
                        "text": "资源盘点",
                        "children": [{"text": "预算申请"}, {"text": "人力分工"}, {"text": "物资采购清单"}]
                    },
                    {
                        "text": "风险预案",
                        "children": [{"text": "天气因素"}, {"text": "流量突增应对"}]
                    }
                ]
            },
            "org_chart": {
                "text": "组织架构",
                "style": {
                    "layout": "vertical",
                    "node_bg": "#f8fafc",
                    "node_border": "#cbd5e1",
                    "root_bg": "#0f172a",
                    "root_border": "#020617",
                    "root_text_color": "#ffffff",
                    "text_color": "#334155",
                    "edge_color": "#94a3b8",
                    "edge_width": 2,
                    "radius": 4
                },
                "children": [
                    {
                        "text": "研发中心",
                        "children": [{"text": "前端组"}, {"text": "后端组"}, {"text": "测试组"}]
                    },
                    {
                        "text": "市场部",
                        "children": [{"text": "新媒体运营"}, {"text": "商务拓展"}]
                    },
                    {
                        "text": "人力资源",
                        "children": [{"text": "招聘专员"}, {"text": "员工关怀"}]
                    }
                ]
            },
            "family_tree": {
                "text": "家族树",
                "style": {
                    "layout": "vertical",
                    "node_bg": "#fffbeb",
                    "node_border": "#fde68a",
                    "root_bg": "#b45309",
                    "root_border": "#78350f",
                    "root_text_color": "#ffffff",
                    "text_color": "#92400e",
                    "edge_color": "#fcd34d",
                    "edge_width": 2,
                    "radius": 20
                },
                "children": [
                    {
                        "text": "大伯一家",
                        "children": [{"text": "堂兄"}, {"text": "堂姐"}]
                    },
                    {
                        "text": "父亲一家",
                        "children": [{"text": "我"}, {"text": "弟弟"}]
                    },
                    {
                        "text": "姑姑一家",
                        "children": [{"text": "表妹"}]
                    }
                ]
            },
            "match_analysis": {
                "text": "赛事分析",
                "style": {
                    "node_bg": ["#c6def1", "#bcf0d3", "#aaf2c8"],
                    "node_border": ["#a8b8d0", "#9ad0b3", "#8ad0a8"],
                    "root_bg": "#c1c9ff",
                    "root_border": "#a3aee6",
                    "root_text_color": "#2c3e50",
                    "text_color": "#2c3e50",
                    "edge_color": "#93a1c8",
                    "edge_width": 2,
                    "radius": 4,
                    "font_family": "Microsoft YaHei",
                    "font_size": 11,
                    "root_font_size": 13,
                    "root_font_weight": "bold"
                },
                "children": [
                    {
                        "text": "哥伦比亚（主场）",
                        "children": [
                            {"text": "2026世界杯参赛队"}, 
                            {"text": "高海拔优势"}, 
                            {"text": "提振士气需求"}, 
                            {
                                "text": "核心阵容",
                                "children": [{"text": "迪亚斯"}, {"text": "J罗"}, {"text": "全主力战意拉满"}]
                            }
                        ]
                    },
                    {
                        "text": "哥斯达黎加（客场）",
                        "children": [
                            {"text": "未晋级世界杯"}, 
                            {"text": "新老交替重建期"}, 
                            {"text": "战意相对有限"}, 
                            {
                                "text": "阵容劣势",
                                "children": [{"text": "纳瓦斯缺席"}, {"text": "博尔赫斯缺席"}, {"text": "平民化锻炼新人"}]
                            }
                        ]
                    },
                    {
                        "text": "比赛关键点",
                        "children": [{"text": "时间：6月2日07:00"}, {"text": "近期状态：双方均表现不佳"}, {"text": "核心目标：磨合阵容与练兵"}]
                    },
                    {
                        "text": "数据分析与预测",
                        "children": [{"text": "哥伦比亚胜（市场信心足）"}, {"text": "两个整数级别让步"}, {"text": "进球预期：4-5次欢呼"}, {"text": "重点关注：40号、41号球员"}]
                    }
                ]
            }
        }
