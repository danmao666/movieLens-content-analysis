from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


PROJECT_DIR = Path(__file__).resolve().parents[1]
RESUME_DIR = PROJECT_DIR / "简历"
OUTPUT_DIR = PROJECT_DIR / "days"
PHOTO_FILE = RESUME_DIR / "证件照_简历版.jpg"

NAME = "张博能"
PHONE = "18974648806"
EMAIL = "1786013324@qq.com"
LOCATION = "湘潭"
EDUCATION = "湖南科技大学｜计算机科学与工程｜本科在读｜预计2028年6月毕业"
ENGLISH = "大学英语六级（CET-6）：504分"


def load_metrics():
    comparison_path = OUTPUT_DIR / "ml_day18_model_comparison.csv"
    pytorch_path = OUTPUT_DIR / "ml_day17_pytorch_metrics.csv"
    if comparison_path.exists():
        comparison = pd.read_csv(comparison_path)
        forest = comparison.loc[
            comparison["model"] == "random_forest_with_enhanced_features"
        ].iloc[0]
        forest_auc = f"{forest['roc_auc']:.3f}"
        forest_f1 = f"{forest['f1']:.3f}"
    else:
        forest_auc, forest_f1 = "0.860", "0.719"
    if pytorch_path.exists():
        pytorch = pd.read_csv(pytorch_path).iloc[0]
        pytorch_auc = f"{pytorch['roc_auc']:.3f}"
    else:
        pytorch_auc = "0.835"
    return forest_auc, forest_f1, pytorch_auc


FOREST_AUC, FOREST_F1, PYTORCH_AUC = load_metrics()


