"""
内容质量评估模块
评估文章的质量、原创性、技术深度、可读性等指标
"""

import re
import math
from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from storage.database import DatabaseManager
from utils.logger import logger


@dataclass
class QualityMetrics:
    """质量评估指标"""
    overall_score: float
    originality_score: float
    technical_depth_score: float
    readability_score: float
    structure_score: float
    engagement_score: float
    completeness_score: float


@dataclass
class ContentAnalysis:
    """内容分析结果"""
    article_id: str
    quality_metrics: QualityMetrics
    word_count: int
    reading_time: int  # 预估阅读时间（分钟）
    key_points: List[str]
    improvement_suggestions: List[str]
    quality_grade: str  # A, B, C, D


class ContentEvaluator:
    """内容质量评估器"""
    
    def __init__(self, use_mongodb: bool = False):
        self.db = DatabaseManager(use_mongodb=use_mongodb)
        self.initialize_evaluation_criteria()
    
    def initialize_evaluation_criteria(self):
        """初始化评估标准"""
        # 技术深度指示词
        self.technical_indicators = {
            "high": [
                'implementation', 'algorithm', 'architecture', 'source code',
                'performance', 'optimization', 'benchmark', 'internals',
                'deep dive', 'analysis', 'research', 'paper',
                '实现', '算法', '架构', '源码', '性能', '优化', '基准测试',
                '内部原理', '深入分析', '研究', '论文'
            ],
            "medium": [
                'configuration', 'setup', 'integration', 'workflow',
                'best practices', 'comparison', 'review', 'case study',
                '配置', '集成', '工作流', '最佳实践', '对比', '评测', '案例研究'
            ],
            "low": [
                'tutorial', 'getting started', 'introduction', 'basic',
                'overview', 'summary', 'news', 'announcement',
                '教程', '入门', '介绍', '基础', '概述', '总结', '新闻', '公告'
            ]
        }
        
        # 结构化内容指示词
        self.structure_indicators = [
            r'#+\s+',  # Markdown 标题
            r'\d+\.\s+',  # 数字列表
            r'[-*]\s+',  # 无序列表
            r'```[\s\S]*?```',  # 代码块
            r'`[^`]+`',  # 内联代码
            r'\[.*?\]\(.*?\)',  # 链接
            r'!\[.*?\]\(.*?\)',  # 图片
        ]
        
        # 原创性关键词（通常表明是转载或引用）
        self.non_original_indicators = [
            '转载', '来源', '原文链接', '出处', '转自', '引用',
            'source:', 'original:', 'from:', 'via:', 'reposted',
            '本文转载自', '文章来源', '原文地址'
        ]
        
        # 参与度指示词
        self.engagement_indicators = [
            '你觉得', '你认为', '大家', '我们一起', '讨论', '交流',
            '留言', '评论', '分享', '点赞', 'what do you think',
            'let me know', 'share your thoughts', 'comment below'
        ]
    
    def calculate_readability_score(self, content: str) -> float:
        """计算可读性评分"""
        if not content:
            return 0.0
        
        # 去除代码块和特殊符号
        clean_content = re.sub(r'```[\s\S]*?```', '', content)
        clean_content = re.sub(r'`[^`]+`', '', clean_content)
        clean_content = re.sub(r'[^\u4e00-\u9fff\w\s.,!?;:]', ' ', clean_content)
        
        # 分词（中英文混合）
        sentences = re.split(r'[.!?。！？]', clean_content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
        
        # 计算平均句长
        total_words = 0
        for sentence in sentences:
            # 中文按字符计算，英文按单词计算
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', sentence))
            english_words = len(re.findall(r'\b[a-zA-Z]+\b', sentence))
            total_words += chinese_chars + english_words
        
        avg_sentence_length = total_words / len(sentences)
        
        # 可读性评分（基于平均句长，适中的句长得分最高）
        if 10 <= avg_sentence_length <= 25:
            readability = 1.0
        elif 5 <= avg_sentence_length <= 35:
            readability = 0.8
        elif avg_sentence_length <= 50:
            readability = 0.6
        else:
            readability = 0.4
        
        # 段落分布评分
        paragraphs = content.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        if len(paragraphs) > 1:
            avg_paragraph_length = len(content) / len(paragraphs)
            if 200 <= avg_paragraph_length <= 800:
                paragraph_score = 1.0
            elif 100 <= avg_paragraph_length <= 1200:
                paragraph_score = 0.8
            else:
                paragraph_score = 0.6
        else:
            paragraph_score = 0.5  # 单段落文章可读性较差
        
        return (readability * 0.7 + paragraph_score * 0.3)
    
    def calculate_technical_depth(self, title: str, content: str) -> float:
        """计算技术深度评分"""
        text = f"{title} {content}".lower()
        
        depth_scores = {"high": 0, "medium": 0, "low": 0}
        
        for level, indicators in self.technical_indicators.items():
            for indicator in indicators:
                if indicator.lower() in text:
                    depth_scores[level] += 1
        
        # 代码块数量也是技术深度的指标
        code_blocks = len(re.findall(r'```[\s\S]*?```', content))
        inline_code = len(re.findall(r'`[^`]+`', content))
        
        if code_blocks > 5 or inline_code > 20:
            depth_scores["high"] += 2
        elif code_blocks > 2 or inline_code > 10:
            depth_scores["medium"] += 1
        
        # 技术术语密度
        total_words = len(text.split())
        if total_words > 0:
            tech_density = (depth_scores["high"] * 3 + depth_scores["medium"] * 2 + depth_scores["low"]) / total_words
            if tech_density > 0.1:
                depth_scores["high"] += 1
            elif tech_density > 0.05:
                depth_scores["medium"] += 1
        
        # 计算最终评分
        total_score = depth_scores["high"] * 3 + depth_scores["medium"] * 2 + depth_scores["low"]
        max_possible = max(total_score, 10)  # 设置最大可能分数
        
        return min(total_score / max_possible, 1.0)
    
    def calculate_originality_score(self, content: str) -> float:
        """计算原创性评分"""
        if not content:
            return 0.0
        
        # 检查非原创指示词
        non_original_count = 0
        for indicator in self.non_original_indicators:
            if indicator in content:
                non_original_count += 1
        
        # 原创性基础分数
        originality = 1.0 - (non_original_count * 0.2)
        
        # 检查内容重复度（简单的重复句子检测）
        sentences = re.split(r'[.!?。！？]', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        if len(sentences) > 1:
            unique_sentences = set(sentences)
            repetition_rate = 1 - (len(unique_sentences) / len(sentences))
            originality -= repetition_rate * 0.3
        
        # 检查是否包含大量链接（可能是聚合内容）
        links = re.findall(r'https?://[^\s]+', content)
        if len(links) > 10:
            originality -= 0.2
        
        return max(originality, 0.0)
    
    def calculate_structure_score(self, content: str) -> float:
        """计算结构化评分"""
        if not content:
            return 0.0
        
        structure_elements = 0
        
        for pattern in self.structure_indicators:
            matches = re.findall(pattern, content)
            if pattern.startswith(r'#+'):  # 标题权重更高
                structure_elements += len(matches) * 2
            else:
                structure_elements += len(matches)
        
        # 内容长度归一化
        content_length = len(content)
        if content_length > 0:
            structure_density = structure_elements / (content_length / 1000)  # 每1000字符的结构元素数
            return min(structure_density / 5, 1.0)  # 最高评分为1.0
        
        return 0.0
    
    def calculate_engagement_score(self, title: str, content: str) -> float:
        """计算参与度评分"""
        text = f"{title} {content}".lower()
        
        engagement_count = 0
        for indicator in self.engagement_indicators:
            if indicator in text:
                engagement_count += 1
        
        # 问句数量（增加参与度）
        questions = len(re.findall(r'[?？]', content))
        engagement_count += min(questions / 3, 2)  # 最多加2分
        
        # 归一化评分
        return min(engagement_count / 5, 1.0)
    
    def calculate_completeness_score(self, title: str, content: str) -> float:
        """计算完整性评分"""
        completeness = 0.0
        
        # 标题完整性
        if title and len(title.strip()) > 5:
            completeness += 0.2
        
        # 内容长度评分
        content_length = len(content)
        if content_length > 2000:
            completeness += 0.4
        elif content_length > 1000:
            completeness += 0.3
        elif content_length > 500:
            completeness += 0.2
        elif content_length > 100:
            completeness += 0.1
        
        # 结论或总结
        if any(keyword in content.lower() for keyword in ['conclusion', 'summary', '总结', '结论', '小结']):
            completeness += 0.2
        
        # 示例代码或图片
        has_code = bool(re.search(r'```[\s\S]*?```', content))
        has_images = bool(re.search(r'!\[.*?\]\(.*?\)', content))
        
        if has_code:
            completeness += 0.1
        if has_images:
            completeness += 0.1
        
        return min(completeness, 1.0)
    
    def extract_key_points(self, content: str, max_points: int = 5) -> List[str]:
        """提取文章要点"""
        if not content:
            return []
        
        key_points = []
        
        # 提取标题作为要点
        headers = re.findall(r'#+\s+(.+)', content)
        key_points.extend(headers[:max_points])
        
        # 提取列表项
        if len(key_points) < max_points:
            list_items = re.findall(r'(?:[-*]\s+|^\d+\.\s+)(.+)', content, re.MULTILINE)
            remaining = max_points - len(key_points)
            key_points.extend(list_items[:remaining])
        
        # 提取包含关键技术词汇的句子
        if len(key_points) < max_points:
            sentences = re.split(r'[.!?。！？]', content)
            tech_sentences = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 20 and len(sentence) < 200:
                    # 检查是否包含技术关键词
                    if any(tech in sentence.lower() for tech in ['api', 'framework', 'library', 'algorithm', '算法', '框架', '接口']):
                        tech_sentences.append(sentence)
            
            remaining = max_points - len(key_points)
            key_points.extend(tech_sentences[:remaining])
        
        return key_points[:max_points]
    
    def generate_improvement_suggestions(self, metrics: QualityMetrics, content_length: int) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        if metrics.readability_score < 0.6:
            suggestions.append("考虑缩短句子长度，增加段落分隔，提高可读性")
        
        if metrics.technical_depth_score < 0.5:
            suggestions.append("增加技术细节，提供更多代码示例或实现原理")
        
        if metrics.structure_score < 0.5:
            suggestions.append("添加标题、列表、代码块等结构化元素")
        
        if metrics.originality_score < 0.7:
            suggestions.append("增加原创观点和个人见解，减少直接引用")
        
        if metrics.engagement_score < 0.4:
            suggestions.append("增加互动元素，如问题、讨论点或实践建议")
        
        if content_length < 500:
            suggestions.append("扩展内容深度，提供更详细的解释和示例")
        elif content_length > 5000:
            suggestions.append("考虑拆分长文章，或添加目录导航")
        
        if metrics.completeness_score < 0.7:
            suggestions.append("添加总结部分，确保内容完整性")
        
        return suggestions
    
    def evaluate_article_quality(self, article: Dict[str, Any]) -> ContentAnalysis:
        """评估单篇文章质量"""
        article_id = str(article.get('id', ''))
        title = article.get('title', '')
        content = article.get('content', '')
        
        # 计算各项评分
        readability_score = self.calculate_readability_score(content)
        technical_depth_score = self.calculate_technical_depth(title, content)
        originality_score = self.calculate_originality_score(content)
        structure_score = self.calculate_structure_score(content)
        engagement_score = self.calculate_engagement_score(title, content)
        completeness_score = self.calculate_completeness_score(title, content)
        
        # 计算综合评分（加权平均）
        weights = {
            'technical_depth': 0.25,
            'originality': 0.20,
            'completeness': 0.20,
            'readability': 0.15,
            'structure': 0.15,
            'engagement': 0.05
        }
        
        overall_score = (
            technical_depth_score * weights['technical_depth'] +
            originality_score * weights['originality'] +
            completeness_score * weights['completeness'] +
            readability_score * weights['readability'] +
            structure_score * weights['structure'] +
            engagement_score * weights['engagement']
        )
        
        # 创建质量指标对象
        quality_metrics = QualityMetrics(
            overall_score=overall_score,
            originality_score=originality_score,
            technical_depth_score=technical_depth_score,
            readability_score=readability_score,
            structure_score=structure_score,
            engagement_score=engagement_score,
            completeness_score=completeness_score
        )
        
        # 计算其他指标
        word_count = len(content)
        reading_time = max(1, word_count // 200)  # 假设200字/分钟的阅读速度
        
        key_points = self.extract_key_points(content)
        improvement_suggestions = self.generate_improvement_suggestions(quality_metrics, word_count)
        
        # 确定质量等级
        if overall_score >= 0.8:
            quality_grade = "A"
        elif overall_score >= 0.6:
            quality_grade = "B"
        elif overall_score >= 0.4:
            quality_grade = "C"
        else:
            quality_grade = "D"
        
        return ContentAnalysis(
            article_id=article_id,
            quality_metrics=quality_metrics,
            word_count=word_count,
            reading_time=reading_time,
            key_points=key_points,
            improvement_suggestions=improvement_suggestions,
            quality_grade=quality_grade
        )
    
    def batch_evaluate_quality(self, limit: int = None) -> Dict[str, Any]:
        """批量评估文章质量"""
        logger.info("开始批量质量评估")
        
        try:
            # 获取文章数据
            if self.db.use_mongodb:
                query = {}
                if limit:
                    articles = list(self.db.articles_collection.find(query).limit(limit))
                else:
                    articles = list(self.db.articles_collection.find(query))
            else:
                with self.db.get_session() as session:
                    from storage.models import ArticleDB
                    query = session.query(ArticleDB)
                    if limit:
                        query = query.limit(limit)
                    articles = query.all()
                    articles = [article.to_dict() for article in articles]
            
            if not articles:
                return {"error": "没有找到文章数据"}
            
            # 评估每篇文章
            evaluations = []
            quality_stats = {"A": 0, "B": 0, "C": 0, "D": 0}
            metric_totals = defaultdict(float)
            
            for article in articles:
                try:
                    analysis = self.evaluate_article_quality(article)
                    evaluations.append(analysis)
                    
                    # 统计质量等级分布
                    quality_stats[analysis.quality_grade] += 1
                    
                    # 累计各项指标
                    metric_totals["overall"] += analysis.quality_metrics.overall_score
                    metric_totals["originality"] += analysis.quality_metrics.originality_score
                    metric_totals["technical_depth"] += analysis.quality_metrics.technical_depth_score
                    metric_totals["readability"] += analysis.quality_metrics.readability_score
                    metric_totals["structure"] += analysis.quality_metrics.structure_score
                    metric_totals["engagement"] += analysis.quality_metrics.engagement_score
                    metric_totals["completeness"] += analysis.quality_metrics.completeness_score
                    
                except Exception as e:
                    logger.warning(f"评估文章 {article.get('id', 'unknown')} 时出错: {str(e)}")
                    continue
            
            # 计算平均值
            total_evaluated = len(evaluations)
            avg_metrics = {
                metric: round(total / total_evaluated, 3)
                for metric, total in metric_totals.items()
            } if total_evaluated > 0 else {}
            
            # 生成总结报告
            summary = {
                "total_articles": len(articles),
                "successfully_evaluated": total_evaluated,
                "quality_distribution": quality_stats,
                "average_metrics": avg_metrics,
                "quality_insights": {
                    "high_quality_rate": round((quality_stats["A"] + quality_stats["B"]) / total_evaluated * 100, 1) if total_evaluated > 0 else 0,
                    "needs_improvement_rate": round(quality_stats["D"] / total_evaluated * 100, 1) if total_evaluated > 0 else 0,
                    "average_word_count": round(sum(eval.word_count for eval in evaluations) / total_evaluated, 0) if total_evaluated > 0 else 0,
                    "average_reading_time": round(sum(eval.reading_time for eval in evaluations) / total_evaluated, 1) if total_evaluated > 0 else 0
                },
                "evaluation_time": datetime.now().isoformat()
            }
            
            return {
                "summary": summary,
                "evaluations": [
                    {
                        "article_id": eval.article_id,
                        "quality_grade": eval.quality_grade,
                        "overall_score": round(eval.quality_metrics.overall_score, 3),
                        "word_count": eval.word_count,
                        "reading_time": eval.reading_time,
                        "key_points": eval.key_points[:3],  # 只返回前3个要点
                        "improvement_count": len(eval.improvement_suggestions),
                        "metrics": {
                            "originality": round(eval.quality_metrics.originality_score, 3),
                            "technical_depth": round(eval.quality_metrics.technical_depth_score, 3),
                            "readability": round(eval.quality_metrics.readability_score, 3),
                            "structure": round(eval.quality_metrics.structure_score, 3),
                            "engagement": round(eval.quality_metrics.engagement_score, 3),
                            "completeness": round(eval.quality_metrics.completeness_score, 3)
                        }
                    }
                    for eval in evaluations[:50]  # 返回前50个结果
                ]
            }
            
        except Exception as e:
            logger.error(f"批量质量评估失败: {str(e)}")
            return {"error": str(e)}
        finally:
            self.db.close()
    
    def get_quality_insights(self, min_quality_score: float = 0.0) -> Dict[str, Any]:
        """获取质量洞察报告"""
        try:
            evaluation_results = self.batch_evaluate_quality()
            
            if "error" in evaluation_results:
                return evaluation_results
            
            evaluations = evaluation_results["evaluations"]
            high_quality_articles = [
                eval for eval in evaluations 
                if eval["overall_score"] >= min_quality_score
            ]
            
            # 分析高质量文章的特征
            if high_quality_articles:
                avg_word_count = sum(eval["word_count"] for eval in high_quality_articles) / len(high_quality_articles)
                common_patterns = []
                
                # 分析高质量文章的模式
                if avg_word_count > 1500:
                    common_patterns.append("高质量文章通常篇幅较长，内容详实")
                
                high_structure_rate = sum(1 for eval in high_quality_articles if eval["metrics"]["structure"] > 0.7) / len(high_quality_articles)
                if high_structure_rate > 0.6:
                    common_patterns.append("高质量文章普遍具有良好的结构化")
                
                insights = {
                    "high_quality_characteristics": {
                        "average_word_count": round(avg_word_count, 0),
                        "common_patterns": common_patterns,
                        "sample_count": len(high_quality_articles)
                    },
                    "improvement_recommendations": [
                        "增加内容深度和技术细节",
                        "改善文章结构和可读性",
                        "提高原创性和个人观点",
                        "增加实践示例和代码"
                    ]
                }
            else:
                insights = {"message": "未找到符合标准的高质量文章"}
            
            return {
                "quality_insights": insights,
                "evaluation_summary": evaluation_results["summary"]
            }
            
        except Exception as e:
            logger.error(f"质量洞察分析失败: {str(e)}")
            return {"error": str(e)}