RESUMES = {
    "数据分析": {
        "filename": "张博能_数据分析方向.docx",
        "target": "求职方向：数据分析｜经营分析｜内容分析｜风险分析",
        "summary": (
            "计算机科学与工程本科在读，已使用 SQL、Python 和 Excel 完成公开内容平台数据的端到端分析。"
            "能够进行指标定义、数据清洗、用户/内容分析、留存与异常监控，并使用基础机器学习方法完成预测与误差分析。"
            "希望从数据分析或经营分析初级岗位开始积累真实业务经验。"
        ),
        "project_bullets": [
            "基于 MovieLens 25M 公开数据搭建用户表、内容表、行为表和日期表；使用 DuckDB SQL 完成多表关联、CTE、窗口函数、Top N、留存、漏斗和异常检测。",
            "计算 DAU、新增用户代理、行为次数、活跃内容、D1/D7/D30 留存和内容集中度，使用 Python/pandas/NumPy 完成数据质量检查、EDA 与趋势分析。",
            "使用 Excel 制作 KPI、DAU 趋势、用户分层、内容排名、留存和异常日期看板，并撰写业务问题、指标定义、发现、建议和数据局限报告。",
            f"以用户快照构造未来30天评分活跃代理标签，按时间切分训练/测试集；Random Forest 测试 ROC-AUC 为 {FOREST_AUC}、F1 为 {FOREST_F1}，并完成特征工程、误判样本和数据泄漏检查。",
            "设计用户级推荐策略 A/B 实验方案，定义七日活跃主指标、内容多样性和评分质量护栏指标，说明显著性、置信区间与因果限制。",
            "项目数据为公开数据，评分行为仅作为用户活跃代理；明确区分数据事实、业务假设和待验证结论。",
        ],
        "skills": [
            "SQL：SELECT、JOIN、CTE、子查询、窗口函数、日期函数、留存、漏斗、Top N、移动平均和异常检测。",
            "Python：pandas、NumPy、Matplotlib、Seaborn、scikit-learn；能够完成清洗、EDA、可视化和基础分类模型。",
            "业务分析：DAU、留存、cohort、用户分层、内容表现、频次、集中度、指标波动和 A/B 实验设计。",
            "工具：DuckDB、Excel、JupyterLab、PyCharm、R（dplyr/ggplot2）、PyTorch 基础、PySpark 基础。",
        ],
    },
    "内容增长": {
        "filename": "张博能_内容游戏增长分析方向.docx",
        "target": "求职方向：内容分析｜游戏增长｜用户运营｜产品运营",
        "summary": (
            "计算机科学与工程本科在读，围绕公开内容平台数据完成用户增长、内容表现、留存、分层、推荐策略和 A/B 实验分析。"
            "能够用数据拆解用户活跃变化、识别高覆盖内容、分析 cohort 留存并提出可验证的运营建议，适合内容/游戏增长分析和初级运营分析岗位。"
        ),
        "project_bullets": [
            "以 MovieLens 25M 模拟内容平台业务，围绕“用户为什么不活跃、哪些内容带来高活跃、指标为何波动”建立分析问题和指标字典。",
            "使用 SQL 计算 DAU、用户频次、D1/D7/D30 留存、月度 cohort、内容活跃用户和 Top 10 内容集中度，使用 NTILE 完成用户活动四分位分层。",
            "分析内容类型/Genre、用户活跃分层和 cohort 留存，制作内容排名、用户分层、留存热力图、DAU 趋势和集中度图表。",
            "设计推荐策略 A/B 实验：以用户为分流单位，以七日评分活跃率为主指标，以内容多样性、评分质量、活动频次和数据完整性为护栏指标。",
            "设计异常监控规则，结合环比、28日移动均值、标准差、z-score和行为/内容变化率，形成异常日期与初步排查原因。",
            "使用 Python 完成未来活动代理预测，测试集 Random Forest ROC-AUC 为 {FOREST_AUC}；明确 MovieLens 没有曝光、点击、观看时长和真实实验分流。",
        ],
        "skills": [
            "增长分析：DAU、留存、cohort、用户频次、用户分层、内容活跃度、内容集中度和异常定位。",
            "实验设计：实验假设、用户级分流、主指标、护栏指标、显著性、置信区间、样本量和因果边界。",
            "数据工具：SQL/DuckDB、Python/pandas、Excel Dashboard、Matplotlib、Seaborn、scikit-learn。",
            "基础技术：PyTorch MLP、PySpark groupBy/join/窗口函数、R dplyr/ggplot2。",
        ],
    },
    "AI数据应用": {
        "filename": "张博能_AI数据应用方向.docx",
        "target": "求职方向：AI/数据应用助理｜数据开发助理｜产品/解决方案助理",
        "summary": (
            "计算机科学与工程本科在读，已完成 SQL 数据建模、Python 数据处理、基础机器学习、PyTorch 和 PySpark 项目。"
            "能够将业务问题转化为数据指标和分析流程，完成数据质量检查、模型训练验证、误差分析和结果汇报，适合 AI/数据应用、产品助理和实施支持类初级岗位。"
        ),
        "project_bullets": [
            "使用 DuckDB 建立 MovieLens 25M 数据模型，处理 25,000,095 条评分行为、162,541 个用户和 59,047 个活跃内容，并输出可复用的 SQL 指标表。",
            "使用 pandas/NumPy 完成样本检查、缺失值/重复值/异常值检查、特征构造和可视化；使用 Excel 输出指标看板和分析结果。",
            f"构造未来30天用户评分活跃代理标签，完成 Logistic Regression、PyTorch MLP 和 Random Forest 对比；PyTorch 测试 ROC-AUC 为 {PYTORCH_AUC}，并保存训练/验证记录和模型权重。",
            f"完成特征工程、误判样本、特征重要性和数据泄漏审计；Random Forest 测试 ROC-AUC 为 {FOREST_AUC}，F1 为 {FOREST_F1}。",
            "使用 PySpark 完成可复现抽样数据的 groupBy、join、窗口排名、分区和物理计划分析；能够解释 Shuffle、分区和本地内存限制。",
            "使用 MovieLens tags 完成 TF-IDF + Logistic Regression 文本分类基线，了解 Tokenization、Embedding、Self-Attention 和 Transformer 基本概念。",
        ],
        "skills": [
            "Python：pandas、NumPy、Matplotlib、Seaborn、scikit-learn、PyTorch 基础、PySpark 基础。",
            "SQL：DuckDB、CTE、窗口函数、数据质量检查、指标计算、留存和异常检测。",
            "机器学习：分类、时间切分、特征工程、类别不平衡、ROC-AUC/F1、误判分析和数据泄漏检查。",
            "应用能力：需求拆解、指标定义、Excel 看板、项目报告、A/B 实验方案和技术结果表达。",
        ],
    },
}


def set_run_font(run, size=10.5, bold=False, color=None):
    run.font.name = "Microsoft YaHei"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)


def set_paragraph_spacing(paragraph, before=0, after=3, line=1.05):
    format_ = paragraph.paragraph_format
    format_.space_before = Pt(before)
    format_.space_after = Pt(after)
    format_.line_spacing = line


def add_section_heading(document, text):
    paragraph = document.add_paragraph()
    set_paragraph_spacing(paragraph, before=7, after=3, line=1)
    run = paragraph.add_run(text)
    set_run_font(run, size=11.5, bold=True, color=(31, 78, 121))
    return paragraph


def add_bullet(document, text):
    paragraph = document.add_paragraph(style="List Bullet")
    paragraph.paragraph_format.left_indent = Cm(0.45)
    paragraph.paragraph_format.first_line_indent = Cm(-0.2)
    set_paragraph_spacing(paragraph, after=2, line=1.03)
    run = paragraph.add_run(text)
    set_run_font(run, size=9.5)
    return paragraph


def remove_table_borders(table):
    table_properties = table._tbl.tblPr
    borders = table_properties.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        table_properties.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = "w:" + edge
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "nil")


def add_header(document, target):
    table = document.add_table(rows=1, cols=2)
    table.autofit = False
    table.columns[0].width = Cm(14.5)
    table.columns[1].width = Cm(3.2)
    remove_table_borders(table)

    left_cell, right_cell = table.rows[0].cells
    left_cell.width = Cm(14.5)
    right_cell.width = Cm(3.2)

    name = left_cell.paragraphs[0]
    name.alignment = WD_ALIGN_PARAGRAPH.LEFT
    set_paragraph_spacing(name, after=2, line=1)
    run = name.add_run(NAME)
    set_run_font(run, size=20, bold=True, color=(31, 78, 121))

    contact = left_cell.add_paragraph()
    set_paragraph_spacing(contact, after=2, line=1)
    contact_run = contact.add_run(
        f"男｜{PHONE}｜{EMAIL}｜现居：{LOCATION}"
    )
    set_run_font(contact_run, size=9.5)

    target_paragraph = left_cell.add_paragraph()
    set_paragraph_spacing(target_paragraph, after=3, line=1)
    target_run = target_paragraph.add_run(target)
    set_run_font(target_run, size=10.5, bold=True, color=(89, 89, 89))

    photo_paragraph = right_cell.paragraphs[0]
    photo_paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_paragraph_spacing(photo_paragraph, after=0, line=1)
    if PHOTO_FILE.exists():
        photo_paragraph.add_run().add_picture(
            str(PHOTO_FILE),
            width=Cm(2.8),
            height=Cm(3.6),
        )
    else:
        placeholder = photo_paragraph.add_run("证件照")
        set_run_font(placeholder, size=9, color=(128, 128, 128))

    spacer = document.add_paragraph()
    set_paragraph_spacing(spacer, after=1, line=1)


def add_resume(title, config):
    document = Document()
    section = document.sections[0]
    section.top_margin = Cm(1.15)
    section.bottom_margin = Cm(1.05)
    section.left_margin = Cm(1.55)
    section.right_margin = Cm(1.55)

    normal = document.styles["Normal"]
    normal.font.name = "Microsoft YaHei"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    normal.font.size = Pt(9.5)

    add_header(document, config["target"])

    add_section_heading(document, "教育背景")
    education = document.add_paragraph()
    set_paragraph_spacing(education, after=3, line=1.05)
    education_run = education.add_run(EDUCATION)
    set_run_font(education_run, size=10, bold=True)

    add_section_heading(document, "个人简介")
    summary = document.add_paragraph()
    set_paragraph_spacing(summary, after=3, line=1.08)
    summary_run = summary.add_run(config["summary"])
    set_run_font(summary_run, size=9.5)

    add_section_heading(document, "项目经历")
    project_title = document.add_paragraph()
    set_paragraph_spacing(project_title, after=2, line=1)
    project_run = project_title.add_run(
        "泛文娱内容平台增长与推荐分析｜MovieLens 25M公开数据模拟项目"
    )
    set_run_font(project_run, size=10.5, bold=True)
    for bullet in config["project_bullets"]:
        add_bullet(document, bullet)

    add_section_heading(document, "专业技能")
    for skill in config["skills"]:
        add_bullet(document, skill)

    add_section_heading(document, "英语能力")
    english = document.add_paragraph()
    set_paragraph_spacing(english, after=2, line=1)
    english_run = english.add_run(ENGLISH)
    set_run_font(english_run, size=9.5)

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_run = footer.add_run(
        "公开数据项目｜项目结果不代表真实公司业务成果"
    )
    set_run_font(footer_run, size=8, color=(128, 128, 128))

    path = RESUME_DIR / config["filename"]
    document.save(path)
    return path


def main():
    RESUME_DIR.mkdir(parents=True, exist_ok=True)
    generated = []
    for title, config in RESUMES.items():
        path = add_resume(title, config)
        generated.append(path.name)

    readme = """# 简历文件说明

已根据张博能提供的信息生成三版简历：

- `张博能_数据分析方向.docx`
- `张博能_内容游戏增长分析方向.docx`
- `张博能_AI数据应用方向.docx`

基本信息：湖南科技大学计算机科学与工程本科在读，预计2028年6月毕业，英语六级504分。

投递前请检查：

1. 目标岗位是否接受2028届学生。
2. 项目指标是否与 `days` 目录中的真实结果一致。
3. 是否需要补充照片、籍贯、政治面貌等学校模板要求。
4. 不要把公开数据模拟项目写成真实公司实习经历。
"""
    (RESUME_DIR / "README.md").write_text(readme, encoding="utf-8")
    print("Generated:")
    for filename in generated:
        print(RESUME_DIR / filename)


if __name__ == "__main__":
    main()
